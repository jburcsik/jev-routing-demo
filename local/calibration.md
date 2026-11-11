# Calibration on 250 Banking77 tickets

Source: PolyAI Banking77 test split (CC-BY-4.0), 250 queries stratified over all 77 intents, each intent mapped to one of three teams by a fixed table in `banking77_250.json`. 125 'fit' rows were used only to fit one temperature for the local model; every number below is on the other 125 'eval' rows unless stated. Flag threshold 0.7 throughout. ECE: 10 equal-width bins on top-label confidence. Brier: multi-class sum over the three teams.

Fitted temperature for the local model: **T = 0.95** (grid search on NLL over the fit half; T > 1 softens, T < 1 sharpens).

## Accuracy on all 250

| | Local OpenJev 4B | Jev 1.13 | Sonnet 5.5 |
|---|---|---|---|
| Routed correctly | 79.6% | 84.0% | 92.4% |
| Average latency | 1170 ms | 331 ms | 1742 ms |
| Cost | $0 | $0.0056 | $0.4437 |



## Calibration on the 125 eval rows

| System | Acc | ECE | Brier | Conf when right | Conf when wrong | Correct flagged (< 0.70) | Wrong unflagged (>= 0.70) | Distinct conf values |
|---|---|---|---|---|---|---|---|---|
| Local OpenJev 4B, raw (top prob) | 81.6% | 0.088 | 0.311 | 0.77 | 0.67 | 37/102 | 9/23 | 47 |
| Local OpenJev 4B, raw (margin) | 81.6% | 0.279 | n/a | 0.57 | 0.39 | 57/102 | 5/23 | 65 |
| Local OpenJev 4B, T=0.95 (top prob) | 81.6% | 0.077 | 0.310 | 0.78 | 0.68 | 36/102 | 9/23 | 48 |
| Jev 1.13 (its confidence field) | 84.8% | 0.064 | 0.194 | 0.87 | 0.51 | 15/106 | 4/19 | 39 |
| Jev 1.13 (top prob) | 84.8% | 0.040 | 0.194 | 0.92 | 0.67 | 8/106 | 8/19 | 39 |
| Sonnet 5.5 (self-reported) | 92.8% | 0.124 | n/a | 0.82 | 0.60 | 20/116 | 1/9 | 18 |

## Threshold sweep on the eval rows (correct flagged / wrong unflagged)

| Threshold | Local, T-scaled top prob | Jev confidence | Sonnet self-reported |
|---|---|---|---|
| 0.9 | 68 / 3 | 34 / 2 | 72 / 0 |
| 0.8 | 52 / 6 | 26 / 4 | 27 / 0 |
| 0.7 | 36 / 9 | 15 / 4 | 20 / 1 |
| 0.6 | 19 / 15 | 12 / 5 | 7 / 7 |
| 0.5 | 3 / 21 | 7 / 8 | 0 / 9 |

## Reliability, local model after temperature (eval rows)

| Confidence bin | n | Mean confidence | Accuracy |
|---|---|---|---|
| 0.4 to 0.5 | 5 | 0.45 | 0.60 |
| 0.5 to 0.6 | 22 | 0.55 | 0.73 |
| 0.6 to 0.7 | 23 | 0.66 | 0.74 |
| 0.7 to 0.8 | 19 | 0.76 | 0.84 |
| 0.8 to 0.9 | 19 | 0.86 | 0.84 |
| 0.9 to 1.0 | 37 | 0.95 | 0.92 |

## Reliability, Jev confidence (eval rows)

| Confidence bin | n | Mean confidence | Accuracy |
|---|---|---|---|
| 0.1 to 0.2 | 2 | 0.11 | 0.50 |
| 0.2 to 0.3 | 5 | 0.28 | 0.60 |
| 0.3 to 0.4 | 5 | 0.34 | 0.20 |
| 0.4 to 0.5 | 7 | 0.44 | 0.43 |
| 0.5 to 0.6 | 7 | 0.57 | 0.57 |
| 0.6 to 0.7 | 5 | 0.65 | 0.80 |
| 0.7 to 0.8 | 11 | 0.75 | 1.00 |
| 0.8 to 0.9 | 9 | 0.86 | 0.78 |
| 0.9 to 1.0 | 74 | 0.98 | 0.97 |

## Summary

- Accuracy on all 250: Sonnet 92.4%, Jev 84.0%, local 79.6%.
- Wrong answers caught at 0.70 (eval rows): Jev 15 of 19, Sonnet 8 of 9, local 14 of 23.
- Correct answers flagged at 0.70 (eval rows): Jev 15 of 106, Sonnet 20 of 116, local 36 of 102.
- 3 of Jev's 40 misses on all 250 are unanimous: all three models chose the same team against the label.
- Latency: Jev 331 ms, local 1170 ms, Sonnet 1742 ms. Cost for 250: Jev $0.0056, Sonnet $0.4437.
