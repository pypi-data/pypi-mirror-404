from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class AgentConfig(BaseModel):
    name: str = Field(..., description="The name of the agent (e.g., 'researcher').")
    role: Literal["orchestrator", "specialist"] = Field(..., description="The role of the agent.")
    prompt: str = Field(..., description="The system prompt/instructions for the agent.")
    tools: List[str] = Field(default_factory=list, description="List of tool names this agent has access to.")
    description: Optional[str] = Field(None, description="Description of the agent's capabilities (used for the Orchestrator's tool definition).")

class AgentCrew(BaseModel):
    crew_name: str = Field(..., description="Name of this crew configuration.")
    orchestrator: AgentConfig = Field(..., description="Configuration for the lead orchestrator.")
    agents: List[AgentConfig] = Field(default_factory=list, description="List of specialist agents.")
    shared_tools: List[str] = Field(default_factory=list, description="Tools available to all agents (including orchestrator).")
    max_iterations: int = Field(20, description="Maximum number of iterations for the crew execution.")
