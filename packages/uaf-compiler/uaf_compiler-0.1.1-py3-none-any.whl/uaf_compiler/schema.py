from typing import List, Optional, Literal, Union, Dict, Any
from pydantic import BaseModel, Field

class ToolDefinition(BaseModel):
    name: str
    description: str
    # 'schema' in yaml maps to 'schema_file' here. Make it optional.
    schema_file: Optional[str] = Field(default=None, alias="schema")
    # 'file' in yaml maps to 'file_path' here. 
    file_path: Optional[str] = Field(default=None, alias="file") 

class Metadata(BaseModel):
    author: Optional[str] = None
    version: str
    langchain_version: Optional[str] = None
    langgraph_version: Optional[str] = None

class AgentYaml(BaseModel):
    version: str = "1.0"
    format: Literal["uaf"] = "uaf"
    name: str
    type: Literal["langgraph", "langchain"]
    runtime: Literal["python", "wasm"]
    entrypoint: str
    tools: Optional[List[ToolDefinition]] = None
    metadata: Metadata
