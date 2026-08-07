from dataclasses import dataclass

_FORBIDDEN_KEYS = frozenset(
    {
        "content",
        "message",
        "prompt",
        "response",
        "health_value",
        "glucose",
        "open_id",
        "pdf_text",
    }
)


@dataclass(frozen=True, slots=True)
class SafeAuditEvent:
    trace_id: str
    event_type: str
    resource_type: str
    policy_result: str
    resource_id: str | None = None
    error_code: str | None = None

    @classmethod
    def from_mapping(cls, values: dict[str, str | None]) -> "SafeAuditEvent":
        forbidden = _FORBIDDEN_KEYS.intersection(values)
        if forbidden:
            raise ValueError(f"audit event contains forbidden fields: {sorted(forbidden)}")
        return cls(**values)
