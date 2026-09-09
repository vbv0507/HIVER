# AmazonHelp Data Profile & Conversation Reconstruction Report (Step 1.5)

**Date:** September 9, 2026  
**Pipeline Step:** Step 1.5 — Extract and Reconstruct AmazonHelp Data  
**Random Sampling Seed:** `42` (100% deterministic & reproducible)  
**Status:** Complete & Verified

---

## 1. Dataset Source & Provenance

- **Upstream Dataset:** Customer Support on Twitter (`data/raw/twcs.csv`, Kaggle thoughtvector/customer-support-on-twitter)
- **Raw Scale:** 2,811,774 rows (516,508,641 bytes)
- **Synthetic Fallback:** NONE. No mock data, no synthetic row generators, and zero fallback scripts used.

## 2. Extraction Methodology

1. **Author Identification:** Official brand handle identification based on outbound tweet volume (`author_id == 'AmazonHelp'`, `inbound == False`).
2. **Graph-Pointer Traversal:** Conversations were reconstructed strictly using TWCS relationship fields (`tweet_id`, `in_response_to_tweet_id`, and `response_tweet_id`). Text regex matching (e.g. searching for `@AmazonHelp`) was explicitly avoided to prevent noise and capture threads where handles were omitted in follow-up turns.
3. **Root Identification & Cycle Checking:** Traced parent pointers backwards to discover root tweet IDs (`conversation_id`), verifying acyclicity.
4. **Chronological Thread Assembly:** Turns within each conversation were ordered chronologically by Twitter timestamp.

## 3. Identified AmazonHelp Author ID(s)

| Author ID | Total Tweets | Outbound (Support) | Inbound | Classification & Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `AmazonHelp` | 169,840 | 169,840 | 0 | Official verified brand handle: 169,840 outbound replies (100.00% outbound) demonstrating dedicated customer support role. |

## 4. Tweet Volume & Role Distribution

| Metric | Count | Percentage |
| :--- | :--- | :--- |
| **Total Extracted Tweets** | **373,438** | 100.00% |
| **Inbound Customer Tweets** | **203,598** | 54.52% |
| **Outbound AmazonHelp Tweets** | **169,840** | 45.48% |

## 5. Conversation Thread Statistics

- **Total Reconstructed Conversations:** 82,556
- **Threads with Both Customer and Support Turns:** 100.00%
- **Median Conversation Length:** 3 turns
- **Mean Conversation Length:** 4.52 turns
- **Maximum Conversation Length:** 448 turns

### Conversation Length Breakdown

| Thread Length | Conversation Count | Percentage |
| :--- | :--- | :--- |
| **1 Turn** (isolated tweet) | 0 | 0.00% |
| **2 Turns** (standard Customer → Support) | 31,369 | 38.00% |
| **3+ Turns** (multi-turn back-and-forth) | 51,187 | 62.00% |

## 6. Response Coverage & Customer Reach

- **Customer Tweets Receiving Response:** 168,181 / 203,598 (82.60%)
- **Unique Customers Assisted:** 73,425

## 7. Data Quality Audit

| Quality Check | Result | Status |
| :--- | :--- | :--- |
| Duplicate `tweet_id` records | 0 | PASS |
| Empty or null text entries | 0 | PASS |
| Graph cyclic relationships | 0 | PASS |
| Orphaned parent references (parent outside dataset) | 3,862 | Documented (expected in Twitter scrape) |
| Orphaned child reply references | 4,034 | Documented (expected in Twitter scrape) |

## 8. 20 Random Real Customer Messages

*Extracted with fixed random seed `42` directly from genuine inbound tweets:*

1. **[Tweet 2474911 | User 707551]**: `@133260 @AmazonHelp Lo paso por DM, aunque me se la respuesta.Ah! y tengo la respuesta al correo que envié a Amazon justo al realizar el pedido, advirtiendo de esta circunstancia.`
2. **[Tweet 332754 | User 195246]**: `@116618 glad I can watch Thursday night football with prime. But please address the quality and consistency with your streaming service when it comes to live football. Thank you.`
3. **[Tweet 101206 | User 138149]**: `@AmazonHelp I'm honestly not sure. I wasn't necessarily expecting it the same day, but I did think it would arrive the same week, or at the very least the same month!`
4. **[Tweet 2881244 | User 799492]**: `@AmazonHelp, placed an order yesterday with One-Day delivery for Prime. The order was supposed to be delivered today but got a notification for tomorrow delivery. Called CC &amp; spoke to Himanshu who was of no use. Pls help. @115850`
5. **[Tweet 851597 | User 322297]**: `Why is it @115830 that you guys said I wasn't in to take my delivery when i was, not even a knock at the door`
6. **[Tweet 751683 | User 137851]**: `@AmazonHelp Uno de los productos sí, el otro aparece como pendiente. Iban en la misma caja supongo, porque tenia un sólo número de seguimiento.`
7. **[Tweet 666973 | User 278937]**: `Great! Order reached in city yet delayed. Pay &amp; wait for months with @115821 The worst service always. No consumer consideration. Go to hell @115850 Tired of this. https://t.co/YJc4meO7PU`
8. **[Tweet 401586 | User 210965]**: `@AmazonHelp Thanks. Expected 8 October. 9 October almost done and still not delivered. Contacting you ‘for assistance’ not easy. https://t.co/p35ECOI8o7`
9. **[Tweet 2866009 | User 796034]**: `@AmazonHelp 楽しみですっ いつもお世話になってます\❤︎/`
10. **[Tweet 315491 | User 129428]**: `@AmazonHelp Danke. Ich habe sehr lange nach diesem Link gesucht. Ihr solltet es Kunden einfacher machen so etwas zu melden.`
11. **[Tweet 2626371 | User 277610]**: `@AmazonHelp No, today was the first time. Luckily it wasn't anything fragile, but a totally preposterous move, given multiple hiding spots on my porch`
12. **[Tweet 2877863 | User 234877]**: `@AmazonHelp Cyber Monday/black Friday/Christmas are annual events. Surely a little forethought and extra resources would ensure that customers still get the service they signed up for?`
13. **[Tweet 2073954 | User 613390]**: `@AmazonHelp ....and waiting... https://t.co/RLD7DdmN9B`
14. **[Tweet 279356 | User 182606]**: `@AmazonHelp  https://t.co/2duzJWltTu`
15. **[Tweet 2296039 | User 666642]**: `@AmazonHelp podrías haber empezado por ahí y nos ahorramos la pérdida de tiempo... gracias por su ayuda`
16. **[Tweet 1392412 | User 443851]**: `@AmazonHelp just found my parcel left right by notice saying not to leave parcels. I was home too &amp; courier didn’t attempt contact #fail https://t.co/a2BtiOMlrZ`
17. **[Tweet 125378 | User 144110]**: `@AmazonHelp até quando vai essa promoção do Kindle?`
18. **[Tweet 120159 | User 142676]**: `Amazonプライム勝手に継続登録になって無駄にお金払ってから約半年..  そう言えば映画とかアニメ観れたよな〜 って3日前から作業中に鋼錬の旧アニ垂れ流しで全話観て、今日昼から旧劇も観たんやけど、来年もプライム会員継続しようかと心揺れてる笑  キョロちゃんまで配信されてるんやで？やばない？笑`
19. **[Tweet 291342 | User 185012]**: `@AmazonHelp Done, your customer service rep was most helpful!`
20. **[Tweet 650126 | User 274560]**: `Plz help me @115850  I saw a job advertisement for the post of amazon supervisor  on @29757  when i called them they offering jobs to freshers but to get this job they asked me to deposit 1550₹ in delhi for uniform charges. Is this genuine or fraud? I hv attached their msg https://t.co/cRJ0oZS9EZ`

## 9. 20 Random Customer → AmazonHelp Response Examples

*Extracted with fixed random seed `42` showing actual support interactions:*

### Example 1 (Tweet 872180 → 872182)
- **Customer (327066):** @AmazonHelp Yes! Was supposed to arrive by 8pm on October 13.. looks like I'll get it Monday October 16! 😡
- **AmazonHelp:** @327066 Sorry Haley - is the issue with the carrier or the dispatch ? ^TD

### Example 2 (Tweet 2337934 → 2337936)
- **Customer (676382):** @AmazonHelp It sends me back to the orders page which does NOT help. I see no option to buy as an individual
- **AmazonHelp:** @676382 Please click on the link above&gt;&gt;Select an issue&gt;&gt;Select the mode of contact(email/chat/call) and we'll assist you. ^AU

### Example 3 (Tweet 2824664 → 2824663)
- **Customer (761895):** @AmazonHelp Unfortunately, I was only interested in it with the sale price. Thank you for your help, though.
- **AmazonHelp:** @761895 No problem Kyle, let me know if there's anything else we can do for you.^TI

### Example 4 (Tweet 126844 → 126843)
- **Customer (144473):** @117086 eu assinei o Kindle Unlimited sem querer, se eu cancelar agora mesmo serei cobrado normalmente??
- **AmazonHelp:** @144473 Olá, Quasímedu! Neste caso sugiro para você entrar em contato com o nosso SAC, acessando o seguinte link: https://t.co/qGpkDwGRhX. ^NB

### Example 5 (Tweet 2610754 → 2610753)
- **Customer (738309):** @115850 the default delivery speed has been changed and now the default delivery is one day delivery even though you dont select it it does so automatically in app. Now i cant use buy now option as i have to change the delivery speed each time pin code 500067.
- **AmazonHelp:** @738309 I understand your concern regarding your address change. Please get in touch with us via https://t.co/TxK11znixD and we'll help you out with it. ^AM

### Example 6 (Tweet 735310 → 735311)
- **Customer (219794):** @AmazonHelp Lol which mail....see I told u @115821 @115850 have a #pathetic system in place #Amazon....@138673 losing customers as well
- **AmazonHelp:** @219794 I understand your concern, Kapil. Please refer and revert on the same email for further assistance. ^MK

### Example 7 (Tweet 2531101 → 2531099)
- **Customer (720447):** あ～～～アマゾンのミュージックアンリミテッド入会しちゃった～～～ああ～～～ジュディマリ聴き放題～～～あああ～～～～
- **AmazonHelp:** @720447 ご登録ありがとうございます。(◍•ᴗ•◍) ET

### Example 8 (Tweet 1699096 → 1699098)
- **Customer (186225):** @AmazonHelp As a suggestion.. please start accepting Sodexo Coupons.. you could put @8815 out of business. :) Huge difference in pricing.
- **AmazonHelp:** @186225 I'll pass along your comments internally as feedback. Thank you. ^HK

### Example 9 (Tweet 823576 → 823574)
- **Customer (259388):** @AmazonHelp It’s in transit, says it’s coming Monday. I was only told my payment didnt go through on the sunday before the book was to come out though?
- **AmazonHelp:** @259388 Thank you for confirming, Alyssa! Did you choose Release-Date Delivery for your pre-order? https://t.co/sYMe3QZv3E ^FD

### Example 10 (Tweet 1929434 → 1929435)
- **Customer (574155):** @AmazonHelp ok I have done that ! Said they would send return slip by email but haven't received it ! Does this take a while ?
- **AmazonHelp:** @574155 It should be there as soon as they send it. Have you checked spam/junk folders in your e-mail? ^TR

### Example 11 (Tweet 2764383 → 2764382)
- **Customer (773237):** @AmazonHelp いつも利用させていただいています(ゝω・´★) ありがとうございます(*^o^)／＼(^-^*)
- **AmazonHelp:** @773237 こちらこそ、いつもご利用ありがとうございます♪(*^^*) またぜひご利用くださいませ～！＼(＾▽＾)／ TN

### Example 12 (Tweet 1072592 → 1072591)
- **Customer (208543):** hey @AmazonHelp yet more issues with AMZL_US delivery provider--in fact, I can't think of a delivery from them that DIDN'T have problems
- **AmazonHelp:** @208543 I'm sorry for the issues, let us look into this for you. Fill info and all details in here: https://t.co/K5w657bB6K ^AH

### Example 13 (Tweet 30002 → 30004)
- **Customer (122601):** @AmazonHelp Called them last night and was fobbed off with an email and no assistance whatsoever in actually getting my parcel. And that was the second time around as I got hung up on the first time. Terrible customer service!
- **AmazonHelp:** @122601 Oh no! I'm so sorry to hear about this. Were you provided with an updated delivery date? Please keep us posted! ^SD

### Example 14 (Tweet 546421 → 546419)
- **Customer (247055):** Not sure if @115821 is ready for "Prime" time.  3/4 orders on Black Friday misfired with 1 still AWOL. Fingers crossed my order comes today
- **AmazonHelp:** @247055 I'm sorry to hear it hasn't arrived. What's the delivery date and most recent tracking shown here: https://t.co/Y5jpI9gRhE? ^LI

### Example 15 (Tweet 1715339 → 1715343)
- **Customer (373962):** @AmazonHelp please amazon don't do this with me i gifted this phone to my friend and now she is asking me abt the reduced price.it ws not my fault
- **AmazonHelp:** @373962 Pricing is a decision of the seller and our prices tend to fluctuate on regular basis. As informed earlier, 1/2 ^EM

### Example 16 (Tweet 1331872 → 1331871)
- **Customer (424986):** .@115821 customer service: "we apologize it wasnt delivered same day. It should be there by 9 am." Ma'am it's 8:57, is hedwig delivering it?
- **AmazonHelp:** @424986 Oh my! Were you able to reach us with the link sent by SE? If not, please do. We'd like to look into this further for you. ^AL

### Example 17 (Tweet 1071055 → 1071054)
- **Customer (363133):** Te amo, @116875
- **AmazonHelp:** @363133 Ale, ¿qué hemos hecho para merecer tu amor? ❤ ^DA

### Example 18 (Tweet 531523 → 531521)
- **Customer (243138):** @115821 mi piacerebbe, quando scelgo un prodotto nel vostro emarket, sapere prima se compro #MadeinChina oppure no. Fare una ricerca a tappeto diventa snervante. Aggiungetelo come filtro. Che è ora.
- **AmazonHelp:** @243138 Ti ringrazio per il feedback. Ti ricordo che, a seconda del tipo di articolo,  hai la possibilità di filtrare i risultati di ricerca per: marca, occasione o modello. A presto! ^MA

### Example 19 (Tweet 800305 → 800304)
- **Customer (201487):** @115850 PATHETIC CHAT AGENTS u have https://t.co/XQc9VKB1fq
- **AmazonHelp:** @201487 Our apologies. We'd like to help. Could you tell us more about your concern for better assistance? ^YP

### Example 20 (Tweet 1318275 → 1318274)
- **Customer (427880):** @115830 why has peppa pig clips stopped working on kids mode in fire???!!! Very upset child today
- **AmazonHelp:** @427880 Sorry to hear this - pls contact the Kindle Team for assistance:  https://t.co/JzP7hlA23B ^TD

## 10. 10 Random Multi-Turn Conversations (3+ Turns)

*Extracted with fixed random seed `42` demonstrating multi-turn dialogue progression:*

### Conversation 1 [ID: 319769 | Length: 10 turns]
  - **Turn 1 [Customer (159049) | Tweet 319769]:** 1 week competed but @34028  didn't give any solution not the product. Don't go to tht site. #india @115850 #Delhi #bangalore
  - **Turn 2 [AmazonHelp | Tweet 319767]:** @159049 Just to confirm, have you dropped in your details using the link provided earlier? We'd like to have a look into it. ^AB
  - **Turn 3 [Customer (159049) | Tweet 319768]:** @AmazonHelp Keep parroting the same thing. I have several times #atrociousamazon #worstcustomerservice #sayno2amazon
  - **Turn 4 [AmazonHelp | Tweet 319770]:** @159049 If you've shared the details we'll surely work on it. If not, kindly do so. We're trying to help you. ^SG
  - **Turn 5 [Customer (159049) | Tweet 319771]:** @AmazonHelp U guys have been working on it since Sunday. Shame such companies keep on looting ppl and @118342 govt does nothing. #atrociousamazon
  - **Turn 6 [AmazonHelp | Tweet 319772]:** @159049 I get you being upset. Could you confirm if you've shared the details as requested earlier? ^MS
  - **Turn 7 [Customer (159049) | Tweet 319773]:** @AmazonHelp Either u guys r nuts or don't know English. I have mentioned in several tweets that I have.
  - **Turn 8 [AmazonHelp | Tweet 319776]:** @159049 Apologies! As you confirm to have dropped the details already, thus I believe we must have already 1/3 ^AB
  - **Turn 9 [AmazonHelp | Tweet 319775]:** @159049 got back to you on this via email. Kindly check for any latest correspondence from our 2/3 ^AB
  - **Turn 10 [AmazonHelp | Tweet 319774]:** @159049 side here: https://t.co/NTkrxpsbHJ and if need be reply to the email received with further query. 3/3 ^AB

### Conversation 2 [ID: 295854 | Length: 17 turns]
  - **Turn 1 [Customer (186459) | Tweet 295854]:** @115830 wheres my damn package !!!! Next day delivery my arse
  - **Turn 2 [AmazonHelp | Tweet 295852]:** @186459 I'm sorry for the wait! What does the tracking show here: https://t.co/aaDyEz1VgE Have there been delays? Let us know! ^KN
  - **Turn 3 [Customer (186459) | Tweet 295853]:** @AmazonHelp @115830 @Amazonhelp It's simply says OUT FOR DELIVERY.... But NOTHING
  - **Turn 4 [AmazonHelp | Tweet 295855]:** @186459 We can still deliver up until 21:00! Please let us know if you haven't received your parcel by this time! ^KJ
  - **Turn 5 [Customer (186459) | Tweet 295858]:** @AmazonHelp Yea yea yea.... we'll see.  Lack of #CustomerService
  - **Turn 6 [Customer (186459) | Tweet 295856]:** @AmazonHelp Still nothing .... if this doesn't arrive it's going to cause me real issues
  - **Turn 7 [Customer (186459) | Tweet 295857]:** @AmazonHelp 9PM AND STILL NOTHING FROM YOU
  - **Turn 8 [AmazonHelp | Tweet 295859]:** @186459 When you have a moment, please phone us here: https://t.co/JzP7hlA23B to report this and discuss re-delivery. ^LB
  - **Turn 9 [Customer (186459) | Tweet 295861]:** @AmazonHelp Your staff are utterly incompetent and none of them know what's happening or where it is pr when it will be delivered #customerexperience
  - **Turn 10 [Customer (186459) | Tweet 295860]:** @AmazonHelp I have called you but NO LUCK. Awful customer service with NO ANSWERS #customerexperience
  - **Turn 11 [AmazonHelp | Tweet 295862]:** @186459 What is showing on the order at the moment? We would be unable to give a time slot.^CD
  - **Turn 12 [Customer (186459) | Tweet 295863]:** @AmazonHelp They are saying massively different information from new challenge other and from what your staff say. This is ridiculous #CustomerService
  - **Turn 13 [AmazonHelp | Tweet 295864]:** @186459 Apologies, did they ask you to wait until a certain date? ^JJ
  - **Turn 14 [Customer (186459) | Tweet 295865]:** @AmazonHelp No. Again, THEY KEEP CONTRADICTING EACH OTHER. I was told I would get a call for confirmation in 30 mins nearly 3hrs ago #customerexperience
  - **Turn 15 [AmazonHelp | Tweet 295866]:** @186459 Did you get an email after contacting the agents? ^JJ
  - **Turn 16 [Customer (186459) | Tweet 295867]:** @AmazonHelp Nope
  - **Turn 17 [AmazonHelp | Tweet 295868]:** @186459 Did you check your spam/junk folder? Also, has there been any update in tracking today?: https://t.co/aaDyEz1VgE ^PK

### Conversation 3 [ID: 1263069 | Length: 4 turns]
  - **Turn 1 [Customer (415813) | Tweet 1263069]:** Wow. Pakete sorgsam behandeln ist wohl zu schwierig :‘&gt; @124285 @AmazonHelp https://t.co/wBVYRAj9WX
  - **Turn 2 [AmazonHelp | Tweet 1263067]:** @415813 So solltest du dein Paket nicht erhalten. :( Ist denn der Inhalt heil geblieben? ^SK
  - **Turn 3 [Customer (415813) | Tweet 1263068]:** @AmazonHelp Sagen Sie mir, ob Bücher so aussehen sollten :/ https://t.co/lFG4GGF7AI
  - **Turn 4 [AmazonHelp | Tweet 1263070]:** @415813 Eher nicht! 😕 Bitte kontaktiere unseren Kundenservice, damit dieser weitere Schritte einleiten kann: https://t.co/ohyvGrpvrY ^VM

### Conversation 4 [ID: 311303 | Length: 4 turns]
  - **Turn 1 [Customer (190341) | Tweet 311303]:** Ordered deliver from @697 via Amazon @153820. Food was missing. RR bounced us to @153820 for refund.
  - **Turn 2 [Customer (190341) | Tweet 311302]:** @697 @153820 Amazon Restaurants doesn't *have* a clear way to file a complaint for missing food, or for requesting refunds because Red Robin screwed up.
  - **Turn 3 [Customer (190341) | Tweet 311301]:** @697 @153820 And there was no point in demanding someone deliver the missing *half* of the desert sampler, and my salad dressing...but we're still out $.
  - **Turn 4 [AmazonHelp | Tweet 311300]:** @190341 I'm sorry you didn't receive part of your order. Have we refunded you for the missing items? What options were discussed? ^AM

### Conversation 5 [ID: 1196331 | Length: 6 turns]
  - **Turn 1 [Customer (196818) | Tweet 1196331]:** @AmazonHelp I want the new Kindle reading app. I've deleted &amp; DL'd REPEATEDLY but still have shitty old app. Help. 7.18.0.1 updated Oct9th.
  - **Turn 2 [AmazonHelp | Tweet 1196326]:** @196818 I'm sorry for the trouble updating the app. For version 6.0 you will iOS 9.0 or higher. ^BH
  - **Turn 3 [Customer (196818) | Tweet 1196327]:** @AmazonHelp No. According to your own website and MULITPLE tech articles out TODAY your app is for Android &amp; PC available NOW. https://t.co/AcIbgTYsOH
  - **Turn 4 [Customer (196818) | Tweet 1196329]:** @AmazonHelp I called support they told me the Android app isn't compatible with Samsung Note8 phones it's Samsungs fault. Do ALL Amazon workers lie!?
  - **Turn 5 [Customer (196818) | Tweet 1196328]:** @AmazonHelp They said 7.18.0.1v IS the new app but I have to wait for Samsung to update my app so it will work right. What kind of bullshit is this!?
  - **Turn 6 [Customer (196818) | Tweet 1196330]:** @AmazonHelp I was hung up on when I said that is insane since my tablet and my phone have 7.18.0.1 &amp; they are running different UIs w/ SAME version!

### Conversation 6 [ID: 1130541 | Length: 5 turns]
  - **Turn 1 [Customer (386433) | Tweet 1130541]:** Dreamt @115821 added a checkout button to send a gift to @13571. I was racking my brains trying to decide which space book he'd like.
  - **Turn 2 [AmazonHelp | Tweet 1130539]:** @386433 Awesome! I like the way you dream. There are so many amazing books to choose from. Which book did you pick out? ^DA
  - **Turn 3 [Customer (386433) | Tweet 1130540]:** @AmazonHelp Haha, I know it's cheesy, but I was going to send one of mine... https://t.co/MJSxnnQ2tO
  - **Turn 4 [AmazonHelp | Tweet 1130542]:** @386433 There is nothing cheesy about standing behind your work. I hope that he will be able to read your book one day. Cheers! ^DA
  - **Turn 5 [Customer (386433) | Tweet 1130543]:** @AmazonHelp Thanks...have a great day as well!

### Conversation 7 [ID: 2335800 | Length: 3 turns]
  - **Turn 1 [Customer (675853) | Tweet 2335800]:** @AmazonHelp poxa, eu to tentando comprar nessa feira de livro de 39,90, mas quando vou adicionar no carrinho o preço dos dois fica normal
  - **Turn 2 [Customer (675853) | Tweet 2335799]:** @AmazonHelp sim, abaixo está como ''feira do livro'' https://t.co/IEengX9yVX
  - **Turn 3 [AmazonHelp | Tweet 2335798]:** @675853 Olá! Por favor, continue com o processo. O preço final com o desconto será mostrando antes de finalizar a compra. ^CR

### Conversation 8 [ID: 835178 | Length: 3 turns]
  - **Turn 1 [Customer (318847) | Tweet 835178]:** @119356 @115850 , Thank you for delivering used mobile phone. #LenovoZ2Plus. Quick replacement will be appreciated. https://t.co/zilIUJeXze
  - **Turn 2 [AmazonHelp | Tweet 835179]:** @318847 I'm sorry for the unpleasant experience with this order, our support team will reach out to you 1/2 ^MJ
  - **Turn 3 [AmazonHelp | Tweet 835177]:** @318847 with an update regarding the returns. Appreciate your patience. 2/2 ^MJ

### Conversation 9 [ID: 158668 | Length: 4 turns]
  - **Turn 1 [Customer (152475) | Tweet 158668]:** @115850  I ordered ponds bb cream which was not the original product similarly few months back I ordered for lakme eyeliner that was also duplicate... No quality assurance at all.. Worst services
  - **Turn 2 [AmazonHelp | Tweet 158666]:** @152475 We're sorry to hear that the order delivered didn't meet your expectation. Just to ensure, did you report this to our support team here: https://t.co/rS49hgaADF? Do keep us posted. ^SM
  - **Turn 3 [Customer (152475) | Tweet 158667]:** @AmazonHelp I did for the bb cream.. Not for the eyeliner..   They gave me some amazon credit balance which was hardly for 2-3 days..  I wonder y the cosmetics things are not genuine... It can have several implications..
  - **Turn 4 [AmazonHelp | Tweet 158669]:** @152475 Apologies. You may report this to our support team with the same procedure and we will get this issue sorted. ^MN

### Conversation 10 [ID: 2829497 | Length: 4 turns]
  - **Turn 1 [Customer (149159) | Tweet 2829497]:** Why isn't prime next day delivery at the moment? @115830
  - **Turn 2 [AmazonHelp | Tweet 2829495]:** @149159 Hi, Joe! Please visit us here for more information: https://t.co/7xZmChSgZ7 ^RB
  - **Turn 3 [Customer (149159) | Tweet 2829496]:** @AmazonHelp Thank you
  - **Turn 4 [AmazonHelp | Tweet 2829498]:** @149159 You're very welcome, Joe! Please let us know if there's anything else at all we could assist with! ^SD

