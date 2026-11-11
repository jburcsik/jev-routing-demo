#!/usr/bin/env python3
"""Rebuild README.md from results.json (written by demo.py). Observation text lives here."""
import json, os, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(HERE, "results.json")))
S = {}
for r in R:
    S.setdefault(r["set"], []).append(r)

def bold_if(cond, s):
    return f"**{s}**" if cond else s

def table(rows, expected_col=True, mark_wrong=False):
    hdr = "| # | Expected | Ticket | Jev team | Jev conf | Jev action | Jev flag | Sonnet team | Sonnet conf | Sonnet action | Sonnet flag |"
    sep = "|---|---|---|---|---|---|---|---|---|---|---|"
    out = [hdr, sep]
    for r in rows:
        j, h = r["jev"], r["sonnet"]
        jw = mark_wrong and j["team"] != r["expected"]
        hw = mark_wrong and h["team"] != r["expected"]
        out.append(
            f"| {r['id']} | {r['expected']} | {r['text']} | {bold_if(jw, j['team'])} | {j['conf']:.2f} | {j['action']:.2f} | {r['jev_flag']} | "
            f"{bold_if(hw, h['team'])} | {h['conf']:.2f} | {h['action']:.2f} | {h['flag']} |"
        )
    return "\n".join(out)

def right(rows, m): return sum(r[m]["team"] == r["expected"] for r in rows)
def flagged(rows, m): return sum(bool(r["jev_flag"] if m == "jev" else r["sonnet"]["flag"]) for r in rows)

scorable = [r for r in R if r["set"] not in ("mixed", "noise")]
def confs(m, ok):
    return [r[m]["conf"] for r in scorable if (r[m]["team"] == r["expected"]) == ok]
jr, jw, hr, hw = confs("jev", True), confs("jev", False), confs("sonnet", True), confs("sonnet", False)
distinct = lambda m: len(set(round(r[m]["conf"], 2) for r in R))
lat = lambda m: (st.mean(r[m]["ms"] for r in R), min(r[m]["ms"] for r in R), max(r[m]["ms"] for r in R))
cost = lambda m: sum(r[m]["cost"] for r in R)
jl, hl = lat("jev"), lat("sonnet")
jc, hc = cost("jev"), cost("sonnet")
n = len(R)
hard = S["hard"]

md = f"""# Jev ticket routing benchmark

Jev (TypeSafe AI, `typesafe/jev-1.13`) is a decision model: it takes a message and a closed set of options and returns one option with a probability for each. It generates no text. [OpenRouter docs](https://openrouter.ai/docs/guides/community/jev).

This repo routes support tickets to one of three teams with three systems: Jev, Claude Sonnet 5.5, and OpenJev 4B (an open Jev-style model) on a laptop. Same tickets, team definitions and flag rule for all three. Run on Nov 10 2026.

## Results

**{n} invented tickets** ({len(scorable)} with one correct team):

| | Jev | Sonnet 5.5 | OpenJev 4B, laptop |
|---|---|---|---|
| Routed correctly | {len(jr)}/{len(scorable)} | {len(hr)}/{len(scorable)} | 36/48 |
| Wrong answers unflagged | {sum(not r['jev_flag'] for r in scorable if r['jev']['team']!=r['expected'])} | {sum(not r['sonnet']['flag'] for r in scorable if r['sonnet']['team']!=r['expected'])} | 0 |
| Correct answers flagged | {sum(bool(r['jev_flag']) for r in scorable if r['jev']['team']==r['expected'])} | {sum(bool(r['sonnet']['flag']) for r in scorable if r['sonnet']['team']==r['expected'])} | 18 |
| Noise tickets flagged | {flagged(S['noise'],'jev')}/{len(S['noise'])} | {flagged(S['noise'],'sonnet')}/{len(S['noise'])} | 6/6 |
| Mixed (two-ask) tickets flagged | {flagged(S['mixed'],'jev')}/{len(S['mixed'])} | {flagged(S['mixed'],'sonnet')}/{len(S['mixed'])} | 5/6 |
| Mean latency | {jl[0]/1000:.2f} s | {hl[0]/1000:.2f} s | 2.05 s |
| Cost | ${jc:.4f} | ${hc:.4f} | $0 |

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
- Jev is {hl[0]/jl[0]:.1f}x faster than Sonnet on the invented set and 79x cheaper on Banking77.
- No system reliably flags tickets with two requests: Jev {flagged(S['mixed'],'jev')}/6, Sonnet {flagged(S['mixed'],'sonnet')}/6.

**Limits**

- One run per system.
- One LLM tested. Haiku 5.5 was not tested.
- Three teams only.
- No real support-queue tickets: {n} invented, 250 from Banking77 mapped to three teams.
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
{{
  "model": "typesafe/jev-1.13",
  "state": "My login stopped working this morning, also how much would it cost to add 50 more users to our account?",
  "questions": {{
    "team":   {{"type": "choice", "instructions": "Which team should handle this message?",
               "criteria": {{"support": "...", "technical": "...", "sales_billing": "..."}}}},
    "action": {{"type": "noul", "instructions": "Does this message contain a concrete request or problem ...?"}}
  }}
}}
```

```json
{{
  "model": "typesafe/jev-1.13-20260917",
  "answers": {{
    "team":   {{"type": "choice", "choice": "technical",
               "probabilities": {{"technical": 0.60, "support": 0.25, "sales_billing": 0.15}}, "confidence": 0.40}},
    "action": {{"type": "noul", "noul": 0.98}}
  }},
  "usage": {{"input_tokens": 448, "output_tokens": 71, "cost": 0.000018816}}
}}
```

## Data

| Set | Count | Content |
|---|---|---|
| Clean | {len(S['clean'])} | 6 per team, unambiguous |
| Mixed | {len(S['mixed'])} | Two requests in one message |
| Noise | {len(S['noise'])} | Nothing to act on |
| Red herring | {len(S['trap'])} | Keywords point to one team, content to another |
| Hard | {len(S['hard'])} | Vague, short, no keywords |

All {n} tickets are invented, in English and French. Every row and both models' answers are in [full-results.md](full-results.md).

## Results by set

| Set | Jev correct | Sonnet correct | Jev flagged | Sonnet flagged |
|---|---|---|---|---|
| Clean | {right(S['clean'],'jev')}/{len(S['clean'])} | {right(S['clean'],'sonnet')}/{len(S['clean'])} | {flagged(S['clean'],'jev')} | {flagged(S['clean'],'sonnet')} |
| Red herring | {right(S['trap'],'jev')}/{len(S['trap'])} | {right(S['trap'],'sonnet')}/{len(S['trap'])} | {flagged(S['trap'],'jev')} | {flagged(S['trap'],'sonnet')} |
| Hard | {right(hard,'jev')}/{len(hard)} | {right(hard,'sonnet')}/{len(hard)} | {flagged(hard,'jev')} | {flagged(hard,'sonnet')} |
| Mixed | n/a | n/a | {flagged(S['mixed'],'jev')}/{len(S['mixed'])} | {flagged(S['mixed'],'sonnet')}/{len(S['mixed'])} |
| Noise | n/a | n/a | {flagged(S['noise'],'jev')}/{len(S['noise'])} | {flagged(S['noise'],'sonnet')}/{len(S['noise'])} |

Wrong answers, with confidence:

{table([r for r in scorable if r['jev']['team']!=r['expected'] or r['sonnet']['team']!=r['expected']], mark_wrong=True)}

## Confidence

| | Jev | Sonnet 5.5 |
|---|---|---|
| Mean confidence when right | {st.mean(jr):.2f} | {st.mean(hr):.2f} |
| Mean confidence when wrong | {st.mean(jw):.2f} | {st.mean(hw):.2f} |
| Confidence on each wrong answer | {', '.join(f'{x:.2f}' for x in jw)} | {', '.join(f'{x:.2f}' for x in hw)} |
| Distinct confidence values, {n} tickets | {distinct('jev')} | {distinct('sonnet')} |

## Latency and cost ({n} tickets)

| | Jev | Sonnet 5.5 |
|---|---|---|
| Mean latency | {jl[0]:.0f} ms | {hl[0]:.0f} ms |
| Fastest / slowest | {jl[1]:.0f} / {jl[2]:.0f} ms | {hl[1]:.0f} / {hl[2]:.0f} ms |
| Total cost | ${jc:.4f} | ${hc:.4f} |
| Price on OpenRouter | $0.042 per M input, output free | $2 per M input, $10 per M output |

## Local model

`local/` runs OpenJev 4B (MIT, 8.5 GB) on Apple Silicon against the same 60 tickets and the 250 Banking77 tickets. See [local/README.md](local/README.md) and [local/calibration.md](local/calibration.md).

## Run it

```
set -a; . ./.env; set +a      # .env holds OPENROUTER_API_KEY
python3 demo.py               # {n} tickets, Jev and Sonnet; writes results.json
python3 demo.py --jev-only
python3 build_readme.py       # rebuilds README.md and full-results.md from results.json
```

`demo.py` uses the standard library only.

## Licence and credits

Code, the {n} invented tickets and the write-ups: MIT, see `LICENSE`.

`local/banking77_250.json` holds 250 queries sampled from Banking77 (Casanueva et al., 2020, "Efficient Intent Detection with Dual Sentence Encoders", PolyAI, https://huggingface.co/datasets/PolyAI/banking77), CC BY 4.0. Changes: a 250-query sample, 77 intents mapped to three teams, 12 labels overridden after review (marked `override`). That file stays under CC BY 4.0.

No model weights are in this repo. Jev and Claude Sonnet are reached through OpenRouter under their providers' terms. This project is independent and not affiliated with TypeSafe AI, Anthropic, OpenRouter or PolyAI.
"""
open(os.path.join(HERE, "README.md"), "w").write(md)
full = "# Full results, all " + str(n) + " tickets\n\nSame run as README.md.\n\n"
for name, title in (("clean", "Clean"), ("mixed", "Mixed"), ("noise", "Noise"), ("trap", "Red herrings"), ("hard", "Hard and vague")):
    full += f"## {title}\n\n" + table(S[name], mark_wrong=name in ("trap", "hard")) + "\n\n"
full += f"""## Stats

| | Jev | Sonnet 5.5 |
|---|---|---|
| Tickets | {n} | {n} |
| Routed correctly (clean, red herring, hard) | {len(jr)}/{len(scorable)} | {len(hr)}/{len(scorable)} |
| Mixed tickets sent to a human | {flagged(S['mixed'],'jev')}/{len(S['mixed'])} | {flagged(S['mixed'],'sonnet')}/{len(S['mixed'])} |
| Noise tickets sent to a human | {flagged(S['noise'],'jev')}/{len(S['noise'])} | {flagged(S['noise'],'sonnet')}/{len(S['noise'])} |
| Mean confidence when right | {st.mean(jr):.2f} | {st.mean(hr):.2f} |
| Mean confidence when wrong | {st.mean(jw):.2f} | {st.mean(hw):.2f} |
| Average latency per ticket | {jl[0]:.0f} ms | {hl[0]:.0f} ms |
| Total time, all {n} calls | {sum(r['jev']['ms'] for r in R)/1000:.1f} s | {sum(r['sonnet']['ms'] for r in R)/1000:.1f} s |
| Total cost | ${jc:.4f} | ${hc:.4f} |
"""
open(os.path.join(HERE, "full-results.md"), "w").write(full)
print("README.md written,", len(md.splitlines()), "lines")
