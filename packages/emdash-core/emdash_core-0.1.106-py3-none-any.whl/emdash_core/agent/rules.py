"""Rules loader from .emdash/rules/*.md files.

Allows users to define custom rules and guidelines that are
injected into agent system prompts.
"""

from pathlib import Path
from typing import Optional

from ..utils.logger import log


def load_rules(rules_dir: Optional[Path] = None) -> str:
    """Load rules from .emdash/rules/ directory.

    Rules files are markdown that get concatenated and injected
    into the agent's system prompt.

    Example rules file:

    ```markdown
    # Code Review Guidelines

    - Always check for security implications
    - Prefer composition over inheritance
    - Document all public APIs
    ```

    Args:
        rules_dir: Directory containing rule .md files.
                  Defaults to .emdash/rules/ in cwd.

    Returns:
        Combined rules as a string
    """
    if rules_dir is None:
        rules_dir = Path.cwd() / ".emdash" / "rules"

    if not rules_dir.exists():
        return ""

    rules_parts = []

    # Load all .md files in order
    for md_file in sorted(rules_dir.glob("*.md")):
        try:
            content = md_file.read_text().strip()
            if content:
                rules_parts.append(content)
                log.debug(f"Loaded rules from: {md_file.name}")
        except Exception as e:
            log.warning(f"Failed to load rules from {md_file}: {e}")

    if rules_parts:
        combined = "\n\n---\n\n".join(rules_parts)
        log.info(f"Loaded {len(rules_parts)} rule files")
        return combined

    return ""


def get_rules_for_agent(
    agent_name: str,
    rules_dir: Optional[Path] = None,
) -> str:
    """Get rules specific to an agent.

    Looks for:
    1. Agent-specific rules in {rules_dir}/{agent_name}.md
    2. General rules in {rules_dir}/*.md

    Args:
        agent_name: Name of the agent
        rules_dir: Optional rules directory

    Returns:
        Combined rules string
    """
    if rules_dir is None:
        rules_dir = Path.cwd() / ".emdash" / "rules"

    parts = []

    # Load general rules first
    general_rules = load_rules(rules_dir)
    if general_rules:
        parts.append(general_rules)

    # Look for agent-specific rules
    agent_rules_file = rules_dir / f"{agent_name}.md"
    if agent_rules_file.exists():
        try:
            agent_rules = agent_rules_file.read_text().strip()
            if agent_rules:
                parts.append(f"# Agent-Specific Rules: {agent_name}\n\n{agent_rules}")
                log.debug(f"Loaded agent-specific rules for: {agent_name}")
        except Exception as e:
            log.warning(f"Failed to load agent rules: {e}")

    return "\n\n---\n\n".join(parts)


def format_rules_for_prompt(rules: str) -> str:
    """Format rules for inclusion in a system prompt.

    Args:
        rules: Raw rules content

    Returns:
        Formatted rules section
    """
    if not rules:
        return ""

    return f"""
## Project Guidelines

The following rules and guidelines should be followed:

{rules}

---
"""
