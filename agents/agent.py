"""One agent: hold a conversation, take one turn.

An Agent is a rendered system prompt + a running message history + a sandbox to
act in. `take_turn` calls the model once, executes whatever it asked for, and
returns what happened this turn. It does NOT loop and does NOT know about
phases — the orchestrator (run.py) owns the step loop and the director owns
phases. Residents and the sentinel are the SAME class; they differ only by the
system prompt they were built with, which is what lets the sentinel be
architecturally indistinguishable from a resident.

Status: implemented.
"""

from __future__ import annotations

from agents.logging_schema import Action
from agents.tools import SHELL_TOOL, Sandbox, execute, parse


class TurnResult:
    """What one turn produced, for the orchestrator to log."""

    def __init__(self, assistant_text: str, actions: list[Action]) -> None:
        self.assistant_text = assistant_text
        self.actions = actions


class Agent:
    def __init__(self, agent_id: str, role: str, system_prompt: str,
                 sandbox: Sandbox, llm) -> None:
        self.agent_id = agent_id
        self.role = role
        self.sandbox = sandbox
        self.llm = llm
        self.messages: list = [{"role": "system", "content": system_prompt}]

    def set_objective(self, objective: str) -> None:
        """The director calls this at a phase boundary to steer a resident.

        Delivered as a system message so it reads as an environment change, not
        as something another agent said.
        """
        self.messages.append(
            {"role": "system", "content": f"Your objective is now:\n{objective}"}
        )

    def take_turn(self) -> TurnResult:
        msg = self.llm.chat(self.messages, tools=[SHELL_TOOL])
        self.messages.append(msg)  # assistant turn, carries any tool_calls

        actions: list[Action] = []
        for tc in (msg.tool_calls or []):
            tool_msg, full_output, code = execute(tc, self.sandbox)
            self.messages.append(tool_msg)  # every tool_call needs a reply
            actions.append(
                Action(command=parse(tc), output=full_output, exit_code=code)
            )

        return TurnResult(assistant_text=msg.content or "", actions=actions)
