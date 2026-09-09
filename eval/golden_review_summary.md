# Golden Evaluation Set Review Summary & Audit

**Dataset:** `eval/golden_eval_set.csv`  
**Total Examples:** 200  
**Reviewed Examples:** 200 / 200  
**Review State:** COMPLETE  

---

## 1. Intent Distribution (Human Gold Labels)

| Intent | Count | Percentage |
| :--- | :---: | :---: |
| **Delivery Tracking & Status** | 9 | 4.50% |
| **Delivery Problem & Logistics** | 39 | 19.50% |
| **Returns, Replacements & Refunds** | 10 | 5.00% |
| **Payment, Billing & Gift Cards** | 4 | 2.00% |
| **Prime & Subscription Services** | 4 | 2.00% |
| **Order & Checkout** | 16 | 8.00% |
| **Account Access & Security** | 6 | 3.00% |
| **Digital Services & Devices** | 21 | 10.50% |
| **Seller & Product Quality** | 18 | 9.00% |
| **General / Feedback / Other** | 73 | 36.50% |

## 2. Orthogonal Metadata Distributions

### Language Distribution

| Language | Count | Percentage |
| :---: | :---: | :---: |
| `en` | 150 | 75.00% |
| `es` | 7 | 3.50% |
| `ja` | 16 | 8.00% |
| `de` | 4 | 2.00% |
| `pt` | 7 | 3.50% |
| `fr` | 14 | 7.00% |
| `it` | 1 | 0.50% |
| `other` | 1 | 0.50% |

### Conversation State Distribution

| Conversation State | Count | Percentage |
| :--- | :---: | :---: |
| `new_issue` | 41 | 20.50% |
| `active_troubleshooting` | 114 | 57.00% |
| `dm_handoff` | 7 | 3.50% |
| `follow_up` | 24 | 12.00% |
| `resolved_or_acknowledgment` | 14 | 7.00% |
| `unclear` | 0 | 0.00% |

## 3. Escalation & Security Summary

- **Total Security Alerts Flagged (`my_final_is_security_alert`):** 5
- **Human Escalation Rate (`my_final_escalate`):** 79 / 200 (39.50%)
- **Priority Breakdown:** {'standard': 195, 'P0_CRITICAL': 5}

## 4. AI Suggestion Agreement Statistics

- **AI Intent Agreement:** 105 / 200 = **52.5%**
- **AI Escalation Agreement:** 128 / 200 = **64.0%**

*(Note: Agreement statistics only; these do NOT constitute model evaluation metrics.)*

## 5. Sample Disagreements & Difficult Decisions

- **[Tweet 1721]**: `@AmazonHelp Never got the beta and now I’m being told I won’t get ANY of the other stuff. Including `
  - AI Suggested: `General / Feedback / Other`
  - Human Gold:   `Digital Services & Devices`
  - Notes: Assistant proposal for study/review; not an independently human-authored gold label. Reason: The issue concerns Amazon apps, devices, digital content, or streaming/media services.

- **[Tweet 49143]**: `@AmazonHelp Yes but it is a robot emails! I tried and mailed several emails with my bank statement a`
  - AI Suggested: `General / Feedback / Other`
  - Human Gold:   `Payment, Billing & Gift Cards`
  - Notes: Assistant proposal for study/review; not an independently human-authored gold label. Reason: The message concerns a charge, payment method, invoice, balance, or gift-card/voucher use.

- **[Tweet 57428]**: `@AmazonHelp It say's "Could not set your address. Please ensure you have correctly entered a complet`
  - AI Suggested: `General / Feedback / Other`
  - Human Gold:   `Order & Checkout`
  - Notes: Assistant proposal for study/review; not an independently human-authored gold label. Reason: The issue concerns order management, checkout, pricing, deals, promotions, or pre-shipment changes.

- **[Tweet 61025]**: `So I change my country of residence &amp; I get charged again for prime services without mentioning `
  - AI Suggested: `General / Feedback / Other`
  - Human Gold:   `Prime & Subscription Services`
  - Notes: Assistant proposal for study/review; not an independently human-authored gold label. Reason: The core topic is Prime/subscription membership, renewal, cancellation, or subscription access/fees.

- **[Tweet 83454]**: `Pedido en @116928 este lunes (cybermonday)

Esta mañana en el tracking me pone que se ha retrasado..`
  - AI Suggested: `General / Feedback / Other`
  - Human Gold:   `Delivery Problem & Logistics`
  - Notes: Assistant proposal for study/review; not an independently human-authored gold label. Reason: Delivery is overdue, failed, missing, misdelivered, or involves a courier/logistics problem.

- **[Tweet 86157]**: `@115850 @AmazonHelp do you take any action when delivery boy falsely claims that he attempted delive`
  - AI Suggested: `General / Feedback / Other`
  - Human Gold:   `Delivery Problem & Logistics`
  - Notes: Assistant proposal for study/review; not an independently human-authored gold label. Reason: Delivery is overdue, failed, missing, misdelivered, or involves a courier/logistics problem.

- **[Tweet 95437]**: `@AmazonHelp - It is really poor service or has your online chat support been hacked ?`
  - AI Suggested: `General / Feedback / Other`
  - Human Gold:   `Account Access & Security`
  - Notes: Assistant proposal for study/review; not an independently human-authored gold label. Reason: The message concerns account access, login/security, account compromise, or suspicious/phishing communication.

- **[Tweet 137150]**: `@AmazonHelp I’ve looked in there and there is no option for that, I’ve had items delivered before at`
  - AI Suggested: `General / Feedback / Other`
  - Human Gold:   `Delivery Tracking & Status`
  - Notes: Assistant proposal for study/review; not an independently human-authored gold label. Reason: Routine shipment status, tracking, or ETA inquiry without a clear delivery failure.

- **[Tweet 139986]**: `Sympa, quand tu commande une Yankee candle sur @120533 et qu'elle arrive en mille morceaux 😠`
  - AI Suggested: `General / Feedback / Other`
  - Human Gold:   `Delivery Problem & Logistics`
  - Notes: Assistant proposal for study/review; not an independently human-authored gold label. Reason: Delivery is overdue, failed, missing, misdelivered, or involves a courier/logistics problem.

- **[Tweet 140066]**: `@AmazonHelp Voici : C20025897313 Parceque j'ai beau me plaindre à chaque fois (genre colis ouvert po`
  - AI Suggested: `General / Feedback / Other`
  - Human Gold:   `Delivery Problem & Logistics`
  - Notes: Assistant proposal for study/review; not an independently human-authored gold label. Reason: Delivery is overdue, failed, missing, misdelivered, or involves a courier/logistics problem.

