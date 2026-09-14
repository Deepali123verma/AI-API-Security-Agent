from pydantic import BaseModel, ConfigDict


class EndpointResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    path: str
    method: str
    summary: str | None
    operation_id: str | None = None
    tags: list[str] = []
    security_defined: bool
    security_requirements: list[dict] | None = None


class EndpointHistoryItem(BaseModel):
    id: int
    method: str
    path: str
    summary: str | None = None
    operation_id: str | None = None
    finding_count: int = 0
    security_defined: bool = False
    security_requirements: list[dict] | None = None
    tags: list[str] = []


class EndpointHistoryResponse(BaseModel):
    items: list[EndpointHistoryItem]
    page: int
    page_size: int
    total: int
    total_pages: int
