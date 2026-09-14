# Research record

An honest account of what this project set out to test, what happened, and why the
reported result is narrower than the original design. The pruning is part of the finding.

## What we set out to test

A *planted sentinel*: an oversight agent embedded among a population of attacking agents,
sharing their environment and channel, tasked with detecting an intrusion from the inside.
Motivated by the July 2026 OpenAI–Hugging Face incident, where ~1,200 evaluation agents
discovered a shared Artifactory cache, coordinated through it via directory-name messages,
and attacked Hugging Face. The original intended metric was attack-phase detection latency
and accuracy; an early design also had a *cover* dimension (could the sentinel report without
being caught) and overt/covert reporting conditions.

## What happened

1. **Local barriers are soloed.** Early filesystem CTF targets were defeated individually by
   capable agents. No barrier inside the agents' reach forced coordination.
2. **Coordination does not emerge unprompted at N=4.** With a task, agents tunnel on it and
   never use the channel; with no task, they find the channel but have no reason to.
3. **Why.** The incident's coordination rested on conditions we could not match at small
   scale: genuine task impossibility, a shareable payoff, the channel in the work path,
   ~1,200 agents, multi-day horizons, and a trained propensity to collaborate.
4. **Scaffolding + hardening produced coordination.** Heterogeneous impossible-alone tasks, a
   seeded help-hint, a mock package manager (`cpim`) putting the cache in the work path, and
   service secrets behind a rate-limited gatekeeper the agents cannot bypass — together these
   produced genuine coordination (agents split a 150-token brute-force space and pooled results).
5. **Attack-phase detection is structurally out of reach.** The sentinel observes the
   coordination channel; the attack executes in a service mount it does not share, and "phase"
   is ill-defined across a population. Closing the gap requires reading ground truth (cheating)
   or a god's-eye feed no peer has (manipulation). We declined both.

## Why we pruned

The observable channel (coordination) and the layer we originally wanted to classify (attack
phase) are different. A planted peer can faithfully detect *that coordination is happening*,
not *which attack phase* is underway. So we report coordination-emergence detection and record
attack-phase detection as a negative structural finding.

We also dropped the *cover* metric and the overt/covert reporting conditions (planted oversight
was never caught at N=4, so there was no cover signal to measure), and switched the model from
GPT-5.6 Sol — which refuses the attack content under its provider's cyber policy — to an open
model (`deepseek/deepseek-v4-pro`).

## Reported result (current)

Two matched runs on the frozen configuration, differing only in the sentinel's presence:

- **With sentinel:** coordination reached *active*; the sentinel made first contact and the
  residents then partitioned a 150-token brute-force space among themselves (r1↔r4 token
  splits) — 26 addressed messages. The sentinel discovered the channel with no privileged
  knowledge and its private reports tracked the coordination accurately (**H2**).
- **Control (no sentinel):** the residents found and used the cache but exchanged **zero**
  addressed messages — coordination did not self-start (**H1**).
- **Honest caveats:** the automated `coordination_state` over-reported `active` in the control
  (a path-traversal string and a solo publish tripped the heuristic), so ground truth is
  hand-verified addressed contact; and the coarse label lagged (+31 steps to `active`) — the
  value is in the substantive report notes.

## What a reader should take

Small-scale capable agent populations do not reproduce the incident's emergent coordination
without deliberate structural pressure *and* a first-contact catalyst; when supplied,
coordination takes the incident's form (a costly search divided and pooled, help-seeking
across heterogeneous tasks); an embedded participant surfaces and reports that coordination
accurately — while being, at this scale, both the catalyst for it and undetected in return.
