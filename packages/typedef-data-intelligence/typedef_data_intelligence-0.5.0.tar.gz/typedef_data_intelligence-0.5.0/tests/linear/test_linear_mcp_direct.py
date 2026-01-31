"""Simple test script to call Linear MCP server tools using FastMCP.

For the linear MCP api, see https://opentools.com/registry/linear-remote
"""
import datetime
import json
import pytest
import pytest_asyncio
from fastmcp import Client

# see https://pypi.org/project/linear-api/
from linear_api import LinearClient, LinearIssueInput, LinearPriority, LinearState



MCP_URL = "https://mcp.linear.app/mcp"
#TEST_ISSUE_ID = "f33140bf-4404-493e-8ad0-e9935155a50f"
#TEST_USER_ID = "edcc3b76-7b32-4fac-8fb8-21dcebfa2bd0" # analyst-agent

TEST_ISSUE = "DAV-2"
TEST_USER_1 = "analyst-agent"
TEST_USER_2 = "data-engineer-agent"
TEST_LABEL_NAME = "test"


async def find_label_id_by_name(mcp_client, label_name: str, team_id: str = None) -> str | None:
    """Helper function to find a label ID by name by checking existing issues."""
    # List issues to find one with the label
    tool_args = {"limit": 50}
    if team_id:
        tool_args["team"] = team_id

    result = await mcp_client.call_tool(
        "list_issues",
        tool_args,
        raise_on_error=False
    )

    if result.is_error:
        return None

    # Process the result
    issues = None
    if result.structured_content:
        issues = result.structured_content
    elif result.data:
        issues = result.data
    elif result.content:
        if isinstance(result.content, list):
            if len(result.content) > 0 and hasattr(result.content[0], 'text'):
                issues = json.loads(result.content[0].text)
            else:
                issues = result.content

    if not issues:
        return None

    # Handle new API format: {"issues": [...]} or {"nodes": [...]}
    if isinstance(issues, dict):
        issues = issues.get("nodes") or issues.get("issues") or []

    if not isinstance(issues, list):
        return None

    # Search through issues for the label
    for issue in issues:
        labels = issue.get('labels', [])
        for label in labels:
            if label.get('name', '').lower() == label_name.lower():
                return label.get('id')

    return None


@pytest_asyncio.fixture
async def mcp_client(linear_api_key):
    """Fixture for Linear MCP client."""
    client = Client(MCP_URL, auth=linear_api_key)
    async with client:
        yield client


@pytest.mark.asyncio
async def test_linear_mcp_list(mcp_client, linear_api_key, linear_team_id):
    """Test calling list_issues tool on Linear MCP server."""
    # Prepare arguments for list_issues
    tool_args = {
        "team": linear_team_id,
        "limit": 10
    }
    
    # Call the tool
    result = await mcp_client.call_tool(
        "list_issues",
        tool_args,
        raise_on_error=True
    )
    
    assert not result.is_error, f"Tool returned error: {result.content}"
    
    # Process the result
    issues = None
    if result.structured_content:
        issues = result.structured_content
    elif result.data:
        issues = result.data
    elif result.content:
        if isinstance(result.content, list):
            if len(result.content) > 0 and hasattr(result.content[0], 'text'):
                issues = json.loads(result.content[0].text)
            else:
                issues = result.content
    
    assert issues is not None, "No data returned from tool"

    # Handle new API format: {"issues": [...]} or {"nodes": [...]}
    if isinstance(issues, dict):
        issues = issues.get("nodes") or issues.get("issues") or []

    assert isinstance(issues, list), f"Issues is not a list: {type(issues)}"
    assert len(issues) > 0, "No issues returned"
    
    # Verify issue structure
    if len(issues) > 0:
        issue = issues[0]
        assert 'id' in issue, "Issue missing 'id' field"
        assert 'title' in issue, "Issue missing 'title' field"


@pytest.mark.asyncio
async def test_linear_mcp_get_issue(mcp_client, linear_api_key):
    """Test calling get_issue tool on Linear MCP server."""
    # Call get_issue
    result = await mcp_client.call_tool(
        "get_issue",
        {"id": TEST_ISSUE},
        raise_on_error=True
    )
    
    assert not result.is_error, f"Tool returned error: {result.content}"
    
    # Process the result
    issue = None
    if result.structured_content:
        issue = result.structured_content
    elif result.data:
        issue = result.data
    elif result.content:
        if isinstance(result.content, list) and len(result.content) > 0:
            if hasattr(result.content[0], 'text'):
                issue = json.loads(result.content[0].text)
            else:
                issue = result.content[0]
    
    assert issue is not None, "No data returned from tool"
    assert issue.get('identifier') == TEST_ISSUE, f"Issue identifier mismatch: {issue.get('identifier')} != {TEST_ISSUE}"
    assert 'title' in issue, "Issue missing 'title' field"


@pytest.mark.asyncio
async def test_linear_mcp_add_comment(mcp_client, linear_api_key):
    """Test calling add_comment tool on Linear MCP server."""
    # Test add_comment
    test_comment = "This is a test comment from the Linear MCP test script"
    test_author = "test-script"
    
    tool_args = {
        "issueId": TEST_ISSUE,
        "body": f"[{test_author}] {test_comment}"
    }
    
    # Call the tool
    result = await mcp_client.call_tool(
        "create_comment",
        tool_args,
        raise_on_error=True
    )
    
    assert not result.is_error, f"Tool returned error: {result.content}"
    
    # Verify by getting the issue again
    get_result = await mcp_client.call_tool(
        "get_issue",
        {"id": TEST_ISSUE},
        raise_on_error=True
    )
    
    assert not get_result.is_error, "Failed to retrieve issue after adding comment"
    
    if get_result.content and len(get_result.content) > 0:
        if hasattr(get_result.content[0], 'text'):
            try:
                issue = json.loads(get_result.content[0].text)
                assert issue.get('identifier') == TEST_ISSUE, "Retrieved issue identifier mismatch"
            except json.JSONDecodeError:
                pass  # Still consider it success if the tool call succeeded


@pytest.mark.asyncio
async def test_linear_mcp_update_ticket(mcp_client, linear_api_key):
    """Test calling update_issue tool on Linear MCP server with multiple fields."""
    # Get current issue state to tweak existing values
    get_result = await mcp_client.call_tool(
        "get_issue",
        {"id": TEST_ISSUE},
        raise_on_error=True
    )
    
    assert not get_result.is_error, "Failed to retrieve current issue"
    
    current_issue = None
    if get_result.content and len(get_result.content) > 0:
        if hasattr(get_result.content[0], 'text'):
            try:
                current_issue = json.loads(get_result.content[0].text)
            except json.JSONDecodeError:
                pass
    
    assert current_issue is not None, "Could not retrieve current issue state"
    
    # Extract current values
    current_title = current_issue.get('title', '')
    current_description = current_issue.get('description', '')
    current_priority = current_issue.get('priority', {})
    current_priority_value = current_priority.get('value', 2)

    current_state_name = current_issue.get('status', 'Backlog')

    current_assignee = current_issue.get('assignee')

    current_labels = current_issue.get('labels', [])
    current_label_ids = [label.get('id') for label in current_labels]

    # Find test label ID and check if it's currently on the issue
    test_label_id = None
    for label in current_labels:
        if label.get('name', '').lower() == TEST_LABEL_NAME.lower():
            test_label_id = label.get('id')
            break

    # If test label not found in current labels, try to find it from other issues
    if test_label_id is None:
        test_label_id = await find_label_id_by_name(mcp_client, TEST_LABEL_NAME)

    # Prepare updated values (tweak existing values)
    updated_title = f"{current_title} [UPDATED]"
    updated_description = f"{current_description}\n\n--- Updated via test script ---"

    # Cycle priority: 1->2->3->4->1 (Urgent->High->Medium->Low->Urgent)
    priority_cycle = {1: 2, 2: 3, 3: 4, 4: 1}
    updated_priority = priority_cycle.get(current_priority_value, 2)

    # Cycle state: Backlog -> Todo -> In Progress -> Done -> Backlog
    state_cycle = {
        "Backlog": "Todo",
        "Todo": "In Progress",
        "In Progress": "Done",
        "Done": "Backlog"
    }
    updated_state = state_cycle.get(current_state_name, "Todo")

    if current_assignee == TEST_USER_1:
        updated_assignee = TEST_USER_2
    else:
        updated_assignee = TEST_USER_1

    # Toggle test label: add if not present, remove if present
    updated_labels = current_label_ids[:]  # Start with existing
    if test_label_id:
        if test_label_id in current_label_ids:
            # Remove test label
            updated_labels.remove(test_label_id)
        else:
            # Add test label
            updated_labels.append(test_label_id)

    tool_args = {
        "id": TEST_ISSUE,
        "title": updated_title,
        "description": updated_description,
        "priority": updated_priority,
        "state": updated_state,
        "assignee": updated_assignee,
    }

    # Always include labelIds (even if empty) to ensure labels are updated
    tool_args["labelIds"] = updated_labels
    # Call the tool
    result = await mcp_client.call_tool(
        "update_issue",
        tool_args,
        raise_on_error=True
    )
    assert not result.is_error, f"Tool returned error: {result.content}"
    
    # Process the result
    updated_issue = None
    if result.structured_content:
        updated_issue = result.structured_content
    elif result.data:
        updated_issue = result.data
    elif result.content:
        if isinstance(result.content, list) and len(result.content) > 0:
            if hasattr(result.content[0], 'text'):
                try:
                    updated_issue = json.loads(result.content[0].text)
                except json.JSONDecodeError:
                    pass
    
    assert updated_issue is not None, "Failed to parse updated issue response"
    assert updated_issue.get('identifier') == TEST_ISSUE, "Updated issue identifier mismatch"
    assert updated_issue.get('title') == updated_title, "Title was not updated correctly"
    
    priority = updated_issue.get('priority', {})
    priority_value = priority.get('value')
    assert priority_value == updated_priority, f"Priority mismatch: {priority_value} != {updated_priority}"

    # Verify assignee was set correctly
    assignee = updated_issue.get('assignee')
    assert assignee == updated_assignee, f"Assignee mismatch: {assignee} != {updated_assignee}"

    # Verify test label was toggled correctly
    if test_label_id:
        updated_issue_labels = updated_issue.get('labels', [])
        updated_issue_label_ids = [label.get('id') for label in updated_issue_labels]
        expected_has_label = test_label_id not in current_label_ids
        actual_has_label = test_label_id in updated_issue_label_ids
        assert actual_has_label == expected_has_label, (
            f"Test label toggle failed: expected {'added' if expected_has_label else 'removed'}, "
            f"but label is {'present' if actual_has_label else 'absent'}"
        )


@pytest.mark.asyncio
async def test_linear_mcp_create_ticket(mcp_client, linear_api_key, linear_team_id):
    """Test calling create_issue tool on Linear MCP server with all fields."""
    # Prepare dummy values for all fields
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    dummy_title = f"Test Issue Created at {timestamp}"
    dummy_description = """This is a test issue created by the Linear MCP test script.

## Test Fields:
- **Title**: Test issue with timestamp
- **Description**: This markdown description
- **Priority**: Medium (2)
- **State**: Todo
- **Assignee**: analyst-agent
- **Labels**: Test label (if available)

## Purpose:
This ticket is created to test the create_ticket MCP tool functionality with all available fields populated.
"""
    dummy_priority = 2  # Medium priority
    dummy_state = "Todo"

    # Find and add test label if available
    test_label_id = await find_label_id_by_name(mcp_client, TEST_LABEL_NAME, linear_team_id)
    dummy_label_ids = []
    if test_label_id:
        dummy_label_ids = [test_label_id]

    tool_args = {
        "team": linear_team_id,
        "assignee": TEST_USER_1,
        "title": dummy_title,
        "description": dummy_description,
        "priority": dummy_priority,
        "state": dummy_state,
    }
    
    if dummy_label_ids:
        tool_args["labelIds"] = dummy_label_ids
    
    # Call the tool
    result = await mcp_client.call_tool(
        "create_issue",
        tool_args,
        raise_on_error=True
    )
    
    assert not result.is_error, f"Tool returned error: {result.content}"
    
    # Process the result
    created_issue = None
    if result.structured_content:
        created_issue = result.structured_content
    elif result.data:
        created_issue = result.data
    elif result.content:
        if isinstance(result.content, list) and len(result.content) > 0:
            if hasattr(result.content[0], 'text'):
                try:
                    created_issue = json.loads(result.content[0].text)
                except json.JSONDecodeError:
                    pass
    
    assert created_issue is not None, "Failed to parse created issue response"
    assert created_issue.get('title') == dummy_title, "Title mismatch"
    assert 'id' in created_issue, "Created issue missing 'id' field"
    assert 'identifier' in created_issue, "Created issue missing 'identifier' field"
    assert 'assignee' in created_issue, "Created issue missing 'assignee' field"
    assert created_issue.get('assignee') == TEST_USER_1, f"Assignee mismatch: {created_issue.get('assignee')} != {TEST_USER_1}"
    assert created_issue.get('status') == dummy_state, "State mismatch"
    priority = created_issue.get('priority', {})
    priority_value = priority.get('value')
    assert priority_value == dummy_priority, f"Priority mismatch: {priority_value} != {dummy_priority}"

    # Verify test label was added if it was found
    if test_label_id:
        created_issue_labels = created_issue.get('labels', [])
        created_issue_label_ids = [label.get('id') for label in created_issue_labels]
        assert test_label_id in created_issue_label_ids, (
            f"Test label '{TEST_LABEL_NAME}' was not added to the created issue"
        )


@pytest.mark.asyncio
async def test_linear_py_api_create_and_delete_ticket(linear_api_key, linear_team_id):
    """Test creating and deleting a ticket using the Linear Python API."""
    client = LinearClient(api_key=linear_api_key)
    me = client.users.get_me()

    print(f"me: {me}")

    create_issue_data = LinearIssueInput(
        title="Test Issue",
        description="This is a test issue",
        priority=3,
        stateName="Todo",
        assigneeId=me.id,
        teamName="DEV - Data Engineer Demo"
    )
    #print(type(LinearIssueInput))
    issue = client.issues.create(create_issue_data)

    #print(f"issue: {issue}")
    client.issues.delete(issue.id)