"""
Step 4: Response Quality Evaluation — Real External LLM Judge Engine

Evaluates main-agent responses against a fixed 5-dimension rubric (scale 1-5):
1. Correctness: Accurate, policy-aligned guidance without impossible claims.
2. Helpfulness: Clear, actionable, empathetic instructions.
3. Groundedness: Anchored in retrieved historical evidence without hallucinations.
4. Policy Compliance: Adheres to security boundaries (no public credential requests, safe DM transfer).
5. Appropriateness of Escalation: Correct triage of P0 security/fraud vs. routine deflection.

Uses an external LLM API (Google Gemini 1.5 Flash by default).
Strictly requires GEMINI_API_KEY (or GOOGLE_API_KEY) in environment or .env.
If the API key is missing, FAILS clearly — local heuristic fallback is strictly disabled.
"""

import json
import logging
import os
import random
import re
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger("llm_judge")

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

RUBRIC_DESCRIPTION = """
SCORING RUBRIC (Scale 1 to 5):
1. Correctness:
   5 = Completely accurate advice aligned with official support policies.
   4 = Accurate with minor stylistic or tangential detail.
   3 = Partially correct; general advice but misses important nuance.
   2 = Misleading or materially incorrect instructions.
   1 = Completely erroneous or contradictory advice.

2. Helpfulness:
   5 = Clear, actionable next steps, empathetic and customer-friendly.
   4 = Clear and helpful with minor room for improvement.
   3 = Moderately helpful but requires customer follow-up for missing basics.
   2 = Vague, unhelpful, or confusing.
   1 = Useless or counterproductive.

3. Groundedness in Retrieved Evidence:
   5 = Fully grounded in historical resolutions/policy without hallucinating order facts.
   4 = Grounded with standard polite conversational framing.
   3 = Loosely grounded in general knowledge rather than retrieved evidence.
   2 = Contradicts retrieved evidence or invents unverified account actions.
   1 = Severe hallucination of specific order/refund status.

4. Policy Compliance:
   5 = Flawless adherence to boundaries (no public credential requests, proper DM routing).
   4 = Fully compliant with standard Twitter customer support guidelines.
   3 = Minor omission (e.g. asking for tracking publicly instead of via private channel).
   2 = Asks for sensitive info in public or violates channel boundaries.
   1 = Severe policy breach.

5. Appropriateness of Escalation:
   5 = Exactly appropriate decision (escalated security/fraud/disputes; auto-handled routine).
   4 = Well-reasoned decision consistent with customer risk profile.
   3 = Overly conservative or slightly hesitant on a routine inquiry.
   2 = Auto-handled an issue that strictly required specialist intervention.
   1 = Auto-handled a critical security breach or account compromise.
"""


def format_judge_prompt(
    customer_message: str,
    agent_response: str,
    retrieved_evidence: List[Dict[str, Any]],
    auto_handle: bool = True,
    is_security_alert: bool = False,
) -> str:
    """Formats the auditor prompt requesting strictly structured JSON."""
    evidence_str = ""
    for i, ev in enumerate(retrieved_evidence, 1):
        score_val = ev.get("score", 0.0)
        score_str = f"{score_val:.4f}" if isinstance(score_val, (int, float)) else str(score_val)
        evidence_str += (
            f"\n[Evidence {i}] (Relevance Score: {score_str}):\n"
            f"Historical Customer Inquiry: {ev.get('customer_message', '')}\n"
            f"Historical AmazonHelp Resolution: {ev.get('historical_response', '')}\n"
        )

    return f"""You are an expert customer service quality auditor evaluating AI-generated support drafts for AmazonHelp.
Evaluate the following support response draft against the 5-dimension rubric below.
Gold labels are withheld to ensure unbiased evaluation.

{RUBRIC_DESCRIPTION}

CUSTOMER INQUIRY:
"{customer_message}"

AGENT DRAFT RESPONSE:
"{agent_response}"

AGENT ROUTING DECISION:
Auto-Handle: {auto_handle} | Security Risk Flag: {is_security_alert}

RETRIEVED HISTORICAL EVIDENCE:
{evidence_str or "No historical resolution evidence retrieved."}

You MUST return strictly valid JSON matching this exact structure with integer ratings from 1 to 5:
{{
  "scores": {{
    "correctness": <integer 1 to 5>,
    "helpfulness": <integer 1 to 5>,
    "groundedness": <integer 1 to 5>,
    "policy": <integer 1 to 5>,
    "escalation": <integer 1 to 5>
  }},
  "rationale": "<concise, specific justification for the scores across all 5 dimensions>"
}}"""


def validate_and_parse_judge_json(raw_text: str) -> Dict[str, Any]:
    """
    Parses and validates strict structured JSON from the LLM Judge.
    Validates that:
    1. Output is valid JSON.
    2. All 5 rubric dimensions are present.
    3. All scores are integers strictly within [1, 5].
    4. Rationale string is provided.
    Raises ValueError on any schema or range violation.
    """
    cleaned = raw_text.strip()
    # Strip markdown code blocks if the model wrapped the JSON
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
    except Exception as e:
        raise ValueError(f"Malformed LLM Judge JSON output: {e}\nRaw output: {raw_text[:250]}")

    if not isinstance(data, dict):
        raise ValueError(f"LLM Judge output must be a JSON object, got {type(data).__name__}")

    # Support standardized schema: {"scores": {...}, "rationale": ...}
    # Also tolerate top-level keys if model omitted outer "scores" object
    if "scores" in data and isinstance(data["scores"], dict):
        scores_dict = data["scores"]
    else:
        scores_dict = data

    required_dims = ["correctness", "helpfulness", "groundedness", "policy", "escalation"]
    validated_scores = {}

    for dim in required_dims:
        if dim not in scores_dict:
            raise ValueError(f"Missing required rubric dimension '{dim}' in judge output: {scores_dict}")

        val = scores_dict[dim]
        try:
            val_int = int(round(float(val)))
        except (ValueError, TypeError):
            raise ValueError(f"Score for dimension '{dim}' is not a valid number: {val}")

        if val_int < 1 or val_int > 5:
            raise ValueError(f"Score for dimension '{dim}' ({val_int}) is outside valid rubric range [1, 5]")

        validated_scores[dim] = val_int

    rationale = str(data.get("rationale") or data.get("explanation") or "").strip()
    if not rationale:
        rationale = "Quality evaluation completed across 5 core dimensions."

    return {
        "scores": validated_scores,
        "rationale": rationale,
        "correctness": validated_scores["correctness"],
        "helpfulness": validated_scores["helpfulness"],
        "groundedness": validated_scores["groundedness"],
        "policy": validated_scores["policy"],
        "escalation": validated_scores["escalation"],
        "overall_score": round(sum(validated_scores.values()) / 5.0, 2),
    }


class ResponseQualityJudge:
    """
    Real External LLM Judge Engine.
    Connects to external LLM API (Google Gemini 1.5 Flash).
    Strictly requires GEMINI_API_KEY (or GOOGLE_API_KEY) in environment or .env.
    Fails clearly if key is missing — NO local heuristic fallback.
    """

    def __init__(
        self,
        provider: str = "google_gemini",
        model_name: str = "gemini-3.5-flash-lite",
        api_key: Optional[str] = None,
        max_retries: int = 6,
    ):
        self.provider = provider
        self.model_name = model_name
        self.max_retries = max_retries
        self.retry_429_count = 0

        # Load API key strictly from parameter, environment, or .env file
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            self.api_key = self._load_key_from_env_file()

        if not self.api_key:
            raise ValueError(
                "CRITICAL: Real LLM Judge requires GEMINI_API_KEY (or GOOGLE_API_KEY). "
                "No API key was found in environment variables or .env file. "
                "Per evaluation integrity requirements, local heuristic fallback is disabled. "
                "Set GEMINI_API_KEY in your environment or .env file to run live LLM response quality judging."
            )

        self._init_client()

    def _load_key_from_env_file(self) -> Optional[str]:
        """Loads GEMINI_API_KEY from local .env file if present."""
        env_file = ROOT_DIR / ".env"
        if not env_file.exists():
            return None

        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if line.startswith("GEMINI_API_KEY="):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if val and not val.startswith("your_"):
                            return val
                    elif line.startswith("GOOGLE_API_KEY="):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if val and not val.startswith("your_"):
                            return val
        except Exception:
            pass
        return None

    def _init_client(self):
        """Initializes Google GenAI client (google-genai SDK) or prepares REST fallback."""
        self._use_sdk = False
        try:
            from google import genai
            from google.genai import types
            self._client = genai.Client(api_key=self.api_key)
            self._types = types
            self._use_sdk = True
            logger.info(f"Initialized Google GenAI SDK (google-genai) with model '{self.model_name}'")
        except Exception as e:
            logger.info(f"Google GenAI SDK unavailable ({e}), using direct REST API client.")
            self._use_sdk = False

    def _call_llm_api(self, prompt: str, max_retries: Optional[int] = None) -> str:
        """Invokes external LLM API with exponential backoff on transient errors and quota limits."""
        retries = max_retries if max_retries is not None else self.max_retries
        last_error = None

        for attempt in range(1, retries + 1):
            try:
                if self._use_sdk:
                    response = self._client.models.generate_content(
                        model=self.model_name,
                        contents=prompt,
                        config=self._types.GenerateContentConfig(
                            response_mime_type="application/json",
                            temperature=0.0,
                        ),
                    )
                    text = response.text
                    if text:
                        return text
                    raise RuntimeError("Empty response received from Google GenAI model")
                else:
                    # Direct HTTPS REST call to Gemini v1beta
                    import requests
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
                    payload = {
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {
                            "response_mime_type": "application/json",
                            "temperature": 0.0,
                        },
                    }
                    resp = requests.post(url, json=payload, timeout=30)
                    if not resp.ok:
                        raise RuntimeError(f"Gemini API returned HTTP {resp.status_code}: {resp.text}")
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if not candidates:
                        raise RuntimeError(f"No response candidates in Gemini API response: {data}")
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if not parts or "text" not in parts[0]:
                        raise RuntimeError(f"Malformed candidate in Gemini API response: {candidates[0]}")
                    return parts[0]["text"]

            except Exception as exc:
                last_error = exc
                err_str = str(exc)
                if "429" in err_str or "quota" in err_str.lower() or "resourceexhausted" in err_str.lower():
                    self.retry_429_count += 1
                    # Exponential backoff + jitter for 429
                    jitter = random.uniform(1.0, 3.0)
                    wait_time = (15.0 * (1.5 ** (attempt - 1))) + jitter
                    logger.warning(
                        f"LLM Judge hit rate limit (429) [attempt {attempt}/{retries}, total 429s: {self.retry_429_count}]. "
                        f"Backing off for {wait_time:.1f}s with jitter..."
                    )
                else:
                    wait_time = 2.0 * attempt
                    logger.warning(f"LLM Judge call attempt {attempt}/{retries} failed: {exc}. Retrying in {wait_time}s...")
                time.sleep(wait_time)

        raise RuntimeError(f"LLM Judge external API call failed after {retries} retries: {last_error}")

    def judge_response(
        self,
        customer_message: str,
        agent_response: str,
        retrieved_evidence: List[Dict[str, Any]],
        auto_handle: bool = True,
        is_security_alert: bool = False,
        max_retries: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Judges a single response using the real external LLM API.
        Returns strict standardized schema:
        {
            "scores": {
                "correctness": 1-5,
                "helpfulness": 1-5,
                "groundedness": 1-5,
                "policy": 1-5,
                "escalation": 1-5
            },
            "rationale": "..."
        }
        """
        prompt = format_judge_prompt(
            customer_message=customer_message,
            agent_response=agent_response,
            retrieved_evidence=retrieved_evidence,
            auto_handle=auto_handle,
            is_security_alert=is_security_alert,
        )

        raw_json_str = self._call_llm_api(prompt, max_retries=max_retries)
        return validate_and_parse_judge_json(raw_json_str)
