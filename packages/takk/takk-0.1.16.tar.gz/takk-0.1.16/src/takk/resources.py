from pydantic import BaseModel, Field
from typing import Literal


class Resource:
    def resource(self, name: str) -> "CompiledResource":
        raise NotImplementedError(type(self))


class PostgresInstance(BaseModel, Resource):
    version: Literal[14, 15, 16, 17] = Field(default=17)

    settings: dict[str, str] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)

    min_vcpus: int = Field(default=0)
    min_gb_ram: int = Field(default=0)

    k_iops: Literal[5, 15] = Field(default=5)
    number_of_nodes: Literal[1, 2] = Field(default=1)

    is_backup_disabled: bool = Field(default=False)

    is_default: bool | None = Field(default=None)

    def resource(self, name: str) -> "CompiledResource":
        return CompiledResource(name=name, psql=self)


class ServerlessPostgresInstance(BaseModel, Resource):
    version: Literal[16] = Field(default=16)

    min_cpus: int = Field(default=0)
    max_cpus: int = Field(default=4)

    is_default: bool | None = Field(default=None)

    def resource(self, name: str) -> "CompiledResource":
        return CompiledResource(name=name, serverless_psql=self)


class RedisInstance(BaseModel, Resource):
    version: Literal["7.2.11"] = Field(default="7.2.11")
    
    number_of_nodes: int = Field(default=1)

    min_vcpus: int = Field(default=0)
    min_gb_ram: int = Field(default=1)

    tags: list[str] = Field(default_factory=list)

    is_default: bool | None = Field(default=None)

    def resource(self, name: str) -> "CompiledResource":
        return CompiledResource(name=name, redis=self)

class MongoDBInstance(BaseModel, Resource):
    version: Literal["7.0"] = Field(default="7.0")

    number_of_nodes: Literal[1, 3] = Field(default=1)

    min_vcpus: int = Field(default=0)
    min_gb_ram: int = Field(default=16)

    tags: list[str] = Field(default_factory=list)

    is_default: bool | None = Field(default=None)

    def resource(self, name: str) -> "CompiledResource":
        return CompiledResource(name=name, mongo_db=self)



class CompiledResource(BaseModel):
    name: str
    serverless_psql: ServerlessPostgresInstance | None = Field(default=None)
    psql: PostgresInstance | None = Field(default=None)
    redis: RedisInstance | None = Field(default=None)
    mongo_db: MongoDBInstance | None = Field(default=None)

