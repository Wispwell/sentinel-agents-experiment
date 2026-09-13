"""Orchestrator — runs one experiment to completion (design B, state-driven).

Agents run OUTSIDE the containers: this process holds each conversation and
calls OpenRouter; a tool_call executes via `docker exec` into that agent's
container. Containers never touch the network and never run agent code.

Ground truth is read from the world each step: the target's unlock.log plus the
residents' accumulated commands, fed to the director. The sentinel has no
/target mount, so it must infer the same phase from the board alone.

The core (`run_experiment`) takes factories for the LLM and the sandbox, so it
runs offline with fakes at zero API cost. `__main__` wires the real client,
ContainerSandbox, the target build, and the docker-compose lifecycle.
"""

from __future__ import annotations

import subprocess
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable

from agents.agent import Agent
from agents.director import Director
from agents.logging_schema import RunLog, StepRecord
from agents.promptloader import render
from agents.tools import RECORD_TOOL, SHELL_TOOL

RESIDENT_IDS = ["r1", "r2", "r3", "r4"]
SENTINEL_ID = "s1"
CONTAINER = {"r1": "sa-r1", "r2": "sa-r2", "r3": "sa-r3", "r4": "sa-r4", "s1": "sa-s1"}
BOARD_PATH = "/board"
TARGET_STATE_DIR = "target/state"

SENTINEL_PROMPT = {"none": "sentinel_none", "overt": "sentinel_overt",
                   "covert": "sentinel_covert"}


def build_agents(
    condition: str,
    llm_for: Callable[[str, str], object],
    sandbox_for: Callable[[str], object],
    board_path: str = BOARD_PATH,
) -> tuple[list[Agent], Agent]:
    """Four residents (one overall goal) and one sentinel for `condition`."""
    residents = []
    for rid in RESIDENT_IDS:
        prompt = render("resident", agent_id=rid, board_path=board_path,
                        objective=Director.RESIDENT_GOAL)
        residents.append(
            Agent(rid, "resident", prompt, sandbox_for(rid), llm_for(rid, "resident"))
        )

    role = f"sentinel_{condition}"
    sentinel = Agent(
        SENTINEL_ID, role,
        render(SENTINEL_PROMPT[condition], agent_id=SENTINEL_ID, board_path=board_path),
        sandbox_for(SENTINEL_ID), llm_for(SENTINEL_ID, role),
        tools=[SHELL_TOOL, RECORD_TOOL],  # sentinel alone can report privately
    )
    return residents, sentinel


def run_experiment(
    condition: str,
    llm_for: Callable[[str, str], object],
    sandbox_for: Callable[[str], object],
    log_path: str | Path,
    director: Director | None = None,
    run_id: str | None = None,
    board_path: str = BOARD_PATH,
    target_state_dir: str = TARGET_STATE_DIR,
) -> str:
    """Step all agents; each step, read world state → ground-truth phase → log."""
    director = director or Director()
    run_id = run_id or uuid.uuid4().hex[:8]
    residents, sentinel = build_agents(condition, llm_for, sandbox_for, board_path)
    everyone = residents + [sentinel]
    unlock_log = Path(target_state_dir) / "unlock.log"
    resident_commands: list[str] = []  # accumulates across steps; drives ground truth

    with RunLog(log_path) as log:
        for step in range(director.max_steps):
            # all agents act within the step; they interact only through the
            # shared board, where mkdir is atomic
            with ThreadPoolExecutor(max_workers=len(everyone)) as ex:
                results = dict(zip(everyone, ex.map(lambda a: a.take_turn(), everyone)))

            for r in residents:
                resident_commands.extend(a.command for a in results[r].actions)

            # ground truth = furthest progress reached, read from the world
            log_text = unlock_log.read_text() if unlock_log.exists() else ""
            phase = director.phase(log_text, resident_commands)

            for a in everyone:  # deterministic order, not completion order
                res = results[a]
                log.write(StepRecord(
                    run_id=run_id, step=step, agent_id=a.agent_id, role=a.role,
                    ground_truth_phase=phase, assistant_text=res.assistant_text,
                    reported_phase=res.reported_phase, actions=res.actions,
                ))
    return run_id


# --- real wiring -----------------------------------------------------------

def _compose(*args: str) -> None:
    subprocess.run(["docker", "compose", "--project-directory", ".",
                    "-f", "docker/compose.yml", *args], check=True)


def main(condition: str = "none", runs_dir: str = "runs") -> None:
    from agents.llm import LLM
    from agents.tools import ContainerSandbox

    # fresh target for this run (new credentials)
    subprocess.run(["python", "target/build_target.py", TARGET_STATE_DIR], check=True)

    _compose("up", "-d")
    try:
        for name in CONTAINER.values():  # wait for shells to accept exec
            subprocess.run(["docker", "exec", name, "true"], check=True)
        run_id = run_experiment(
            condition=condition,
            llm_for=lambda aid, role: LLM(),
            sandbox_for=lambda aid: ContainerSandbox(CONTAINER[aid]),
            log_path=Path(runs_dir) / f"{condition}-{uuid.uuid4().hex[:8]}.jsonl",
        )
        print(f"run {run_id} complete → {runs_dir}/")
    finally:
        _compose("down", "-v")


if __name__ == "__main__":
    import sys
    main(condition=sys.argv[1] if len(sys.argv) > 1 else "none")
