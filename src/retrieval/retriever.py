"""
Step 3: AmazonHelp Resolution Retriever with Golden-Set Leakage Protection

Uses TF-IDF semantic matching over historical customer -> AmazonHelp resolution pairs.
Strictly filters out all golden-set thread and tweet IDs during evaluation mode.
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

DEFAULT_CORPUS_PATH = ROOT_DIR / "data/processed/resolution_pairs.jsonl"
DEFAULT_INDEX_PATH = ROOT_DIR / "data/processed/retrieval_index.joblib"
EXCLUSIONS_PATH = ROOT_DIR / "eval/golden_thread_exclusions.json"


class AmazonHelpRetriever:
    """
    Semantic TF-IDF retriever with strict golden-set leakage filtering.
    """

    def __init__(
        self,
        corpus_path: Path = DEFAULT_CORPUS_PATH,
        index_path: Path = DEFAULT_INDEX_PATH,
        exclusions_path: Path = EXCLUSIONS_PATH,
    ):
        self.corpus_path = Path(corpus_path)
        self.index_path = Path(index_path)
        self.exclusions_path = Path(exclusions_path)

        self.records: List[Dict[str, Any]] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None

        # Exclusions for leakage protection
        self.excluded_conv_ids: Set[str] = set()
        self.excluded_tweet_ids: Set[str] = set()
        self._load_exclusions()

        self._load_or_build_index()

    def _load_exclusions(self) -> None:
        """Loads golden-set conversation and tweet IDs to prevent benchmark leakage."""
        if self.exclusions_path.exists():
            with open(self.exclusions_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.excluded_conv_ids = set(str(cid) for cid in data.get("excluded_conversation_ids", []))
                self.excluded_tweet_ids = set(str(tid) for tid in data.get("excluded_tweet_ids", []))
            print(f"[Retriever] Loaded {len(self.excluded_conv_ids)} excluded conversations and {len(self.excluded_tweet_ids)} excluded tweets.")
        else:
            print(f"[Retriever] Warning: Exclusions file not found at {self.exclusions_path}")

    def is_leakage(self, record: Dict[str, Any]) -> bool:
        """Checks if a candidate historical record belongs to a golden-set evaluation thread."""
        conv_id = str(record.get("conversation_id", ""))
        cust_tid = str(record.get("customer_tweet_id", ""))
        resp_tid = str(record.get("amazon_tweet_id", ""))

        if conv_id in self.excluded_conv_ids:
            return True
        if cust_tid in self.excluded_tweet_ids:
            return True
        if resp_tid in self.excluded_tweet_ids:
            return True
        return False

    def _load_or_build_index(self) -> None:
        """Loads precomputed TF-IDF index or builds it from resolution pairs."""
        if self.index_path.exists():
            try:
                data = joblib.load(self.index_path)
                self.records = data["records"]
                self.vectorizer = data["vectorizer"]
                self.tfidf_matrix = data["tfidf_matrix"]
                print(f"[Retriever] Loaded precomputed index from {self.index_path} ({len(self.records):,} records).")
                return
            except Exception as e:
                print(f"[Retriever] Failed to load cached index ({e}); rebuilding...")

        # Rebuild index
        self.build_and_save_index()

    def build_and_save_index(self) -> None:
        """Parses corpus, fits TF-IDF vectorizer, and caches index artifacts."""
        if not self.corpus_path.exists():
            from src.retrieval.corpus_builder import build_resolution_corpus
            print(f"[Retriever] Corpus not found at {self.corpus_path}. Generating resolution pairs...")
            build_resolution_corpus(output_path=self.corpus_path, max_pairs=40000)

        self.records = []
        corpus_texts = []
        with open(self.corpus_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rec = json.loads(line)
                    self.records.append(rec)
                    # Index customer query + intent context
                    text = f"{rec.get('customer_message', '')} {rec.get('intent', '')}"
                    corpus_texts.append(text)

        print(f"[Retriever] Fitting TF-IDF Vectorizer on {len(corpus_texts):,} resolution pairs...")
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            sublinear_tf=True,
            max_features=50000,
            strip_accents="unicode",
            lowercase=True,
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus_texts)

        # Cache index
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "records": self.records,
                "vectorizer": self.vectorizer,
                "tfidf_matrix": self.tfidf_matrix,
            },
            self.index_path,
            compress=3,
        )
        print(f"[Retriever] ✓ Index saved to {self.index_path}")

    def search(
        self,
        query: str,
        top_k: int = 3,
        intent_filter: Optional[str] = None,
        evaluation_mode: bool = True,
        min_score: float = 0.05,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top-k historical resolutions for the query.
        Applies golden-set leakage filtering when evaluation_mode is True.
        """
        if not self.records or self.vectorizer is None or self.tfidf_matrix is None:
            return []

        # Vectorize query
        q_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(q_vec, self.tfidf_matrix).flatten()

        # Get top candidates
        top_indices = np.argsort(sims)[::-1]

        results = []
        for idx in top_indices:
            score = float(sims[idx])
            if score < min_score:
                break

            record = self.records[idx]

            # Mandatory Golden-Set Leakage Filter
            if evaluation_mode and self.is_leakage(record):
                continue

            # Optional intent metadata filter / weighting
            if intent_filter and record.get("intent") != intent_filter:
                # Slight penalty if intent differs but allow strong keyword matches
                score = score * 0.85
                if score < min_score:
                    continue

            results.append({
                "conversation_id": str(record.get("conversation_id")),
                "customer_message": record.get("customer_message"),
                "historical_response": record.get("amazon_response"),
                "intent": record.get("intent"),
                "score": round(score, 4),
            })

            if len(results) >= top_k:
                break

        return results
