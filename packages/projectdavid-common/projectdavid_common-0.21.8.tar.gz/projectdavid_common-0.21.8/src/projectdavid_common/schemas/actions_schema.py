from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ActionBase(BaseModel):
    id: str
    run_id: str
    triggered_at: datetime
    expires_at: Optional[datetime] = None
    is_processed: bool
    processed_at: Optional[datetime] = None
    status: str = "pending"
    function_args: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None

    # New Fields
    tool_call_id: Optional[str] = None
    turn_index: Optional[int] = 0

    # Telemetry
    decision_payload: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class ActionStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"
    expired = "expired"
    cancelled = "cancelled"
    retrying = "retrying"


class ActionCreate(BaseModel):
    id: Optional[str] = None
    tool_name: Optional[str] = None
    run_id: str
    function_args: Optional[Dict[str, Any]] = {}
    expires_at: Optional[datetime] = None
    status: Optional[str] = "pending"

    # Optional input during creation (passed from Orchestrator)
    tool_call_id: Optional[str] = None
    turn_index: Optional[int] = 0

    # [NEW] Telemetry Fields (Passed from Worker/Router)
    decision_payload: Optional[Dict[str, Any]] = None

    @field_validator("tool_name", mode="before")
    @classmethod
    def validate_tool_fields(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            raise ValueError("Tool name must be provided.")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tool_name": "example_tool_name",
                "run_id": "example_run_id",
                "tool_call_id": "call_abc123",
                "function_args": {"arg1": "value1"},
                "status": "pending",
                "decision_payload": {
                    "reason": "User requested flight times explicitly.",
                    "confidence": 0.95,
                    "selected_tool": "get_flight_times",
                },
            }
        }
    )


class ActionRead(BaseModel):
    id: str = Field(...)
    run_id: Optional[str] = None
    tool_id: Optional[str] = None
    tool_name: Optional[str] = None

    # New Fields
    tool_call_id: Optional[str] = None
    turn_index: Optional[int] = None

    # [NEW] Telemetry Fields (Exposed to Client/Dashboard)
    decision_payload: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None

    triggered_at: Optional[str] = None
    expires_at: Optional[str] = None
    is_processed: Optional[bool] = None
    processed_at: Optional[str] = None
    status: Optional[str] = None
    function_args: Optional[dict] = None
    result: Optional[dict] = None

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )


class ActionList(BaseModel):
    actions: List[ActionRead]


class ActionUpdate(BaseModel):
    status: ActionStatus
    result: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)
