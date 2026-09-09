"""
Unit tests for data loader, text cleaner, and thread builder.
"""

import unittest
import pandas as pd
from src.text_cleaner import clean_tweet_text
from src.thread_builder import reconstruct_threads, find_root_tweet_id, build_conversation_graph


class TestTextCleaner(unittest.TestCase):
    def test_url_removal(self):
        text = "Check this out https://t.co/abc1234 or www.example.com for more info"
        cleaned = clean_tweet_text(text)
        self.assertNotIn("https://", cleaned)
        self.assertNotIn("www.example.com", cleaned)
        self.assertIn("Check this out", cleaned)

    def test_brand_mention_removal(self):
        text = "@AmazonHelp: My package is late! Please help @amazonhelp"
        cleaned = clean_tweet_text(text, brand_handle="AmazonHelp")
        self.assertNotIn("@AmazonHelp", cleaned)
        self.assertNotIn("@amazonhelp", cleaned)
        self.assertIn("My package is late!", cleaned)

    def test_emoji_and_tone_preservation(self):
        text = "WHERE IS MY ORDER?!?! 😡📦 I am SO ANGRY."
        cleaned = clean_tweet_text(text, brand_handle="AmazonHelp")
        # Ensure casing, punctuation, and emojis remain untouched
        self.assertIn("WHERE IS MY ORDER?!?!", cleaned)
        self.assertIn("😡📦", cleaned)
        self.assertIn("SO ANGRY", cleaned)

    def test_html_unescape(self):
        text = "Apples &amp; Oranges &lt; Bananas"
        cleaned = clean_tweet_text(text)
        self.assertEqual(cleaned, "Apples & Oranges < Bananas")


class TestThreadBuilder(unittest.TestCase):
    def setUp(self):
        self.test_df = pd.DataFrame([
            {
                "tweet_id": 1,
                "author_id": "115858",
                "inbound": True,
                "created_at": "Tue Oct 31 10:00:00 +0000 2017",
                "text": "@AmazonHelp My order #123 has not arrived! 😡",
                "response_tweet_id": "2",
                "in_response_to_tweet_id": pd.NA,
            },
            {
                "tweet_id": 2,
                "author_id": "AmazonHelp",
                "inbound": False,
                "created_at": "Tue Oct 31 10:10:00 +0000 2017",
                "text": "@115858 We are so sorry! Please DM us your order ID.",
                "response_tweet_id": "3",
                "in_response_to_tweet_id": 1,
            },
            {
                "tweet_id": 3,
                "author_id": "115858",
                "inbound": True,
                "created_at": "Tue Oct 31 10:15:00 +0000 2017",
                "text": "@AmazonHelp DM sent. Please check ASAP.",
                "response_tweet_id": pd.NA,
                "in_response_to_tweet_id": 2,
            },
        ])

    def test_reconstruct_threads(self):
        threads = reconstruct_threads(self.test_df, brand_handle="AmazonHelp")
        self.assertEqual(len(threads), 1)

        conv = threads[0]
        self.assertEqual(conv["conversation_id"], "1")
        self.assertEqual(conv["total_turns"], 3)
        self.assertEqual(conv["customer_turns"], 2)
        self.assertEqual(conv["brand_turns"], 1)
        self.assertTrue(conv["is_multi_turn"])

        # Check turn order and roles
        turns = conv["turns"]
        self.assertEqual(turns[0]["role"], "customer")
        self.assertEqual(turns[0]["tweet_id"], "1")
        self.assertEqual(turns[1]["role"], "brand")
        self.assertEqual(turns[1]["tweet_id"], "2")
        self.assertEqual(turns[2]["role"], "customer")
        self.assertEqual(turns[2]["tweet_id"], "3")

        # Verify text cleaning in turns
        self.assertNotIn("@AmazonHelp", turns[0]["text_clean"])
        self.assertIn("😡", turns[0]["text_clean"])


if __name__ == "__main__":
    unittest.main()
