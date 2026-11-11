#!/usr/bin/env python3
"""Score the 250 Banking77 tickets with the local OpenJev 4B (team choice only). Writes local/banking77_local.json
with the raw per-option entailment probabilities so calibration can be fitted afterwards."""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from local_demo import load, predict, TEMPLATE

HERE = os.path.dirname(os.path.abspath(__file__))
_D = json.load(open(os.path.join(HERE, "banking77_250.json")))
TEAMS, Q = _D["teams"], _D["question"]  # one definition, shared by every model


def main():
    data = json.load(open(os.path.join(HERE, "banking77_250.json")))
    print("loading model...", end=" ", flush=True); ctx = load(); print("ok")
    predict([("warm up", "x")], *ctx)
    out = []
    t_all = time.perf_counter()
    for t in data["tickets"]:
        pairs = [(t["text"], TEMPLATE.format(instr=Q, label=k, crit=v)) for k, v in TEAMS.items()]
        t0 = time.perf_counter(); ent = predict(pairs, *ctx); ms = (time.perf_counter() - t0) * 1000
        s = sum(ent) or 1e-9
        probs = {k: e / s for k, e in zip(TEAMS, ent)}
        out.append({**t, "entail": dict(zip(TEAMS, ent)), "probs": probs, "pred": max(probs, key=probs.get), "ms": ms})
        if t["id"] % 25 == 0: print(t["id"], f"{time.perf_counter() - t_all:.0f}s", flush=True)
    json.dump({"teams": TEAMS, "rows": out}, open(os.path.join(HERE, "banking77_local.json"), "w"), indent=1, ensure_ascii=False)
    acc = sum(r["pred"] == r["team"] for r in out) / len(out)
    print(f"done: accuracy {acc:.3f}, avg {sum(r['ms'] for r in out)/len(out):.0f} ms")

if __name__ == "__main__":
    main()
