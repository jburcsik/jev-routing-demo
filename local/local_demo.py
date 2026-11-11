#!/usr/bin/env python3
"""Run the 60 demo tickets through an open Jev-style decision model on this Mac.

Model: AlexWortega/openjev, checkpoint qwen3.5-4b-nli-v5 (MIT). A Qwen3.5-4B cross-encoder that
answers entailment / contradiction / neutral for a (premise, hypothesis) pair. A decision is scored
the way the author's JevBench adapter does it: every option becomes one hypothesis over the ticket,
P(entailment) is normalised over the options. One forward pass per option, nothing generated.

Usage:  local/.venv/bin/python local/local_demo.py          (first run downloads nothing; model must be in local/models)
Writes: local/results.json, local/results.md
"""
import json, os, sys, time
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MODEL_DIR = os.path.join(HERE, "models", "openjev", "qwen3.5-4b-nli-v5")
THRESHOLD = 0.70
ENT = 1
TEMPLATE = 'The answer to "{instr}" is {label}: {crit}'  # same hypothesis shape as the author's adapter

TEAMS = {
    "support": "Support, tier 1: questions a help-desk agent answers from existing documentation without opening the customer's account. How do I, can the product do X, where do I find Y, how long does something normally take, what are the limits. The default when neither of the other two teams applies.",
    "technical": "Technical, tier 2: something has gone wrong for this customer and someone must investigate their specific account, login, data or system. Login failing, errors, bugs, outages, messages not sending, things that look broken. Takes precedence over support when the customer's own account, data or system must be examined.",
    "sales_billing": "Sales and billing: money the company charges or the relationship itself. Pricing, costs, plans, onboarding a new organisation, demos, partnerships, contracts, agreements, and concerns raised by a customer's leadership. Takes precedence over the other teams whenever money or the relationship is the subject.",
}
TEAM_Q = "Which team should handle this message?"
ACTION_Q = "Does this message contain a concrete request or problem that someone needs to act on?"
ACTION_OPTS = {"no": "There is nothing concrete to act on.", "yes": "There is a concrete request or problem to act on."}


def load():
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(MODEL_DIR)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR, dtype=torch.bfloat16).to(device).eval()
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    tok.padding_side = "right"
    tc = model.config.get_text_config()
    if tc.pad_token_id is None:
        tc.pad_token_id = tok.pad_token_id
    template = getattr(model.config, "nli_template", None) or "Premise: {premise}\nHypothesis: {hypothesis}"
    backbone = getattr(model, model.base_model_prefix)
    return tok, model, backbone, template, device


@torch.no_grad()
def predict(pairs, tok, model, backbone, template, device):
    texts = [template.format(premise=p.strip(), hypothesis=h.strip()) for p, h in pairs]
    enc = tok(texts, truncation=True, max_length=4096, padding=True, return_tensors="pt")
    enc = {k: v.to(device) for k, v in enc.items()}
    h = backbone(**enc).last_hidden_state
    last = enc["attention_mask"].sum(1) - 1
    pooled = h[torch.arange(h.shape[0], device=h.device), last]
    return torch.softmax(model.score(pooled).float(), -1)[:, ENT].cpu().tolist()


def decide(text, ctx):
    pairs = [(text, TEMPLATE.format(instr=TEAM_Q, label=k, crit=v)) for k, v in TEAMS.items()]
    pairs += [(text, TEMPLATE.format(instr=ACTION_Q, label=k, crit=v)) for k, v in ACTION_OPTS.items()]
    t0 = time.perf_counter()
    ent = predict(pairs, *ctx)
    ms = (time.perf_counter() - t0) * 1000
    tp = ent[: len(TEAMS)]
    s = sum(tp) or 1e-9
    probs = {k: p / s for k, p in zip(TEAMS, tp)}
    ranked = sorted(probs.values(), reverse=True)
    team = max(probs, key=probs.get)
    conf = ranked[0] - ranked[1]  # margin over the runner-up; the hosted Jev's confidence formula is not published
    ap = ent[len(TEAMS):]
    action = ap[1] / ((ap[0] + ap[1]) or 1e-9)
    return {"team": team, "conf": conf, "probs": probs, "action": action, "ms": ms}


def main():
    tickets = json.load(open(os.path.join(ROOT, "tickets.json")))
    print("loading model...", end=" ", flush=True)
    t0 = time.perf_counter()
    ctx = load()
    print(f"{time.perf_counter() - t0:.0f} s on {ctx[-1]}")
    decide("warm up", ctx)

    rows = []
    hdr = f"{'#':>2} {'set:expected':15} | {'Local':9} {'conf':>5} {'act':>5} {'ms':>5} | message"
    print(hdr); print("-" * (len(hdr) + 40))
    for t in tickets:
        d = decide(t["text"], ctx)
        reasons = [r for r, hit in (("conf", d["conf"] < THRESHOLD), ("action", d["action"] < 0.5)) if hit]
        flag = "HUMAN (" + ",".join(reasons) + ")" if reasons else ""
        rows.append({**t, "local": d, "local_flag": flag})
        label = f"{t['set']}:{t['expected']}" if t["set"] in ("trap", "hard") else t["expected"]
        print(f"{t['id']:>2} {label:15} | {d['team']:9} {d['conf']:5.2f} {d['action']:5.2f} {d['ms']:5.0f} | "
              f"{t['text'][:50]}{'...' if len(t['text']) > 50 else ''}  {flag}")
    json.dump(rows, open(os.path.join(HERE, "results.json"), "w"), indent=1, ensure_ascii=False)
    write_report(rows)


def write_report(rows):
    import statistics as st
    hosted = {r["id"]: r for r in json.load(open(os.path.join(ROOT, "results.json")))}
    sc = [r for r in rows if r["set"] in ("clean", "trap", "hard")]
    def right(m, rs):
        return sum((r["local"]["team"] if m == "local" else hosted[r["id"]][m]["team"]) == r["expected"] for r in rs)
    def flagged(m, rs):
        return sum(bool(r["local_flag"] if m == "local" else (hosted[r["id"]]["jev_flag"] if m == "jev" else hosted[r["id"]]["sonnet"]["flag"])) for r in rs)
    def conf(m, r):
        return r["local"]["conf"] if m == "local" else hosted[r["id"]][m]["conf"]
    def team(m, r):
        return r["local"]["team"] if m == "local" else hosted[r["id"]][m]["team"]
    sets = {}
    for r in rows:
        sets.setdefault(r["set"], []).append(r)
    n = len(rows)
    lat = [r["local"]["ms"] for r in rows]
    agree_jev = sum(team("local", r) == team("jev", r) for r in rows)
    agree_sonnet = sum(team("local", r) == team("sonnet", r) for r in rows)
    md = ["# Local model results: OpenJev 4B v5 on this Mac", "",
          "Same 60 tickets, same two questions, same flag rules as the hosted run in `../results.json`. "
          "Model: AlexWortega/openjev `qwen3.5-4b-nli-v5` (Qwen3.5-4B cross-encoder, MIT), bf16 on Apple Silicon via PyTorch MPS. "
          "Confidence here is the margin between the top team probability and the runner-up; the hosted Jev's formula is not published, so the two confidence columns are not directly comparable.", "",
          "## Stats", "", "| | Local OpenJev 4B | Jev (hosted) | Sonnet 5.5 |", "|---|---|---|---|"]
    def row(label, f):
        md.append(f"| {label} | {f('local')} | {f('jev')} | {f('sonnet')} |")
    row("Routed correctly (clean, red herring, hard)", lambda m: f"{right(m, sc)}/{len(sc)}")
    for s, title in (("clean", "Clean"), ("trap", "Red herrings"), ("hard", "Hard and vague")):
        row(f"{title} routed correctly", lambda m, s=s: f"{right(m, sets[s])}/{len(sets[s])}")
    row("Mixed tickets sent to a human", lambda m: f"{flagged(m, sets['mixed'])}/{len(sets['mixed'])}")
    row("Noise tickets sent to a human", lambda m: f"{flagged(m, sets['noise'])}/{len(sets['noise'])}")
    row("Correct answers flagged anyway", lambda m: f"{sum(bool(r['local_flag'] if m=='local' else (hosted[r['id']]['jev_flag'] if m=='jev' else hosted[r['id']]['sonnet']['flag'])) for r in sc if team(m, r)==r['expected'])}")
    row("Wrong answers unflagged", lambda m: f"{sum(not (r['local_flag'] if m=='local' else (hosted[r['id']]['jev_flag'] if m=='jev' else hosted[r['id']]['sonnet']['flag'])) for r in sc if team(m, r)!=r['expected'])}")
    row("Mean confidence when right", lambda m: f"{st.mean([conf(m, r) for r in sc if team(m, r)==r['expected']] or [0]):.2f}")
    row("Mean confidence when wrong", lambda m: f"{st.mean([conf(m, r) for r in sc if team(m, r)!=r['expected']] or [0]):.2f}")
    row("Average latency per ticket", lambda m: f"{st.mean(lat if m=='local' else [hosted[r['id']][m]['ms'] for r in rows]):.0f} ms")
    row("Total time, all 60 calls", lambda m: f"{sum(lat if m=='local' else [hosted[r['id']][m]['ms'] for r in rows])/1000:.1f} s")
    row("Cost", lambda m: "$0 (laptop)" if m == "local" else f"${sum(hosted[r['id']][m]['cost'] for r in rows):.4f}")
    md += ["", f"Team agreement with Jev: {agree_jev}/{n}. With Sonnet: {agree_sonnet}/{n}.", "",
           "## All rows", "", "| # | Set | Expected | Ticket | Local team | Local conf | Local action | Local flag | Jev team | Jev conf | Sonnet team | Sonnet conf |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        h = hosted[r["id"]]; d = r["local"]
        w = lambda m, t: f"**{t}**" if r["set"] in ("clean", "trap", "hard") and t != r["expected"] else t
        md.append(f"| {r['id']} | {r['set']} | {r['expected']} | {r['text']} | {w('local', d['team'])} | {d['conf']:.2f} | {d['action']:.2f} | {r['local_flag']} | "
                  f"{w('jev', h['jev']['team'])} | {h['jev']['conf']:.2f} | {w('sonnet', h['sonnet']['team'])} | {h['sonnet']['conf']:.2f} |")
    open(os.path.join(HERE, "results.md"), "w").write("\n".join(md) + "\n")
    print("\nwrote local/results.json and local/results.md")


if __name__ == "__main__":
    main()
