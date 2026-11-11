# Local model results: OpenJev 4B v5 on this Mac

Same 60 tickets, same two questions, same flag rules as the hosted run in `../results.json`. Model: AlexWortega/openjev `qwen3.5-4b-nli-v5` (Qwen3.5-4B cross-encoder, MIT), bf16 on Apple Silicon via PyTorch MPS. Confidence here is the margin between the top team probability and the runner-up; the hosted Jev's formula is not published, so the two confidence columns are not directly comparable.

## Stats

| | Local OpenJev 4B | Jev (hosted) | Sonnet 5.5 |
|---|---|---|---|
| Routed correctly (clean, red herring, hard) | 36/48 | 42/48 | 44/48 |
| Clean routed correctly | 18/18 | 18/18 | 18/18 |
| Red herrings routed correctly | 6/6 | 5/6 | 6/6 |
| Hard and vague routed correctly | 12/24 | 19/24 | 20/24 |
| Mixed tickets sent to a human | 5/6 | 2/6 | 3/6 |
| Noise tickets sent to a human | 6/6 | 6/6 | 6/6 |
| Correct answers flagged anyway | 18 | 8 | 16 |
| Wrong answers unflagged | 0 | 1 | 0 |
| Mean confidence when right | 0.75 | 0.93 | 0.78 |
| Mean confidence when wrong | 0.52 | 0.64 | 0.47 |
| Average latency per ticket | 2052 ms | 326 ms | 1364 ms |
| Total time, all 60 calls | 123.1 s | 19.6 s | 81.9 s |
| Cost | $0 (laptop) | $0.0014 | $0.1000 |

Team agreement with Jev: 46/60. With Sonnet: 48/60.

## All rows

| # | Set | Expected | Ticket | Local team | Local conf | Local action | Local flag | Jev team | Jev conf | Sonnet team | Sonnet conf |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | clean | support | Hi, how do I add a second admin to our account? I can't find it in settings anywhere | support | 0.89 | 0.89 |  | support | 1.00 | support | 0.90 |
| 2 | clean | support | can your service send attachments or just plain text emails?? need to know before thursday | support | 0.83 | 0.74 |  | support | 1.00 | support | 0.88 |
| 3 | clean | support | Bonjour, est-ce que je peux exporter les réponses d'un formulaire en CSV? Merci | support | 0.99 | 0.81 |  | support | 1.00 | support | 0.95 |
| 4 | clean | support | Is there a way to schedule a message to go out at 9am instead of sending it right away. thx | support | 0.63 | 0.93 | HUMAN (conf) | support | 1.00 | support | 0.93 |
| 5 | clean | support | quick q - does your product have a french date picker or do we build our own | support | 0.97 | 0.59 |  | support | 0.96 | support | 0.80 |
| 6 | clean | support | How do we set up a template so every team member sends the same wording? New to this sorry | support | 0.75 | 0.55 |  | support | 0.86 | support | 0.93 |
| 7 | clean | technical | My login is not working. I enter my password, it spins and then goes back to the login page. Tried chrome and edge. | technical | 0.80 | 0.90 |  | technical | 1.00 | technical | 0.95 |
| 8 | clean | technical | there is a bug, the submit button on our form is greyed out for some users but not others | technical | 0.98 | 0.98 |  | technical | 1.00 | technical | 0.88 |
| 9 | clean | technical | Getting 502 errors from the API since about 10:30 this morning. Our batch job failed 3 times. | technical | 0.94 | 0.74 |  | technical | 1.00 | technical | 0.96 |
| 10 | clean | technical | les courriels ne partent plus depuis hier, le statut reste à 'sending' pendant des heures | technical | 0.42 | 0.59 | HUMAN (conf) | technical | 1.00 | technical | 0.93 |
| 11 | clean | technical | I think this is a bug?? The French version of our form shows English error messages. maybe we set it up wrong but it looks broken | technical | 0.88 | 0.87 |  | technical | 1.00 | technical | 0.62 |
| 12 | clean | technical | 2FA code never arrives on my phone. Already checked spam. Locked out for 2 days now, this is urgent | technical | 0.68 | 0.90 | HUMAN (conf) | technical | 1.00 | technical | 0.95 |
| 13 | clean | sales_billing | We are a regional agency and would like to use your messaging service for our customer alerts. Who do we talk to about onboarding? | sales_billing | 0.62 | 0.39 | HUMAN (conf,action) | sales_billing | 1.00 | sales_billing | 0.93 |
| 14 | clean | sales_billing | how much does this cost? our director wants a number before we commit to anything | sales_billing | 0.94 | 0.95 |  | sales_billing | 1.00 | sales_billing | 0.97 |
| 15 | clean | sales_billing | Our company is evaluating form builders. Could you do a 30 min demo for our VP next week? | sales_billing | 0.89 | 0.99 |  | sales_billing | 1.00 | sales_billing | 0.97 |
| 16 | clean | sales_billing | Nous aimerions explorer un partenariat entre nos deux équipes pour la prochaine année financière | sales_billing | 0.94 | 0.80 |  | sales_billing | 1.00 | sales_billing | 0.93 |
| 17 | clean | sales_billing | Is there an enterprise tier with an SLA? We'd need 99.9% for a program launching in Q4. | sales_billing | 0.86 | 0.97 |  | sales_billing | 0.97 | sales_billing | 0.93 |
| 18 | clean | sales_billing | Can we partner together on a pilot? We have budget for a small proof of concept | sales_billing | 0.96 | 0.94 |  | sales_billing | 1.00 | sales_billing | 0.96 |
| 19 | mixed | mixed | My login stopped working this morning, also how much would it cost to add 50 more users to our account? | technical | 0.20 | 0.95 | HUMAN (conf) | technical | 0.66 | sales_billing | 0.50 |
| 20 | mixed | mixed | How do I export responses to CSV? Also the export button throws an error when I click it so maybe that's the problem | support | 0.02 | 0.92 | HUMAN (conf) | technical | 0.79 | technical | 0.80 |
| 21 | mixed | mixed | We want to roll this out to the whole branch (about 400 people). Can someone walk us through pricing, and also can the forms do conditional logic? | sales_billing | 0.72 | 0.82 |  | sales_billing | 0.97 | sales_billing | 0.85 |
| 22 | mixed | mixed | bug report: emails going to spam. unrelated but we'd love to talk about a partnership for the fall campaign | sales_billing | 0.62 | 0.46 | HUMAN (conf,action) | technical | 0.38 | sales_billing | 0.55 |
| 23 | mixed | mixed | Quick how-to question about templates and also our API key seems to have stopped authenticating since yesterday | technical | 0.13 | 0.74 | HUMAN (conf) | technical | 0.98 | technical | 0.80 |
| 24 | mixed | mixed | hi, our VP wants a demo next week. before that can you tell me why the dashboard shows 0 sent messages when we sent 200 yesterday | technical | 0.61 | 0.98 | HUMAN (conf) | technical | 0.88 | sales_billing | 0.50 |
| 25 | noise | noise | Hey team, just circling back on the login thing we talked about at the townhall, not urgent, no bug or anything, just wanted to say the new dashboard looks great, pricing aside haha. Anyway have a good long weekend | sales_billing | 0.22 | 0.00 | HUMAN (conf,action) | support | 0.56 | support | 0.60 |
| 26 | noise | noise | Following up on my earlier follow up. Not sure if this is a technical thing or a sales thing or what. Just wanted to flag that I flagged it. Thanks! | support | 0.25 | 0.05 | HUMAN (conf,action) | support | 0.73 | support | 0.40 |
| 27 | noise | noise | Bonjour! Petit message pour dire merci pour la démo la semaine passée, pas de question, pas de bug, juste un merci. Bonne journée | sales_billing | 0.89 | 0.00 | HUMAN (action) | sales_billing | 0.82 | sales_billing | 0.55 |
| 28 | noise | noise | Random thought: has anyone ever considered that forms are kind of like emails but for data? Anyway, partnership vibes. Cheers | sales_billing | 0.95 | 0.01 | HUMAN (action) | sales_billing | 0.43 | sales_billing | 0.45 |
| 29 | noise | noise | test test is this thing on. ignore this. or don't. login, api, pricing, lol. just checking the contact form works | support | 0.49 | 0.06 | HUMAN (conf,action) | technical | 0.64 | support | 0.60 |
| 30 | noise | noise | Per my last email (see below, see above, see attached), no action needed, I just like to keep everyone in the loop re: the whole situation with the thing. | support | 0.83 | 0.00 | HUMAN (action) | support | 0.97 | support | 0.60 |
| 31 | trap | support | Bug: my colleague says there's a bug but really she just can't find the export button. Where is it? | support | 0.75 | 0.45 | HUMAN (action) | support | 1.00 | support | 0.90 |
| 32 | trap | technical | I'd like to buy more credits for our account but the checkout page returns a 500 error every time I click pay | technical | 0.54 | 0.98 | HUMAN (conf) | technical | 0.96 | technical | 0.60 |
| 33 | trap | sales_billing | How do I get our whole organisation set up? We'd need about 300 user licences and a signed agreement our VP can approve | sales_billing | 0.61 | 0.88 | HUMAN (conf) | sales_billing | 1.00 | sales_billing | 0.95 |
| 34 | trap | support | My login is not working because I forgot which email address I signed up with. How do I find out which one it was? | support | 0.59 | 0.73 | HUMAN (conf) | **technical** | 0.60 | support | 0.55 |
| 35 | trap | support | We partnered with another team and they shared a form with us. How do I edit a form someone else shared with me? | support | 0.83 | 0.93 |  | support | 1.00 | support | 0.93 |
| 36 | trap | technical | How do I make the form stop deleting my responses? Every submission since Monday just vanishes from the dashboard | technical | 0.07 | 0.84 | HUMAN (conf) | technical | 1.00 | technical | 0.85 |
| 37 | hard | technical | Something's off with the thing we set up last month, the numbers don't look like they did before. Not sure if it's us or you. | **sales_billing** | 0.87 | 0.20 | HUMAN (action) | technical | 0.98 | technical | 0.60 |
| 38 | hard | sales_billing | We've been going back and forth internally about whether to keep going with this. Would be good to chat. | sales_billing | 0.75 | 0.10 | HUMAN (action) | sales_billing | 0.73 | sales_billing | 0.80 |
| 39 | hard | support | Is it normal that it takes this long? | support | 0.97 | 0.02 | HUMAN (action) | support | 0.97 | support | 0.50 |
| 40 | hard | sales_billing | My director asked me to reach out. She had some concerns after the meeting. | **support** | 0.06 | 0.89 | HUMAN (conf) | sales_billing | 0.89 | sales_billing | 0.80 |
| 41 | hard | technical | I did what the guide said and it still looks the same. | **support** | 0.76 | 0.26 | HUMAN (action) | technical | 0.55 | **support** | 0.55 |
| 42 | hard | sales_billing | Hello, we are looking at options for next year and your name came up. Also one of our people couldn't get in last week, not sure if related. | sales_billing | 0.42 | 0.76 | HUMAN (conf) | sales_billing | 0.49 | sales_billing | 0.60 |
| 43 | hard | technical | The French is wrong. | **support** | 0.92 | 0.01 | HUMAN (action) | **support** | 0.64 | **support** | 0.60 |
| 44 | hard | sales_billing | Can you point me to whoever handles the agreement side of things? Our procurement people have questions. | sales_billing | 0.91 | 0.98 |  | sales_billing | 1.00 | sales_billing | 0.90 |
| 45 | hard | technical | Honestly not sure this is the right place to ask, but when we send to a big list some people say they got nothing and others got it twice. | **support** | 0.83 | 0.08 | HUMAN (action) | technical | 0.92 | technical | 0.85 |
| 46 | hard | support | Is there a way to make it do the other thing instead? The thing it does now isn't what we expected. | support | 0.91 | 0.42 | HUMAN (action) | support | 0.46 | support | 0.60 |
| 47 | hard | sales_billing | Following our chat on Tuesday, where do we go from here? | **support** | 0.38 | 0.17 | HUMAN (conf,action) | **support** | 0.68 | sales_billing | 0.40 |
| 48 | hard | support | Our team lead left and nobody knows how any of this was set up. Help. | support | 0.64 | 0.35 | HUMAN (conf,action) | **technical** | 0.72 | support | 0.40 |
| 49 | hard | technical | It's doing it again. | **support** | 0.03 | 0.04 | HUMAN (conf,action) | technical | 0.94 | technical | 0.60 |
| 50 | hard | sales_billing | Circling back on the thing from before. Any movement on your end? | **support** | 0.38 | 0.37 | HUMAN (conf,action) | **support** | 0.66 | **support** | 0.40 |
| 51 | hard | support | Which one am I supposed to click? | support | 0.20 | 0.05 | HUMAN (conf,action) | support | 0.83 | support | 0.60 |
| 52 | hard | technical | Since the update nothing feels right. | **support** | 0.73 | 0.06 | HUMAN (action) | technical | 0.76 | technical | 0.50 |
| 53 | hard | sales_billing | Our CEO's office has taken an interest. | **support** | 0.16 | 0.35 | HUMAN (conf,action) | sales_billing | 0.98 | sales_billing | 0.60 |
| 54 | hard | support | What's the difference between the two? | support | 0.72 | 0.04 | HUMAN (action) | support | 1.00 | support | 0.50 |
| 55 | hard | technical | Half of them came back. | **support** | 0.94 | 0.02 | HUMAN (action) | **support** | 0.55 | **support** | 0.35 |
| 56 | hard | sales_billing | We'd need something in writing before we can go further. | sales_billing | 0.87 | 0.98 |  | sales_billing | 1.00 | sales_billing | 0.60 |
| 57 | hard | support | Can it do the thing where you pick from a list? | support | 0.99 | 0.16 | HUMAN (action) | support | 1.00 | support | 0.80 |
| 58 | hard | technical | Error. Screenshot attached. | technical | 0.14 | 0.31 | HUMAN (conf,action) | technical | 1.00 | technical | 0.80 |
| 59 | hard | sales_billing | Who owns this relationship now that Marc has moved on? | **support** | 0.21 | 0.26 | HUMAN (conf,action) | sales_billing | 1.00 | sales_billing | 0.85 |
| 60 | hard | support | Where did the old version go? The new layout confuses our staff. | support | 0.97 | 0.85 |  | support | 0.91 | support | 0.72 |
