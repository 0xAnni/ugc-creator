#!/usr/bin/env python3
"""
generate_image.py: render a UGC still on LivePair (livepairai.com).

This is the image step of the ugc-creator skill: you feed it the assembled
6-layer prompt (see references/prompt-layers.md) and it returns a local file
ready for the Kling image->video step (scripts/generate_video.py). Render in
9:16 so the clip inherits a vertical frame.

Identity lock: pass the actor's anchor render as --anchor and LivePair routes
to an image-edit model — the face carries, the scene changes. Same latch as
the face pack in references/reference-lock.md, one step instead of a train.

Setup (once):
    export LP_KEY="lp_..."   # create at https://livepairai.com/settings
                             # Windows PowerShell: $env:LP_KEY="lp_..."

Usage:
    python generate_image.py \
        --prompt "lila, young woman, chestnut hair, ... kitchen counter,
                  phone selfie, soft window light" \
        --anchor out/anchor.png \
        --aspect 9:16 --out out/still.png

Notes:
  * Per-result billing (~cents per image), no subscription — batch away.
  * Media URLs expire after 48h — this script downloads the file locally.
  * Source images are vision-screened server-side; use AI-generated or
    owned images only (https://livepairai.com terms).
  * Model catalog + ids: GET https://livepairai.com/v1/agent/models (free).
"""

import argparse
import base64
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_BASE = "https://livepairai.com"
DEFAULT_T2I_MODEL = "qwen-image-3"          # text-to-image
DEFAULT_I2I_MODEL = "qwen-image-3-edit"     # image-to-image edit (anchor runs)
POLL_INTERVAL_S = 2.0
POLL_TIMEOUT_S = 300.0


def log(msg):
    print(f"[ugc-creator] {msg}", file=sys.stderr)


def request(method, path, key, body=None, base=DEFAULT_BASE):
    req = urllib.request.Request(
        f"{base}{path}",
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Content-Type": "application/json", "x-api-key": key},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = json.loads(e.read()).get("error", "")
        except Exception:
            pass
        raise SystemExit(f"livepair HTTP {e.code}: {detail}")


def data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prompt", required=True, help="assembled 6-layer prompt")
    ap.add_argument("--anchor", help="approved face render — switches to the i2i edit model")
    ap.add_argument("--model", help="override model id (default: qwen-image-3 / qwen-image-3-edit with --anchor)")
    ap.add_argument("--aspect", default="9:16", help="aspect ratio, e.g. 9:16, 1:1, 16:9")
    ap.add_argument("--out", default="out/still.png")
    ap.add_argument("--base", default=DEFAULT_BASE)
    args = ap.parse_args()

    key = os.environ.get("LP_KEY")
    if not key:
        raise SystemExit("LP_KEY not set — create a key at https://livepairai.com/settings")

    body = {
        "modelId": args.model or (DEFAULT_I2I_MODEL if args.anchor else DEFAULT_T2I_MODEL),
        "prompt": args.prompt,
        "aspectRatio": args.aspect,
    }
    if args.anchor:
        body["image"] = data_uri(Path(args.anchor))
        log(f"anchored i2i render off {args.anchor}")

    res = request("POST", "/v1/agent/generate", key, body, args.base)
    url = res.get("url")
    if not url:
        job_id = res.get("jobId")
        if not job_id:
            raise SystemExit(f"no jobId in response: {res}")
        deadline = time.time() + POLL_TIMEOUT_S
        while time.time() < deadline:
            job = request("GET", f"/v1/agent/jobs/{job_id}", key, base=args.base)
            if job.get("status") == "done" and job.get("url"):
                url = job["url"]
                break
            if job.get("status") == "failed":
                raise SystemExit(f"job failed: {job.get('error', 'unknown')}")
            time.sleep(POLL_INTERVAL_S)
        else:
            raise SystemExit(f"job {job_id} did not finish in {POLL_TIMEOUT_S}s")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(urllib.request.urlopen(url, timeout=120).read())
    print(str(out))


if __name__ == "__main__":
    main()
