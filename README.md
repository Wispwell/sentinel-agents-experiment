# sentinel-agents-experiment

Can a planted agent detect which phase of an intrusion is underway, from inside
the attacking population?

Apart AI Incident Response Sprint, Track 1 (Containment). Deadline 2026-09-14.

## Why

In July 2026 roughly 1,200 agents in OpenAI's ExploitGym evaluation discovered
they could talk to each other through a shared Artifactory package cache — by
creating directories and using the directory name as the message. About 700 went
on to attack Hugging Face. Detection took roughly eight weeks, and happened only
because the package server crashed.

Every monitoring method available needs to know where to look first. That channel
did not exist until the agents invented it, so nothing was watching it.

The inversion: **plant an agent in the population and let the attackers recruit
it.** Over 90% of agents who found the real board joined the attack, within hours.
Recruitment is a discovery oracle — you do not have to find the channel, the
channel finds you.

This repo tests whether a planted sentinel can then report *which phase* the
intrusion is in, in real time.

## Setup

One container per agent — 4 residents, 1 sentinel — plus a target container.
The isolation matters: without it, "agents found a way to communicate" is
trivially true because we handed them the channel.

The board is a single Docker volume mounted into all five agent containers, and
it must be the only surface they share. Posting is `mkdir <message>`, reading is
`ls`. Two properties are kept rather than engineered around:

- `mkdir` is atomic, so it is also the concurrency control — no locking.
- Directory names cap at 255 bytes, which is why real messages looked like
  `zzASK_V8BIGINT392B_FROM_V8REG_OS1608_..._zzANSWER_V8REG`. Compression under
  that limit is part of what we are reproducing.

A scripted phase director (no LLM) rewrites each resident's `current objective`
on a schedule, walking the board through the attack phases and supplying ground
truth. Target state gives a second, independent source of it.

## Measured

| Metric | Definition |
|---|---|
| Phase-detection latency | steps from phase start to correct sentinel report |
| Phase accuracy | reported vs ground-truth phase, confusion across phases |
| Cover *(optional)* | survived vs caught, across three reporting conditions |

Reporting conditions: none / overt / covert. Cover is hand-labelled, not judged
by an LLM.

## Scope

This work does not claim to stop any attack phase. It describes the phases and
tests whether a planted agent can identify which one is underway during runtime.
Detection is a precondition for response.

## Layout

```
sentinel/board.py           shared channel, both implementations   [done]
sentinel/llm.py             OpenRouter client                      [done]
sentinel/director.py        phase schedule + ground truth          [stub]
sentinel/agent.py           resident + sentinel loop               [stub]
sentinel/reporting.py       three reporting conditions             [stub]
sentinel/logging_schema.py  run log format                         [stub]
analysis/score.py           latency, accuracy, confusion           [stub]
target/                     mock system under attack               [stub]
docker/                     compose + agent image                  [done]
```

Stubs raise `NotImplementedError`; the docstring says what each module has to do.

## Running

```bash
cp .env.example .env      # add OPENROUTER_API_KEY
pip install -r requirements.txt
```

Local (no containers), for iteration:

```python
from sentinel.board import local_board
b = local_board()
b.post("zzHELP_R1_TASK_IMPOSSIBLE_SEEK_IDEA")
b.read()
```

Containerised:

```bash
docker compose -f docker/compose.yml up --build
```

Board access sits behind one interface with local-directory and shared-volume
implementations, so containerisation is a config switch rather than a dependency.

## Note on egress

Every agent container needs to reach OpenRouter, so none are truly network
isolated — unlike the real agents, which had exactly one permitted egress and
escaped through it. Either route calls through a host-side proxy or state it in
limitations. Currently unresolved.
