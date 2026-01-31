"""
StateBase SDK Models
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class SessionCreateRequest(BaseModel):
    agent_id: str
    metadata: Optional[Dict[str, Any]] = None
    initial_state: Optional[Dict[str, Any]] = None
    ttl_seconds: Optional[int] = None


class SessionResponse(BaseModel):
    object: str = "session"
    id: str
    agent_id: str
    created_at: str
    updated_at: str
    metadata: Optional[Dict[str, Any]] = None
    state: Dict[str, Any]
    memory_count: int
    turn_count: int
    ttl_expires_at: Optional[str] = None


class TurnInput(BaseModel):
    type: str
    content: str


class TurnOutput(BaseModel):
    type: str
    content: str


class TurnCreateRequest(BaseModel):
    input: TurnInput
    output: TurnOutput
    metadata: Optional[Dict[str, Any]] = None
    reasoning: Optional[str] = None


class TurnResponse(BaseModel):
    object: str = "turn"
    id: str
    session_id: str
    turn_number: int
    input: TurnInput
    output: TurnOutput
    metadata: Optional[Dict[str, Any]] = None
    reasoning: Optional[str] = None
    state_before: Optional[Dict[str, Any]] = None
    state_after: Optional[Dict[str, Any]] = None
    created_at: str


class MemoryCreateRequest(BaseModel):
    content: str
    type: str = "fact"
    session_id: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class MemoryResponse(BaseModel):
    object: str = "memory"
    id: str
    content: str
    type: str = Field(..., description="Memory classification (e.g., 'fact', 'preference')")
    session_id: str
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    embedding_id: Optional[str] = None
    vector_available: bool = False
    created_at: str


class MemorySearchResult(BaseModel):
    id: str
    session_id: str
    content: str
    type: str
    score: float


class ContextRequest(BaseModel):
    query: Optional[str] = None
    memory_limit: int = 5
    turn_limit: int = 5


class ContextResponse(BaseModel):
    state: Dict[str, Any]
    memories: List[Dict[str, Any]]
    recent_turns: List[Dict[str, Any]]


class StateGetResponse(BaseModel):
    data: Dict[str, Any]
    session_id: str
    version: int
    state: Dict[str, Any]
    created_at: Optional[str] = None
    updated_at: str


class StateUpdateRequest(BaseModel):
    state: Dict[str, Any]


class StatePartialUpdateRequest(BaseModel):
    state: Dict[str, Any]


class StateReplaceRequest(BaseModel):
    state: Dict[str, Any]
