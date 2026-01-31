# typedef Data Intelligence

Unified lineage management and AI-powered analytics platform for dbt projects.

## Features

- **Interactive TUI**: Terminal-based interface for exploring data lineage
- **AI-Powered Analysis**: Semantic analysis of your dbt models using LLMs

## Requirements

- Python 3.12+
- API keys: `ANTHROPIC_API_KEY` and `OPENAI_API_KEY`
- A dbt project with compiled artifacts (`dbt compile`)
- Snowflake access

## Installation

```bash
pip install typedef-data-intelligence
```

## Quick Start

1. **Initialize** - Run the setup wizard to configure your environment:

   ```bash
   typedef init
   ```

2. **Sync** - Load your dbt project into the Knowledge Graph:

   ```bash
   typedef sync
   ```

3. **Chat** - Start the interactive AI assistant:

   ```bash
   typedef chat
   ```

## Documentation

For detailed documentation, architecture guides, and API reference, see the [GitHub repository](https://github.com/typedef-ai/data-intelligence).

## Support

- [Issues](https://github.com/typedef-ai/data-intelligence/issues)
- [typedef.ai](https://typedef.ai)
