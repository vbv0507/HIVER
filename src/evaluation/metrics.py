"""
Step 4: Comprehensive Evaluation Metrics Library

Implements reproducible metric calculations for:
1. Multi-class Intent Classification (Accuracy, Macro F1, Per-class Precision/Recall/F1, Confusion Matrix)
2. Language & Conversation State Accuracy and F1
3. Escalation & Security Binary Metrics (Accuracy, Precision, Recall, F1)
4. Deterministic Response Checks (Existence, Hallucination checks, Policy compliance)
5. Retrieval Hit-rate & Availability
6. Latency Percentiles (p50, p95)
"""

import math
import re
from collections import Counter
from typing import Dict, Any, List, Optional, Tuple


def compute_classification_metrics(
    y_true: List[str],
    y_pred: List[str],
    labels: List[str],
) -> Dict[str, Any]:
    """
    Computes accuracy, macro F1, per-class precision/recall/F1, and confusion matrix.
    """
    n = len(y_true)
    if n == 0:
        return {
            "accuracy": 0.0,
            "macro_f1": 0.0,
            "per_class": {},
            "confusion_matrix": {},
        }

    label_set = list(labels)
    label_to_idx = {lbl: i for i, lbl in enumerate(label_set)}
    k = len(label_set)

    # Initialize confusion matrix [true_idx][pred_idx]
    matrix = [[0 for _ in range(k)] for _ in range(k)]

    correct = 0
    for true_val, pred_val in zip(y_true, y_pred):
        if true_val == pred_val:
            correct += 1
        t_idx = label_to_idx.get(true_val)
        p_idx = label_to_idx.get(pred_val)
        if t_idx is not None and p_idx is not None:
            matrix[t_idx][p_idx] += 1

    accuracy = correct / n

    # Compute per-class metrics
    per_class = {}
    f1_sum = 0.0

    for i, lbl in enumerate(label_set):
        tp = matrix[i][i]
        fp = sum(matrix[r][i] for r in range(k) if r != i)
        fn = sum(matrix[i][c] for c in range(k) if c != i)
        support = sum(matrix[i])

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

        f1_sum += f1
        per_class[lbl] = {
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "support": support,
        }

    macro_f1 = f1_sum / k if k > 0 else 0.0

    # Format confusion matrix as dictionary
    cm_dict = {
        lbl: {label_set[col]: matrix[i][col] for col in range(k)}
        for i, lbl in enumerate(label_set)
    }

    return {
        "accuracy": round(accuracy, 4),
        "macro_f1": round(macro_f1, 4),
        "per_class": per_class,
        "per_intent": per_class,
        "confusion_matrix": cm_dict,
    }


def compute_binary_metrics(
    y_true: List[bool],
    y_pred: List[bool],
) -> Dict[str, Any]:
    """
    Computes accuracy, precision, recall, and F1 for binary classification flags.
    """
    n = len(y_true)
    if n == 0:
        return {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0, "tp": 0, "fp": 0, "fn": 0, "tn": 0}

    tp = sum(1 for t, p in zip(y_true, y_pred) if t and p)
    fp = sum(1 for t, p in zip(y_true, y_pred) if not t and p)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t and not p)
    tn = sum(1 for t, p in zip(y_true, y_pred) if not t and not p)

    accuracy = (tp + tn) / n
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "support": sum(1 for t in y_true if t),
    }


def compute_deterministic_response_checks(
    records: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Runs deterministic quality audits across generated drafts:
    - Checks existence & non-emptiness
    - Detects fabricated tracking details or fabricated dollar amounts
    - Checks whether escalation policy wording is present when escalated
    """
    total = len(records)
    if total == 0:
        return {"has_response_rate": 0.0, "no_hallucination_rate": 0.0, "policy_compliance_rate": 0.0}

    has_response_count = 0
    clean_facts_count = 0
    policy_compliant_count = 0

    # Patterns indicating fabricated specific order execution facts
    fake_facts_pat = re.compile(
        r"(i have refunded you \$[0-9.]+|i cancelled your order #[0-9]+|your package was delivered at [0-9]{1,2}:[0-9]{2} [AP]M)",
        re.IGNORECASE,
    )

    for r in records:
        if "main_agent_output" in r and isinstance(r["main_agent_output"], dict):
            text = str(r["main_agent_output"].get("draft_reply", "")).strip()
            auto_handle = r["main_agent_output"].get("auto_handle", True)
            is_sec = r.get("gold_security_alert", False) or r["main_agent_output"].get("is_security_alert", False)
        else:
            text = str(r.get("draft_reply", "")).strip()
            auto_handle = r.get("auto_handle", True)
            is_sec = r.get("gold_security_alert", False) or r.get("is_security_alert", False)

        # 1. Existence check
        if len(text) >= 15:
            has_response_count += 1

        # 2. Fact fabrication check
        if not fake_facts_pat.search(text):
            clean_facts_count += 1

        # 3. Policy compliance check
        # If security alert or not auto-handled, response must guide to private DM or specialist
        if not auto_handle or is_sec:
            if re.search(r"\b(dm|direct message|specialist|investigat|secur|private|escalat)\b", text, re.IGNORECASE):
                policy_compliant_count += 1
            else:
                pass
        else:
            # Routine auto-handle response should provide actionable guidance
            if len(text) >= 20:
                policy_compliant_count += 1

    return {
        "total_evaluated": total,
        "non_empty_count": has_response_count,
        "has_response_rate": round(has_response_count / total, 4),
        "no_hallucination_rate": round(clean_facts_count / total, 4),
        "policy_compliance_rate": round(policy_compliant_count / total, 4),
    }


def compute_retrieval_metrics(
    records: List[Dict[str, Any]],
    min_score_threshold: float = 0.10,
) -> Dict[str, Any]:
    """
    Computes evidence availability rate and retrieval hit rates.
    Hit rate definition: top evidence item shares the query's gold intent or has score >= 0.25.
    """
    total = len(records)
    if total == 0:
        return {"evidence_availability_rate": 0.0, "hit_rate_at_1": 0.0, "top_1_hit_rate": 0.0, "hit_rate_at_3": 0.0}

    available_count = 0
    hit_at_1 = 0
    hit_at_3 = 0

    for r in records:
        evidence = r.get("retrieved_evidence", [])
        gold_intent = r.get("gold_intent", "")

        if evidence and len(evidence) > 0:
            top_ev = evidence[0]
            if top_ev.get("score", 0.0) >= min_score_threshold:
                available_count += 1

            # Check hit at 1
            if top_ev.get("intent") == gold_intent or top_ev.get("score", 0.0) >= 0.25:
                hit_at_1 += 1

            # Check hit at 3
            if any(ev.get("intent") == gold_intent or ev.get("score", 0.0) >= 0.20 for ev in evidence[:3]):
                hit_at_3 += 1

    return {
        "evidence_availability_rate": round(available_count / total, 4),
        "hit_rate_at_1": round(hit_at_1 / total, 4),
        "top_1_hit_rate": round(hit_at_1 / total, 4),
        "hit_rate_at_3": round(hit_at_3 / total, 4),
    }


def compute_latency_metrics(latencies_ms: List[float]) -> Dict[str, Any]:
    """
    Computes p50 (median), p95, mean, min, and max latencies.
    """
    if not latencies_ms:
        return {"p50_ms": 0.0, "p95_ms": 0.0, "mean_ms": 0.0, "min_ms": 0.0, "max_ms": 0.0}

    sorted_l = sorted(latencies_ms)
    n = len(sorted_l)

    p50_idx = int(n * 0.50)
    p95_idx = min(n - 1, int(n * 0.95))

    return {
        "p50_ms": round(sorted_l[p50_idx], 2),
        "p50_latency_ms": round(sorted_l[p50_idx], 2),
        "p95_ms": round(sorted_l[p95_idx], 2),
        "p95_latency_ms": round(sorted_l[p95_idx], 2),
        "mean_ms": round(sum(sorted_l) / n, 2),
        "min_ms": round(sorted_l[0], 2),
        "max_ms": round(sorted_l[-1], 2),
    }
