# Customer Support Dataset: Top 10 Brands Exploration Report

- **Dataset Scanned**: 4,306 tweets
- **Purpose**: Select the best candidate brand for training/evaluating the customer support agent.

## 1. Top 10 Brands Summary Table

| Brand Handle         |   Brand Replies |   Customer Inbound |   Total Est. Vol |   Avg Thread Depth | Multi-turn %   |
|----------------------|-----------------|--------------------|------------------|--------------------|----------------|
| **@AmazonHelp**      |             533 |                765 |            1,298 |               2.74 | 61.7%          |
| **@AppleSupport**    |             354 |                515 |              869 |               2.73 | 61.9%          |
| **@Uber_Support**    |             184 |                279 |              463 |               2.63 | 58.5%          |
| **@SpotifyCares**    |             159 |                225 |              384 |               2.61 | 53.1%          |
| **@Delta**           |             145 |                205 |              350 |               2.57 | 50.7%          |
| **@Tesco**           |              99 |                154 |              253 |               2.39 | 45.3%          |
| **@AmericanAir**     |              85 |                129 |              214 |               2.49 | 50.0%          |
| **@TMobileHelp**     |              68 |                112 |              180 |               2.22 | 38.3%          |
| **@comcastcares**    |              59 |                 96 |              155 |               2.42 | 50.0%          |
| **@British_Airways** |              52 |                 88 |              140 |               2.22 | 39.7%          |

---

## 2. Brand Profiles & Sample Raw Customer Messages

### 1. @AmazonHelp
- **Brand Responses**: 533
- **Avg Thread Length**: 2.74 turns
- **Multi-Turn Thread %**: 61.7%
- **5 Sample Raw Messages**:
  1. `"@AmazonHelp Charged twice on my credit card for Prime membership. Please refund immediately."`
  2. `"@AmazonHelp Just sent you a DM with the reference number. Please reply quickly, this is urgent!"`
  3. `"@AmazonHelp Sent DM. How long does it usually take for someone to reply?"`
  4. `"@AmazonHelp Ordered a birthday gift last week, still hasn't shipped. Order #112-998811! Need this ASAP."`
  5. `"@AmazonHelp Just sent you a DM with the reference number. Please reply quickly, this is urgent!"`

### 2. @AppleSupport
- **Brand Responses**: 354
- **Avg Thread Length**: 2.73 turns
- **Multi-Turn Thread %**: 61.9%
- **5 Sample Raw Messages**:
  1. `"@AppleSupport I already sent a DM an hour ago and no one has gotten back to me!"`
  2. `"@AppleSupport How do I transfer photos from my old iPad to MacBook without iCloud storage?"`
  3. `"@AppleSupport Sent DM. How long does it usually take for someone to reply?"`
  4. `"@AppleSupport Battery draining 50% in 2 hours on standby! Unacceptable for a phone this expensive."`
  5. `"@AppleSupport My iPhone 11 screen is flickering green after the iOS update. Is anyone else having this? https://t.co/applefix"`

### 3. @Uber_Support
- **Brand Responses**: 184
- **Avg Thread Length**: 2.63 turns
- **Multi-Turn Thread %**: 58.5%
- **5 Sample Raw Messages**:
  1. `"@Uber_Support Driver was extremely rude and drove aggressively on the freeway. Unsafe ride."`
  2. `"@Uber_Support Thanks, just messaged you."`
  3. `"@Uber_Support DM sent. Really hoping this gets resolved today."`
  4. `"@Uber_Support The app crashed while requesting a ride, but my bank account shows a pending charge."`
  5. `"@Uber_Support Driver took an absurdly long detour and my fare went from $18 to $45! Check the GPS route please."`

### 4. @SpotifyCares
- **Brand Responses**: 159
- **Avg Thread Length**: 2.61 turns
- **Multi-Turn Thread %**: 53.1%
- **5 Sample Raw Messages**:
  1. `"@SpotifyCares DM sent. Really hoping this gets resolved today."`
  2. `"@SpotifyCares I already sent a DM an hour ago and no one has gotten back to me!"`
  3. `"@SpotifyCares Sent DM. How long does it usually take for someone to reply?"`
  4. `"@SpotifyCares Sent DM. How long does it usually take for someone to reply?"`
  5. `"@SpotifyCares Why does music randomly pause every 30 seconds? Premium subscriber here."`

### 5. @Delta
- **Brand Responses**: 145
- **Avg Thread Length**: 2.57 turns
- **Multi-Turn Thread %**: 50.7%
- **5 Sample Raw Messages**:
  1. `"@Delta Just sent you a DM with the reference number. Please reply quickly, this is urgent!"`
  2. `"@Delta Thanks, just messaged you."`
  3. `"@Delta Just sent you a DM with the reference number. Please reply quickly, this is urgent!"`
  4. `"@Delta Gate agent was super helpful during the boarding chaos today, want to submit a commendation!"`
  5. `"@Delta Need to rebook my flight due to a family medical emergency. Can change fees be waived?"`

### 6. @Tesco
- **Brand Responses**: 99
- **Avg Thread Length**: 2.39 turns
- **Multi-Turn Thread %**: 45.3%
- **5 Sample Raw Messages**:
  1. `"@Tesco Bought pre-packed chicken yesterday and it's 2 days past use-by date. Disgusting!"`
  2. `"@Tesco Clubcard points didn't register on my receipt from the Manchester store today."`
  3. `"@Tesco Just sent you a DM with the reference number. Please reply quickly, this is urgent!"`
  4. `"@Tesco Bought pre-packed chicken yesterday and it's 2 days past use-by date. Disgusting!"`
  5. `"@Tesco Delivery driver didn't show up during the 2-hour reserved delivery slot."`

### 7. @AmericanAir
- **Brand Responses**: 85
- **Avg Thread Length**: 2.49 turns
- **Multi-Turn Thread %**: 50.0%
- **5 Sample Raw Messages**:
  1. `"@AmericanAir Just sent you a DM with the reference number. Please reply quickly, this is urgent!"`
  2. `"@AmericanAir Just sent you a DM with the reference number. Please reply quickly, this is urgent!"`
  3. `"@AmericanAir Just sent you a DM with the reference number. Please reply quickly, this is urgent!"`
  4. `"@AmericanAir Thanks, just messaged you."`
  5. `"@AmericanAir Thanks, just messaged you."`

### 8. @TMobileHelp
- **Brand Responses**: 68
- **Avg Thread Length**: 2.22 turns
- **Multi-Turn Thread %**: 38.3%
- **5 Sample Raw Messages**:
  1. `"@TMobileHelp SIM card swap request without my authorization! Suspect fraud please freeze my account immediately!"`
  2. `"@TMobileHelp Trying to unlock my device before traveling abroad, submitted request 5 days ago."`
  3. `"@TMobileHelp Just sent you a DM with the reference number. Please reply quickly, this is urgent!"`
  4. `"@TMobileHelp No cell service or LTE in entire zip code 94103 for the past 3 hours! Is there an outage? https://t.co/cellstatus"`
  5. `"@TMobileHelp Trying to unlock my device before traveling abroad, submitted request 5 days ago."`

### 9. @comcastcares
- **Brand Responses**: 59
- **Avg Thread Length**: 2.42 turns
- **Multi-Turn Thread %**: 50.0%
- **5 Sample Raw Messages**:
  1. `"@comcastcares TV box stuck on 'Connecting to Xfinity' error code RDK-03004."`
  2. `"@comcastcares TV box stuck on 'Connecting to Xfinity' error code RDK-03004."`
  3. `"@comcastcares Just sent you a DM with the reference number. Please reply quickly, this is urgent!"`
  4. `"@comcastcares Just sent you a DM with the reference number. Please reply quickly, this is urgent!"`
  5. `"@comcastcares Internet has dropped 6 times today during work video meetings. Technician came Tuesday and didn't fix it."`

### 10. @British_Airways
- **Brand Responses**: 52
- **Avg Thread Length**: 2.22 turns
- **Multi-Turn Thread %**: 39.7%
- **5 Sample Raw Messages**:
  1. `"@British_Airways Lost luggage reference LHRBA19827 still showing 'tracing continues' for 48 hours."`
  2. `"@British_Airways DM sent. Really hoping this gets resolved today."`
  3. `"@British_Airways Lost luggage reference LHRBA19827 still showing 'tracing continues' for 48 hours."`
  4. `"@British_Airways Just sent you a DM with the reference number. Please reply quickly, this is urgent!"`
  5. `"@British_Airways Can someone help change our seat assignments so my 4yo child can sit next to us?"`

---

## 3. Brand Recommendations for AI Agent Assignment

1. **@AmazonHelp**: **Highest Volume & Diversity**.
   - *Pros*: Covers e-commerce (shipping, missing items, Prime subscriptions, refunds). Very rich multi-turn dialogues.
   - *Best for*: Building a realistic retail/e-commerce support agent with clear action intents.

2. **@AppleSupport**: **High Technical Depth**.
   - *Pros*: Complex troubleshooting queries (iOS bugs, battery life, hardware faults, Apple ID).
   - *Best for*: Technical support & diagnosis workflows.

3. **@SpotifyCares**: **Focused Subscription & App Domain**.
   - *Pros*: Clean problem domains (billing, family plan, offline downloads, sync). High multi-turn follow-ups.
   - *Best for*: SaaS/Digital subscription assistant.

4. **@Delta** or **@AmericanAir**: **High-Stakes Escalation & Policy**.
   - *Pros*: Flight rebooking, baggage tracking, delay compensations. High emotional urgency.
   - *Best for*: Policy-heavy and sentiment-sensitive support agents.