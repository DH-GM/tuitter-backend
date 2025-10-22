# webhook.py
import hmac
import hashlib
import os
import json
import subprocess
from fastapi import APIRouter, Request, HTTPException

router = APIRouter()


def _verify_signature(secret: bytes, body: bytes, sig_header: str) -> bool:
    # sig_header is like: "sha256=<hex>"
    if not sig_header or not sig_header.startswith("sha256="):
        return False
    received_sig = sig_header.split("=", 1)[1]
    expected = hmac.new(secret, body, hashlib.sha256).hexdigest()
    # constant-time compare
    return hmac.compare_digest(received_sig, expected)


@router.post("/webhook/github")
async def github_webhook(request: Request):
    secret_env = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    if not secret_env:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")
    secret = secret_env.encode("utf-8")

    raw_body = await request.body()
    sig_header = request.headers.get("X-Hub-Signature-256", "")
    event = request.headers.get("X-GitHub-Event", "")
    # Optional extra defense: limit to GitHub’s allowed IPs via a reverse proxy or VPC

    if not _verify_signature(secret, raw_body, sig_header):
        raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Only react to push events on main
    if event != "push":
        return {"ignored": True, "reason": "not a push event"}
    if payload.get("ref") != "refs/heads/main":
        return {"ignored": True, "reason": "not main branch"}

    # Kick off deploy script NON-BLOCKING so we return immediately
    deploy_script = "/home/ec2-user/tuitter-backend/deploy.sh"
    try:
        subprocess.Popen(
            [deploy_script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start deploy: {e}")

    # 202 Accepted: deployment started
    return {"ok": True, "action": "deploy", "branch": "main"}


# Small change for testing push webhook
