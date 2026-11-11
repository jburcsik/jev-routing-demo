# Jev ticket routing benchmark

Jev (TypeSafe AI, `typesafe/jev-1.13`) is a decision model: it takes a message and a closed set of options and returns one option with a probability for each. It generates no text. [OpenRouter docs](https://openrouter.ai/docs/guides/community/jev).

This repo routes support tickets to one of three teams with three systems: Jev, Claude Sonnet 5.5, and OpenJev 4B (an open Jev-style model) on a laptop. Same tickets, team definitions and flag rule for all three. Run on Nov 10 2026.

## Results

**60 invented tickets** (48 with one correct team):

| | Jev | Sonnet 5.5 | OpenJev 4B, laptop |
|---|---|---|---|
| Routed correctly | 42/48 | 44/48 | 36/48 |
| Wrong answers unflagged | 1 | 0 | 0 |
| Correct answers flagged | 8 | 16 | 18 |
| Noise tickets flagged | 6/6 | 6/6 | 6/6 |
| Mixed (two-ask) tickets flagged | 2/6 | 3/6 | 5/6 |
| Mean latency | 0.33 s | 1.36 s | 2.05 s |
| Cost | $0.0014 | $0.1000 | $0 |

**250 Banking77 tickets** (accuracy on all 250; confidence rows on the 125 held-out rows; details in [local/calibration.md](local/calibration.md)):

| | Jev | Sonnet 5.5 | OpenJev 4B, laptop |
|---|---|---|---|
| Routed correctly | 84.0% | 92.4% | 79.6% |
| Mean confidence, right / wrong | 0.87 / 0.51 | 0.82 / 0.60 | 0.78 / 0.68 |
| Wrong answers caught at 0.70 | 15 of 19 | 8 of 9 | 14 of 23 |
| Correct answers flagged at 0.70 | 15 of 106 | 20 of 116 | 36 of 102 |
| ECE | 0.064 | 0.124 | 0.077 |
| Mean latency | 0.33 s | 1.74 s | 1.17 s |
| Cost | $0.0056 | $0.4437 | $0 |
| Cost per 1,000 tickets | $0.022 | $1.77 | $0 |

**Findings**

- Accuracy on Banking77: Sonnet 92.4%, Jev 84.0%, OpenJev 4B 79.6%.
- At a 0.70 cut-off, Sonnet lets 1 of 125 held-out tickets reach the wrong queue; Jev 4; OpenJev 9.
- Jev is 4.2x faster than Sonnet on the invented set and 79x cheaper on Banking77.
- No system reliably flags tickets with two requests: Jev 2/6, Sonnet 3/6.

**Limits**

- One run per system.
- One LLM tested. Haiku 5.5 was not tested.
- Three teams only.
- No real support-queue tickets: 60 invented, 250 from Banking77 mapped to three teams.
- Sonnet writes reasoning before its JSON, so it gets up to 1,024 output tokens.

## Method

Each ticket gets two questions in one call.

| Key | Type | Question | Returned |
|---|---|---|---|
| `team` | choice | Which team should handle this message? | Chosen team, a probability per team, a confidence |
| `action` | yes/no | Does this message contain a concrete request or problem that someone needs to act on? | Probability of yes |

Teams, as sent to every model:

| Team | Description |
|---|---|
| support | Support, tier 1: questions a help-desk agent answers from existing documentation without opening the customer's account. How do I, can the product do X, where do I find Y, how long does something normally take, what are the limits. The default when neither of the other two teams applies. |
| technical | Technical, tier 2: something has gone wrong for this customer and someone must investigate their specific account, login, data or system. Login failing, errors, bugs, outages, messages not sending, things that look broken. Takes precedence over support when the customer's own account, data or system must be examined. |
| sales_billing | Sales and billing: money the company charges or the relationship itself. Pricing, costs, plans, onboarding a new organisation, demos, partnerships, contracts, agreements, and concerns raised by a customer's leadership. Takes precedence over the other teams whenever money or the relationship is the subject. |

- Jev: both questions through `POST /api/alpha/decisions`. Confidence comes from its output distribution.
- Sonnet: one prompt, temperature 0, reply as JSON with team, team confidence (0 to 1) and action probability. Confidence is self-reported.
- Flag rule, same for all: team confidence < 0.70 or action < 0.50 sends the ticket to a human.

Example Jev request and response (ticket 19):

```json
{
  "model": "typesafe/jev-1.13",
  "state": "My login stopped working this morning, also how much would it cost to add 50 more users to our account?",
  "questions": {
    "team":   {"type": "choice", "instructions": "Which team should handle this message?",
               "criteria": {"support": "...", "technical": "...", "sales_billing": "..."}},
    "action": {"type": "noul", "instructions": "Does this message contain a concrete request or problem ...?"}
  }
}
```

```json
{
  "model": "typesafe/jev-1.13-20260917",
  "answers": {
    "team":   {"type": "choice", "choice": "technical",
               "probabilities": {"technical": 0.60, "support": 0.25, "sales_billing": 0.15}, "confidence": 0.40},
    "action": {"type": "noul", "noul": 0.98}
  },
  "usage": {"input_tokens": 448, "output_tokens": 71, "cost": 0.000018816}
}
```

## Data

| Set | Count | Content |
|---|---|---|
| Clean | 18 | 6 per team, unambiguous |
| Mixed | 6 | Two requests in one message |
| Noise | 6 | Nothing to act on |
| Red herring | 6 | Keywords point to one team, content to another |
| Hard | 24 | Vague, short, no keywords |

All 60 tickets are invented, in English and French. Every row and both models' answers are in [full-results.md](full-results.md).

## Results by set

| Set | Jev correct | Sonnet correct | Jev flagged | Sonnet flagged |
|---|---|---|---|---|
| Clean | 18/18 | 18/18 | 0 | 1 |
| Red herring | 5/6 | 6/6 | 1 | 2 |
| Hard | 19/24 | 20/24 | 12 | 17 |
| Mixed | n/a | n/a | 2/6 | 3/6 |
| Noise | n/a | n/a | 6/6 | 6/6 |

Wrong answers, with confidence:

| # | Expected | Ticket | Jev team | Jev conf | Jev action | Jev flag | Sonnet team | Sonnet conf | Sonnet action | Sonnet flag |
|---|---|---|---|---|---|---|---|---|---|---|
| 34 | support | My login is not working because I forgot which email address I signed up with. How do I find out which one it was? | **technical** | 0.60 | 0.96 | HUMAN (conf) | support | 0.55 | 0.80 | HUMAN (conf) |
| 41 | technical | I did what the guide said and it still looks the same. | technical | 0.55 | 0.71 | HUMAN (conf) | **support** | 0.55 | 0.60 | HUMAN (conf) |
| 43 | technical | The French is wrong. | **support** | 0.64 | 0.10 | HUMAN (conf,action) | **support** | 0.60 | 0.45 | HUMAN (conf,action) |
| 47 | sales_billing | Following our chat on Tuesday, where do we go from here? | **support** | 0.68 | 0.73 | HUMAN (conf) | sales_billing | 0.40 | 0.60 | HUMAN (conf) |
| 48 | support | Our team lead left and nobody knows how any of this was set up. Help. | **technical** | 0.72 | 0.90 |  | support | 0.40 | 0.55 | HUMAN (conf) |
| 50 | sales_billing | Circling back on the thing from before. Any movement on your end? | **support** | 0.66 | 0.51 | HUMAN (conf) | **support** | 0.40 | 0.60 | HUMAN (conf) |
| 55 | technical | Half of them came back. | **support** | 0.55 | 0.07 | HUMAN (conf,action) | **support** | 0.35 | 0.15 | HUMAN (conf,action) |

## Confidence

| | Jev | Sonnet 5.5 |
|---|---|---|
| Mean confidence when right | 0.93 | 0.78 |
| Mean confidence when wrong | 0.64 | 0.47 |
| Confidence on each wrong answer | 0.60, 0.64, 0.68, 0.72, 0.66, 0.55 | 0.55, 0.60, 0.40, 0.35 |
| Distinct confidence values, 60 tickets | 26 | 16 |

## Latency and cost (60 tickets)

| | Jev | Sonnet 5.5 |
|---|---|---|
| Mean latency | 326 ms | 1364 ms |
| Fastest / slowest | 251 / 884 ms | 914 / 3559 ms |
| Total cost | $0.0014 | $0.1000 |
| Price on OpenRouter | $0.042 per M input, output free | $2 per M input, $10 per M output |

## Local model

`local/` runs OpenJev 4B (MIT, 8.5 GB) on Apple Silicon against the same 60 tickets and the 250 Banking77 tickets. See [local/README.md](local/README.md) and [local/calibration.md](local/calibration.md).

## Run it

```
set -a; . ./.env; set +a      # .env holds OPENROUTER_API_KEY
python3 demo.py               # 60 tickets, Jev and Sonnet; writes results.json
python3 demo.py --jev-only
python3 build_readme.py       # rebuilds README.md and full-results.md from results.json
```

`demo.py` uses the standard library only.

## Licence and credits

Code, the 60 invented tickets and the write-ups: MIT, see `LICENSE`.

`local/banking77_250.json` holds 250 queries sampled from Banking77 (Casanueva et al., 2020, "Efficient Intent Detection with Dual Sentence Encoders", PolyAI, https://huggingface.co/datasets/PolyAI/banking77), CC BY 4.0. Changes: a 250-query sample, 77 intents mapped to three teams, 12 labels overridden after review (marked `override`). That file stays under CC BY 4.0.

No model weights are in this repo. Jev and Claude Sonnet are reached through OpenRouter under their providers' terms. This project is independent and not affiliated with TypeSafe AI, Anthropic, OpenRouter or PolyAI.
