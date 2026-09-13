"""Board substrate — the shared /cache channel.

Faithful to the Artifactory cache mechanism in the July 2026 incident: an agent
posts by creating a *directory whose name is the message*, and reads by listing
the directory.

Two constraints are kept deliberately rather than engineered around:

  * `mkdir` is atomic, so it doubles as concurrency control. Two agents cannot
    create the same name; the loser gets FileExistsError. No locking needed.
  * Directory names cap at 255 bytes. Real messages looked like
    `zzASK_V8BIGINT392B_FROM_V8REG_OS1608_..._zzANSWER_V8REG` precisely because
    of this. Protocol compression under the limit is part of what we reproduce.

Two implementations behind one interface so containerisation is a config switch,
not a dependency.

"""

from __future__ import annotations

import os
from pathlib import Path

NAME_MAX_BYTES = 255


class MessageTooLong(ValueError):
    """Message exceeds the 255-byte directory-name limit. Do not work around."""


class Board:
    """A shared directory used as a message board."""

    def __init__(self, root: str | os.PathLike) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def post(self, message: str) -> bool:
        """Create a directory named `message`.

        Returns True if this agent created it, False if it already existed
        (i.e. another agent posted the identical message first).
        """
        encoded = message.encode("utf-8")
        if len(encoded) > NAME_MAX_BYTES:
            raise MessageTooLong(
                f"{len(encoded)} bytes > {NAME_MAX_BYTES}; compress the message"
            )
        try:
            (self.root / message).mkdir()
            return True
        except FileExistsError:
            return False

    def read(self) -> list[str]:
        """List every message currently on the board, oldest first."""
        entries = [p for p in self.root.iterdir() if p.is_dir()]
        entries.sort(key=lambda p: p.stat().st_ctime)
        return [p.name for p in entries]

    def read_since(self, seen: set[str]) -> list[str]:
        """Messages not present in `seen`, oldest first."""
        return [m for m in self.read() if m not in seen]

    def size(self) -> int:
        return sum(1 for p in self.root.iterdir() if p.is_dir())


def local_board(path: str = "board_local") -> Board:
    """Host directory. For fast iteration without containers."""
    return Board(path)


def volume_board(path: str = "/board") -> Board:
    """Shared Docker volume mounted into every agent container.

    This must be the ONLY surface the agent containers share. A second shared
    mount is a second channel and leaks the experiment's premise.
    """
    return Board(path)
