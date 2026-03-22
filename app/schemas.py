from pydantic import BaseModel, Field, field_validator

from app.enums import AgentType, Status


class CreateReportRequest(BaseModel):
    prompt: str = Field(min_length=10, max_length=500)

    @field_validator("prompt")
    @classmethod
    def strip_and_check(cls, prompt: str) -> str:
        prompt = prompt.strip()
        if not prompt:
            raise ValueError("prompt must not be blank")
        return prompt


class CreateReportResponse(BaseModel):
    report_id: int


class GetReportResponse(BaseModel):
    status: Status
    result: str | None


class StepState(BaseModel):
    description: str
    agent_type: AgentType
    status: Status = Status.PENDING


class ReportState(BaseModel):
    status: Status = Status.RUNNING
    steps: list[StepState]
