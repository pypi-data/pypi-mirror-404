"""Enable running CLI runner as a module.

Usage:
    python -m lineage.agent.pydantic analyst
    python -m lineage.agent.pydantic engineer "What models exist?"
"""
from lineage.agent.pydantic.cli_runner import main

if __name__ == "__main__":
    main()
