"""
Mock data generator for testing and demonstration when twcs.csv is not yet downloaded.
Generates realistic multi-turn conversations matching the Kaggle twcs.csv schema
for the top 10 real-world brands in the dataset.
"""

from pathlib import Path
import random
import pandas as pd

TOP_BRANDS = [
    "AmazonHelp",
    "AppleSupport",
    "Uber_Support",
    "SpotifyCares",
    "Delta",
    "Tesco",
    "AmericanAir",
    "TMobileHelp",
    "comcastcares",
    "British_Airways",
]

CUSTOMER_TEMPLATES = {
    "AmazonHelp": [
        ("My package was supposed to arrive yesterday and tracking says delayed! 😡 Where is it? https://t.co/track1", "Package Delivery"),
        ("Ordered a birthday gift last week, still hasn't shipped. Order #112-998811! Need this ASAP.", "Shipping Status"),
        ("I received an empty box instead of the headphones I ordered! Please help @AmazonHelp", "Damaged/Missing Item"),
        ("Can I change my delivery address? It's shipping to my old apartment by mistake!", "Address Modification"),
        ("Charged twice on my credit card for Prime membership. Please refund immediately.", "Billing/Refund"),
        ("Your driver left my package out in the pouring rain when I have a covered porch. Completely soaked!", "Delivery Complaint"),
        ("How do I return an item purchased from a third-party seller?", "Return Policy"),
        ("The promo code for 20% off electronics is giving an invalid error at checkout.", "Promotions/Discount"),
    ],
    "AppleSupport": [
        ("My iPhone 11 screen is flickering green after the iOS update. Is anyone else having this? https://t.co/applefix", "Software Bug"),
        ("Battery draining 50% in 2 hours on standby! Unacceptable for a phone this expensive.", "Battery Drain"),
        ("Locked out of my Apple ID because two-factor auth is sending SMS to my lost phone number. Need urgent access!", "Account Access"),
        ("My AirPods Pro left earbud stopped charging completely even after cleaning the case.", "Hardware Fault"),
        ("App Store charged me $9.99 for a subscription I cancelled 3 days ago.", "Unauthorized Subscription"),
        ("Bluetooth keeps disconnecting every 5 minutes in my car. Started happening after 17.2 update.", "Connectivity Issue"),
        ("How do I transfer photos from my old iPad to MacBook without iCloud storage?", "Device Migration"),
    ],
    "Uber_Support": [
        ("Driver cancelled after making me wait 20 minutes, and you charged me a $5 cancellation fee! Refund please.", "Cancellation Fee"),
        ("I left my laptop bag in the back of a Toyota Prius (plate #7XYZ12) 30 mins ago. How do I contact the driver?", "Lost Item"),
        ("Driver took an absurdly long detour and my fare went from $18 to $45! Check the GPS route please.", "Fare Discrepancy"),
        ("The app crashed while requesting a ride, but my bank account shows a pending charge.", "Payment Issue"),
        ("Driver was extremely rude and drove aggressively on the freeway. Unsafe ride.", "Safety/Driver Conduct"),
        ("Uber Eats delivery arrived completely cold and missing drinks.", "Order Quality"),
    ],
    "SpotifyCares": [
        ("Offline downloads keep disappearing every time I open the app on Android! 🤬 https://t.co/musicerr", "Offline Playback"),
        ("Upgraded to Family Plan but my partner is not receiving the invite email.", "Account/Subscription"),
        ("Local files won't sync between desktop app and my phone anymore.", "Sync Issue"),
        ("Why does music randomly pause every 30 seconds? Premium subscriber here.", "Playback Interruption"),
        ("Payment failed with my debit card even though funds are available.", "Billing Error"),
    ],
    "Delta": [
        ("Flight DL1204 from JFK was delayed 4 hours, and now I'm going to miss my connecting flight to Paris! Help!", "Flight Delay/Connection"),
        ("Our checked bags never arrived on the carousel in Atlanta. Where is our luggage? https://t.co/deltabag", "Lost Baggage"),
        ("Need to rebook my flight due to a family medical emergency. Can change fees be waived?", "Flight Rebooking"),
        ("App won't let me check in online. Says 'System unavailable'. Departure is in 3 hours.", "Check-in Issue"),
        ("Gate agent was super helpful during the boarding chaos today, want to submit a commendation!", "Compliment/Staff"),
    ],
    "Tesco": [
        ("Home grocery delivery was missing 4 items including the milk and baby diapers!", "Missing Grocery Items"),
        ("Clubcard points didn't register on my receipt from the Manchester store today.", "Loyalty Card/Points"),
        ("Bought pre-packed chicken yesterday and it's 2 days past use-by date. Disgusting!", "Expired Goods"),
        ("Delivery driver didn't show up during the 2-hour reserved delivery slot.", "Missed Delivery"),
    ],
    "AmericanAir": [
        ("Delayed on the tarmac in Dallas for 2.5 hours with no water or AC. What is going on? @AmericanAir", "Tarmac Delay"),
        ("Lost baggage desk at MIA had a 2-hour line with only one agent working.", "Baggage Service"),
        ("My refund for flight cancellation was supposed to take 7 business days; it has been 3 weeks.", "Refund Delay"),
        ("Can I bring a musical instrument as a carry-on for flight AA402?", "Baggage Policy"),
    ],
    "TMobileHelp": [
        ("No cell service or LTE in entire zip code 94103 for the past 3 hours! Is there an outage? https://t.co/cellstatus", "Network Outage"),
        ("Billed $45 for international roaming that was promised as free under my Magenta plan.", "Roaming Overcharge"),
        ("Trying to unlock my device before traveling abroad, submitted request 5 days ago.", "Device Unlock"),
        ("SIM card swap request without my authorization! Suspect fraud please freeze my account immediately!", "Security/Fraud"),
    ],
    "comcastcares": [
        ("Internet has dropped 6 times today during work video meetings. Technician came Tuesday and didn't fix it.", "Intermittent Connection"),
        ("Bill jumped by $35 without notice. Contract was supposed to be price-locked for 2 years.", "Bill Increase"),
        ("TV box stuck on 'Connecting to Xfinity' error code RDK-03004.", "Hardware Error"),
        ("Need to schedule equipment return after moving to an area without Comcast service.", "Cancellation/Return"),
    ],
    "British_Airways": [
        ("Flight cancelled last night from Heathrow, no hotel voucher given and left stranded at terminal 5! 😡", "Cancelled Flight"),
        ("Can someone help change our seat assignments so my 4yo child can sit next to us?", "Seat Allocation"),
        ("Executive Club tier points for flight BA178 didn't credit to my account.", "Frequent Flyer Points"),
        ("Lost luggage reference LHRBA19827 still showing 'tracing continues' for 48 hours.", "Delayed Luggage"),
    ],
}

BRAND_REPLIES = [
    "We're sorry to hear about this! Could you please DM us with your details or account info so we can investigate right away? https://t.co/helpDM",
    "Thanks for reaching out! We'd love to take a closer look at this for you. Please send us a direct message with your reference number.",
    "Apologies for the inconvenience. Let's get this sorted out for you! Please share your order or booking ID via DM.",
    "That certainly shouldn't happen! Please DM us your full name, email, and issue details so our support team can assist.",
]

CUSTOMER_FOLLOW_UPS = [
    "Just sent you a DM with the reference number. Please reply quickly, this is urgent!",
    "Sent DM. How long does it usually take for someone to reply?",
    "I already sent a DM an hour ago and no one has gotten back to me!",
    "DM sent. Really hoping this gets resolved today.",
    "Thanks, just messaged you.",
]

BRAND_CLOSINGS = [
    "Got it! We've received your DM and an agent is reviewing your details now. We'll reply shortly.",
    "Thanks for the details! We have processed the adjustment and sent confirmation to your email.",
    "Thank you for your patience while we resolved this for you. Have a wonderful rest of your day!",
]


def generate_mock_twcs_dataset(
    output_path: Path = Path("data/raw/twcs.csv"),
    num_conversations: int = 1500,
) -> pd.DataFrame:
    """
    Generate a representative mock twcs.csv dataset.
    Creates rich multi-turn threads across all top 10 brands with varied lengths.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    current_tweet_id = 100_001

    # Distribution weights for top brands
    brand_weights = [30, 20, 12, 9, 8, 6, 5, 4, 3, 3]

    for _ in range(num_conversations):
        brand = random.choices(TOP_BRANDS, weights=brand_weights)[0]
        customer_id = str(random.randint(110_000, 990_000))

        # Sample customer initial issue
        inquiries = CUSTOMER_TEMPLATES.get(brand, CUSTOMER_TEMPLATES["AmazonHelp"])
        raw_msg, _ = random.choice(inquiries)

        # Prepend brand mention to customer message if not already present
        if f"@{brand}" not in raw_msg:
            raw_msg = f"@{brand} {raw_msg}"

        # Root tweet (Turn 1: Customer)
        root_tid = current_tweet_id
        current_tweet_id += 1

        # Determine thread depth (1-turn, 2-turn, 3-turn, or 4-turn)
        # Depth 2: Cust -> Brand
        # Depth 3: Cust -> Brand -> Cust
        # Depth 4: Cust -> Brand -> Cust -> Brand
        thread_type = random.choices([2, 3, 4], weights=[40, 45, 15])[0]

        # Brand reply (Turn 2: Brand)
        reply_tid = current_tweet_id
        current_tweet_id += 1
        brand_reply = f"@{customer_id} {random.choice(BRAND_REPLIES)}"

        # If multi-turn
        followup_tid = None
        closing_tid = None
        if thread_type >= 3:
            followup_tid = current_tweet_id
            current_tweet_id += 1
            customer_followup = f"@{brand} {random.choice(CUSTOMER_FOLLOW_UPS)}"

        if thread_type >= 4:
            closing_tid = current_tweet_id
            current_tweet_id += 1
            brand_closing = f"@{customer_id} {random.choice(BRAND_CLOSINGS)}"

        # Assemble row 1: Customer initial
        rows.append({
            "tweet_id": root_tid,
            "author_id": customer_id,
            "inbound": True,
            "created_at": "Tue Oct 31 10:15:00 +0000 2017",
            "text": raw_msg,
            "response_tweet_id": str(reply_tid),
            "in_response_to_tweet_id": pd.NA,
        })

        # Assemble row 2: Brand reply
        rows.append({
            "tweet_id": reply_tid,
            "author_id": brand,
            "inbound": False,
            "created_at": "Tue Oct 31 10:20:00 +0000 2017",
            "text": brand_reply,
            "response_tweet_id": str(followup_tid) if followup_tid else pd.NA,
            "in_response_to_tweet_id": root_tid,
        })

        # Assemble row 3: Customer follow-up
        if followup_tid:
            rows.append({
                "tweet_id": followup_tid,
                "author_id": customer_id,
                "inbound": True,
                "created_at": "Tue Oct 31 10:35:00 +0000 2017",
                "text": customer_followup,
                "response_tweet_id": str(closing_tid) if closing_tid else pd.NA,
                "in_response_to_tweet_id": reply_tid,
            })

        # Assemble row 4: Brand closing
        if closing_tid:
            rows.append({
                "tweet_id": closing_tid,
                "author_id": brand,
                "inbound": False,
                "created_at": "Tue Oct 31 10:45:00 +0000 2017",
                "text": brand_closing,
                "response_tweet_id": pd.NA,
                "in_response_to_tweet_id": followup_tid,
            })

    # Add a few unresponded customer tweets for realism
    for _ in range(int(num_conversations * 0.1)):
        brand = random.choice(TOP_BRANDS)
        customer_id = str(random.randint(110_000, 990_000))
        inquiries = CUSTOMER_TEMPLATES.get(brand, CUSTOMER_TEMPLATES["AmazonHelp"])
        raw_msg, _ = random.choice(inquiries)
        rows.append({
            "tweet_id": current_tweet_id,
            "author_id": customer_id,
            "inbound": True,
            "created_at": "Tue Oct 31 11:00:00 +0000 2017",
            "text": f"@{brand} {raw_msg}",
            "response_tweet_id": pd.NA,
            "in_response_to_tweet_id": pd.NA,
        })
        current_tweet_id += 1

    random.shuffle(rows)
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    return df
