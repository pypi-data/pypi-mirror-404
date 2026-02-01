"""Hanary MCP Server implementation."""

import argparse
import os
import sys

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .client import HanaryClient


def create_server(squad: str | None, client: HanaryClient) -> Server:
    """Create and configure the MCP server."""
    server = Server("hanary")

    # Determine mode description
    if squad:
        task_scope = f"squad '{squad}'"
    else:
        task_scope = "personal tasks (including assigned squad tasks)"

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        tools = [
            Tool(
                name="get_task",
                description="Get a single task with full details including children, ancestors, and time summary.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "Task ID (required)",
                        },
                        "include_children": {
                            "type": "boolean",
                            "description": "Include child tasks (default: false)",
                        },
                        "include_ancestors": {
                            "type": "boolean",
                            "description": "Include ancestor chain to root (default: false)",
                        },
                        "include_time_summary": {
                            "type": "boolean",
                            "description": "Include time tracking summary (default: false)",
                        },
                    },
                    "required": ["task_id"],
                },
            ),
            Tool(
                name="search_tasks",
                description=f"Search tasks in {task_scope} with filters (status, assignee, due date, text query).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Full-text search in title and description (optional)",
                        },
                        "status": {
                            "type": "string",
                            "description": "Filter by status: pending, in_progress, completed, all (default: pending)",
                            "enum": ["pending", "in_progress", "completed", "all"],
                        },
                        "assignee_id": {
                            "type": "string",
                            "description": "Filter by assignee ID. Use 'me' for current user (optional)",
                        },
                        "has_estimate": {
                            "type": "boolean",
                            "description": "Filter by whether task has time estimate (optional)",
                        },
                        "due_before": {
                            "type": "string",
                            "description": "Filter tasks due before this date (ISO 8601, optional)",
                        },
                        "due_after": {
                            "type": "string",
                            "description": "Filter tasks due after this date (ISO 8601, optional)",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum results (default: 50)",
                        },
                    },
                },
            ),
            Tool(
                name="list_tasks",
                description=f"List tasks for {task_scope}. WARNING: Can return large responses. For status checks or overviews, use get_tasks_summary instead. Only use this when you need full task details or filtering.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "include_completed": {
                            "type": "boolean",
                            "description": "Include completed tasks (default: false)",
                        },
                        "executor_type": {
                            "type": "string",
                            "description": "Filter by executor type: 'ai' for AI tasks, 'human' for my tasks, or omit for all tasks",
                            "enum": ["ai", "human", "collab"],
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of tasks to return. Returns top priority tasks first. (default: all tasks)",
                        },
                    },
                },
            ),
            Tool(
                name="get_tasks_summary",
                description=f"Get a compact summary of tasks for {task_scope}. Returns counts and top priority tasks without full task details. PREFERRED for status checks and overviews - uses ~10x fewer tokens than list_tasks.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "top_n": {
                            "type": "integer",
                            "description": "Number of top priority tasks to include (default: 5)",
                        },
                    },
                },
            ),
            Tool(
                name="get_tasks_summary",
                description=f"Get compact summary of tasks in {task_scope}. Uses ~10x fewer tokens than list_tasks.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "top_n": {
                            "type": "integer",
                            "description": "Number of top priority tasks to include (default: 5)",
                        }
                    },
                },
            ),
            Tool(
                name="create_task",
                description=f"Create a new task in {task_scope}.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Task title (required)",
                        },
                        "description": {
                            "type": "string",
                            "description": "Task description (optional)",
                        },
                        "parent_id": {
                            "type": "string",
                            "description": "Parent task ID for subtask (optional)",
                        },
                        "purpose": {
                            "type": "string",
                            "description": "Why this task needs to be done - motivation and goals (optional)",
                        },
                        "background": {
                            "type": "string",
                            "description": "Context and circumstances that led to this task (optional)",
                        },
                    },
                    "required": ["title"],
                },
            ),
            Tool(
                name="update_task",
                description="Update an existing task's title, description, or notes (purpose/background/retrospective).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "Task ID (required)",
                        },
                        "title": {
                            "type": "string",
                            "description": "New title (optional)",
                        },
                        "description": {
                            "type": "string",
                            "description": "New description (optional)",
                        },
                        "purpose": {
                            "type": "string",
                            "description": "Why this task needs to be done - motivation and goals (optional)",
                        },
                        "background": {
                            "type": "string",
                            "description": "Context and circumstances that led to this task (optional)",
                        },
                        "retrospective": {
                            "type": "string",
                            "description": "Lessons learned, improvements, and reflections (optional)",
                        },
                    },
                    "required": ["task_id"],
                },
            ),
            Tool(
                name="complete_task",
                description="Mark a task as completed. Optionally add a retrospective note.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "Task ID to complete (required)",
                        },
                        "retrospective": {
                            "type": "string",
                            "description": "Lessons learned, improvements, and reflections from completing this task (optional)",
                        },
                    },
                    "required": ["task_id"],
                },
            ),
            Tool(
                name="uncomplete_task",
                description="Mark a completed task as incomplete.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "Task ID to uncomplete (required)",
                        }
                    },
                    "required": ["task_id"],
                },
            ),
            Tool(
                name="delete_task",
                description="Soft delete a task.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "Task ID to delete (required)",
                        }
                    },
                    "required": ["task_id"],
                },
            ),
            Tool(
                name="get_top_task",
                description="Get the highest priority incomplete task. Returns the deepest uncompleted task along with its ancestor chain. If the top task has is_llm_boundary=true, it means all LLM-assignable tasks are completed and you should stop working.",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="start_task",
                description="Start time tracking for a task. Creates a new time session.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "Task ID to start time tracking (required)",
                        }
                    },
                    "required": ["task_id"],
                },
            ),
            Tool(
                name="stop_task",
                description="Stop time tracking for a task. Ends the current time session.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "Task ID to stop time tracking (required)",
                        }
                    },
                    "required": ["task_id"],
                },
            ),
            Tool(
                name="reorder_task",
                description="Change the order of a task among its siblings. Moves the task to the specified rank position.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "Task ID to reorder (required)",
                        },
                        "new_rank": {
                            "type": "integer",
                            "description": "New rank position (0-based index among siblings, required)",
                        },
                    },
                    "required": ["task_id", "new_rank"],
                },
            ),
            # Calibration tools (Self-Calibration feature)
            Tool(
                name="get_weekly_stats",
                description="Get weekly task completion statistics for the past 4 weeks. Returns weekly averages of time spent on tasks.",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="get_estimation_accuracy",
                description="Get estimation accuracy statistics. Returns the ratio of actual time spent vs estimated time. Ratio > 1.0 means underestimating, < 1.0 means overestimating.",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="suggest_duration",
                description="Get suggested duration for a task based on similar completed tasks. Useful for setting realistic time estimates.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "Task ID to get suggestion for (required)",
                        }
                    },
                    "required": ["task_id"],
                },
            ),
            Tool(
                name="detect_overload",
                description="Detect overload signals. Checks for: tasks taking 2x longer than estimated, stale tasks (7+ days incomplete), low completion rate.",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="detect_underload",
                description="Detect underload signals. Checks if tasks are being completed in less than 50% of estimated time.",
                inputSchema={"type": "object", "properties": {}},
            ),
            # Session review tools (8시간 초과 자동 중지 세션 관리)
            Tool(
                name="list_sessions_needing_review",
                description="List time sessions that need review. These are sessions that were auto-stopped after 8+ hours and may need time correction.",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="approve_session",
                description="Approve an auto-stopped session. Keeps the recorded time as-is and removes the needs_review flag.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "session_id": {
                            "type": "string",
                            "description": "Session ID to approve (required)",
                        }
                    },
                    "required": ["session_id"],
                },
            ),
            Tool(
                name="review_session",
                description="Review and correct an auto-stopped session's end time.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "session_id": {
                            "type": "string",
                            "description": "Session ID to review (required)",
                        },
                        "ended_at": {
                            "type": "string",
                            "description": "Corrected end time in ISO 8601 format (required)",
                        },
                    },
                    "required": ["session_id", "ended_at"],
                },
            ),
            Tool(
                name="delete_session",
                description="Delete a time session. Also recalculates the task's total time spent.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "session_id": {
                            "type": "string",
                            "description": "Session ID to delete (required)",
                        }
                    },
                    "required": ["session_id"],
                },
            ),
            Tool(
                name="get_current_user",
                description="Get current user info and squad permissions. Use this to understand who you are acting as.",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="list_questions",
                description="List inquiry questions for Socratic analysis of claims.",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="get_question",
                description="Get a single inquiry question with its root claims.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "question_id": {
                            "type": "string",
                            "description": "Question ID (required)",
                        }
                    },
                    "required": ["question_id"],
                },
            ),
            Tool(
                name="create_question",
                description="Create a new inquiry question for Socratic analysis. Questions are starting points for exploring claims and hidden premises.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "The question to explore (e.g., '좋은 콘텐츠란 무엇인가?')",
                        },
                    },
                    "required": ["content"],
                },
            ),
            Tool(
                name="delete_question",
                description="Delete an inquiry question and all its associated claims.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "question_id": {
                            "type": "string",
                            "description": "Question ID to delete (required)",
                        },
                    },
                    "required": ["question_id"],
                },
            ),
            Tool(
                name="get_claim_tree",
                description="Get a claim and all its descendants (premises) in hierarchical tree structure.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "claim_id": {
                            "type": "string",
                            "description": "Claim ID (required)",
                        }
                    },
                    "required": ["claim_id"],
                },
            ),
            Tool(
                name="add_claim",
                description="Add a root claim to a question for analysis.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "question_id": {
                            "type": "string",
                            "description": "Question ID (required)",
                        },
                        "content": {
                            "type": "string",
                            "description": "Claim content (required)",
                        },
                    },
                    "required": ["question_id", "content"],
                },
            ),
            Tool(
                name="add_premise",
                description="Add a hidden premise to an existing claim. AI can use this to decompose claims.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "parent_claim_id": {
                            "type": "string",
                            "description": "Parent claim ID (required)",
                        },
                        "content": {
                            "type": "string",
                            "description": "Premise content (required)",
                        },
                        "ai_reasoning": {
                            "type": "string",
                            "description": "AI reasoning for this premise (optional)",
                        },
                    },
                    "required": ["parent_claim_id", "content"],
                },
            ),
        ]

        # Add squad-only tools when squad is specified
        if squad:
            tools.extend(
                [
                    Tool(
                        name="get_squad",
                        description="Get details of the current squad.",
                        inputSchema={"type": "object", "properties": {}},
                    ),
                    Tool(
                        name="list_squad_members",
                        description="List members of the current squad.",
                        inputSchema={"type": "object", "properties": {}},
                    ),
                    Tool(
                        name="list_messages",
                        description="List messages in the current squad.",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "limit": {
                                    "type": "integer",
                                    "description": "Number of messages to retrieve (default: 50)",
                                }
                            },
                        },
                    ),
                    Tool(
                        name="create_message",
                        description="Send a message to the current squad.",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "content": {
                                    "type": "string",
                                    "description": "Message content (required)",
                                }
                            },
                            "required": ["content"],
                        },
                    ),
                    Tool(
                        name="list_squad_events",
                        description="List events/schedules for the current squad.",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "type": {
                                    "type": "string",
                                    "description": "Filter by event type (optional)",
                                    "enum": [
                                        "meeting",
                                        "interview",
                                        "onboarding",
                                        "notice",
                                        "deadline",
                                        "other",
                                    ],
                                },
                                "upcoming_only": {
                                    "type": "boolean",
                                    "description": "Only return upcoming events (default: false)",
                                },
                                "days": {
                                    "type": "integer",
                                    "description": "Days ahead for upcoming events (default: 7)",
                                },
                            },
                        },
                    ),
                    Tool(
                        name="get_online_members",
                        description="Get currently online members in the squad.",
                        inputSchema={"type": "object", "properties": {}},
                    ),
                ]
            )

        return tools

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        try:
            result = await handle_tool_call(name, arguments, squad, client)
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    return server


async def handle_tool_call(
    name: str, arguments: dict, squad: str | None, client: HanaryClient
) -> str:
    """Handle individual tool calls."""
    # Task tools
    if name == "get_task":
        return await client.get_task(
            task_id=arguments["task_id"],
            include_children=arguments.get("include_children", False),
            include_ancestors=arguments.get("include_ancestors", False),
            include_time_summary=arguments.get("include_time_summary", False),
        )

    elif name == "search_tasks":
        return await client.search_tasks(
            squad_slug=squad,
            query=arguments.get("query"),
            status=arguments.get("status", "pending"),
            assignee_id=arguments.get("assignee_id"),
            has_estimate=arguments.get("has_estimate"),
            due_before=arguments.get("due_before"),
            due_after=arguments.get("due_after"),
            limit=arguments.get("limit", 50),
        )

    elif name == "list_tasks":
        return await client.list_tasks(
            squad_slug=squad,
            include_completed=arguments.get("include_completed", False),
            executor_type=arguments.get("executor_type"),
            limit=arguments.get("limit"),
        )

    elif name == "get_tasks_summary":
        return await client.get_tasks_summary(
            squad_slug=squad,
            top_n=arguments.get("top_n", 5),
        )

    elif name == "get_tasks_summary":
        return await client.get_tasks_summary(
            squad_slug=squad,
            top_n=arguments.get("top_n", 5),
        )

    elif name == "create_task":
        return await client.create_task(
            title=arguments["title"],
            squad_slug=squad,
            description=arguments.get("description"),
            parent_id=arguments.get("parent_id"),
            purpose=arguments.get("purpose"),
            background=arguments.get("background"),
        )

    elif name == "update_task":
        return await client.update_task(
            task_id=arguments["task_id"],
            title=arguments.get("title"),
            description=arguments.get("description"),
            purpose=arguments.get("purpose"),
            background=arguments.get("background"),
            retrospective=arguments.get("retrospective"),
        )

    elif name == "complete_task":
        return await client.complete_task(
            task_id=arguments["task_id"],
            retrospective=arguments.get("retrospective"),
        )

    elif name == "uncomplete_task":
        return await client.uncomplete_task(task_id=arguments["task_id"])

    elif name == "delete_task":
        return await client.delete_task(task_id=arguments["task_id"])

    elif name == "get_top_task":
        return await client.get_top_task(squad_slug=squad)

    elif name == "start_task":
        return await client.start_task(task_id=arguments["task_id"])

    elif name == "stop_task":
        return await client.stop_task(task_id=arguments["task_id"])

    elif name == "reorder_task":
        return await client.reorder_task(
            task_id=arguments["task_id"],
            new_rank=arguments["new_rank"],
        )

    # Calibration tools
    elif name == "get_weekly_stats":
        return await client.get_weekly_stats()

    elif name == "get_estimation_accuracy":
        return await client.get_estimation_accuracy()

    elif name == "suggest_duration":
        return await client.suggest_duration(task_id=arguments["task_id"])

    elif name == "detect_overload":
        return await client.detect_overload()

    elif name == "detect_underload":
        return await client.detect_underload()

    # Session review tools
    elif name == "list_sessions_needing_review":
        return await client.list_sessions_needing_review(squad_slug=squad)

    elif name == "approve_session":
        return await client.approve_session(session_id=arguments["session_id"])

    elif name == "review_session":
        return await client.review_session(
            session_id=arguments["session_id"],
            ended_at=arguments["ended_at"],
        )

    elif name == "delete_session":
        return await client.delete_session(session_id=arguments["session_id"])

    # Squad tools
    elif name == "get_squad":
        return await client.get_squad(squad_slug=squad)

    elif name == "list_squad_members":
        return await client.list_squad_members(squad_slug=squad)

    # Message tools
    elif name == "list_messages":
        return await client.list_messages(
            squad_slug=squad,
            limit=arguments.get("limit", 50),
        )

    elif name == "create_message":
        return await client.create_message(
            squad_slug=squad,
            content=arguments["content"],
        )

    elif name == "list_squad_events":
        return await client.list_squad_events(
            squad_slug=squad,
            event_type=arguments.get("type"),
            upcoming_only=arguments.get("upcoming_only", False),
            days=arguments.get("days", 7),
        )

    elif name == "get_online_members":
        return await client.get_online_members(squad_slug=squad)

    # User tools
    elif name == "get_current_user":
        return await client.get_current_user(squad_slug=squad)

    # Inquiry tools
    elif name == "list_questions":
        return await client.list_questions()

    elif name == "get_question":
        return await client.get_question(question_id=arguments["question_id"])

    elif name == "create_question":
        return await client.create_question(content=arguments["content"])

    elif name == "delete_question":
        return await client.delete_question(question_id=arguments["question_id"])

    elif name == "get_claim_tree":
        return await client.get_claim_tree(claim_id=arguments["claim_id"])

    elif name == "add_claim":
        return await client.add_claim(
            question_id=arguments["question_id"],
            content=arguments["content"],
        )

    elif name == "add_premise":
        return await client.add_premise(
            parent_claim_id=arguments["parent_claim_id"],
            content=arguments["content"],
            ai_reasoning=arguments.get("ai_reasoning"),
        )

    else:
        raise ValueError(f"Unknown tool: {name}")


async def run_server(squad: str | None, api_token: str, api_url: str):
    """Run the MCP server."""
    client = HanaryClient(api_token=api_token, api_url=api_url)
    server = create_server(squad, client)

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream, server.create_initialization_options()
        )


def main():
    from . import __version__

    parser = argparse.ArgumentParser(
        description="Hanary MCP Server - Task management for Claude Code & OpenCode"
    )
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=f"hanary-mcp {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command")

    init_parser = subparsers.add_parser(
        "init", help="Initialize Hanary integration in current directory"
    )
    init_parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Overwrite existing files",
    )
    init_parser.add_argument(
        "--squad",
        "-s",
        default=None,
        help="Squad slug to bind to. If not specified, uses personal tasks mode.",
    )
    init_parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Target directory (default: current directory)",
    )

    parser.add_argument(
        "--squad",
        "-s",
        default=None,
        help="Squad slug to bind to. If not specified, manages personal tasks.",
    )
    parser.add_argument(
        "--token",
        "-t",
        default=os.environ.get("HANARY_API_TOKEN"),
        help="Hanary API token (or set HANARY_API_TOKEN env var)",
    )
    parser.add_argument(
        "--api-url",
        default=os.environ.get("HANARY_API_URL", "https://hanary.org"),
        help="Hanary API URL (default: https://hanary.org)",
    )

    args = parser.parse_args()

    if args.command == "init":
        from .init import init_project

        init_project(args.target, args.force, args.squad)
        return

    api_token = args.token
    if not api_token:
        print(
            "Error: --token argument or HANARY_API_TOKEN environment variable is required",
            file=sys.stderr,
        )
        sys.exit(1)

    import asyncio

    asyncio.run(run_server(args.squad, api_token, args.api_url))


if __name__ == "__main__":
    main()
