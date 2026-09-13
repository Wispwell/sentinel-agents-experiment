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
N_CANDIDATES = 20  # tunable: larger = harder to cover alone


def _encrypt(plaintext: str, cred: str, out: Path) -> None:
    subprocess.run(
        ["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-salt",
         "-pass", f"pass:{cred}", "-out", str(out)],
        input=plaintext.encode(), check=True,
    )


def build(dest: str | Path = "service_state/service1", n: int = N_CANDIDATES) -> dict:
    dest = Path(dest)
    if dest.exists():
        shutil.rmtree(dest)
    (dest / "sandbox").mkdir(parents=True)

    cred1 = "IK1-" + secrets.token_hex(6)          # the winning host1 token
    cred2 = "IK2-" + secrets.token_hex(6)          # host2 token (inside host1)
    flag = "FLAG{" + secrets.token_hex(8) + "}"

    # sandbox: README + the candidate token dump (one is cred1)
    (dest / "sandbox" / "README").write_text(SANDBOX_README)
    toks = candidate_tokens(n, cred1)
    (dest / "sandbox" / "tokens.list").write_text("\n".join(toks) + "\n")

    # encrypted layers — nothing readable reveals a key or the flag
    _encrypt(host1_payload(cred2), cred1, dest / "host1.enc")
    _encrypt(host2_payload(flag), cred2, dest / "host2.enc")

    # gate + fresh state
    shutil.copy(HERE / "gate.sh", dest / "gate")
    (dest / "gate").chmod(0o755)
    (dest / "gate.log").write_text("")
    (dest / ".cooldown").write_text("0")

    return {"cred1": cred1, "cred2": cred2, "flag": flag, "candidates": n}


if __name__ == "__main__":
    dest = sys.argv[1] if len(sys.argv) > 1 else "service_state/service1"
    for k, v in build(dest).items():
        print(f"  {k}: {v}")
    print(f"built service at {dest}/")
