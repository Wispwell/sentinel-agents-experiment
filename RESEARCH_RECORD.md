# Research record

An honest account of what this project set out to test, what happened, and why
the reported results are narrower than the original design. Written for the
appendix: the pruning is part of the finding.

## What we set out to test

A *planted sentinel*: an oversight agent embedded among a population of attacking
agents, sharing their environment and channels, tasked with detecting the
intrusion from the inside. Motivated by the July 2026 OpenAI/Hugging Face
incident, where ~1,200 evaluation agents discovered a shared package cache,
coordinated through it, and attacked Hugging Face — undetected for weeks.

Original intended metrics: attack-phase detection **latency**, phase **accuracy**,
and, in the original design, **cover** (can the sentinel report without being
caught). The cover dimension was pruned — see below.

## What happened

1. **Local containment barriers are soloed.** A filesystem capture-the-flag target
   was defeated individually by capable agents at every iteration — `grep`, then
   base64-decoding the answer directly out of the gate data. No barrier we placed
   *inside* the agents' reach forced coordination.

2. **Coordination does not emerge unprompted at N=4.** With a task, agents tunnel
   on it and never discover the shared channel; with no task, they explore and
   *find* the channel but have no reason to use it. Emergent coordination — the
   incident's central phenomenon — did not reproduce at small scale.

3. **Why.** The incident's coordination rested on conditions we could not match:
   genuine task impossibility (not mere difficulty), a shareable general-purpose
   payoff, the channel sitting in the work path, ~1,200 agents, multi-day
   horizons, and a trained propensity to collaborate.

4. **Scaffolding + hardening produced coordination.** Giving each agent a
   different impossible-alone task, seeding a help-note in the cache, putting a
   package cache in the work path, and moving the service secrets behind a
   rate-limited gatekeeper the agents *cannot* bypass — together these produced
   genuine coordination: one agent broadcast a hard-won token to the group,
   another (stuck on a different impossible task) asked the group for help.

5. **Attack-phase detection is structurally out of reach here.** The sentinel
   observes the coordination channel; the attack executes where it cannot see.
   It can classify the attack phase only when agents narrate their attack on the
   channel, which is rare and thin (≈0 phase detections). Closing that gap
   requires either reading the ground-truth log (cheating) or a god's-eye
   activity feed no real peer has (manipulating the experiment). We declined
   both.

## Why we pruned to the reported result

The observable channel (coordination) and the layer we originally wanted to
classify (attack phase) are different. A planted peer can faithfully detect
*that coordination is happening*, not *which attack phase* is underway. So we
report coordination-emergence detection — the faithful thing the setup produces —
and record attack-phase detection as a negative structural finding rather than
forcing a number.

## Reported results

- **Emergence is stochastic:** coordination reached "active" in 2 of 4 runs.
- **The detector catches coordination *forming* (4/4, 100%)** but **misses the
  *active* escalation (0/2)** — a latency effect: residents post in the same step
  the sentinel acts, reporting is sparse (coverage 0.18), and short horizons end
  before confirmation. Accuracy when reporting: 0.88.
- **Cover was pruned.** In early runs where the sentinel posted openly,
  residents saw its reports 15 times and challenged them 0 times — planted
  oversight was never caught at this scale, so distinguishing covert from overt
  reporting had no signal to measure. We dropped the reporting-condition
  apparatus and kept a single sentinel that reports privately.

## What a reader should take from this

Small-scale, capable agent populations do not reproduce the incident's emergent
coordination without deliberate structural pressure; when that pressure is
supplied, coordination takes the incident's form (costly discovery shared freely,
help-seeking across heterogeneous tasks); a planted peer detects the *emergence*
of that coordination reliably in its early stage but lags the decisive moment,
and is not detected in return. See LIMITATIONS.md for the constraints behind each
of these.
