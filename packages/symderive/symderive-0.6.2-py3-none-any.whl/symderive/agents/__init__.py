"""
Agent personas for agentic workflows.

Pre-prompted contexts that transform general-purpose LLMs into domain experts
in mathematical and physical reasoning.

Usage:
    from symderive.agents import load_agent, list_agents, get_agent_path

    # Get the system prompt for Ed (theoretical physicist)
    prompt = load_agent("ed")

    # List all available agents
    agents = list_agents()

    # Get path to agent file (for external tools)
    path = get_agent_path("steve")
"""

from pathlib import Path
from typing import Optional
import yaml


_AGENTS_DIR = Path(__file__).parent


def list_agents() -> list[str]:
    """List all available agent IDs.

    Returns:
        List of agent IDs (e.g., ['ed', 'steve', 'atiyah', ...])
    """
    return [
        f.stem.replace('.agent', '')
        for f in _AGENTS_DIR.glob('*.agent.md')
    ]


def get_agent_path(agent_id: str) -> Path:
    """Get the file path for an agent's prompt file.

    Args:
        agent_id: The agent identifier (e.g., 'ed', 'steve')

    Returns:
        Path to the agent's .agent.md file

    Raises:
        FileNotFoundError: If agent doesn't exist
    """
    path = _AGENTS_DIR / f"{agent_id}.agent.md"
    if not path.exists():
        available = list_agents()
        raise FileNotFoundError(
            f"Agent '{agent_id}' not found. Available: {available}"
        )
    return path


def load_agent(agent_id: str) -> str:
    """Load an agent's system prompt.

    Args:
        agent_id: The agent identifier (e.g., 'ed', 'steve')

    Returns:
        The full text of the agent's system prompt

    Raises:
        FileNotFoundError: If agent doesn't exist
    """
    return get_agent_path(agent_id).read_text()


def load_agents_index() -> dict:
    """Load the AGENTS.yaml index with metadata for all agents.

    Returns:
        Dict with categories, agents, and routing metadata
    """
    yaml_path = _AGENTS_DIR / "AGENTS.yaml"
    if not yaml_path.exists():
        return {}
    with open(yaml_path) as f:
        return yaml.safe_load(f)


def get_agent_metadata(agent_id: str) -> Optional[dict]:
    """Get metadata for a specific agent from AGENTS.yaml.

    Args:
        agent_id: The agent identifier

    Returns:
        Dict with summary, tags, use_when, etc. or None if not found
    """
    index = load_agents_index()
    all_agents = (
        agent
        for category in index.get('categories', {}).values()
        for agent in category.get('agents', [])
    )
    return next((a for a in all_agents if a.get('id') == agent_id), None)


__all__ = [
    'list_agents',
    'get_agent_path',
    'load_agent',
    'load_agents_index',
    'get_agent_metadata',
]
