# Linear MCP Ticketing Backend

This backend integrates with Linear through Linear's hosted MCP (Model Context Protocol) endpoint, providing seamless ticket management through Linear's API.

## Features

Connects to Linear's hosted MCP server at `https://mcp.linear.app/mcp`:

### Issue Management

- ✅ **Create issues** with full field support (title, description, team, project, parent/child relationships)
- ✅ **Update existing issues** (priority, description, etc.)
- ✅ **Delete issues** (single or bulk deletion)
- ✅ **Search issues** with filtering and by identifier
- ✅ **Associate issues** with projects
- ✅ **Create parent/child** issue relationships
- ✅ **Comment management** (create, update, delete comments)
- ✅ **Comment resolution** handling (resolve/unresolve comments)

### Project Management

- ✅ **Create projects** with associated issues
- ✅ **Get project information**
- ✅ **List all projects** with optional filtering
- ✅ **Associate issues** with projects
- ✅ **Project milestone** management (create, update, delete)

### Team Management

- ✅ **Get team information** (with states and workflow details)
- ✅ **Access team states** and labels

### Batch Operations

- ✅ **Bulk issue creation**
- ✅ **Bulk issue deletion**

## Setup

### 1. Get Linear API Keys

Get **Personal API Keys** from Linear for both analyst and data engineer roles:

1. Go to Linear: Your Personal Settings > API > Personal API Keys
2. Click "Create key", give it a label (e.g., "Data Intelligence Analyst MCP"), and copy the generated key
3. Repeat for the data engineer role (e.g., "Data Intelligence Data Engineer MCP")

**Note**: You can use the same API key for both roles if desired, but separate keys allow for better audit trails and permission management.

### 2. Configure

Add to your `config.yml` and set the environment variables:

```yaml
ticket:
  enabled: true
  backend: linear
  mcp_server_url: https://mcp.linear.app/mcp
  team_id: ${LINEAR_TEAM_ID?} # Optional - use ? suffix to make env var optional
  project_id: ${LINEAR_PROJECT_ID?} # Optional - use ? suffix to make env var optional
  analyst_user_token: ${LINEAR_ANALYST_API_KEY?} # Optional in config (but required at runtime)
  data_engineer_user_token: ${LINEAR_DATA_ENGINEER_API_KEY?} # Optional in config (but required at runtime)
```

```bash
export LINEAR_ANALYST_API_KEY=your-analyst-api-key
export LINEAR_DATA_ENGINEER_API_KEY=your-data-engineer-api-key
export LINEAR_TEAM_ID=your-team-id  # Optional
export LINEAR_PROJECT_ID=your-project-id  # Optional
```

**Note**: The API keys (`LINEAR_ANALYST_API_KEY` and `LINEAR_DATA_ENGINEER_API_KEY`) are optional in the config file (using the `?` suffix), which allows the config to load even if they're not set. However, at least one of these API keys must be set in the environment at runtime for the Linear backend to initialize. If neither is set, the ticket backend will be gracefully disabled.

### 3. Role Selection

The role (`analyst` or `data_engineer`) is automatically determined when the orchestrator configures the Linear backend. Each agent type (analyst orchestrator, data engineer orchestrator) uses its corresponding API key:

- **Analyst orchestrator** → Uses `LINEAR_ANALYST_API_KEY`
- **Data engineer orchestrator** → Uses `LINEAR_DATA_ENGINEER_API_KEY`

This ensures that tickets created by each agent type are properly attributed and use the correct authentication credentials.

## Configuration Options

| Option                     | Type   | Required | Description                                                                        |
| -------------------------- | ------ | -------- | ---------------------------------------------------------------------------------- |
| `backend`                  | string | Yes      | Must be "linear"                                                                   |
| `mcp_server_url`           | string | Yes      | URL of Linear's hosted MCP server (use `https://mcp.linear.app/mcp`)               |
| `team_id`                  | string | No       | Linear team ID for tickets                                                         |
| `project_id`               | string | No       | Linear project ID for tickets                                                      |
| `analyst_user_token`       | string | No       | Analyst's Linear API key (use `${LINEAR_ANALYST_API_KEY}` for env var)             |
| `data_engineer_user_token` | string | No       | Data engineer's Linear API key (use `${LINEAR_DATA_ENGINEER_API_KEY}` for env var) |

**Note**: The `analyst_user_token` and `data_engineer_user_token` config fields are optional. The backend actually reads API keys directly from the environment variables `LINEAR_ANALYST_API_KEY` and `LINEAR_DATA_ENGINEER_API_KEY` based on the role selected by the orchestrator. The config fields are provided for documentation purposes and can reference environment variables using `${VAR_NAME}` syntax.

## Usage

### Creating Tickets

```python
from lineage.backends.tickets.protocol import TicketPriority

# Create a ticket
ticket = ticket_storage.create_ticket(
    title="Fix ARR calculation",
    description="ARR calculation in fct_arr_reporting_monthly is incorrect",
    priority=TicketPriority.HIGH,
    created_by="data-engineer-agent",
    tags=["bug", "finance"]
)
```

### Updating Tickets

```python
# Update ticket status
updated_ticket = ticket_storage.update_ticket(
    ticket_id="LIN-123456",
    status=TicketStatus.IN_PROGRESS,
    priority=TicketPriority.URGENT
)
```

### Adding Comments

```python
# Add a comment
ticket_storage.add_comment(
    ticket_id="LIN-123456",
    author="analyst-agent",
    comment="Found the issue in the calculation logic"
)
```

### Listing Tickets

```python
# List all open tickets
open_tickets = ticket_storage.list_tickets(
    status=TicketStatus.OPEN,
    limit=10
)

# List high priority tickets
urgent_tickets = ticket_storage.list_tickets(
    priority=TicketPriority.URGENT
)
```

## Linear Integration Details

### Status Mapping

| Our Status    | Linear State |
| ------------- | ------------ |
| `OPEN`        | Todo         |
| `IN_PROGRESS` | In Progress  |
| `BLOCKED`     | In Progress  |
| `COMPLETED`   | Done         |
| `CANCELLED`   | Canceled     |

### Priority Mapping

| Our Priority | Linear Priority |
| ------------ | --------------- |
| `URGENT`     | 1               |
| `HIGH`       | 2               |
| `MEDIUM`     | 3               |
| `LOW`        | 4               |

## Troubleshooting

### Common Issues

1. **"Failed to initialize Linear ticket storage"**
   - Verify `LINEAR_ANALYST_API_KEY` and/or `LINEAR_DATA_ENGINEER_API_KEY` are set correctly
   - Check Linear API token permissions
   - Ensure the tokens have access to the workspace you're trying to use
   - Verify the role being used matches the available API key (analyst vs data_engineer)

2. **"MCP communication failed"**
   - Verify `mcp_server_url` is set to `https://mcp.linear.app/mcp`
   - Check your internet connection
   - Ensure the Linear MCP endpoint is accessible from your network

3. **"MCP tool error"**
   - Verify the tool name matches Linear's MCP API
   - Check that required arguments are provided
   - Ensure Linear API permissions allow the requested operation
   - Verify your API tokens are valid and haven't expired
   - Confirm the correct API key is being used for the agent's role (analyst vs data_engineer)

### Debug Mode

Enable debug logging to see MCP tool calls:

```python
import logging
logging.getLogger("lineage.backends.tickets.linear_backend").setLevel(logging.DEBUG)
```

## Example Configuration Files

See the following example configuration files in the repository:

- `config.yml` - Local development configuration
- `config.medallion.docker.yml` - Docker-based configuration with Linear ticket backend

Both files demonstrate the Linear ticket backend configuration with dual API keys for analyst and data engineer roles.
