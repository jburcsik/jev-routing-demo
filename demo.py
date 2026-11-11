#!/usr/bin/env python3
"""Jev vs Claude Sonnet: route synthetic support tickets to a team.

Usage:  OPENROUTER_API_KEY=sk-or-... python3 demo.py [--jev-only]
"""
import json, os, sys, time, urllib.request

KEY = os.environ.get("OPENROUTER_API_KEY") or sys.exit("Set OPENROUTER_API_KEY")
JEV = "typesafe/jev-1.13"
LLM = "anthropic/claude-sonnet-5.5"
THRESHOLD = 0.70  # below this, Jev's answer goes to a human
JEV_ONLY = "--jev-only" in sys.argv

TEAMS = {
    "support": "Support, tier 1: questions a help-desk agent answers from existing documentation without opening the customer's account. How do I, can the product do X, where do I find Y, how long does something normally take, what are the limits. The default when neither of the other two teams applies.",
    "technical": "Technical, tier 2: something has gone wrong for this customer and someone must investigate their specific account, login, data or system. Login failing, errors, bugs, outages, messages not sending, things that look broken. Takes precedence over support when the customer's own account, data or system must be examined.",
    "sales_billing": "Sales and billing: money the company charges or the relationship itself. Pricing, costs, plans, onboarding a new organisation, demos, partnerships, contracts, agreements, and concerns raised by a customer's leadership. Takes precedence over the other teams whenever money or the relationship is the subject.",
}
ROUTE_Q = "Which team should handle this message?"


def post(path, body):
    req = urllib.request.Request(
        "https://openrouter.ai" + path,
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
    )
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=60) as r:
        out = json.load(r)
    return out, (time.perf_counter() - t0) * 1000


def ask_jev(text):
    body = {
        "model": JEV,
        "state": text,
        "questions": {
            "team": {
                "type": "choice",
                "instructions": ROUTE_Q,
                "criteria": TEAMS,
            },
            "action": {
                "type": "noul",
                "instructions": "Does this message contain a concrete request or problem that someone needs to act on?",
            },
        },
    }
    out, ms = post("/api/alpha/decisions", body)
    a = out["answers"]
    return {
        "team": a["team"]["choice"],
        "conf": a["team"]["confidence"],
        "probs": a["team"]["probabilities"],
        "action": a["action"]["noul"],
        "ms": ms,
        "cost": out["usage"]["cost"],
    }


def ask_llm(text):
    prompt = (
        "You triage support messages. Answer two questions about the message below.\n"
        "1. team: " + ROUTE_Q + "\n"
        + "\n".join(f"   - {k}: {v}" for k, v in TEAMS.items())
        + "\n   Also give team_confidence, 0.0 to 1.0, how sure you are of the team.\n"
        "2. action: probability 0.0 to 1.0 that the message contains a concrete request or problem that someone needs to act on.\n"
        'Reply with a bare JSON object only: {"team": "<support|technical|sales_billing>", "team_confidence": <0-1>, "action": <0-1>}\n\n'
        "Message:\n" + text
    )
    body = {
        "model": LLM,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": 1024,
        "usage": {"include": True},
    }
    out, ms = post("/api/v1/chat/completions", body)
    raw = out["choices"][0]["message"]["content"] or ""
    raw = raw[raw.find("{"): raw.rfind("}") + 1]
    try:
        d = json.loads(raw)
        team, conf, action = d["team"], float(d["team_confidence"]), float(d["action"])
    except Exception:
        team, conf, action = f"?? {raw[:20]}", 0.0, 1.0
    return {"team": team, "conf": conf, "action": action, "ms": ms, "cost": out["usage"].get("cost", 0)}


def main():
    tickets = json.load(open(os.path.join(os.path.dirname(__file__), "tickets.json")))
    tot = {"jev_ms": 0, "jev_cost": 0, "llm_ms": 0, "llm_cost": 0}
    ok = {"clean": [0, 0, 0], "trap": [0, 0, 0], "hard": [0, 0, 0], "mixed": [0, 0, 0], "noise": [0, 0, 0]}
    disagree = []; jc = {"right": [], "wrong": []}; lc = {"right": [], "wrong": []}; rows = []  # [jev, llm, n] or [flagged, n]
    hdr = f"{'#':>2} {'set:expected':15} | {'Jev':9} {'conf':>5} {'act':>5} {'ms':>5} | {'Sonnet':9} {'conf':>5} {'act':>5} {'ms':>6} | message"
    print(hdr)
    print("-" * (len(hdr) + 40))
    for t in tickets:
        j = ask_jev(t["text"])
        reasons = [r for r, hit in (("conf", j["conf"] < THRESHOLD), ("action", j["action"] < 0.5)) if hit]
        flag = "HUMAN (" + ",".join(reasons) + ")" if reasons else ""
        l = ask_llm(t["text"]) if not JEV_ONLY else {"team": "-", "conf": 0, "action": 1, "ms": 0, "cost": 0}
        lr = [r for r, hit in (("conf", l["conf"] < THRESHOLD), ("action", l["action"] < 0.5)) if hit]
        l["flag"] = "HUMAN (" + ",".join(lr) + ")" if (lr and not JEV_ONLY) else ""
        rows.append({**t, "jev": j, "sonnet": l, "jev_flag": flag})
        tot["jev_ms"] += j["ms"]; tot["jev_cost"] += j["cost"]
        tot["llm_ms"] += l["ms"]; tot["llm_cost"] += l["cost"]
        b = ok[t["set"]]
        if t["set"] in ("mixed", "noise"):
            b[0] += bool(flag); b[1] += 1; b[2] += bool(l["flag"])
        else:
            b[0] += j["team"] == t["expected"]; b[1] += l["team"] == t["expected"]; b[2] += 1
            jc["right" if j["team"] == t["expected"] else "wrong"].append(j["conf"])
            lc["right" if l["team"] == t["expected"] else "wrong"].append(l["conf"])
            if j["team"] != l["team"]:
                disagree.append((t["id"], t["expected"], j["team"], j["conf"], l["team"], l["conf"]))
        label = f"{t['set']}:{t['expected']}" if t["set"] in ("trap", "hard") else t["expected"]
        print(
            f"{t['id']:>2} {label:15} | {j['team']:9} {j['conf']:5.2f} {j['action']:5.2f} {j['ms']:5.0f} | "
            f"{l['team']:9} {l['conf']:5.2f} {l['action']:5.2f} {l['ms']:6.0f} | {t['text'][:50]}{'...' if len(t['text']) > 50 else ''}  {flag} {l['flag']}"
        )
    n = len(tickets)
    json.dump(rows, open(os.path.join(os.path.dirname(__file__), "results.json"), "w"), indent=1, ensure_ascii=False)
    print()
    print(f"Clean tickets routed correctly:        Jev {ok['clean'][0]}/{ok['clean'][2]}   Sonnet {ok['clean'][1]}/{ok['clean'][2]}")
    print(f"Red-herring tickets routed correctly:  Jev {ok['trap'][0]}/{ok['trap'][2]}   Sonnet {ok['trap'][1]}/{ok['trap'][2]}")
    print(f"Hard/vague tickets routed correctly:   Jev {ok['hard'][0]}/{ok['hard'][2]}   Sonnet {ok['hard'][1]}/{ok['hard'][2]}")
    print(f"Mixed tickets flagged for a human:     Jev {ok['mixed'][0]}/{ok['mixed'][1]}   Sonnet {ok['mixed'][2]}/{ok['mixed'][1]}")
    print(f"Noise tickets flagged for a human:     Jev {ok['noise'][0]}/{ok['noise'][1]}   Sonnet {ok['noise'][2]}/{ok['noise'][1]}")
    print(f"Flag rule: conf < {THRESHOLD} or action < 0.5")
    avg = lambda xs: sum(xs) / len(xs) if xs else float("nan")
    print(f"Mean confidence when right:   Jev {avg(jc['right']):.2f}   Sonnet {avg(lc['right']):.2f}")
    print(f"Mean confidence when wrong:   Jev {avg(jc['wrong']):.2f}   Sonnet {avg(lc['wrong']):.2f}   (n: Jev {len(jc['wrong'])}, Sonnet {len(lc['wrong'])})")
    if disagree:
        print(f"\nDisagreements ({len(disagree)}):  #  expected | Jev (conf) | Sonnet (conf)")
        for d in disagree:
            print(f"  {d[0]:>2} {d[1]:9} | {d[2]} ({d[3]:.2f}) | {d[4]} ({d[5]:.2f})")
    print(f"Avg latency:  Jev {tot['jev_ms']/n:.0f} ms   Sonnet {tot['llm_ms']/n:.0f} ms")
    print(f"Total cost:   Jev ${tot['jev_cost']:.5f}   Sonnet ${tot['llm_cost']:.5f}")


if __name__ == "__main__":
    main()
