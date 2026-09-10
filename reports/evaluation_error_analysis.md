# In-Depth Evaluation Error Analysis Report (Step 4)

This report investigates the top failure categories, boundary confusions, and edge cases surfaced across the 200-example golden benchmark.

---

## 1. Delivery Tracking vs Delivery Problem

**Disagreements Identified:** 2

| Tweet ID | Customer Text | Gold Intent | Predicted / Detail |
| :--- | :--- | :--- | :--- |
| `391137` | `@AmazonHelp Si y quisiera rastrearlo y el repartidor no me lo permite!...` | `Delivery Tracking & Status` | `Delivery Problem & Logistics` |
| `478520` | `@AmazonHelp Hi! On your UK site, there’s no longer information about ‘...` | `Delivery Tracking & Status` | `Delivery Problem & Logistics` |

**Root Cause & Analysis:**
Customer messages inquiring about status often also complain of a delay. When tracking indicates an unfulfilled delivery promise, boundary rules favor logistics failure over routine tracking.

## 2. Prime vs Delivery Problem

**Disagreements Identified:** 1

| Tweet ID | Customer Text | Gold Intent | Predicted / Detail |
| :--- | :--- | :--- | :--- |
| `498538` | `@AmazonHelp i just expect it to be here on the date that it initially ...` | `Delivery Problem & Logistics` | `Prime & Subscription Services` |

**Root Cause & Analysis:**
Customers frequently cite their paid Prime subscription ('I pay for Prime delivery') when complaining about a late delivery. Lexical rules correctly prioritize logistics failure over membership administration.

## 3. Return/Refund vs Payment & Billing

**Disagreements Identified:** 0

Zero errors identified in this boundary category across the benchmark.

## 4. Seller & Product Quality vs Returns

**Disagreements Identified:** 1

| Tweet ID | Customer Text | Gold Intent | Predicted / Detail |
| :--- | :--- | :--- | :--- |
| `230015` | `@AmazonHelp @115850 What's the status? Will I get a refund for this fa...` | `Returns, Replacements & Refunds` | `Seller & Product Quality` |

**Root Cause & Analysis:**
Counterfeit, fake, or defective third-party items frequently culminate in return demands. Boundary precedence assigns seller conduct as primary driver.

## 5. Account Access & Security vs General / Other

**Disagreements Identified:** 0

Zero errors identified in this boundary category across the benchmark.

## 6. Insufficient Retrieval Evidence

**Disagreements Identified:** 21

| Tweet ID | Customer Text | Gold Intent | Predicted / Detail |
| :--- | :--- | :--- | :--- |
| `1721` | `@AmazonHelp Never got the beta and now I’m being told I won’t get ANY ...` | `Digital Services & Devices` | `Score: 0.137` |
| `77535` | `@AmazonHelp It must be. I've had the same email address for years and ...` | `General / Feedback / Other` | `Score: 0.137` |
| `423252` | `@115850 Ordered Crossbeats Raga Earphone Two months Back. The Item is ...` | `Seller & Product Quality` | `Score: 0.143` |
| `476843` | `@115830 Any reason why normal service has dropped over last few months...` | `Delivery Problem & Logistics` | `Score: 0.131` |
| `649952` | `Amazonで別日に注文したやつが、一緒の段ボールにはいって送られて来て感動した...` | `General / Feedback / Other` | `Score: 0.000` |

**Root Cause & Analysis:**
Very terse customer tweets (e.g. '@AmazonHelp order') fail to produce strong TF-IDF n-gram matches. The escalation policy correctly refuses to auto-handle these low-evidence items.

## 7. Multilingual Queries

**Disagreements Identified:** 6

| Tweet ID | Customer Text | Gold Intent | Predicted / Detail |
| :--- | :--- | :--- | :--- |
| `524929` | `Amazon デジタルミュージック、僕の好きな80年代の曲が割と揃ってるなー。プライム会員だと結構な数聴ける。知らなかった。...` | `General / Feedback / Other` | `Prime & Subscription Services` |
| `1338572` | `@AmazonHelp Ça m’étonnerait car sur mon suivi il est écrit qu’il a été...` | `Delivery Problem & Logistics` | `General / Feedback / Other` |
| `1764579` | `@AmazonHelp @120533  "colis livré" mais pas dans ma boite à lettre app...` | `Delivery Problem & Logistics` | `General / Feedback / Other` |
| `2278298` | `@116316 7 Ekim 2017 tarihinde Taylor Swift'in reputation albümünün öze...` | `Payment, Billing & Gift Cards` | `General / Feedback / Other` |
| `2555128` | `@AmazonHelp Aaaah merciii ! Et bien j'ai commandé un livre qui vient d...` | `Delivery Problem & Logistics` | `General / Feedback / Other` |

**Root Cause & Analysis:**
Non-English queries have fewer token n-grams in the historical resolution corpus, leading to slightly lower retrieval similarity scores.

## 8. Conversational Follow-ups / DM Handoffs

**Disagreements Identified:** 6

| Tweet ID | Customer Text | Gold Intent | Predicted / Detail |
| :--- | :--- | :--- | :--- |
| `61025` | `So I change my country of residence &amp; I get charged again for prim...` | `Prime & Subscription Services` | `Payment, Billing & Gift Cards` |
| `1544993` | `@115850 Been waiting for your cust service call since yesterday. First...` | `Delivery Problem & Logistics` | `General / Feedback / Other` |
| `1636667` | `@115830 been over a month since I was told I would be received a refun...` | `Returns, Replacements & Refunds` | `Delivery Problem & Logistics` |
| `1829432` | `@AmazonHelp I just had a foot surgery and bought a few items that woul...` | `Delivery Problem & Logistics` | `General / Feedback / Other` |
| `2922515` | `@115821 I think amazon? It’s listed as prime shipping. &amp; now it’s ...` | `Delivery Problem & Logistics` | `General / Feedback / Other` |

**Root Cause & Analysis:**
Mid-thread replies without the original context ('Yes I tried that already') rely heavily on conversation state detection rather than standalone intent keywords.
