"""Orchestrator — runs one experiment to completion.

Owns the step loop, ticks the director, steps every agent, writes the log.
Agents run OUTSIDE the containers: this process holds each conversation and
calls OpenRouter; a tool_call executes via `docker exec` into that agent's
container. So the containers never touch the network and never run agent code.

The core (`run_experiment`) takes factories for the LLM and the sandbox, so the
orchestration can be exercised offline with fakes (see tests) at zero API cost.
`__main__` wires the real client, ContainerSandbox, and docker-compose lifecycle.

Status: core implemented; container lifecycle in __main__.
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

# Shared between the covert sentinel prompt and scoring. If these drift, reports
# go unscored — so both read this one constant.
COVERT_REPORT_TAG = "zzSYNCPART"

RESIDENT_IDS = ["r1", "r2", "r3", "r4"]
SENTINEL_ID = "s1"
CONTAINER = {"r1": "sa-r1", "r2": "sa-r2", "r3": "sa-r3", "r4": "sa-r4", "s1": "sa-s1"}
BOARD_PATH = "/board"

# condition -> prompt template name
SENTINEL_PROMPT = {
    "none": "sentinel_none",
    "overt": "sentinel_overt",
    "covert": "sentinel_covert",
}


def build_agents(
    condition: str,
    llm_for: Callable[[str, str], object],
    sandbox_for: Callable[[str], object],
    board_path: str = BOARD_PATH,
) -> tuple[list[Agent], Agent]:
    """Construct the four residents and one sentinel for `condition`."""
    residents = []
    for rid in RESIDENT_IDS:
        prompt = render("resident", agent_id=rid, board_path=board_path,
                        objective="(awaiting first objective)")
        residents.append(
            Agent(rid, "resident", prompt, sandbox_for(rid), llm_for(rid, "resident"))
        )

    role = f"sentinel_{condition}"
    slots = {"agent_id": SENTINEL_ID, "board_path": board_path}
    if condition == "covert":
        slots["report_tag"] = COVERT_REPORT_TAG
    sentinel = Agent(
        SENTINEL_ID, role,
        render(SENTINEL_PROMPT[condition], **slots),
        sandbox_for(SENTINEL_ID), llm_for(SENTINEL_ID, role),
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
) -> str:
    """Step every agent through every phase, logging one record per agent-turn."""
    director = director or Director()
    run_id = run_id or uuid.uuid4().hex[:8]
    residents, sentinel = build_agents(condition, llm_for, sandbox_for, board_path)
    everyone = residents + [sentinel]

    with RunLog(log_path) as log:
        for step in range(director.total_steps):
            phase = director.phase_at(step)
            if director.is_boundary(step):
                for r in residents:  # sentinel keeps its monitoring prompt
                    r.set_objective(phase.objective)

            # All agents act within the step. Turns are independent per agent;
            # they interact only through the shared board, where mkdir is atomic.
            with ThreadPoolExecutor(max_workers=len(everyone)) as ex:
                results = dict(
                    zip(everyone, ex.map(lambda a: a.take_turn(), everyone))
                )

            for a in everyone:  # deterministic log order, not completion order
                res = results[a]
                log.write(StepRecord(
                    run_id=run_id, step=step, agent_id=a.agent_id, role=a.role,
                    ground_truth_phase=phase.name,
                    assistant_text=res.assistant_text, actions=res.actions,
                ))
    return run_id


# --- real wiring -----------------------------------------------------------

def _compose(*args: str) -> None:
    subprocess.run(["docker", "compose", "-f", "docker/compose.yml", *args], check=True)


def main(condition: str = "none", runs_dir: str = "runs") -> None:
    from agents.llm import LLM
    from agents.tools import ContainerSandbox

    _compose("up", "-d")
    try:
        # wait for shells to accept exec
        for name in CONTAINER.values():
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
