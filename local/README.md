# Running a Jev-style model locally

Jev's weights are closed. The idea is not: score a closed set of options from a model's own
probabilities, generate nothing. Several open reproductions exist, most on Qwen. This folder runs one
of them on this Mac against the same 60 tickets as the hosted demo.

## Model

| | |
|---|---|
| Checkpoint | `AlexWortega/openjev`, subfolder `qwen3.5-4b-nli-v5` |
| Base | Qwen3.5-4B, trained as a 3-way NLI cross-encoder (entailment / contradiction / neutral) |
| Licence | MIT, ungated |
| Size on disk | 8.5 GB bf16 |
| JevBench v1.2 public (231 items) | 0.814 vs Jev 1.13 at 0.866 |
| Runtime here | PyTorch 2.14 on Apple Silicon (MPS), bf16, Python 3.12 venv |

How a decision is scored, same as the author's JevBench adapter: each option becomes a hypothesis over
the ticket, `The answer to "<question>" is <option>: <rubric>`. P(entailment) is normalised across the
options. Five forward passes per ticket (three teams, yes/no for action), one batch, nothing generated.

Confidence here is the margin between the top team and the runner-up. The hosted Jev's confidence
formula is not published, so the two confidence columns are not on the same scale.

## Results on the 60 tickets

Same tickets, questions, team definitions and flag rules as the hosted run in `../results.json`. Confidence here is the margin between the top team and the runner-up; Jev's formula is not published, so the confidence columns are not on one scale.

| | Local OpenJev 4B | Jev (hosted) | Sonnet 5.5 |
|---|---|---|---|
| Routed correctly (clean, red herring, hard) | 36/48 | 42/48 | 44/48 |
| Clean | 18/18 | 18/18 | 18/18 |
| Red herrings | 6/6 | 5/6 | 6/6 |
| Hard and vague | 12/24 | 19/24 | 20/24 |
| Mixed tickets sent to a human | 5/6 | 2/6 | 3/6 |
| Noise tickets sent to a human | 6/6 | 6/6 | 6/6 |
| Correct answers flagged anyway | 18 | 8 | 16 |
| Wrong answers unflagged | 0 | 1 | 0 |
| Mean confidence when right / wrong | 0.75 / 0.52 | 0.93 / 0.64 | 0.78 / 0.47 |
| Average latency per ticket | 2052 ms | 326 ms | 1364 ms |
| Cost | $0 | $0.0014 | $0.1000 |

Team agreement with Jev: 46/60. With Sonnet: 48/60. Full rows in `results.md`.

- 11 of the 12 local misses go to support.
- Noise action scores: 0.00 to 0.06.
- Latency is about 2 s per ticket on Apple Silicon. The Qwen3.5 linear-attention kernels have no Apple Silicon build and fall back to reference PyTorch.
- Memory: about 9 GB.

## Run it

    cd jev-routing-demo
    /opt/homebrew/bin/python3.12 -m venv local/.venv
    local/.venv/bin/pip install -r local/requirements.txt
    local/.venv/bin/python -c "from huggingface_hub import snapshot_download; snapshot_download('AlexWortega/openjev', allow_patterns=['qwen3.5-4b-nli-v5/*'], local_dir='local/models/openjev')"
    local/.venv/bin/python local/local_demo.py

First run: 9 GB download, 20 s model load, then about 80 s for the 60 tickets. Writes `local/results.json` and `local/results.md`. The venv and the model folder are gitignored.

## Other open options

| Project | Base | Notes |
|---|---|---|
| SemIf (TheoLeeCJ), formerly OpenJev | Qwen3.5-4B | JevBench 73.1 vs Jev 74.4, the closest open score |
| Open-Jev 27B v1.1 (Zefan Cai) | Qwen3.5-27B + LoRA | 85.3% of 231 public items, Apache 2.0, needs the pinned Qwen base |
| Laya (Convai) | ModernBERT-large 421M | MLX build, fastest on Apple Silicon, lower accuracy |
| NanoJev, agent-jev | Qwen3-0.6B | tiny, ship their whole training pipeline |
| openjev/openjev (Loop AI) | open base | CC BY-NC, not for work use without a licence |

## Calibration on real tickets

`calibration.md`: 250 Banking77 queries (PolyAI, Casanueva et al. 2020, CC BY 4.0, https://huggingface.co/datasets/PolyAI/banking77), 77 intents mapped to three teams, half used to fit a temperature for the local model, half to measure accuracy, ECE and Brier against hosted Jev and Sonnet.

Teams are defined by the work the handler does, with a precedence rule (sales and billing, then technical, then support) in the team descriptions. Definitions live in `banking77_250.json`; every model receives the same text:

| Team | Test | Banking77 intents |
|---|---|---|
| support | Answerable from documentation without opening the account | 34: how to top up, change PIN, forgot passcode, delivery estimate, pending status, how to get a card |
| technical | Someone must investigate this customer's account, card, device or transaction | 27: declined, failed, blocked, not received, not showing up, charged twice, unrecognised, lost or stolen, card never arrived |
| sales_billing | Money the company charges or products it offers | 16: fees, exchange rates, unexpected charge on statement, supported currencies and countries, age limit, close account |

12 rows are overridden against their intent after review, each marked `override` in `banking77_250.json`.

| On 250 real tickets | Local OpenJev 4B (T=0.95) | Jev 1.13 | Sonnet 5.5 |
|---|---|---|---|
| Routed correctly | 79.6% | 84.0% | 92.4% |
| ECE (125 eval rows) | 0.077 | 0.064 | 0.124 |
| Brier | 0.310 | 0.194 | n/a |
| Confidence when right / wrong | 0.78 / 0.68 | 0.87 / 0.51 | 0.82 / 0.60 |
| Wrong answers caught at 0.70 | 14 of 23 | 15 of 19 | 8 of 9 |
| Latency | 1170 ms | 331 ms | 1742 ms |

