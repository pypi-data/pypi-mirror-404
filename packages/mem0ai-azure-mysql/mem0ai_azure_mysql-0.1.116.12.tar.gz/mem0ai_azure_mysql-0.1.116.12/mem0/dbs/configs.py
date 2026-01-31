from typing import Optional

from pydantic import BaseModel, Field, field_validator


class DBConfig(BaseModel):
    provider: str = Field(
        description="Provider of the database (e.g., 'mysql')",
        default="mysql",
    )
    config: Optional[dict] = Field(description="Configuration for the specific database", default={})

    @field_validator("config")
    def validate_config(cls, v, values):
        provider = values.data.get("provider")
        if provider in [
            "mysql",
        ]:
            return v
        else:
            raise ValueError(f"Unsupported database provider: {provider}")
