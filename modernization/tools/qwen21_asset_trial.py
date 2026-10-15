"""Submit one reference-preserving image trial to the local managed Qwen-Image 2.1 workbench.

No game asset is overwritten. This helper uses LocalModelManager's loopback
workbench gateway, which queues the GPU job and its ComfyUI children.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import mimetypes
import time
import urllib.parse
import urllib.request
from pathlib import Path


BASE = "http://127.0.0.1:8790/workbench"
PROMPT = (
    "Restore and enhance this exact vintage fantasy game's blank open grimoire backdrop. "
    "Keep the same 4:3 straight-on composition, the exact book and page outline, "
    "black surrounding margin, central spine, tabs, metal clasps, aged brown parchment "
    "color, placement and empty readable page surfaces. Enhance only fine leather, "
    "paper and metal texture detail. No writing, symbols, characters, added objects, "
    "new decorations, crop, viewpoint change, or altered page boundaries."
)


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.load(response)


def cancel_job(job_id: str) -> None:
    request = urllib.request.Request(
        BASE + "/api/keyframe2/jobs/" + urllib.parse.quote(job_id) + "/cancel",
        data=b"{}", headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        json.load(response)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--size", default="1024x768")
    parser.add_argument("--steps", type=int, default=40)
    parser.add_argument("--seed", type=int, default=260926)
    parser.add_argument("--job-id", help="Resume a previously submitted managed job")
    parser.add_argument("--timeout", type=int, default=1200)
    parser.add_argument("--prompt", default=PROMPT)
    args = parser.parse_args()

    source = args.source.resolve(strict=True)
    output = args.output.resolve()
    if source == output:
        parser.error("output must differ from source")
    if output.exists():
        parser.error("output exists; choose a new candidate filename")
    mime = mimetypes.guess_type(source.name)[0]
    if mime not in {"image/jpeg", "image/png", "image/bmp"}:
        parser.error("source must be JPEG, PNG or BMP")
    raw = source.read_bytes()
    if args.job_id:
        job_id = args.job_id
    else:
        health = get_json(BASE + "/api/keyframe2/status")
        if not health.get("engines", {}).get("qwen21", {}).get("ok"):
            raise RuntimeError("Managed Qwen-Image 2.1 is unavailable")
        payload = {
            "engine": "qwen21",
            "reference_images": [f"data:{mime};base64," + base64.b64encode(raw).decode("ascii")],
            "prompt": args.prompt,
            "negative_prompt": "text, letters, logos, new objects, changed layout, distorted pages",
            "nickname": "Magic and Mayhem restoration trial",
            "quality": "quality",
            "size": args.size,
            "steps": args.steps,
            "seed": args.seed,
            "per_round": 1,
            "official_prompt_enhance": False,
            "transparent": False,
        }
        request = urllib.request.Request(
            BASE + "/api/keyframe2/jobs",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=45) as response:
            submitted = json.load(response)
        job_id = submitted["job"]["id"]
    print("Managed Qwen-Image 2.1 job:", job_id, flush=True)
    deadline = time.monotonic() + args.timeout
    last_phase = None
    try:
        while time.monotonic() < deadline:
            job = get_json(BASE + "/api/keyframe2/jobs/" + urllib.parse.quote(job_id))["job"]
            if job.get("engine") != "qwen21" or job.get("prompt") != args.prompt:
                raise RuntimeError("Job identity does not match this Qwen trial")
            phase = (job.get("status"), job.get("phase"), job.get("progress"))
            if phase != last_phase:
                print(*phase, flush=True)
                last_phase = phase
            if job["status"] in {"completed", "failed", "canceled"}:
                break
            time.sleep(2)
        else:
            raise TimeoutError("Managed job timed out; ID: " + job_id)
    except (KeyboardInterrupt, TimeoutError):
        if not args.job_id:
            cancel_job(job_id)
        raise
    if job["status"] != "completed":
        raise RuntimeError("Qwen-Image 2.1 job " + job["status"] + ": " + str(job.get("phase")))
    candidate = next((seq.get("primary") for seq in job["sequences"] if seq.get("primary")), None)
    if not candidate or not candidate.get("url"):
        raise RuntimeError("Completed job has no downloadable primary result")
    media_url = urllib.parse.urljoin("http://127.0.0.1:8790", candidate["url"])
    if not media_url.startswith(BASE + "/api/"):
        raise RuntimeError("Result URL is outside the Manager workbench gateway")
    with urllib.request.urlopen(media_url, timeout=60) as response:
        generated = response.read()
    if not generated.startswith(b"\x89PNG\r\n\x1a\n"):
        raise RuntimeError("Result is not a PNG")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(generated)
    manifest = {
        "status": "experimental-unreviewed",
        "model": "Qwen-Image 2.1 via LocalModelManager workbench",
        "source": str(source),
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "output": str(output),
        "output_sha256": hashlib.sha256(generated).hexdigest(),
        "size": args.size,
        "steps": args.steps,
        "seed": args.seed,
        "prompt": args.prompt,
        "official_prompt_enhance": False,
        "manager_job_id": job_id,
        "license_note": "Qwen Research License: research/evaluation only; original game asset rights separate",
    }
    output.with_suffix(".json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Saved", output, flush=True)


if __name__ == "__main__":
    main()
