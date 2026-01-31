# Getting Started with typedef Data Intelligence

This guide walks you through setting up typedef for the first time.

## Prerequisites

Before running setup, make sure you have:

1. **A dbt project** - Either a local directory or a Git repository URL
2. **Snowflake credentials** - Account, user, role, warehouse, and private key authentication
3. **LLM API Keys** - Anthropic/OpenAI (We will provide these!)

## Quick Start

```bash
# Install typedef
pip install typedef-data-intelligence

# Run the setup wizard
typedef init

# Sync your dbt project metadata
typedef sync

# Launch the TUI
typedef chat
```

That's it! The wizard handles the rest.

---

## Step-by-Step Setup

### 1. Run the Setup Wizard

```bash
typedef init
```

This launches an interactive wizard that guides you through configuration. The wizard has 10 steps, but most have sensible defaults.

### 2. Wizard Steps Overview

| Step                     | What It Does                                                          |
| ------------------------ | --------------------------------------------------------------------- |
| **Project Name**         | Name your project (e.g., `my_analytics`)                              |
| **dbt Location**         | Point to your dbt project (local path or Git URL)                     |
| **Sub-Project**          | If your repo has multiple dbt projects, select one                    |
| **Snowflake Connection** | Enter your Snowflake credentials                                      |
| **Database Selection**   | Choose which databases/schemas to use                                 |
| **LLM Keys**             | Add your Anthropic/OpenAI API key                                     |
| **Integrations**         | Set up your ticketing system/Allow telemetry to flow back to typedef. |
| **Profiles Preview**     | Review the generated `profiles.yml`                                   |
| **Validation**           | Runs `dbt deps` and `dbt docs generate`                               |
| **Summary**              | Review and confirm your configuration                                 |

**Tips:**

- Click **"Load from Environment"** on the Snowflake step if you have `SNOWFLAKE_*` environment variables set
- Git URLs are cloned to `~/.typedef/projects/<project_name>/`
- The wizard generates `profiles.yml` outside your repo to avoid git conflicts

### 3. Sync Your Project

After the wizard completes, sync your dbt metadata:

```bash
typedef sync
```

This:

- Parses your dbt `manifest.json`
- Loads models, sources, and columns into the knowledge graph
- Runs semantic analysis to extract measures, dimensions, and grain
- Discovers join patterns between models

**Note:** First sync can take a few minutes depending on project size.

### 4. Launch the TUI

```bash
typedef chat
```

This opens the Data Concierge interface with tabs for each agent:

- **Analyst** - Answer business questions using semantic views
- **Investigator** - Troubleshoot data issues
- **Insights** - Understand your data architecture
- **Copilot** - Build and modify dbt models
- **Tickets** - View and manage work items
- **Daemon** - Run autonomous ticket processing

Press **F1** for help on which agent to use.

---

## Configuration Files

typedef stores configuration in `~/.typedef/`:

```text
~/.typedef/
├── config.yaml          # Main configuration (projects, settings)
├── projects/            # Cloned Git repositories
│   └── <project_name>/
├── profiles/            # dbt profiles.yml files (per project)
│   └── <project_name>/
│       └── profiles.yml
├── exports/             # Exported reports
└── logs/                # Log files
```

---

## Common Commands

| Command                    | Description                                |
| -------------------------- | ------------------------------------------ |
| `typedef init`             | Run setup wizard for a new project         |
| `typedef projects add`     | Add another dbt project                    |
| `typedef projects list`    | Show configured projects                   |
| `typedef project [name]`   | Show or switch the default project         |
| `typedef project --select` | Choose a project via interactive selector  |
| `typedef sync`             | Sync dbt metadata to knowledge graph       |
| `typedef chat [project]`   | Launch the TUI (optionally pick a project) |
| `typedef config show`      | Show current configuration                 |
| `typedef config validate`  | Validate configuration                     |
| `typedef export`           | Export graph for sharing                   |
| `typedef import <archive>` | Import graph from a teammate               |
| `typedef reset`            | Reset all local typedef data               |

---

## Environment Variables

You can pre-set these to speed up the wizard:

```bash
# Snowflake credentials
export SNOWFLAKE_ACCOUNT=abc123.us-west-2
export SNOWFLAKE_USER=your_username
export SNOWFLAKE_ROLE=ANALYST
export SNOWFLAKE_WAREHOUSE=COMPUTE_WH
export SNOWFLAKE_PRIVATE_KEY_PATH=~/.ssh/snowflake_rsa_key.p8

# LLM API keys
export ANTHROPIC_API_KEY=sk-ant-...
export OPENAI_API_KEY=sk-...
```

---

## Troubleshooting

### "Connection failed" on Snowflake step

- Verify your account identifier format (e.g., `abc123.us-west-2`)
- Check that your private key file exists and has correct permissions
- Ensure your role has access to the warehouse

### "No dbt_project.yml found"

- Make sure your path points to the dbt project root (where `dbt_project.yml` lives)
- For monorepos, the wizard will scan subdirectories and let you select

### Sync takes too long

- First sync analyzes all models with LLM - this is normal
- Subsequent syncs are incremental and much faster
- Use `--skip-semantic` flag to skip LLM analysis if needed

### Need to reconfigure?

```bash
# Re-run the wizard for the current project
typedef init --reconfigure

# Or edit config directly
vim ~/.typedef/config.yaml
```

---

## Next Steps

Once setup is complete:

1. Press **F1** in the TUI to see which agent to use for different tasks
2. Try asking the **Analyst**: "What semantic views are available?"
3. Try asking **Insights**: "Explain the data model"
4. See the [Agent User Guide](AGENT_USER_GUIDE.md) for detailed agent documentation
