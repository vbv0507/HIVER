# AmazonHelp Taxonomy Audit & Design Rationale (Step 1.7)

**Document Purpose:** Audit the evolution of the intent taxonomy from Step 1.6 to Step 1.7, document design rationale, evaluate architectural separations, and audit the validity of empirical distributions without introducing ungrounded statistical claims.

---

## 1. Taxonomy Evolution & Changes from Step 1.6

Between Step 1.6 and Step 1.7, several refinements were codified to transform candidate buckets into rigorous, mutually exclusive operational categories:

| Step 1.6 Candidate Name | Step 1.7 Final Name | Changes & Rationale |
| :--- | :--- | :--- |
| **Delivery & Tracking** | **Delivery Tracking & Status** | Clarified that this intent is strictly for in-transit parcels *before* any delivery SLA breach has occurred. |
| **Delivery Problem** | **Delivery Problem & Logistics** | Expanded name to explicitly encompass courier misconduct, failed doorstep attempts, false delivery scans, and physical transit damage. |
| **Return & Refund** | **Returns, Replacements & Refunds** | Explicitly incorporated "Replacements" and "Exchanges" to prevent them from colliding with Order Management. |
| **Payment & Billing** | **Payment, Billing & Gift Cards** | Added Gift Cards, Amazon Pay balances, and Cash on Delivery (COD) to the title to explicitly capture prepaid and wallet payment methods. |
| **Prime & Subscriptions** | **Prime & Subscription Services** | Standardized boundary: strictly membership fees, renewal, and subscription benefits. Late Prime deliveries are firmly excluded and routed to Delivery Problem. |
| **Order, Checkout & Promotions** | **Order & Checkout** | Streamlined title while retaining pre-fulfillment cancellations, modifications, promo codes, and checkout cart errors. |
| **Account & Access** | **Account Access & Security** | Formally unified authentication barriers with security/phishing alerts, with security flagged via orthogonal priority attributes. |
| **Product, Device & Digital Issues** | **Digital Services & Devices** | Refined to focus on Amazon ecosystem hardware (Kindle, Echo, Fire TV) and digital services (Prime Video, Kindle content, app/web glitches). |
| **Seller & Product Quality** | **Seller & Product Quality** | Retained to handle counterfeit goods, marketplace seller disputes, and product defects prior to return requests. |
| **General / Feedback / Other** | **General / Feedback / Other** | Retained as a critical non-transactional container for pure conversational turns, praise, unspecific feedback, and conversational handshakes. |

---

## 2. Audit of the 500-Sample Distribution Validity

In Step 1.6, provisional classification on the 500 sampled messages (Seed `42`) produced the following preliminary counts:
- `Delivery Problem`: 51 (10.20%)
- `Delivery & Tracking`: 37 (7.40%)
- `Prime & Subscriptions`: 35 (7.00%)
- `Return & Refund`: 24 (4.80%)
- `Product, Device & Digital Issues`: 24 (4.80%)
- `Payment & Billing`: 23 (4.60%)
- `Account & Access`: 12 (2.40%)
- `Seller & Product Quality`: 8 (1.60%)
- `Order, Checkout & Promotions`: 6 (1.20%)
- `General / Feedback / Other`: 280 (56.00%)

### Critical Audit Findings:
1. **The Step 1.6 distribution remains valid as an initial heuristic scan**, but **must not be treated as a definitive ground-truth distribution**.
2. **Why `General / Feedback / Other` was elevated (56%):**  
   - In social media customer care, Twitter threads are multi-turn. Over 62% of conversations have 3+ turns. When sampling individual customer tweets in isolation, a substantial fraction are **conversational follow-ups** (e.g. *"Yes, I tried that"*, *"Order # 123-456"*, *"Sent DM"*). Without conversation history, a naive standalone keyword scanner defaults these to `Other`.
   - Furthermore, **multilingual tweets** (Spanish, Japanese, German, etc.) without exact English keyword matches initially flowed into `Other`.
3. **Strict Policy on Percentages:**  
   **We do NOT invent hypothetical percentages for the final taxonomy.** No revised percentage table is presented here because valid empirical percentages require a full, reproducible multi-annotator labeling run over complete conversation contexts rather than guesswork.

---

## 3. Orthogonal Representation: Language, State, and Escalation

Attempting to force language, dialogue progression, and risk urgency into a single flat intent label creates massive label explosion and semantic ambiguity. We enforce strict separation of concerns across 4 orthogonal dimensions:

```text
Message Representation:
{
  "tweet_id": "12345",
  "text": "...",
  "intent": "Delivery Problem & Logistics",
  "language": "es",
  "conversation_state": "new_issue",
  "escalation_level": "standard",
  "is_security_alert": false
}
```

### Dimension A: Language (Metadata Field)
- **Problem:** In TWCS, `@AmazonHelp` receives inquiries in over 6 languages. If we created `Delivery Problem (Spanish)`, the taxonomy would balloon to 60+ classes.
- **Architecture:** Language detection is performed as an upstream or metadata tag (`language: "en"`, `"es"`, `"ja"`, `"de"`, `"pt"`, `"fr"`).
- **Example:**
  - Tweet 851597: `language = "en"`, `intent = "Delivery Problem & Logistics"`
  - Tweet 751683: `language = "es"`, `intent = "Delivery Tracking & Status"`
  - Tweet 120159: `language = "ja"`, `intent = "Prime & Subscription Services"`

### Dimension B: Conversation State (`conversation_state`)
- **Problem:** Many customer tweets merely say *"I sent you a DM"* or *"Here is my order ID"*. Classifying these as `General` obscures their function; classifying them as `Delivery` assumes facts not in the text.
- **Architecture:** Represent the dialogue state independently:
  1. `new_issue`: Initial inquiry opening a customer service thread.
  2. `active_troubleshooting`: Mid-turn back-and-forth exchange clarifying details.
  3. `dm_handoff`: Customer stating they sent or are sending a direct message (*"Sent DM"*, *"Check inbox"*).
  4. `follow_up`: Providing requested details (order number, screenshot, address).
  5. `resolved_or_acknowledgment`: Acknowledging resolution or thanking support.
  6. `unclear`: Ambiguous or fragmentary statements.

### Dimension C: Escalation & Security Priority (`priority` / `is_security_alert`)
- **Problem:** Phishing scams, compromised accounts, or legal/police threats (e.g. Tweet 2067642 reporting to police) occur at low frequency (~1%), but require immediate, high-priority routing.
- **Architecture:** Captured as an orthogonal attribute:
  - `intent`: `Account Access & Security`
  - `is_security_alert`: `true`
  - `priority`: `"P0_CRITICAL"`
  - This guarantees the classifier does not dilute its statistical power while alerting the downstream agent harness to execute emergency triage.

---

## 4. Deep-Dive Audit: `Digital Services & Devices` (Split vs. United)

### The Architectural Question
Should `Digital Services & Devices` be split into two separate classes:
- `Device Hardware & IoT Support` (Kindle e-readers, Fire TV, Echo/Alexa)
- `Digital Services & Media` (Prime Video streaming, Kindle eBook downloads, Amazon Music)?

### Evaluation for a 150–250 Example Golden Set
1. **Sample Prevalence:**  
   In our 500-message empirical sample, all digital and device queries combined accounted for **24 tweets (4.8%)**.
2. **Class Starvation Risk:**  
   If split into two separate classes, each class would represent only ~2.4% of the distribution. In a target golden evaluation set of 150 to 200 messages:
   - `Device Hardware` would contain only **3 to 5 examples**.
   - `Digital Services` would contain only **3 to 5 examples**.
   - A single misclassification in a 4-example class results in a **25% swing in Precision and Recall**, rendering quantitative model benchmarking statistically unreliable.
3. **Recommendation:**  
   **Keep `Digital Services & Devices` as a single unified class for the Step 2/Step 3 golden evaluation benchmark.**  
   To preserve operational utility, annotate a secondary attribute `sub_type` (`hardware_device`, `streaming_media`, `app_website_bug`) so that when the test set expands, the taxonomy can cleanly partition without invalidating previous annotations.

---

## 5. Summary of Decision Boundaries for Golden Set Annotation

When human or automated annotators label the golden set, the following strict priority cascade must be applied:

1. **Security & Account Breach:** Any mention of compromised accounts, phishing, or login lockouts $\rightarrow$ **`Account Access & Security`** (Flag `is_security_alert: true`).
2. **Physical Delivery Overdue/Failed:** Any late package, missing delivery, or courier grievance $\rightarrow$ **`Delivery Problem & Logistics`** (regardless of Prime mentions).
3. **In-Transit Inquiries:** Asking for tracking/ETA before an SLA breach $\rightarrow$ **`Delivery Tracking & Status`**.
4. **Returns & Money Back:** Requesting replacement, return label, or refund for an order $\rightarrow$ **`Returns, Replacements & Refunds`**.
5. **Direct Billing Issues:** Unrecognized credit card charges, invoice requests, or gift card balances without a physical return $\rightarrow$ **`Payment, Billing & Gift Cards`**.
6. **Subscription Management:** Prime membership renewal, fees, or cancellation $\rightarrow$ **`Prime & Subscription Services`**.
7. **Pre-Shipment Changes:** Canceling before dispatch or promo code failures $\rightarrow$ **`Order & Checkout`**.
8. **Digital/Device Issues:** Kindle hardware, Fire TV, app crashes, or streaming errors $\rightarrow$ **`Digital Services & Devices`**.
9. **Defective/Counterfeit Product:** Grievance about item authenticity or manufacturing defect $\rightarrow$ **`Seller & Product Quality`**.
10. **Non-Transactional/Praise/Venting:** $\rightarrow$ **`General / Feedback / Other`**.
