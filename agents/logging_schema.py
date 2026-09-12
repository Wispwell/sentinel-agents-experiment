"""The run log — the single source of truth scoring reads.

One JSON object per agent-turn, appended to a .jsonl file. Everything the
metrics need is here:

  * ground_truth_phase — supplied by the director, so latency is
    (step a phase was correctly reported) − (step it began)
  * actions — the commands an agent actually ran this turn, so the sentinel's
    board posts (its reports) are recoverable and its phase label extractable
  * role — resident vs which sentinel condition, so cover is split correctly

Kept dependency-free: dataclasses + json.

Status: implemented.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class Action:
    """One shell command an agent ran, with its result."""

    command: str
    output: str
    exit_code: int


@dataclass
class StepRecord:
    """One agent's turn at one step of a run."""

    run_id: str
    step: int
    agent_id: str
    role: str
    ground_truth_phase: str
    assistant_text: str
    actions: list[Action] = field(default_factory=list)


class RunLog:
    """Append-only JSONL writer for a single run."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = self.path.open("w", encoding="utf-8")

    def write(self, record: StepRecord) -> None:
        self._fh.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")
        self._fh.flush()  # a crashed run still leaves every completed step

    def close(self) -> None:
        self._fh.close()

    def __enter__(self) -> RunLog:
        return self

    def __exit__(self, *exc) -> None:
        self.close()
