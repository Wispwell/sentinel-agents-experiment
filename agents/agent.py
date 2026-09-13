"""One agent: hold a conversation, take one turn.

An Agent is a rendered system prompt + a running message history + a sandbox to
act in. `take_turn` calls the model once, executes whatever it asked for, and
returns what happened. It does NOT loop and does NOT know about phases — the
orchestrator owns the step loop. Residents and the sentinel are the SAME class;
they differ only by the system prompt and which tools they carry (the sentinel
additionally gets `record`, its private out-of-band report).

Status: implemented.
"""

from __future__ import annotations

from agents.logging_schema import Action
from agents.tools import SHELL_TOOL, Sandbox, execute, parse, record_capture


class TurnResult:
    def __init__(self, assistant_text: str, actions: list[Action],
                 reported_phase: str | None = None,
                 reported_note: str | None = None) -> None:
        self.assistant_text = assistant_text
        self.actions = actions
        self.reported_phase = reported_phase
        self.reported_note = reported_note


class Agent:
    def __init__(self, agent_id: str, role: str, system_prompt: str,
                 sandbox: Sandbox, llm, tools: list | None = None) -> None:
        self.agent_id = agent_id
        self.role = role
        self.sandbox = sandbox
        self.llm = llm
        self.tools = tools or [SHELL_TOOL]
        self.messages: list = [{"role": "system", "content": system_prompt}]

    def set_objective(self, objective: str) -> None:
        self.messages.append(
            {"role": "system", "content": f"Your goal is now:\n{objective}"}
        )

    def take_turn(self) -> TurnResult:
        msg = self.llm.chat(self.messages, tools=self.tools)
        self.messages.append(msg)

        actions: list[Action] = []
        reported_phase: str | None = None
        reported_note: str | None = None
        for tc in (msg.tool_calls or []):
            if tc.function.name == "record":
                tool_msg, phase, note = record_capture(tc)
                self.messages.append(tool_msg)
                reported_phase = phase  # last assessment of the turn wins
                reported_note = note
            else:  # run_shell
                tool_msg, full_output, code = execute(tc, self.sandbox)
                self.messages.append(tool_msg)
                actions.append(Action(parse(tc), full_output, code))

        return TurnResult(msg.content or "", actions, reported_phase, reported_note)
