# Golden Evaluation Set Sampling Methodology

**Date:** September 9, 2026  
**Dataset Source:** `data/processed/AmazonHelp_tweets.csv` (203,598 genuine customer tweets)  
**Sample Size:** Exactly 200 customer messages  
**Random Seed:** `42` (100% deterministic & reproducible)  

---

## 1. Stratification Strategy

Rather than imposing an artificial uniform split (e.g. 20 per class, which distorts real-world Twitter distribution), the sampling was stratified to achieve balanced coverage while respecting operational frequency:

| Stratum / Intent Domain | Target Count | Purpose in Golden Set |
| :--- | :---: | :--- |
| **Delivery Problem & Logistics** | 32 | High-frequency baseline; late deliveries, missed windows, courier failure. |
| **Delivery Tracking & Status** | 24 | In-transit ETA inquiries before SLA breach. |
| **General / Feedback / Other** | 26 | Conversational handshakes ('Sent DM'), praise, unspecific venting. |
| **Returns, Replacements & Refunds** | 20 | Return labels, drop-off questions, refund tracking, exchanges. |
| **Payment, Billing & Gift Cards** | 18 | Unrecognized card charges, gift cards, invoices, Cash on Delivery (COD). |
| **Prime & Subscription Services** | 18 | Membership fees, auto-renewal, cancellations (distinct from delivery). |
| **Digital Services & Devices** | 18 | Kindle e-reader hardware, Prime Video streaming quality, app crashes. |
| **Account Access & Security** | 16 | Login locked, 2FA/OTP failures, phishing reports, security alerts (P0). |
| **Order & Checkout** | 14 | Pre-fulfillment cancellation, checkout promo codes, cart errors. |
| **Seller & Product Quality** | 14 | Counterfeit/fake items, 3rd-party marketplace disputes, defective items. |
| **TOTAL** | **200** | **Complete representation of Twitter customer support domain.** |

## 2. Orthogonal Diversity Controls

1. **Multilingual Inclusion:** Minimum of 25 non-English tweets representing Spanish (`es`), Japanese (`ja`), German (`de`), Portuguese (`pt`), French (`fr`), and Italian (`it`).
2. **Conversation State Variety:** Covers thread openers (`new_issue`), DM handshakes (`dm_handoff`), information follow-ups (`follow_up`), active troubleshooting (`active_troubleshooting`), and thank-you acknowledgments (`resolved_or_acknowledgment`).
3. **High-Priority Security Cases:** Includes 6–8 critical security, fraud, and phishing alerts (`is_security_alert: true`, `priority: "P0_CRITICAL"`).

## 3. Data Leakage Prevention Protocol

- **The Risk:** In retrieval-augmented generation (RAG) and customer support agents, evaluation queries run against historical ticket stores. If historical AmazonHelp responses to the evaluation queries remain in the retrieval corpus, the agent could 'cheat' by simply retrieving the historical Twitter response verbatim.
- **The Solution:** For all 200 sampled evaluation tweets, their entire conversation threads (spanning 2,027 total tweets across all turns) are indexed into `eval/golden_thread_exclusions.json`.
- **Execution Policy:** Downstream evaluation harnesses MUST exclude all IDs listed in `golden_thread_exclusions.json` from the retrieval database index during testing.
