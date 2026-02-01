"""Hanary API Client for MCP Server."""

import json
from typing import Optional

import requests


class HanaryClient:
    """Client for Hanary HTTP MCP API."""

    def __init__(self, api_token: str, api_url: str = "https://hanary.org"):
        self.api_url = api_url.rstrip("/")
        self.api_token = api_token
        self._session: Optional[requests.Session] = None
        self._squad_id_cache: dict[str, int] = {}

    def _get_session(self) -> requests.Session:
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update(
                {
                    "Authorization": f"Bearer {self.api_token}",
                    "Content-Type": "application/json",
                    "User-Agent": "curl/8.7.1",
                }
            )
        return self._session

    async def _call_mcp(self, method: str, params: dict = None) -> dict:
        """Call the Hanary MCP endpoint."""
        session = self._get_session()

        request_body = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or {},
        }

        response = session.post(f"{self.api_url}/mcp", json=request_body)
        response.raise_for_status()

        result = response.json()

        if "error" in result:
            raise Exception(result["error"].get("message", "Unknown error"))

        return result.get("result", {})

    async def _get_squad_id(self, squad_slug: str) -> int:
        """Get squad ID from slug (cached)."""
        if squad_slug in self._squad_id_cache:
            return self._squad_id_cache[squad_slug]

        result = await self._call_mcp(
            "tools/call", {"name": "get_squad", "arguments": {"slug": squad_slug}}
        )

        content = result.get("content", [])
        if content:
            data = json.loads(content[0].get("text", "{}"))
            squad = data.get("squad", {})
            squad_id = squad.get("id")
            if squad_id:
                self._squad_id_cache[squad_slug] = squad_id
                return squad_id

        raise Exception(f"Squad not found: {squad_slug}")

    async def _call_tool(self, name: str, arguments: dict) -> str:
        """Call a tool and return the result as string."""
        result = await self._call_mcp(
            "tools/call",
            {
                "name": name,
                "arguments": arguments,
            },
        )

        content = result.get("content", [])
        if content:
            return content[0].get("text", "{}")
        return "{}"

    # Task methods
    async def list_tasks(
        self,
        squad_slug: Optional[str] = None,
        include_completed: bool = False,
        executor_type: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> str:
        args: dict = {"include_completed": include_completed}
        if squad_slug:
            squad_id = await self._get_squad_id(squad_slug)
            args["squad_id"] = str(squad_id)
        if executor_type:
            args["executor_type"] = executor_type
        if limit is not None:
            args["limit"] = limit
        return await self._call_tool("list_tasks", args)

    async def get_tasks_summary(
        self,
        squad_slug: Optional[str] = None,
        top_n: int = 5,
    ) -> str:
        args = {"top_n": top_n}
        if squad_slug:
            squad_id = await self._get_squad_id(squad_slug)
            args["squad_id"] = str(squad_id)
        return await self._call_tool("get_tasks_summary", args)

    async def create_task(
        self,
        title: str,
        squad_slug: Optional[str] = None,
        description: Optional[str] = None,
        parent_id: Optional[str] = None,
        purpose: Optional[str] = None,
        background: Optional[str] = None,
    ) -> str:
        args = {"title": title}
        if squad_slug:
            squad_id = await self._get_squad_id(squad_slug)
            args["squad_id"] = str(squad_id)
        if description:
            args["description"] = description
        if parent_id:
            args["parent_id"] = parent_id
        if purpose:
            args["purpose"] = purpose
        if background:
            args["background"] = background

        return await self._call_tool("create_task", args)

    async def update_task(
        self,
        task_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        purpose: Optional[str] = None,
        background: Optional[str] = None,
        retrospective: Optional[str] = None,
    ) -> str:
        args = {"task_id": task_id}
        if title:
            args["title"] = title
        if description:
            args["description"] = description
        if purpose:
            args["purpose"] = purpose
        if background:
            args["background"] = background
        if retrospective:
            args["retrospective"] = retrospective

        return await self._call_tool("update_task", args)

    async def complete_task(
        self,
        task_id: str,
        retrospective: Optional[str] = None,
    ) -> str:
        args = {"task_id": task_id}
        if retrospective:
            args["retrospective"] = retrospective
        return await self._call_tool("complete_task", args)

    async def uncomplete_task(self, task_id: str) -> str:
        return await self._call_tool("uncomplete_task", {"task_id": task_id})

    async def delete_task(self, task_id: str) -> str:
        return await self._call_tool("delete_task", {"task_id": task_id})

    async def get_top_task(self, squad_slug: Optional[str] = None) -> str:
        args = {}
        if squad_slug:
            squad_id = await self._get_squad_id(squad_slug)
            args["squad_id"] = str(squad_id)
        return await self._call_tool("get_top_task", args)

    async def start_task(self, task_id: str) -> str:
        return await self._call_tool("start_task", {"task_id": task_id})

    async def stop_task(self, task_id: str) -> str:
        return await self._call_tool("stop_task", {"task_id": task_id})

    async def reorder_task(self, task_id: str, new_rank: int) -> str:
        return await self._call_tool(
            "reorder_task",
            {
                "task_id": task_id,
                "new_rank": new_rank,
            },
        )

    # Calibration methods (Self-Calibration feature)
    async def get_weekly_stats(self) -> str:
        return await self._call_tool("get_weekly_stats", {})

    async def get_estimation_accuracy(self) -> str:
        return await self._call_tool("get_estimation_accuracy", {})

    async def suggest_duration(self, task_id: str) -> str:
        return await self._call_tool("suggest_duration", {"task_id": task_id})

    async def detect_overload(self) -> str:
        return await self._call_tool("detect_overload", {})

    async def detect_underload(self) -> str:
        return await self._call_tool("detect_underload", {})

    # Squad methods
    async def get_squad(self, squad_slug: str) -> str:
        return await self._call_tool("get_squad", {"slug": squad_slug})

    async def list_squad_members(self, squad_slug: str) -> str:
        squad_id = await self._get_squad_id(squad_slug)
        return await self._call_tool(
            "list_squad_members",
            {
                "squad_id": str(squad_id),
            },
        )

    # Message methods
    async def list_messages(self, squad_slug: str, limit: int = 50) -> str:
        squad_id = await self._get_squad_id(squad_slug)
        return await self._call_tool(
            "list_messages",
            {
                "squad_id": str(squad_id),
                "limit": limit,
            },
        )

    async def create_message(self, squad_slug: str, content: str) -> str:
        squad_id = await self._get_squad_id(squad_slug)
        return await self._call_tool(
            "create_message",
            {
                "squad_id": str(squad_id),
                "content": content,
            },
        )

    # Session review methods (8시간 초과 자동 중지 세션 관리)
    async def list_sessions_needing_review(
        self, squad_slug: Optional[str] = None
    ) -> str:
        args = {}
        if squad_slug:
            squad_id = await self._get_squad_id(squad_slug)
            args["squad_id"] = str(squad_id)
        return await self._call_tool("list_sessions_needing_review", args)

    async def approve_session(self, session_id: str) -> str:
        return await self._call_tool("approve_session", {"session_id": session_id})

    async def review_session(self, session_id: str, ended_at: str) -> str:
        return await self._call_tool(
            "review_session",
            {
                "session_id": session_id,
                "ended_at": ended_at,
            },
        )

    async def delete_session(self, session_id: str) -> str:
        return await self._call_tool("delete_session", {"session_id": session_id})

    # New Task methods
    async def get_task(
        self,
        task_id: str,
        include_children: bool = False,
        include_ancestors: bool = False,
        include_time_summary: bool = False,
    ) -> str:
        return await self._call_tool(
            "get_task",
            {
                "task_id": task_id,
                "include_children": include_children,
                "include_ancestors": include_ancestors,
                "include_time_summary": include_time_summary,
            },
        )

    async def search_tasks(
        self,
        squad_slug: Optional[str] = None,
        query: Optional[str] = None,
        status: str = "pending",
        assignee_id: Optional[str] = None,
        has_estimate: Optional[bool] = None,
        due_before: Optional[str] = None,
        due_after: Optional[str] = None,
        limit: int = 50,
    ) -> str:
        args: dict = {"status": status, "limit": limit}
        if squad_slug:
            squad_id = await self._get_squad_id(squad_slug)
            args["squad_id"] = str(squad_id)
        if query:
            args["query"] = query
        if assignee_id:
            args["assignee_id"] = assignee_id
        if has_estimate is not None:
            args["has_estimate"] = has_estimate
        if due_before:
            args["due_before"] = due_before
        if due_after:
            args["due_after"] = due_after
        return await self._call_tool("search_tasks", args)

    async def get_tasks_summary(
        self, squad_slug: Optional[str] = None, top_n: int = 5
    ) -> str:
        args: dict = {"top_n": top_n}
        if squad_slug:
            squad_id = await self._get_squad_id(squad_slug)
            args["squad_id"] = str(squad_id)
        return await self._call_tool("get_tasks_summary", args)

    # User methods
    async def get_current_user(self, squad_slug: Optional[str] = None) -> str:
        args: dict = {}
        if squad_slug:
            squad_id = await self._get_squad_id(squad_slug)
            args["squad_id"] = str(squad_id)
        return await self._call_tool("get_current_user", args)

    # Squad event methods
    async def list_squad_events(
        self,
        squad_slug: str,
        event_type: Optional[str] = None,
        upcoming_only: bool = False,
        days: int = 7,
    ) -> str:
        squad_id = await self._get_squad_id(squad_slug)
        args: dict = {"squad_id": str(squad_id)}
        if event_type:
            args["type"] = event_type
        if upcoming_only:
            args["upcoming_only"] = upcoming_only
            args["days"] = days
        return await self._call_tool("list_squad_events", args)

    async def get_online_members(self, squad_slug: str) -> str:
        squad_id = await self._get_squad_id(squad_slug)
        return await self._call_tool("get_online_members", {"squad_id": str(squad_id)})

    # Inquiry methods
    async def list_questions(self) -> str:
        return await self._call_tool("list_questions", {})

    async def get_question(self, question_id: str) -> str:
        return await self._call_tool("get_question", {"question_id": question_id})

    async def create_question(self, content: str) -> str:
        return await self._call_tool("create_question", {"content": content})

    async def delete_question(self, question_id: str) -> str:
        return await self._call_tool("delete_question", {"question_id": question_id})

    async def get_claim_tree(self, claim_id: str) -> str:
        return await self._call_tool("get_claim_tree", {"claim_id": claim_id})

    async def add_claim(self, question_id: str, content: str) -> str:
        return await self._call_tool(
            "add_claim", {"question_id": question_id, "content": content}
        )

    async def add_premise(
        self, parent_claim_id: str, content: str, ai_reasoning: Optional[str] = None
    ) -> str:
        args: dict = {"parent_claim_id": parent_claim_id, "content": content}
        if ai_reasoning:
            args["ai_reasoning"] = ai_reasoning
        return await self._call_tool("add_premise", args)
