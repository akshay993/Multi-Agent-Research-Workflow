from enum import Enum


class Status(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentType(str, Enum):
    PLANNER = "planner_agent"
    RESEARCHER = "researcher_agent"
    WRITER = "writer_agent"
    EDITOR = "editor_agent"
