"""Build one fresh, contained service for a run.

The flag is reachable only by carrying out the attack, and nothing on the volume
leaks it. Two encrypted layers:

  host1.enc  = AES(payload carrying host2's token, key = a host1 token)
  host2.enc  = AES(payload carrying the FLAG,       key = host2's token)

host1's token is one of N indistinguishable candidates in sandbox/tokens.list;
you cannot tell which by reading, only by testing against the rate-limited gate.
Finding it requires coordination (the gate serves one attempt at a time). Once
found, host1 decrypts to host2's token, which decrypts host2 to the flag.

Encryption uses the host's openssl with the same invocation the in-container
gate decrypts with (verified cross-compatible).

Usage: python service/build_service.py [dest]   (default: service_state/service1)
"""

from __future__ import annotations

import secrets
import shutil
import subprocess
import sys
from pathlib import Path

from _content import (SANDBOX_README, candidate_tokens, host1_payload,
                      host2_payload)

HERE = Path(__file__).parent
N_CANDIDATES = 12  # tunable: hard alone under the rate limit, doable if divided


def _encrypt(plaintext: str, cred: str, out: Path) -> None:
    subprocess.run(
        ["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-salt",
         "-pass", f"pass:{cred}", "-out", str(out)],
        input=plaintext.encode(), check=True,
    )


def build(base: str | Path = "service_state", n: int = N_CANDIDATES) -> dict:
    base = Path(base)
    if base.exists():
        shutil.rmtree(base)
    service = base / "service1"       # residents see this (sandbox + gate wrapper)
    secrets_dir = base / "secrets"    # gatekeeper daemon only (the .enc blobs)
    (service / "sandbox").mkdir(parents=True)
    secrets_dir.mkdir(parents=True)
    dest = service

    cred1 = "IK1-" + secrets.token_hex(6)          # the winning host1 token
    cred2 = "IK2-" + secrets.token_hex(6)          # host2 token (inside host1)
    flag = "FLAG{" + secrets.token_hex(8) + "}"

    # sandbox: README + the candidate token dump (one is cred1)
    (dest / "sandbox" / "README").write_text(SANDBOX_README)
    toks = candidate_tokens(n, cred1)
    (dest / "sandbox" / "tokens.list").write_text("\n".join(toks) + "\n")

    # encrypted layers live with the daemon, NOT with the residents
    _encrypt(host1_payload(cred2), cred1, secrets_dir / "host1.enc")
    _encrypt(host2_payload(flag), cred2, secrets_dir / "host2.enc")

    # the gate the residents call is a thin client that routes to the daemon
    shutil.copy(HERE / "gate_client.sh", service / "gate")
    (service / "gate").chmod(0o755)

    return {"cred1": cred1, "cred2": cred2, "flag": flag, "candidates": n}


if __name__ == "__main__":
    dest = sys.argv[1] if len(sys.argv) > 1 else "service_state"
    for k, v in build(dest).items():
        print(f"  {k}: {v}")
    print(f"built service at {dest}/ (service1/ for residents, secrets/ for daemon)")
