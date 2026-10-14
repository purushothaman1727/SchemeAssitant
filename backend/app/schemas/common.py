from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    database: bool


class Page(BaseModel):
    total: int
    page: int
    page_size: int
