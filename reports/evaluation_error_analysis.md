# In-Depth Evaluation Error Analysis Report (Step 4)

This report investigates the top failure categories, boundary confusions, and edge cases surfaced across the 200-example golden benchmark.

---

## 1. Delivery Tracking vs Delivery Problem

**Disagreements Identified:** 2

| Tweet ID | Customer Text | Gold Intent | Predicted / Detail |
| :--- | :--- | :--- | :--- |
| `391137` | `@AmazonHelp Si y quisiera rastrearlo y el repartidor no me lo permite!...` | `Delivery Tracking & Status` | `Delivery Problem & Logistics` |
| `419420` | `@115850 how come my package was delivered saying that I recieved it? T...` | `Delivery Problem & Logistics` | `Delivery Tracking & Status` |

**Root Cause & Analysis:**
Customer messages inquiring about status often also complain of a delay. When tracking indicates an unfulfilled delivery promise, boundary rules favor logistics failure over routine tracking.

## 2. Prime vs Delivery Problem

**Disagreements Identified:** 7

| Tweet ID | Customer Text | Gold Intent | Predicted / Detail |
| :--- | :--- | :--- | :--- |
| `142870` | `@AmazonHelp Tell you what I will ask is how come prime is no longer ne...` | `Delivery Problem & Logistics` | `Prime & Subscription Services` |
| `498538` | `@AmazonHelp i just expect it to be here on the date that it initially ...` | `Delivery Problem & Logistics` | `Prime & Subscription Services` |
| `701334` | `@115830 my prime now order said it wasn’t able to be delivered but I’v...` | `Delivery Problem & Logistics` | `Prime & Subscription Services` |
| `1219363` | `@AmazonHelp Not a specific carrier. I've several orders run past the g...` | `Delivery Problem & Logistics` | `Prime & Subscription Services` |
| `2539594` | `@115821 why am I paying for 2 day shipping if it’s guaranteed to take ...` | `Delivery Problem & Logistics` | `Prime & Subscription Services` |

**Root Cause & Analysis:**
Customers frequently cite their paid Prime subscription ('I pay for Prime delivery') when complaining about a late delivery. Lexical rules correctly prioritize logistics failure over membership administration.

## 3. Return/Refund vs Payment & Billing

**Disagreements Identified:** 0

Zero errors identified in this boundary category across the benchmark.

## 4. Seller & Product Quality vs Returns

**Disagreements Identified:** 0

Zero errors identified in this boundary category across the benchmark.

## 5. Account Access & Security vs General / Other

**Disagreements Identified:** 1

| Tweet ID | Customer Text | Gold Intent | Predicted / Detail |
| :--- | :--- | :--- | :--- |
| `1764531` | `Hola @116928 estoy teniendo problemas con mi cuenta a la hora de hacer...` | `Account Access & Security` | `General / Feedback / Other` |

**Root Cause & Analysis:**
Vague security inquiries ('did your chat get hacked?') without transactional details can blur into general feedback. High-recall safety rules properly escalate all hack/fraud terms.

## 6. Insufficient Retrieval Evidence

**Disagreements Identified:** 14

| Tweet ID | Customer Text | Gold Intent | Predicted / Detail |
| :--- | :--- | :--- | :--- |
| `77535` | `@AmazonHelp It must be. I've had the same email address for years and ...` | `General / Feedback / Other` | `Score: 0.137` |
| `649952` | `Amazonで別日に注文したやつが、一緒の段ボールにはいって送られて来て感動した...` | `General / Feedback / Other` | `Score: 0.000` |
| `679078` | `初Amazon。 自動遮光カートリッジが安かった。...` | `General / Feedback / Other` | `Score: 0.000` |
| `962503` | `なんかアマゾンで返品したら、送料も半額くらい帰ってきたけど、どこで返金判断出来るんやろクレカで...` | `Returns, Replacements & Refunds` | `Score: 0.000` |
| `1591618` | `アルバムのAmazon支払いしたか覚えてないし支払いのメール来た覚えもないので詰み  (ほんとに買えてんのか)...` | `Payment, Billing & Gift Cards` | `Score: 0.000` |

**Root Cause & Analysis:**
Very terse customer tweets (e.g. '@AmazonHelp order') fail to produce strong TF-IDF n-gram matches. The escalation policy correctly refuses to auto-handle these low-evidence items.

## 7. Multilingual Queries

**Disagreements Identified:** 21

| Tweet ID | Customer Text | Gold Intent | Predicted / Detail |
| :--- | :--- | :--- | :--- |
| `34485` | `@AmazonHelp Bonjour et merci. Un vendeur tiers qui ne répond pas et qu...` | `Seller & Product Quality` | `Account Access & Security` |
| `139986` | `Sympa, quand tu commande une Yankee candle sur @120533 et qu'elle arri...` | `Delivery Problem & Logistics` | `General / Feedback / Other` |
| `140066` | `@AmazonHelp Voici : C20025897313 Parceque j'ai beau me plaindre à chaq...` | `Delivery Problem & Logistics` | `General / Feedback / Other` |
| `162100` | `@AmazonHelp Ja. Komm nicht an der Info vorbei. Bei einem anderen Spiel...` | `Digital Services & Devices` | `General / Feedback / Other` |
| `490648` | `@AmazonHelp Depuis la liste des commandes, impossible de contacter le ...` | `Seller & Product Quality` | `General / Feedback / Other` |

**Root Cause & Analysis:**
Non-English queries have fewer token n-grams in the historical resolution corpus, leading to slightly lower retrieval similarity scores.

## 8. Conversational Follow-ups / DM Handoffs

**Disagreements Identified:** 13

| Tweet ID | Customer Text | Gold Intent | Predicted / Detail |
| :--- | :--- | :--- | :--- |
| `61025` | `So I change my country of residence &amp; I get charged again for prim...` | `Prime & Subscription Services` | `Payment, Billing & Gift Cards` |
| `268666` | `@AmazonHelp My software on the Roku is up-to-date and I deleted and re...` | `Digital Services & Devices` | `General / Feedback / Other` |
| `331978` | `@AmazonHelp If they try again today, I'll be fine. But it says next bu...` | `Delivery Problem & Logistics` | `General / Feedback / Other` |
| `519700` | `@AmazonHelp I just want my psn codes so me and my friends can download...` | `Digital Services & Devices` | `General / Feedback / Other` |
| `1474625` | `@AmazonHelp how long does it take for you guys to release money after ...` | `Returns, Replacements & Refunds` | `General / Feedback / Other` |

**Root Cause & Analysis:**
Mid-thread replies without the original context ('Yes I tried that already') rely heavily on conversation state detection rather than standalone intent keywords.
