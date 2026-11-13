#!/usr/bin/env python3
"""Submit a file to a Kaggle competition via the MCP server, without ever
printing the signed URL or the blob token.

Steps:
  1. Ask the Kaggle MCP server for a competition submission upload session
     (token + create_url) via start_competition_submission_upload.
  2. PUT the file bytes to the signed GCS resumable session.
  3. Call submit_to_competition with the blob file token.
  4. Save the token to a 0600 file for audit (never print it).

Usage:
  python3 submit_competition.py <file> <competition_slug> "<submission description>"
Prints only status, byte counts and the submission response summary.
"""

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

BIN = os.path.expanduser("~/workspace/custom-connectors/custom.kaggle/bin")
CALLS = os.path.expanduser("~/workspace/custom-connectors/custom.kaggle/calls")
SCRATCH = os.path.expanduser("~/workspace/qcc-data/kaggle-subida")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args):
        raise RuntimeError("redirect refused, verify the endpoint")


def call_mcp(name, args):
    args_file = os.path.join(CALLS, f"_submit_{name}.json")
    with open(args_file, "w") as fh:
        json.dump(args, fh)
    result = subprocess.run(
        [sys.executable, os.path.join(BIN, "client.py"), "call-tool",
         "--name", name, "--arguments-file", args_file],
        capture_output=True, text=True, timeout=180,
    )
    if result.returncode != 0:
        print(f"MCP call {name} failed (exit {result.returncode}):", file=sys.stderr)
        print(result.stdout[-2000:], file=sys.stderr)
        print(result.stderr[-2000:], file=sys.stderr)
        sys.exit(1)
    payload = json.loads(result.stdout)
    if payload.get("isError"):
        print(f"MCP call {name} returned isError:", file=sys.stderr)
        print(result.stdout[-2000:], file=sys.stderr)
        sys.exit(1)
    return json.loads(payload["content"][0]["text"])


def get_upload_session(file_path, competition):
    size = os.path.getsize(file_path)
    mtime = int(os.path.getmtime(file_path))
    args = {
        "request": {
            "competitionName": competition,
            "hasCompetitionName": True,
            "contentLength": size,
            "lastModifiedEpochSeconds": mtime,
            "fileName": os.path.basename(file_path),
        }
    }
    data = call_mcp("start_competition_submission_upload", args)
    print("upload session response keys:", sorted(data.keys()), flush=True)
    if "token" not in data or "create_url" not in data:
        print("unexpected upload session response (keys only):", sorted(data.keys()), file=sys.stderr)
        sys.exit(1)
    return data["token"], data["create_url"], size


def upload_bytes(create_url, file_path, size):
    print(f"uploading {size} bytes to the signed session", flush=True)
    with open(file_path, "rb") as fh:
        request = urllib.request.Request(
            create_url,
            data=fh,
            method="PUT",
            headers={
                "Content-Type": "application/octet-stream",
                "Content-Length": str(size),
                "Content-Range": f"bytes 0-{size - 1}/{size}",
            },
        )
        try:
            with urllib.request.build_opener(NoRedirect()).open(request, timeout=900) as response:
                body = response.read()
                print(f"upload complete: HTTP {response.status}, {len(body)} bytes in response", flush=True)
        except urllib.error.HTTPError as error:
            detail = error.read()[:1000]
            print(f"upload failed: HTTP {error.code}: {detail!r}", file=sys.stderr)
            sys.exit(1)


def submit(competition, token, description):
    args = {
        "request": {
            "competitionName": competition,
            "blobFileTokens": token,
            "submissionDescription": description,
            "hasSubmissionDescription": True,
        }
    }
    data = call_mcp("submit_to_competition", args)
    print("submit_to_competition response keys:", sorted(data.keys()), flush=True)
    return data


def main():
    file_path, competition, description = sys.argv[1:4]
    os.makedirs(SCRATCH, exist_ok=True)
    token, create_url, size = get_upload_session(file_path, competition)
    # Save the token for audit, 0600, never printed.
    token_file = os.path.join(SCRATCH, "blob_token_qcc.json")
    with open(token_file, "w") as fh:
        json.dump({"competition": competition, "file": os.path.basename(file_path),
                   "size": size, "token": token}, fh)
    os.chmod(token_file, 0o600)
    print("upload session ready (token saved 0600, not printed)", flush=True)
    upload_bytes(create_url, file_path, size)
    data = submit(competition, token, description)
    out_file = os.path.join(SCRATCH, "submit_response.json")
    with open(out_file, "w") as fh:
        json.dump(data, fh, indent=1)
    # Print a summary without any token/URL.
    summary = {k: v for k, v in data.items()
               if k.lower() not in ("token", "create_url", "url", "blobfiletokens")}
    print("submission response summary:")
    print(json.dumps(summary, indent=1)[:3000], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
