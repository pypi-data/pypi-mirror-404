"""CLI command implementations."""

from .agent import agent
from .db import db
from .auth import auth
from .analyze import analyze
from .embed import embed
from .index import index
from .plan import plan
from .registry import registry
from .rules import rules
from .search import search
from .server import server
from .skills import skills
from .team import team
from .projectmd import projectmd
from .research import research
from .spec import spec
from .tasks import tasks

__all__ = [
    "agent",
    "db",
    "auth",
    "analyze",
    "embed",
    "index",
    "plan",
    "registry",
    "rules",
    "search",
    "server",
    "skills",
    "team",
    "projectmd",
    "research",
    "spec",
    "tasks",
]
