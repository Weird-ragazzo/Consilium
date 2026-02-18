from pydantic import BaseModel


class CouncilRequest(BaseModel):
    prompt: str


class ModelResponse(BaseModel):
    model_name: str
    model_id: str
    initial_response: str
    critique_received: str
    final_response: str
    was_revised: bool


class CouncilResponse(BaseModel):
    prompt: str
    model_a: ModelResponse
    model_b: ModelResponse
    phases_completed: list[str]
