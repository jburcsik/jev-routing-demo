#!/usr/bin/env python3
"""Score the 250 Banking77 tickets with hosted Jev and Claude Sonnet via OpenRouter (team choice only).
Writes local/banking77_hosted.json. Needs OPENROUTER_API_KEY."""
import json, os, sys, time, urllib.error, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from run_banking77_local import TEAMS, Q
KEY = os.environ.get("OPENROUTER_API_KEY") or sys.exit("Set OPENROUTER_API_KEY")

def post(path, body):
    req = urllib.request.Request("https://openrouter.ai" + path, data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=90) as r:
        out = json.load(r)
    return out, (time.perf_counter() - t0) * 1000

def jev(text):
    out, ms = post("/api/alpha/decisions", {"model": "typesafe/jev-1.13", "state": text,
        "questions": {"team": {"type": "choice", "instructions": Q, "criteria": TEAMS}}})
    a = out["answers"]["team"]
    return {"pred": a["choice"], "conf": a["confidence"], "probs": a["probabilities"], "ms": ms, "cost": out["usage"]["cost"]}

def sonnet(text):
    prompt = (Q + "\nTeams:\n" + "\n".join(f"- {k}: {v}" for k, v in TEAMS.items())
              + '\nReply with a bare JSON object: {"team": "<support|technical|sales_billing>", "confidence": <0.0-1.0>}\n\nMessage:\n' + text)
    out, ms = post("/api/v1/chat/completions", {"model": "anthropic/claude-sonnet-5.5", "temperature": 0, "max_tokens": 1024,
                                               "messages": [{"role": "user", "content": prompt}], "usage": {"include": True}})
    raw = out["choices"][0]["message"]["content"] or ""; raw = raw[raw.find("{"): raw.rfind("}") + 1]
    try:
        d = json.loads(raw); pred, conf = d["team"], float(d.get("confidence", 0))
    except Exception:
        pred, conf = "??", 0.0
    return {"pred": pred, "conf": conf, "ms": ms, "cost": out["usage"].get("cost", 0)}

OUT = os.path.join(HERE, "banking77_hosted.json")

def main():
    """Resumable: rows already in banking77_hosted.json are kept; a 402 (no credit) stops the run cleanly."""
    data = json.load(open(os.path.join(HERE, "banking77_250.json")))
    rows = json.load(open(OUT))["rows"] if os.path.exists(OUT) else []
    done = {r["id"] for r in rows}
    for t in data["tickets"]:
        if t["id"] in done:
            continue
        try:
            j = jev(t["text"]); h = sonnet(t["text"])
        except urllib.error.HTTPError as e:
            if e.code == 402:
                print(f"stopped at ticket {t['id']}: OpenRouter credit exhausted (402). Top up and rerun to resume.", file=sys.stderr); break
            print("error", t["id"], e, file=sys.stderr); time.sleep(2); continue
        except Exception as e:
            print("error", t["id"], e, file=sys.stderr); time.sleep(2); continue
        rows.append({**t, "jev": j, "sonnet": h})
        if len(rows) % 25 == 0:
            print(len(rows), flush=True)
            json.dump({"rows": rows}, open(OUT, "w"), indent=1, ensure_ascii=False)
    json.dump({"rows": rows}, open(OUT, "w"), indent=1, ensure_ascii=False)
    print(f"{len(rows)}/{len(data['tickets'])} tickets scored")
    for m in ("jev", "sonnet"):
        acc = sum(r[m]["pred"] == r["team"] for r in rows) / len(rows)
        print(f"{m}: accuracy {acc:.3f}, avg {sum(r[m]['ms'] for r in rows)/len(rows):.0f} ms, cost ${sum(r[m]['cost'] for r in rows):.4f}")

if __name__ == "__main__":
    main()
