"""Phase director — the experimental control.

A plain script, no LLM. Holds the phase schedule, rewrites each resident's
`current objective` line at phase boundaries, and emits ground truth.

Ground truth has two independent sources and both belong here:
  1. the director's own clock (which phase the schedule says we are in)
  2. target state (which host reached, which credential used)

Status: not implemented.
"""

raise NotImplementedError("TODO")
