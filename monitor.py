"""Live monitor — watch every agent act during a run.

Run in a separate terminal (or `claude --bg` session); it follows the newest
run in runs/ and renders each step as the orchestrator writes it. Start it
before or after launching a run — it switches to a newer run file if one appears.

    python monitor.py                # follow the newest/active run
    python monitor.py runs/x.jsonl   # follow a specific file
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

C = {"dim": "\033[2m", "b": "\033[1m", "cyan": "\033[36m", "yellow": "\033[33m",
     "green": "\033[32m", "red": "\033[31m", "mag": "\033[35m", "x": "\033[0m"}


def newest(runs="runs") -> Path | None:
    fs = sorted(Path(runs).glob("*.jsonl"), key=lambda p: p.stat().st_mtime)
    return fs[-1] if fs else None


def render(r: dict) -> None:
    role = r["role"]
    who = f"{C['b']}{r['agent_id']}{C['x']}"
    if role.startswith("sentinel"):
        who = f"{C['mag']}{C['b']}{r['agent_id']}{C['x']} {C['dim']}({role}){C['x']}"
    tail = ""
    if r.get("reported_phase"):
        tail = f"  {C['yellow']}⟶ reports: {r['reported_phase']}{C['x']}"
    print(f"  {who}{tail}")
    for a in r["actions"]:
        code = a["exit_code"]
        mark = f"{C['green']}✓{C['x']}" if code == 0 else f"{C['red']}✗{code}{C['x']}"
        out = a["output"].strip().replace("\n", " ⏎ ")[:66]
        print(f"     {mark} {C['cyan']}$ {a['command'][:74]}{C['x']}")
        if out:
            print(f"        {C['dim']}{out}{C['x']}")
    if not r["actions"] and r["assistant_text"].strip():
        print(f"     {C['dim']}\"{r['assistant_text'].strip()[:74]}\"{C['x']}")


def follow(path: Path) -> None:
    print(f"{C['dim']}── watching {path.name} ──{C['x']}")
    cur_step = None
    with path.open() as f:
        while True:
            line = f.readline()
            if not line:
                # if a newer run started, switch to it
                n = newest()
                if n and n != path and n.stat().st_mtime > path.stat().st_mtime + 1:
                    print(f"\n{C['dim']}── new run: {n.name} ──{C['x']}")
                    return follow(n)
                time.sleep(0.3)
                continue
            r = json.loads(line)
            if r["step"] != cur_step:
                cur_step = r["step"]
                gt = r["ground_truth_phase"]
                print(f"\n{C['b']}── step {cur_step} {C['x']}{C['dim']}│ ground truth: "
                      f"{C['x']}{C['green']}{gt}{C['x']}")
            render(r)


def main() -> None:
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
    else:
        path = newest()
        while path is None:
            print("waiting for a run in runs/ ...", end="\r")
            time.sleep(0.5)
            path = newest()
    try:
        follow(path)
    except KeyboardInterrupt:
        print("\nstopped.")


if __name__ == "__main__":
    main()
