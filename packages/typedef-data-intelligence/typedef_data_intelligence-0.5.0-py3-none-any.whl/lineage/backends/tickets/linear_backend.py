"""Linear implementation of TicketStorage using FastMCP client.

For the linear MCP api, see https://opentools.com/registry/linear-remote"""
from __future__ import annotations

import json
import logging
import os
from textwrap import dedent
from datetime import datetime
from typing import Any, Dict, List, Optional, Literal

from fastmcp import Client

from lineage.backends.tickets.protocol import (
    TicketStorage,
    Ticket,
    TicketStatus,
    TicketPriority,
)

logger = logging.getLogger(__name__)


class LinearTicketStorage(TicketStorage):
    """Linear ticket storage implementation using FastMCP client.

    Connects to the official Linear MCP server at https://mcp.linear.app/mcp
    and provides ticket management capabilities via the TicketStorage protocol.

    Note:
    * presents human readable identifiers and names (e.g. 'DAV-1') instead of Linear UUIDs (e.g. '1234567890')
    * Linear API expects the UUIDs for entity managment, so we populate a lookup cache (dicts) to abstract the UUIDs away from the agent
    * 
    """

    def __init__(
        self,
        mcp_server_url: str,
        team_id: Optional[str] = None,
        project_id: Optional[str] = None,
        role: Optional[Literal["analyst", "data_engineer"]] = "analyst"
    ):
        """Initialize Linear ticket storage.

        Args:
            mcp_server_url: URL of Linear MCP server (e.g., https://mcp.linear.app/mcp)
            team_id: Linear team ID to use for tickets
            project_id: Linear project ID to assign tickets to
            role: Role to use for tickets (analyst or data_engineer).  Dictates which user token to use for Linear.
        """
        logger.debug(f"Initializing LinearTicketStorage with mcp_server_url={mcp_server_url}, team_id={team_id}, project_id={project_id}")
        
        # Validate Linear API key is available

        if role == "analyst":
            linear_token = os.getenv("LINEAR_ANALYST_API_KEY", None)
        elif role == "data_engineer":
            linear_token = os.getenv("LINEAR_DATA_ENGINEER_API_KEY", None)
        
        self.mcp_server_url = mcp_server_url
        self.team_id = team_id
        self.project_id = project_id

        # Modifications to linear API require using the entity IDs instead of names
        self.user_id_to_name = {}
        self.user_name_to_id = {}  # Reverse lookup: name -> id
        self.team_id_to_name = {}
        self.team_name_to_id = {}  # Reverse lookup: name -> id
        self.ticket_id_to_identifier = {}
        self.ticket_identifier_to_id = {}  # Reverse lookup: identifier -> id
        self._caches_initialized = False  # Track if caches have been populated

        # FastMCP client for Linear MCP server
        self._client = Client(str(mcp_server_url), auth=linear_token)
        self._connected = False  # Track connection state

        logger.info(f"✅ Linear ticket storage initialized (server={mcp_server_url})")
        logger.debug(f"LinearTicketStorage initialization complete - team_id={self.team_id}, project_id={self.project_id}")

    async def _ensure_connected(self) -> None:
        """Ensure MCP client is connected (lazy connection on first use)."""
        if not self._connected:
            logger.debug(f"Connecting to Linear MCP server at: {self.mcp_server_url}")
            await self._client.__aenter__()
            self._connected = True
            logger.debug("Linear MCP client connected")
            

   

    async def _initialize_caches(self) -> None:
        """Initialize local id->name/identifier caches by paging API results.

        - Pages through issues (50 per page) and fills ticket_id_to_identifier and ticket_identifier_to_id
        - Lists users and teams and fills user_id_to_name, user_name_to_id, team_id_to_name, and team_name_to_id
        """

        if self._caches_initialized:
            return
        try:
            logger.debug("Initializing Linear caches (tickets, users, teams)")
            # --- Page through issues to populate ticket_id_to_identifier ---
            issues_fetched = 0
            after_cursor: Optional[str] = None
            page_number = 0
            while True:
                page_number += 1
                args: Dict[str, Any] = {"limit": 50}
                if self.team_id:
                    args["team"] = self.team_id
                if after_cursor:
                    args["after"] = after_cursor

                args["includeArchived"] = False

                logger.debug(f"Paging issues (page {page_number}) with args: {json.dumps(args)}")
                try:
                    response = await self._call_mcp_tool("list_issues", args)
                except Exception as e:
                    logger.warning(f"Failed to list issues for cache init on page {page_number}: {e}")
                    import traceback
                    traceback.print_exc()
                    break

                # Response can be either a list of issues or a dict with nodes/pageInfo
                if isinstance(response, list):
                    issues: List[Dict[str, Any]] = response
                    page_info = None
                else:
                    issues = response.get("nodes") or response.get("issues") or []
                    page_info = response.get("pageInfo")

                logger.debug(f"Received {len(issues)} issues on page {page_number}")
                if not issues:
                    break

                for issue in issues:
                    issue_id = issue.get("id")
                    identifier = issue.get("identifier")
                    if issue_id and identifier:
                        self.ticket_id_to_identifier[issue_id] = identifier
                        self.ticket_identifier_to_id[identifier] = issue_id

                issues_fetched += len(issues)

                # Determine if we should continue paging
                has_next = False
                if page_info is not None:
                    has_next = bool(page_info.get("hasNextPage"))
                    after_cursor = page_info.get("endCursor")
                else:
                    # Fallback heuristic: if we got a full page, try to continue using last id
                    has_next = len(issues) >= 50
                    after_cursor = issues[-1].get("id") if issues and has_next else None

                if not has_next or not after_cursor:
                    break

            logger.info(f"✅ Cached {issues_fetched} issue identifiers (ticket_id_to_identifier)")

            # --- List users to populate user_id_to_name ---
            try:
                users_response = await self._call_mcp_tool("list_users", {})
                users: List[Dict[str, Any]] = users_response if isinstance(users_response, list) else users_response.get("nodes") or users_response.get("users") or []
                for user in users:
                    uid = user.get("id")
                    name = user.get("name") or user.get("displayName")
                    if uid and name:
                        self.user_id_to_name[uid] = name
                        self.user_name_to_id[name] = uid
                logger.info(f"✅ Cached {len(self.user_id_to_name)} users (user_id_to_name, user_name_to_id)")
            except Exception as e:
                logger.warning(f"Failed to list users for cache init: {e}")
                import traceback
                traceback.print_exc()
            # --- List teams to populate team_id_to_name ---
            try:
                teams_response = await self._call_mcp_tool("list_teams", {})
                teams: List[Dict[str, Any]] = teams_response if isinstance(teams_response, list) else teams_response.get("nodes") or teams_response.get("teams") or []
                for team in teams:
                    tid = team.get("id")
                    tname = team.get("name") or team.get("key")
                    if tid and tname:
                        self.team_id_to_name[tid] = tname
                        self.team_name_to_id[tname] = tid
                logger.info(f"✅ Cached {len(self.team_id_to_name)} teams (team_id_to_name, team_name_to_id)")
            except Exception as e:
                logger.warning(f"Failed to list teams for cache init: {e}")
                import traceback
                traceback.print_exc()
            self._caches_initialized = True
            logger.debug(f"User ID to name: {self.user_id_to_name}")
            logger.debug(f"User name to ID: {self.user_name_to_id}")
            logger.debug(f"Team ID to name: {self.team_id_to_name}")
            logger.debug(f"Team name to ID: {self.team_name_to_id}")
            logger.debug(f"Ticket ID to identifier: {self.ticket_id_to_identifier}")
            logger.debug(f"Ticket identifier to ID: {self.ticket_identifier_to_id}")
        except Exception as e:
            logger.warning(f"Failed to initialize Linear caches: {e}")
            import traceback
            traceback.print_exc()

    def _resolve_ticket_identifier_to_id(self, ticket_id_or_identifier: str) -> str:
        """Resolve ticket identifier (e.g., 'DAV-1') to Linear ID, or return as-is if already an ID.
        
        Args:
            ticket_id_or_identifier: Either a Linear ID or an identifier like 'DAV-1'
            
        Returns:
            Linear ID for use in API calls
        """
        # Check if it's already a UUID-like ID (Linear IDs are UUIDs)
        # If it contains hyphens and looks like a UUID, assume it's already an ID
        if "-" in ticket_id_or_identifier and len(ticket_id_or_identifier) > 30:
            return ticket_id_or_identifier
        
        # Otherwise, treat as identifier and look it up
        linear_id = self.ticket_identifier_to_id.get(ticket_id_or_identifier)
        if linear_id:
            logger.debug(f"Resolved ticket identifier '{ticket_id_or_identifier}' to ID '{linear_id}'")
            return linear_id
        
        # If not found in cache, assume it's already an ID (might not be in cache yet)
        logger.debug(f"Ticket identifier '{ticket_id_or_identifier}' not in cache, treating as ID")
        return ticket_id_or_identifier
    
    def _resolve_user_name_to_id(self, user_name: str) -> Optional[str]:
        """Resolve user name to Linear ID.
        
        Args:
            user_name: User name (e.g., 'analyst-agent')
            
        Returns:
            Linear user ID, or None if not found
        """
        user_id = self.user_name_to_id.get(user_name)
        if user_id:
            logger.debug(f"Resolved user name '{user_name}' to ID '{user_id}'")
            return user_id
        
        # If not found, check if it's already an ID (UUID format)
        if "-" in user_name and len(user_name) > 30:
            logger.debug(f"Treating '{user_name}' as user ID (not found in cache)")
            return user_name
        
        logger.warning(f"User name '{user_name}' not found in cache and doesn't look like an ID")
        return None
    
    def _resolve_user_id_to_name(self, user_id: str) -> Optional[str]:
        """Resolve user ID to name.
        
        Args:
            user_id: Linear user ID
            
        Returns:
            User name, or None if not found
        """
        user_name = self.user_id_to_name.get(user_id)
        if user_name:
            logger.debug(f"Resolved user ID '{user_id}' to name '{user_name}'")
            return user_name
        
        logger.debug(f"User ID '{user_id}' not found in cache")
        return None

    async def _call_mcp_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Call MCP tool via FastMCP client."""
        logger.debug(f"Calling MCP tool {tool_name} with args: {args}")
        logger.debug(f"MCP server URL: {self.mcp_server_url}")
        
        try:
            # Ensure client is connected
            await self._ensure_connected()
            
            logger.debug(f"Sending MCP tool call: {tool_name}")
            
            # Call MCP tool using FastMCP client
            result = await self._client.call_tool(
                tool_name,
                args,
                raise_on_error=True
            )
            
            logger.debug(f"MCP tool result: {result.content}")
            logger.debug(f"MCP tool data: {result.data}")
            logger.debug(f"MCP tool structured_content: {result.structured_content}")
            logger.debug(f"Result content type: {type(result.content)}")
            logger.debug(f"Result data type: {type(result.data)}")
            logger.debug(f"Result structured_content type: {type(result.structured_content)}")
            
            # Check for errors
            if result.is_error:
                logger.error(f"MCP tool error: {result.content}")
                raise RuntimeError(f"MCP tool error: {result.content}")
            
            # Parse the JSON string response
            response_text = result.content[0].text if not result.is_error else "{}"
            logger.debug(f"Raw response text: {response_text}")
            
            try:
                parsed_response = json.loads(response_text)
                logger.debug(f"Parsed response: {parsed_response}")
                return parsed_response
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Raw response: {response_text}")
                import traceback
                traceback.print_exc()
                raise RuntimeError(f"Invalid JSON response from MCP tool: {e}")
            
        except Exception as e:
            logger.error(f"Failed to call MCP tool {tool_name}: {e}")
            logger.debug(f"Exception type: {type(e).__name__}, Args: {args}")
            import traceback
            traceback.print_exc()
            raise RuntimeError(f"MCP communication failed: {e}")

    def _map_priority_to_linear(self, priority: str) -> int:
        """Map our priority enum to Linear priority numbers."""
        logger.debug(f"Mapping priority '{priority}' to Linear priority number")
        mapping = {
            "urgent": 1,
            "high": 2,
            "medium": 3,
            "low": 4,
        }
        mapped_priority = mapping.get(priority.lower(), 3)
        logger.debug(f"Priority '{priority}' mapped to Linear priority {mapped_priority}")
        return mapped_priority

    def _map_linear_priority_to_enum(self, priority: int) -> TicketPriority:
        """Map Linear priority numbers to our priority enum."""
        logger.debug(f"Mapping Linear priority {priority} to enum")
        mapping = {
            1: TicketPriority.URGENT,
            2: TicketPriority.HIGH,
            3: TicketPriority.MEDIUM,
            4: TicketPriority.LOW,

        }
        if priority:
            mapped_priority = mapping.get(priority.get("value"))
        else:
            mapped_priority = TicketPriority.LOW
        logger.debug(f"Linear priority {priority} mapped to {mapped_priority}")
        return mapped_priority

    def _map_linear_state_to_status(self, status: str) -> TicketStatus:
        """Map Linear state to our ticket status."""
        logger.debug(f"Mapping Linear state '{status}' to ticket status")
        mapping = {
            "Todo": TicketStatus.OPEN,
            "In Progress": TicketStatus.IN_PROGRESS,
            "In Review": TicketStatus.IN_REVIEW,
            "Done": TicketStatus.COMPLETED,
            "Canceled": TicketStatus.CANCELLED,
            "Backlog": TicketStatus.BACKLOG,
        }
        mapped_status = mapping.get(status)
        logger.debug(f"Linear state '{status}' mapped to {mapped_status}")
        return mapped_status

    def _map_status_to_linear_state(self, status: TicketStatus) -> str:
        """Map our ticket status to Linear state."""
        logger.debug(f"Mapping ticket status {status} to Linear state")
        mapping = {
            TicketStatus.OPEN: "Todo",
            TicketStatus.IN_PROGRESS: "In Progress",
            TicketStatus.BLOCKED: "In Progress",  # Linear doesn't have blocked state
            TicketStatus.IN_REVIEW: "In Review",
            TicketStatus.BACKLOG: "Backlog",
            TicketStatus.COMPLETED: "Done",
            TicketStatus.CANCELLED: "Canceled",
        }
        mapped_state = mapping.get(status, "Todo")
        logger.debug(f"Ticket status {status} mapped to Linear state '{mapped_state}'")
        return mapped_state

    def _linear_issue_to_ticket(self, issue: Dict[str, Any], comments: List[Dict[str, Any]]) -> Ticket:
        """Convert Linear issue to Ticket object.
        
        Uses identifier (e.g., 'DAV-1') for Ticket.id and extracts names directly from assignee and createdBy objects.
        """
        logger.debug(f"Converting Linear issue to Ticket: {json.dumps(issue, indent=2)} with comments: {comments}")
        
        # Handle different response formats from Linear API
        status = issue.get("status")
        priority = issue.get("priority")
        logger.debug(f"Processing issue with state: {status}, priority: {priority}")
        
        # Extract status name (could be string or dict)
        status_name = status
        if isinstance(status, dict):
            status_name = status.get("name", status.get("state", ""))
        status_name_str = status_name if isinstance(status_name, str) else str(status_name) if status_name else ""
        
        # Get Linear ID and resolve to identifier
        linear_id = issue.get("id")
        identifier = issue.get("identifier")
        
        # If identifier not in response, try to resolve from cache
        if not identifier and linear_id:
            identifier = self.ticket_id_to_identifier.get(linear_id, linear_id)
        
        assignee_name = issue.get("assignee")
        created_by_name = issue.get("createdBy")

        ticket = Ticket(
            id=identifier or linear_id,  # Use identifier, fallback to ID
            title=issue["title"],
            description=issue.get("description", ""),
            status=self._map_linear_state_to_status(status_name_str),
            priority=self._map_linear_priority_to_enum(priority),
            created_by=created_by_name,
            assigned_to=assignee_name,
            created_at=datetime.fromisoformat(issue["createdAt"].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(issue["updatedAt"].replace("Z", "+00:00")),
            completed_at=datetime.fromisoformat(issue["updatedAt"].replace("Z", "+00:00")) 
                     if status_name_str == "Done" else None,
            tags=issue.get("labels", []),  # Would need to map from Linear labels
            metadata={"linear_team": issue.get("team")},
            comments=comments,
        )
        
        logger.debug(f"Linear to Ticket object: id={ticket.id}, title='{ticket.title}', status={ticket.status}, priority={ticket.priority}")
        return ticket

    async def create_ticket(
        self,
        title: str,
        description: str,
        priority: TicketPriority,
        created_by: str,
        assigned_to: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Ticket:
        """Create a new ticket in Linear.
        
        Args:
            created_by: User name (not used by Linear API, kept for protocol consistency)
            assigned_to: User name (used directly in API call)
        """
        logger.debug(f"Creating ticket: title='{title}', priority={priority}, created_by='{created_by}'")
        logger.debug(f"Optional params: assigned_to={assigned_to}, tags={tags}, metadata={metadata}")

        await self._initialize_caches()
        
        args = {
            "title": title,
            "description": description,
            "priority": self._map_priority_to_linear(priority.value),
        }
        
        if self.team_id:
            args["team"] = self.team_id
        if self.project_id:
            args["projectId"] = self.project_id
        # Use assignee name directly
        if assigned_to:
            args["assignee"] = assigned_to
        # Note: created_by is not used in Linear API (Linear tracks creator automatically)
        # But we keep it for the protocol consistency
        if tags:
            args["labelIds"] = tags
        if metadata:
            args["metadata"] = metadata
        # always create tickets as Todo
        args["state"] = "Todo"

        logger.debug(f"Calling create_issue with args: {json.dumps(args, indent=2)}")
        response = await self._call_mcp_tool("create_issue", args)
        
        logger.debug(f"Received response from create_issue: {json.dumps(response, indent=2)}")
        ticket = self._linear_issue_to_ticket(response, [])
        
        logger.info(f"✅ Created ticket: {ticket.id} - '{ticket.title}'")
        return ticket

    async def get_ticket(self, ticket_id: str) -> Optional[Ticket]:
        """Get ticket by ID or identifier from Linear.
        
        Args:
            ticket_id: Either a Linear ID or identifier like 'DAV-1' (will be resolved to ID)
        """
        await self._initialize_caches()
        logger.debug(f"Getting ticket by ID/identifier: {ticket_id}")
        # Resolve identifier to Linear ID if needed
        linear_id = self._resolve_ticket_identifier_to_id(ticket_id)
        
        ticket_response = await self._call_mcp_tool("get_issue", {"id": linear_id})
        comments_response = await self._call_mcp_tool("list_comments", {"issueId": linear_id})
        
        if not ticket_response:
            logger.warning(f"No ticket or comments found with ID: {ticket_id}")
            return None
        if not comments_response:
            logger.warning(f"No comments found with ID: {ticket_id}")
            comments = []
        else:
            comments = [comment.get("body") for comment in comments_response]

        return self._linear_issue_to_ticket(ticket_response, comments)

    async def update_ticket(
        self,
        ticket_id: str,
        status: Optional[TicketStatus] = None,
        priority: Optional[TicketPriority] = None,
        assigned_to: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Ticket:
        """Update ticket fields in Linear.
        
        Args:
            ticket_id: Either a Linear ID or identifier like 'DAV-1' (will be resolved to ID)
            assigned_to: User name (used directly in API call)
        """
        logger.debug(f"Updating ticket {ticket_id} with: status={status}, priority={priority}, assigned_to={assigned_to}")
        logger.debug(f"Additional params: tags={tags}, metadata={metadata}")
        
        await self._initialize_caches()

        # Resolve identifier to Linear ID if needed
        linear_id = self._resolve_ticket_identifier_to_id(ticket_id)
        args = {"id": linear_id}
        
        if status is not None:
            args["state"] = self._map_status_to_linear_state(status)
        if priority is not None:
            args["priority"] = self._map_priority_to_linear(priority.value)
        if assigned_to is not None:
            args["assignee"] = assigned_to
        if tags is not None:
            args["labelIds"] = tags
        if metadata is not None:
            args["metadata"] = metadata

        logger.debug(f"Calling update_issue with args: {json.dumps(args, indent=2)}")
        response = await self._call_mcp_tool("update_issue", args)
        
        logger.debug(f"Received response from update_issue: {json.dumps(response, indent=2)}")
        ticket = self._linear_issue_to_ticket(response, [])
        
        logger.info(f"✅ Updated ticket: {ticket.id} - '{ticket.title}'")
        return ticket

    async def add_comment(
        self,
        ticket_id: str,
        author: str,
        comment: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Ticket:
        """Add comment to ticket in Linear.
        
        Args:
            ticket_id: Either a Linear ID or identifier like 'DAV-1' (will be resolved to ID)
        """
        logger.debug(f"Adding comment to ticket {ticket_id} by {author}: '{comment}'")
        await self._initialize_caches()
        # Resolve identifier to Linear ID if needed
        linear_id = self._resolve_ticket_identifier_to_id(ticket_id)
        args = {
            "issueId": linear_id,
            "body": f"[{author}] {comment}",
        }
        
        if metadata:
            args["metadata"] = metadata
            logger.debug(f"Added metadata to comment args: {metadata}")

        logger.debug(f"Calling add_comment with args: {json.dumps(args, indent=2)}")
        await self._call_mcp_tool("create_comment", args)
        
        logger.debug(f"Comment added successfully, retrieving updated ticket")
        # Return updated ticket
        updated_ticket = await self.get_ticket(ticket_id)
        
        logger.info(f"✅ Added comment to ticket: {ticket_id}")
        return updated_ticket

    async def list_tickets(
        self,
        status: Optional[TicketStatus] = None,
        priority: Optional[TicketPriority] = None,
        assigned_to: Optional[str] = None,
        created_by: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ) -> List[Ticket]:
        """List tickets from Linear with optional filtering."""
        logger.debug(f"Listing tickets with filters: status={status}, priority={priority}, assigned_to={assigned_to}")
        logger.debug(f"Additional filters: created_by={created_by}, tags={tags}, limit={limit}")
        
        await self._initialize_caches()

        args = {}

        if status is not None:
            args["state"] = self._map_status_to_linear_state(status)
        
        if priority is not None:
            args["priority"] = self._map_priority_to_linear(priority.value)
        
        # Resolve assigned_to name to ID for filtering
        if assigned_to is not None and assigned_to.strip():
            assigned_to_id = self._resolve_user_name_to_id(assigned_to)
            if assigned_to_id:
                args["assignee"] = assigned_to_id
                logger.debug(f"Resolved assigned_to filter '{assigned_to}' to ID '{assigned_to_id}'")
            else:
                logger.warning(f"Could not resolve assigned_to filter '{assigned_to}' to ID, skipping")
        
        # Note: created_by filtering may not be supported by Linear API, but we attempt resolution
        if created_by is not None and created_by.strip():
            created_by_id = self._resolve_user_name_to_id(created_by)
            if created_by_id:
                # Linear may use different field names for creator filter
                args["creatorId"] = created_by_id
                logger.debug(f"Resolved created_by filter '{created_by}' to ID '{created_by_id}'")
            else:
                logger.warning(f"Could not resolve created_by filter '{created_by}' to ID, skipping")
        
        if tags is not None and tags:
            args["labelIds"] = tags
            logger.debug(f"Added labels filter: {tags}")
        
        if limit is not None:
            args["limit"] = limit
            logger.debug(f"Added limit filter: {limit}")
        
        if self.team_id:
            args["team"] = self.team_id
            logger.debug(f"Added team_id filter: {self.team_id}")

        args["includeArchived"] = False

        logger.debug(f"Calling list_issues with args: {json.dumps(args, indent=2)}")
        response = await self._call_mcp_tool("list_issues", args)
        
        logger.debug(f"Received response from list_issues: {json.dumps(response, indent=2)}")
        
        tickets = []
        # Response is a JSON array of issues directly, or a dict with nodes/issues key
        issues = response if isinstance(response, list) else response.get("nodes") or response.get("issues") or []
        logger.debug(f"Processing {len(issues)} issues from response")
        
        for i, issue in enumerate(issues):
            logger.debug(f"Processing issue {i+1}/{len(issues)}: {issue.get('id', 'unknown')} - '{issue.get('title', 'no title')}'")
            ticket = self._linear_issue_to_ticket(issue, [])
            tickets.append(ticket)
        
        logger.info(f"✅ Listed {len(tickets)} tickets")
        return tickets

    def get_agent_hints(self):
        """Get agent hints."""
        return dedent("""
#### AvailableTicket States
    - "open"
    - "in_progress"
    - "blocked"
    - "in_review"
    - "backlog"
    - "completed"
    - "cancelled"

#### Available Ticket Priorities
    - "low"
    - "medium"
    - "high"
    - "urgent"

#### Creating Tickets
 - tickets are always created in 'Todo' state
 - create tickets as 'medium' priority unless otherwise specified

#### Listing Tickets
 - can filter by 'status' (Ticket State), 'priority' (Ticket Priority), 'assigned_to'
 - do not include 'assigned_to' arg unless specifically asked for tickets assigned to or owned by a user
 - if asked for any 'open' tickets, check 'open' AND 'backlog' status tickets

#### Updating Ticket State
 - use if you need to assign the ticket to a different user or change ticket state 
 - e.g. from 'Todo' to In Progress)

#### Adding Comments to Tickets
 - do whenever you are providing status updates or asking for clarification
        """).strip()

    def close(self) -> None:
        """Close the Linear ticket storage."""
        logger.info("Closing Linear ticket storage")
        # FastMCP client will be closed via async context manager