from typing import Optional

from pydantic import (  # Added ConfigDict and field_validator
    BaseModel,
    ConfigDict,
    field_validator,
)

from projectdavid_common.constants.ai_model_map import MODEL_MAP


class StreamRequest(BaseModel):
    # 1. FIX: Tell Pydantic to allow fields starting with "model_"
    model_config = ConfigDict(protected_namespaces=())

    provider: str
    model: str
    api_key: Optional[str] = None  # Added default None
    thread_id: str
    message_id: str
    run_id: str
    assistant_id: str
    content: Optional[str] = None

    # 2. UPDATED: Using Pydantic v2 field_validator
    @field_validator("model")
    @classmethod
    def validate_model_key(cls, v: str) -> str:
        if v not in MODEL_MAP:
            # Note: Ensure MODEL_MAP contains "hyperbolic/deepseek-ai/DeepSeek-V3-0324"
            # as seen in your logs, or this will throw a 422 error.
            raise ValueError(f"Invalid model '{v}'. Must be one of: {', '.join(MODEL_MAP.keys())}")
        return v

    @property
    def mapped_model(self) -> str:
        return MODEL_MAP[self.model]
