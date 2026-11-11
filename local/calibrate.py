#!/usr/bin/env python3
"""Fit a temperature on the Banking77 'fit' half, measure calibration on the 'eval' half, compare with hosted Jev
and Sonnet. Reads banking77_local.json and banking77_hosted.json, writes local/calibration.md."""
import json, math, os
HERE = os.path.dirname(os.path.abspath(__file__))
L = json.load(open(os.path.join(HERE, "banking77_local.json")))["rows"]
HP = os.path.join(HERE, "banking77_hosted.json")
H = {r["id"]: r for r in json.load(open(HP))["rows"]} if os.path.exists(HP) else {}
HOSTED = len(H) == len(L)  # hosted comparison only when every ticket was scored
TEAMS = list(L[0]["probs"].keys())
THR = 0.70

def softmax_T(logits, T):
    m = max(logits); e = [math.exp((x - m) / T) for x in logits]; s = sum(e); return [x / s for x in e]

def local_probs(r, T):
    return dict(zip(TEAMS, softmax_T([math.log(max(r["entail"][k], 1e-9)) for k in TEAMS], T)))

def nll(rows, T):
    return -sum(math.log(max(local_probs(r, T)[r["team"]], 1e-9)) for r in rows) / len(rows)

def ece(confs, correct, bins=10):
    tot = 0.0; n = len(confs)
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        idx = [i for i, c in enumerate(confs) if (lo < c <= hi) or (b == 0 and c == 0)]
        if idx:
            acc = sum(correct[i] for i in idx) / len(idx); conf = sum(confs[i] for i in idx) / len(idx)
            tot += len(idx) / n * abs(acc - conf)
    return tot

def brier(prob_dicts, golds):
    return sum(sum((p[k] - (1.0 if k == g else 0.0)) ** 2 for k in TEAMS) for p, g in zip(prob_dicts, golds)) / len(golds)

def summarise(name, preds, confs, golds, prob_dicts=None):
    correct = [p == g for p, g in zip(preds, golds)]
    right = [c for c, ok in zip(confs, correct) if ok]; wrong = [c for c, ok in zip(confs, correct) if not ok]
    d = {"system": name, "n": len(golds), "acc": sum(correct) / len(golds), "ece": ece(confs, correct),
         "conf_right": sum(right) / len(right) if right else float("nan"), "conf_wrong": sum(wrong) / len(wrong) if wrong else float("nan"),
         "flag_correct": sum(c < THR for c in right), "n_right": len(right), "wrong_unflagged": sum(c >= THR for c in wrong), "n_wrong": len(wrong),
         "distinct": len(set(round(c, 2) for c in confs))}
    d["brier"] = brier(prob_dicts, golds) if prob_dicts else float("nan")
    return d

fit = [r for r in L if r["split"] == "fit"]; ev = [r for r in L if r["split"] == "eval"]
# temperature: grid search on NLL over the fit half
grid = [x / 20 for x in range(2, 121)]  # 0.10 .. 6.00
T = min(grid, key=lambda t: nll(fit, t))
golds = [r["team"] for r in ev]
rows = []
# local, raw (T=1), confidence = top prob
pr = [local_probs(r, 1.0) for r in ev]; rows.append(summarise("Local OpenJev 4B, raw (top prob)", [max(p, key=p.get) for p in pr], [max(p.values()) for p in pr], golds, pr))
# local, raw, confidence = margin (the demo's definition)
rows.append(summarise("Local OpenJev 4B, raw (margin)", [max(p, key=p.get) for p in pr], [sorted(p.values())[-1] - sorted(p.values())[-2] for p in pr], golds))
# local, temperature-scaled, top prob
pt = [local_probs(r, T) for r in ev]; rows.append(summarise(f"Local OpenJev 4B, T={T:.2f} (top prob)", [max(p, key=p.get) for p in pt], [max(p.values()) for p in pt], golds, pt))
if HOSTED:
    jp = [H[r["id"]]["jev"]["probs"] for r in ev]; jpred = [H[r["id"]]["jev"]["pred"] for r in ev]
    rows.append(summarise("Jev 1.13 (its confidence field)", jpred, [H[r["id"]]["jev"]["conf"] for r in ev], golds, jp))
    rows.append(summarise("Jev 1.13 (top prob)", jpred, [max(p.values()) for p in jp], golds, jp))
    rows.append(summarise("Sonnet 5.5 (self-reported)", [H[r["id"]]["sonnet"]["pred"] for r in ev], [H[r["id"]]["sonnet"]["conf"] for r in ev], golds))

# flag-rate sweep for local after T and for Jev conf
def sweep(confs, correct):
    out = []
    for t in (0.9, 0.8, 0.7, 0.6, 0.5):
        out.append((t, sum(c < t for c, ok in zip(confs, correct) if ok), sum(c >= t for c, ok in zip(confs, correct) if not ok)))
    return out
lc = [max(p.values()) for p in pt]; lcorr = [max(p, key=p.get) == g for p, g in zip(pt, golds)]
fmt = lambda x, f: f.format(x) if HOSTED else "pending"
all_acc = {"local": sum(max(local_probs(r,1.0), key=local_probs(r,1.0).get) == r["team"] for r in L) / len(L)}
lat = {"local": sum(r["ms"] for r in L) / len(L)}
cost = {}
if HOSTED:
    jc = [H[r["id"]]["jev"]["conf"] for r in ev]; jcorr = [p == g for p, g in zip(jpred, golds)]
    hc = [H[r["id"]]["sonnet"]["conf"] for r in ev]; hcorr = [H[r["id"]]["sonnet"]["pred"] == g for r, g in zip(ev, golds)]
    for m in ("jev", "sonnet"):
        all_acc[m] = sum(H[r["id"]][m]["pred"] == r["team"] for r in L) / len(L)
        lat[m] = sum(H[r["id"]][m]["ms"] for r in L) / len(L)
        cost[m] = sum(H[r["id"]][m]["cost"] for r in L)

md = [f"# Calibration on 250 Banking77 tickets", "",
      "Source: PolyAI Banking77 test split (CC-BY-4.0), 250 queries stratified over all 77 intents, each intent mapped to one of three teams by a fixed table in `banking77_250.json`. "
      "125 'fit' rows were used only to fit one temperature for the local model; every number below is on the other 125 'eval' rows unless stated. "
      f"Flag threshold {THR} throughout. ECE: 10 equal-width bins on top-label confidence. Brier: multi-class sum over the three teams.", "",
      f"Fitted temperature for the local model: **T = {T:.2f}** (grid search on NLL over the fit half; T > 1 softens, T < 1 sharpens).", "",
      "## Accuracy on all 250", "", "| | Local OpenJev 4B | Jev 1.13 | Sonnet 5.5 |", "|---|---|---|---|",
      f"| Routed correctly | {all_acc['local']:.1%} | {fmt(all_acc.get('jev'), '{:.1%}')} | {fmt(all_acc.get('sonnet'), '{:.1%}')} |",
      f"| Average latency | {lat['local']:.0f} ms | {fmt(lat.get('jev'), '{:.0f} ms')} | {fmt(lat.get('sonnet'), '{:.0f} ms')} |",
      f"| Cost | $0 | {fmt(cost.get('jev'), '${:.4f}')} | {fmt(cost.get('sonnet'), '${:.4f}')} |", "",
      "" if HOSTED else f"Hosted comparison pending: {len(H)}/{len(L)} tickets scored before the OpenRouter credit ran out. Rerun `run_banking77_hosted.py` to resume.", "",
      "## Calibration on the 125 eval rows", "",
      "| System | Acc | ECE | Brier | Conf when right | Conf when wrong | Correct flagged (< 0.70) | Wrong unflagged (>= 0.70) | Distinct conf values |", "|---|---|---|---|---|---|---|---|---|"]
for d in rows:
    b = "n/a" if math.isnan(d["brier"]) else f"{d['brier']:.3f}"
    md.append(f"| {d['system']} | {d['acc']:.1%} | {d['ece']:.3f} | {b} | {d['conf_right']:.2f} | {d['conf_wrong']:.2f} | {d['flag_correct']}/{d['n_right']} | {d['wrong_unflagged']}/{d['n_wrong']} | {d['distinct']} |")
md += ["", "## Threshold sweep on the eval rows (correct flagged / wrong unflagged)", "", "| Threshold | Local, T-scaled top prob | Jev confidence | Sonnet self-reported |", "|---|---|---|---|"]
js = sweep(jc, jcorr) if HOSTED else [(t, "-", "-") for t in (0.9, 0.8, 0.7, 0.6, 0.5)]
hs = sweep(hc, hcorr) if HOSTED else js
for (t, a, b), (_, c, d2), (_, e, f) in zip(sweep(lc, lcorr), js, hs):
    md.append(f"| {t:.1f} | {a} / {b} | {c} / {d2} | {e} / {f} |")
md += ["", "## Reliability, local model after temperature (eval rows)", "", "| Confidence bin | n | Mean confidence | Accuracy |", "|---|---|---|---|"]
for b in range(10):
    lo, hi = b / 10, (b + 1) / 10
    idx = [i for i, c in enumerate(lc) if lo < c <= hi]
    if idx:
        md.append(f"| {lo:.1f} to {hi:.1f} | {len(idx)} | {sum(lc[i] for i in idx)/len(idx):.2f} | {sum(lcorr[i] for i in idx)/len(idx):.2f} |")
md += ["", "## Reliability, Jev confidence (eval rows)", "", "| Confidence bin | n | Mean confidence | Accuracy |", "|---|---|---|---|"]
for b in (range(10) if HOSTED else []):
    lo, hi = b / 10, (b + 1) / 10
    idx = [i for i, c in enumerate(jc) if lo < c <= hi]
    if idx:
        md.append(f"| {lo:.1f} to {hi:.1f} | {len(idx)} | {sum(jc[i] for i in idx)/len(idx):.2f} | {sum(jcorr[i] for i in idx)/len(idx):.2f} |")
if HOSTED:
    allw = [r for r in L if H[r["id"]]["jev"]["pred"] != r["team"]]
    unanimous = sum(H[r["id"]]["jev"]["pred"] == max(local_probs(r,1.0), key=local_probs(r,1.0).get) == H[r["id"]]["sonnet"]["pred"] for r in allw)
    R = {d["system"]: d for d in rows}
    lo = R[f"Local OpenJev 4B, T={T:.2f} (top prob)"]; jv = R["Jev 1.13 (its confidence field)"]; hk = R["Sonnet 5.5 (self-reported)"]
    md += ["", "## Summary", "",
    f"- Accuracy on all 250: Sonnet {all_acc['sonnet']:.1%}, Jev {all_acc['jev']:.1%}, local {all_acc['local']:.1%}.",
    f"- Wrong answers caught at 0.70 (eval rows): Jev {jv['n_wrong'] - jv['wrong_unflagged']} of {jv['n_wrong']}, Sonnet {hk['n_wrong'] - hk['wrong_unflagged']} of {hk['n_wrong']}, local {lo['n_wrong'] - lo['wrong_unflagged']} of {lo['n_wrong']}.",
    f"- Correct answers flagged at 0.70 (eval rows): Jev {jv['flag_correct']} of {jv['n_right']}, Sonnet {hk['flag_correct']} of {hk['n_right']}, local {lo['flag_correct']} of {lo['n_right']}.",
    f"- {unanimous} of Jev's {len(allw)} misses on all 250 are unanimous: all three models chose the same team against the label.",
    f"- Latency: Jev {lat['jev']:.0f} ms, local {lat['local']:.0f} ms, Sonnet {lat['sonnet']:.0f} ms. Cost for 250: Jev ${cost['jev']:.4f}, Sonnet ${cost['sonnet']:.4f}."]
open(os.path.join(HERE, "calibration.md"), "w").write("\n".join(md) + "\n")
print("\n".join(md))
