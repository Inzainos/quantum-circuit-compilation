#!/usr/bin/env python3
"""Poll Kaggle for the public score of submission 58277509 (QCC adopted ZIP).
Checks search_competition_submissions (Date, pageSize 5) every 300 s.
Exits 0 when public_score appears; exits 2 after 20 polls (~100 min) without
a score. Logs every check with a UTC timestamp to poll.log. Prints only
status/score, never tokens.
Usage: python3 -u poll_score.py
"""
import json
import os
import subprocess
import sys
import time

BIN = os.path.expanduser("~/workspace/custom-connectors/custom.kaggle/bin")
CALLS = os.path.expanduser("~/workspace/custom-connectors/custom.kaggle/calls")
SCRATCH = os.path.expanduser("~/workspace/qcc-data/kaggle-subida")
REF = 58277509
COMPETITION = "google-verifiable-quantum-circuit-compilation"
INTERVAL = 300
MAX_POLLS = 20


def log(msg):
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(os.path.join(SCRATCH, "poll.log"), "a") as fh:
        fh.write(line + "\n")


def search():
    args_file = os.path.join(CALLS, "_search_qcc_poll.json")
    with open(args_file, "w") as fh:
        json.dump({"request": {"competitionName": COMPETITION, "sortBy": "Date",
                               "group": "All", "hasPageSize": True, "pageSize": 5}}, fh)
    result = subprocess.run(
        [sys.executable, os.path.join(BIN, "client.py"), "call-tool",
         "--name", "search_competition_submissions", "--arguments-file", args_file],
        capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        return None, f"client exit {result.returncode}: {result.stderr[-300:]}"
    payload = json.loads(result.stdout)
    if payload.get("isError"):
        return None, f"isError: {result.stdout[-500:]}"
    parsed = json.loads(payload["content"][0]["text"])
    subs = parsed if isinstance(parsed, list) else parsed.get("submissions", parsed.get("result", []))
    if isinstance(subs, str):
        subs = json.loads(subs)
    for s in subs:
        if s.get("ref") == REF:
            return s, None
    return None, "ref not in first 5 (unexpected)"


def main():
    for i in range(1, MAX_POLLS + 1):
        sub, err = search()
        if err:
            log(f"poll {i}: ERROR {err}")
        elif sub is None:
            log(f"poll {i}: submission {REF} not found")
        else:
            score = sub.get("public_score")
            status = sub.get("status")
            if score is not None:
                log(f"poll {i}: SCORED public_score={score} status={status}")
                with open(os.path.join(SCRATCH, "score.json"), "w") as fh:
                    json.dump(sub, fh, indent=1)
                with open(os.path.join(SCRATCH, "search_final.json"), "w") as fh:
                    json.dump(sub, fh, indent=1)
                return 0
            log(f"poll {i}: pending (no public_score yet; status={status})")
        if i < MAX_POLLS:
            time.sleep(INTERVAL)
    log(f"timeout after {MAX_POLLS} polls (~{MAX_POLLS * INTERVAL // 60} min): no score yet")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
