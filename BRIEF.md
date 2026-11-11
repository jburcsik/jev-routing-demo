# Jev for ticket routing: what we tested and what we found

November 2026.

## What Jev is

Jev is a new AI model from TypeSafe AI (released 15 September 2026). It does not write text. You give it a message and a closed set of options; it returns one option plus a probability for each, in about 300 ms, for 4 cents per million input tokens. It is built for decisions software can act on: routing, classification, yes/no checks.

## What we did

1. Built a ticket router that asks two questions per ticket: which team, and is there anything to act on.
2. Ran the same tickets, same team definitions and same rules through three systems: Jev, a conventional LLM (Claude Sonnet 5.5), and a free open-source Jev-style model running on a laptop.
3. Tested on 60 invented tickets first, then on 250 real customer messages from a public banking support dataset (Banking77).
4. Defined the three teams by the work the handler does, not by how the customer sounds:

| Team | Test |
|---|---|
| Support | Can a help-desk agent answer it from existing documentation without opening the customer's account? |
| Technical | Does someone need to investigate this customer's own account, data or transaction? |
| Sales and billing | Is it about money we charge, or the relationship itself? |

Routing rule: sales and billing first, then technical, then support. A ticket is sent to a human when the model's confidence is under 0.70 or it finds nothing to act on.

## Results on 250 real tickets

| | Jev | Claude Sonnet | Open model, laptop |
|---|---|---|---|
| Routed to the right team | 84% | 92% | 80% |
| Confidence when right / when wrong | 0.87 / 0.51 | 0.82 / 0.60 | 0.78 / 0.68 |
| Wrong answers caught by the 0.70 rule | 15 of 19 | 8 of 9 | 14 of 23 |
| Correct answers sent to a human anyway | 15 of 106 | 20 of 116 | 36 of 102 |
| Time per ticket | 0.3 s | 1.7 s | 1.2 s |
| Cost for 250 tickets | $0.006 | $0.444 | $0 |

## Facts

- Accuracy: Sonnet 92%, Jev 84%, laptop model 80%.
- At a 0.70 cut-off, wrong answers reaching a queue on the 125 held-out tickets: Sonnet 1, Jev 4, laptop model 9.
- Speed: Jev 0.3 s per ticket, Sonnet 1.7 s.
- Cost per 1,000 tickets: Jev $0.02, Sonnet $1.77.
- Jev returns no explanation. It is text-only and hosted in the US.
- No real ticket text was sent to any model. All 310 tickets were invented or from a public dataset.
