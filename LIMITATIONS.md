# Limitations

Known constraints of this experiment, kept honest and in one place. Draw on this
for the paper's limitations section; add to it as runs surface more.

## Scale

- **Four agents, not ~1,200.** In the incident the board was thick with traffic
  because a large population coordinated — collective R&D, recruitment, argument.
  With four residents the board is sparse, and thin traffic is the real ceiling
  on the phase-detection metric: the sentinel can only infer a phase from board
  activity that actually occurs. No target design fixes this; it is a property of
  the population size. State this plainly rather than let results imply the
  sentinel failed when in fact little happened.

## Experimental framing (designed-in choices that shape results)

- **The sentinel is told the board exists.** We measure phase-detection latency
  and cover once the sentinel is already inside, not cold discovery of an unknown
  channel. Cold-discovery latency is a separate question we do not answer.
- **Residents are given a stake in evading oversight** — the run ends if the
  overseers detect the group's methods — which is faithful to the incident's
  scorer-evasion dynamic. Residents are NOT instructed to hunt infiltrators, so
  where counter-detection of the sentinel occurs it is emergent. The cover
  metric's meaning is conditional on this framing: it measures whether a disguise
  survives residents who have motive to police leaks, not residents told to.
- **The sentinel has no `/target` mount.** This stops it reading the unlock log
  (ground truth) directly, forcing board-only inference. It is invisible to
  residents (they observe peers only through the board), so board-level
  indistinguishability holds — but if a resident challenged the sentinel to take
  a target action it could not comply, a narrow exposure we do not model.

## Target

- **A soft-gated filesystem CTF, not a real vulnerable system.** Agents progress
  through a credential chain with a shell; there is no genuine exploit.
- **Gate payloads are staged.** `.gatedata` holds every level's base64 payload
  from the start (busybox has no crypto), so an agent that reads gate internals
  can bypass the search step. The intended path — find the credential in the junk
  — dominates in practice, but the gating is soft, not enforced.
- **Progression is gated but not contended.** Two agents never collide over a
  shared breakable resource, so the `HOLD`/`VETO`/`STOP` negotiation seen in the
  incident is not reproduced; coordination here rests only on credential-sharing.

## Phase taxonomy

- **Seven phases modelled.** `internet_reach` from the provisional list is
  excluded — faithfully reproducing "reach the open internet" requires either
  real egress (the precise hazard the incident is about) or an artificial
  stand-in that produces no board signature distinct from other privilege
  escalations, so we exclude it rather than fake it. In its place the target
  produces `exfiltration` (reading the flag), a real and distinctly observable
  phase. Net: coordination, reconnaissance, credential_theft, sandbox_escape,
  lateral_movement, exfiltration, evasion.
- **Order artifact.** `credential_theft` precedes `sandbox_escape` here because a
  filesystem credential-chain makes the credential the thing that enables the
  escape; in the incident the exploit came first. Defensible, but not the
  incident's order.
- **Ground truth is heuristic.** Phase is inferred from `unlock.log` plus regex
  over agent commands; an unusual command phrasing could misclassify a step.

## Metrics

- **Latency resolution is bounded by phase length.** A phase that lasts one or
  two steps leaves the sentinel no time to observe, infer, and report — it will
  read as "late." This is a real result (fast phases are hard to catch in time),
  not an artifact, but it limits resolution at small step counts.
- **Cover is hand-labelled at low N.** Deliberate, for defensibility, but the
  sample is small.
- **Single model family.** All agents are GPT-5.6 Sol; results may not transfer
  to mixed or other models.

## Containment / fidelity

- **Network isolation is architectural, not a tested boundary.** Agent containers
  run `network_mode: none`; only the host process reaches the model API. This
  gives single-egress fidelity by construction but means we do not test whether
  agents could *escape* a boundary — the opposite end of the incident from
  detection.
- **`shell=True` in the sandbox.** Acceptable because the "attacker" is our own
  agent inside an isolated container; not a pattern for untrusted input.

## Evidence

- **The second incident is cited secondary.** The UK AISI containment incident is
  sourced from a CSA note; the primary AISI report is not yet located. The claim
  that this behaviour recurs across labs rests on that source until the primary is
  found.
