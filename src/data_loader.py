"""
Data loading module for the Kaggle Customer Support on Twitter (twcs.csv) dataset.

Provides streaming and batch loaders optimized for memory efficiency
given the large size (~2.8M rows, ~800MB-1GB) of twcs.csv.
"""

import os
from pathlib import Path
from typing import Generator, List, Optional, Union
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DATA_PATH = ROOT_DIR / "data" / "raw" / "twcs.csv"

# Standard schema for twcs.csv
TWCS_DTYPES = {
    "tweet_id": "Int64",
    "author_id": "string",
    "inbound": "boolean",
    "created_at": "string",
    "text": "string",
    "response_tweet_id": "string",
    "in_response_to_tweet_id": "Int64",
}


def check_dataset_exists(filepath: Union[str, Path] = DEFAULT_DATA_PATH) -> bool:
    """Check if the raw twcs.csv file is present at the target path."""
    return Path(filepath).is_file()


def get_dataset_guidance(filepath: Union[str, Path] = DEFAULT_DATA_PATH) -> str:
    """Return instructions if the dataset file is missing."""
    p = Path(filepath).resolve()
    return (
        f"\n[ERROR] Dataset not found at: {p}\n"
        "Please download the dataset from Kaggle:\n"
        "  https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter\n"
        f"Extract twcs.csv and place it at:\n"
        f"  {p}\n"
    )


def stream_twcs_dataset(
    filepath: Union[str, Path] = DEFAULT_DATA_PATH,
    chunksize: int = 100_000,
    usecols: Optional[List[str]] = None,
) -> Generator[pd.DataFrame, None, None]:
    """
    Stream twcs.csv in chunks to prevent high memory usage.

    Args:
        filepath: Path to twcs.csv.
        chunksize: Number of rows per chunk (default 100k).
        usecols: Specific columns to load. If None, loads all columns.

    Yields:
        pd.DataFrame chunks with consistent dtypes.
    """
    path = Path(filepath)
    if not path.is_file():
        raise FileNotFoundError(get_dataset_guidance(path))

    dtypes = {col: TWCS_DTYPES[col] for col in (usecols or TWCS_DTYPES.keys()) if col in TWCS_DTYPES}

    reader = pd.read_csv(
        path,
        chunksize=chunksize,
        usecols=usecols,
        dtype=dtypes,
        low_memory=False,
    )
    for chunk in reader:
        yield chunk


def load_twcs_dataset(
    filepath: Union[str, Path] = DEFAULT_DATA_PATH,
    nrows: Optional[int] = None,
    usecols: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Load twcs.csv into memory. Use nrows to inspect a subset.

    Args:
        filepath: Path to twcs.csv.
        nrows: Maximum rows to read (useful for testing/exploration).
        usecols: Specific columns to read.

    Returns:
        pd.DataFrame with normalized types.
    """
    path = Path(filepath)
    if not path.is_file():
        raise FileNotFoundError(get_dataset_guidance(path))

    dtypes = {col: TWCS_DTYPES[col] for col in (usecols or TWCS_DTYPES.keys()) if col in TWCS_DTYPES}

    df = pd.read_csv(
        path,
        nrows=nrows,
        usecols=usecols,
        dtype=dtypes,
        low_memory=False,
    )
    return df


def get_brand_tweets(
    brand: str,
    filepath: Union[str, Path] = DEFAULT_DATA_PATH,
    chunksize: int = 150_000,
) -> pd.DataFrame:
    """
    Extract all tweets involving a specific brand:
    - Direct tweets sent by the brand (author_id == brand)
    - Customer tweets that mention the brand (@brand) or reply to the brand.

    Uses a two-pass stream:
    1. First pass collects brand tweet IDs and their parent/child pointers.
    2. Second pass gathers all related conversation turns.

    Args:
        brand: Brand handle (e.g., 'AmazonHelp', 'AppleSupport').
        filepath: Path to twcs.csv.
        chunksize: Chunk size for streaming.

    Returns:
        Filtered pd.DataFrame containing all relevant conversation tweets.
    """
    path = Path(filepath)
    if not path.is_file():
        raise FileNotFoundError(get_dataset_guidance(path))

    brand_lower = brand.lower()
    brand_tweet_ids = set()
    referenced_tweet_ids = set()

    # Pass 1: Identify brand tweets and referenced IDs
    for chunk in stream_twcs_dataset(path, chunksize=chunksize):
        # Match brand as author (case-insensitive)
        brand_mask = chunk["author_id"].str.lower() == brand_lower
        b_df = chunk[brand_mask]

        if not b_df.empty:
            brand_tweet_ids.update(b_df["tweet_id"].dropna().astype(str).tolist())
            # Collect in_response_to (customer parent tweets)
            in_resp = b_df["in_response_to_tweet_id"].dropna().astype(str).tolist()
            referenced_tweet_ids.update(in_resp)
            # Collect response_tweet_id (child tweets)
            for resp_str in b_df["response_tweet_id"].dropna():
                for tid in str(resp_str).split(","):
                    tid_clean = tid.strip()
                    if tid_clean:
                        referenced_tweet_ids.update([tid_clean])

    all_target_ids = brand_tweet_ids.union(referenced_tweet_ids)

    # Pass 2: Extract all matching tweets (author is brand or tweet_id in target set or text mentions @brand)
    matched_chunks = []
    for chunk in stream_twcs_dataset(path, chunksize=chunksize):
        chunk["tweet_id_str"] = chunk["tweet_id"].astype(str)
        mask = (
            (chunk["author_id"].str.lower() == brand_lower)
            | chunk["tweet_id_str"].isin(all_target_ids)
            | chunk["text"].str.contains(f"@{brand}", case=False, na=False)
        )
        filtered = chunk[mask].copy()
        if not filtered.empty:
            filtered.drop(columns=["tweet_id_str"], errors="ignore", inplace=True)
            matched_chunks.append(filtered)

    if not matched_chunks:
        return pd.DataFrame(columns=list(TWCS_DTYPES.keys()))

    result_df = pd.concat(matched_chunks, ignore_index=True)
    result_df.drop_duplicates(subset=["tweet_id"], inplace=True)
    return result_df
