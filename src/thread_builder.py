"""
Conversation thread reconstruction module for customer support tweets.

Reconstructs multi-turn dialogue trees (Customer -> Brand -> Customer follow-up)
from in_response_to_tweet_id and response_tweet_id pointer fields.
"""

from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
import pandas as pd
from src.text_cleaner import clean_tweet_text


def parse_twitter_date(date_str: Any) -> Optional[datetime]:
    """Parse Twitter timestamp (e.g. 'Tue Oct 31 22:10:47 +0000 2017')."""
    if pd.isna(date_str) or not isinstance(date_str, str):
        return None
    try:
        return datetime.strptime(date_str, "%a %b %d %H:%M:%S %z %Y")
    except Exception:
        try:
            return pd.to_datetime(date_str)
        except Exception:
            return None


def build_conversation_graph(df: pd.DataFrame) -> Tuple[Dict[str, str], Dict[str, List[str]]]:
    """
    Build parent-to-child and child-to-parent pointer mappings.

    Returns:
        parent_map: dict of child_id -> parent_id
        children_map: dict of parent_id -> list of child_ids
    """
    parent_map: Dict[str, str] = {}
    children_map: Dict[str, List[str]] = defaultdict(list)

    for _, row in df.iterrows():
        tid = str(row["tweet_id"]).strip()
        in_resp = row.get("in_response_to_tweet_id")

        if pd.notna(in_resp):
            pid = str(in_resp).replace(".0", "").strip()
            if pid and pid != "nan" and pid != tid:
                parent_map[tid] = pid
                children_map[pid].append(tid)

        resp_str = row.get("response_tweet_id")
        if pd.notna(resp_str):
            for c_id in str(resp_str).split(","):
                cid_clean = c_id.replace(".0", "").strip()
                if cid_clean and cid_clean != "nan" and cid_clean != tid:
                    children_map[tid].append(cid_clean)
                    if cid_clean not in parent_map:
                        parent_map[cid_clean] = tid

    return parent_map, children_map


def find_root_tweet_id(
    tweet_id: str,
    parent_map: Dict[str, str],
    known_tweet_ids: Set[str],
) -> str:
    """
    Trace parent pointers upwards to find the conversation root.
    Guarded against infinite cycles with a visited set.
    """
    curr = tweet_id
    visited = {curr}

    while curr in parent_map:
        nxt = parent_map[curr]
        if nxt in visited or not nxt:
            break
        # If nxt is known in dataset, continue climbing
        if nxt in known_tweet_ids:
            curr = nxt
            visited.add(curr)
        else:
            # Parent is outside the dataset, so curr is our local root
            break

    return curr


def reconstruct_threads(
    df: pd.DataFrame,
    brand_handle: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Reconstruct full multi-turn conversation threads from tweets DataFrame.

    Args:
        df: DataFrame containing tweets with standard twcs columns.
        brand_handle: Optional brand handle for cleaning text and role labeling.

    Returns:
        List of conversation thread dictionaries containing structured turns and metrics.
    """
    if df.empty:
        return []

    # Ensure tweet_id and in_response_to_tweet_id are clean strings
    df_work = df.copy()
    df_work["tweet_id_str"] = df_work["tweet_id"].astype(str).str.replace(".0", "", regex=False).str.strip()
    known_ids = set(df_work["tweet_id_str"].tolist())

    parent_map, _ = build_conversation_graph(df_work)

    # Resolve root ID for every tweet
    root_cache: Dict[str, str] = {}
    for tid in known_ids:
        root_cache[tid] = find_root_tweet_id(tid, parent_map, known_ids)

    df_work["conversation_id"] = df_work["tweet_id_str"].map(root_cache)

    # Parse created_at for sorting
    df_work["datetime"] = df_work["created_at"].apply(parse_twitter_date)

    # Group by conversation_id
    brand_lower = brand_handle.lower().lstrip("@") if brand_handle else None
    conversations = []

    for conv_id, group in df_work.groupby("conversation_id"):
        # Sort chronologically by datetime, or by tweet_id if datetime unavailable
        sorted_group = group.sort_values(
            by=["datetime", "tweet_id_str"],
            ascending=[True, True],
            na_position="first",
        )

        turns = []
        customer_count = 0
        brand_count = 0
        initial_customer_msg = ""

        for idx, (_, row) in enumerate(sorted_group.iterrows(), start=1):
            is_inbound = bool(row.get("inbound", False))
            author = str(row.get("author_id", "")).strip()

            # Determine role: 'customer' or 'brand'
            if brand_lower and author.lower().lstrip("@") == brand_lower:
                role = "brand"
            elif not is_inbound:
                role = "brand"
            else:
                role = "customer"

            if role == "customer":
                customer_count += 1
                if not initial_customer_msg:
                    initial_customer_msg = str(row.get("text", "")).strip()
            else:
                brand_count += 1

            raw_text = str(row.get("text", "")).strip()
            clean_text = clean_tweet_text(raw_text, brand_handle=brand_handle)

            in_resp_raw = row.get("in_response_to_tweet_id")
            in_resp_val = None
            if pd.notna(in_resp_raw):
                val_str = str(in_resp_raw).replace(".0", "").strip()
                if val_str and val_str != "nan":
                    in_resp_val = val_str

            turn_data = {
                "turn_index": idx,
                "tweet_id": row["tweet_id_str"],
                "role": role,
                "author_id": author,
                "inbound": is_inbound,
                "created_at": str(row.get("created_at", "")),
                "in_response_to_tweet_id": in_resp_val,
                "text_raw": raw_text,
                "text_clean": clean_text,
            }
            turns.append(turn_data)

        total_turns = len(turns)
        is_multi_turn = total_turns >= 3 and customer_count >= 2 and brand_count >= 1

        conversations.append({
            "conversation_id": conv_id,
            "brand": brand_handle or (turns[0]["author_id"] if turns else "Unknown"),
            "total_turns": total_turns,
            "customer_turns": customer_count,
            "brand_turns": brand_count,
            "is_multi_turn": is_multi_turn,
            "first_customer_message": clean_tweet_text(initial_customer_msg, brand_handle=brand_handle),
            "turns": turns,
        })

    return conversations
