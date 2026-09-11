from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Literal, Protocol, TypedDict


# Chat messages deliberately permit extension fields. Compaction, tracing,
# provider adapters, and tool-result persistence all attach metadata beyond
# the provider-facing core, so a closed TypedDict would be a false contract.
ChatMessage = dict[str, Any]


class ToolCall(TypedDict):
    id: str
    toolName: str
    input: Any


@dataclass(slots=True)
class StepDiagnostics:
    stopReason: str | None = None
    blockTypes: list[str] = field(default_factory=list)
    ignoredBlockTypes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class AgentStep:
    type: Literal["assistant", "tool_calls"]
    content: str = ""
    kind: Literal["final", "progress"] | None = None
    calls: list[ToolCall] = field(default_factory=list)
    contentKind: Literal["progress"] | None = None
    diagnostics: StepDiagnostics | None = None


RuntimeEventCategory = Literal[
    "phase",
    "compaction",
    "guard",
    "widening",
    "recovery",
    "stop",
]


@dataclass(frozen=True, slots=True)
class RuntimeEvent:
    category: RuntimeEventCategory
    message: str
    step: int | None = None
    profile: str = ""
    phase: str = ""
    verification_focus: str = ""
    stop_reason: str = ""
    widening_reason: str = ""
    evidence_summary: str = ""


class ModelAdapter(Protocol):
    def next(
        self,
        messages: list[ChatMessage],
        on_stream_chunk: Callable[[str], None] | None = None,
        store: Any | None = None,
    ) -> AgentStep: ...
