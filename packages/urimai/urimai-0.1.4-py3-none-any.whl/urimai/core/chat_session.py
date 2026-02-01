"""Chat session management with conversation history."""

from typing import Any
from datetime import datetime
from pydantic import BaseModel


class Message(BaseModel):
    """A message in the conversation."""

    role: str  # "user" or "assistant"
    content: str
    timestamp: str = None

    def __init__(self, **data):
        if "timestamp" not in data or data["timestamp"] is None:
            data["timestamp"] = datetime.now().isoformat()
        super().__init__(**data)


class QueryResult(BaseModel):
    """A query execution result for history."""

    question: str
    sql_query: str
    answer: str
    row_count: int
    timestamp: str = None

    def __init__(self, **data):
        if "timestamp" not in data or data["timestamp"] is None:
            data["timestamp"] = datetime.now().isoformat()
        super().__init__(**data)


class ChatSession:
    """Manages an interactive chat session with conversation history."""

    def __init__(self, db_name: str):
        """Initialize chat session.

        Args:
            db_name: Name of the database being queried
        """
        self.db_name = db_name
        self.conversation_history: list[Message] = []
        self.query_history: list[QueryResult] = []

    def add_user_message(self, question: str) -> None:
        """Add user message to conversation history.

        Args:
            question: User's question
        """
        message = Message(role="user", content=question)
        self.conversation_history.append(message)

    def add_assistant_response(
        self,
        answer: str,
        sql_query: str | None = None,
        row_count: int = 0,
    ) -> None:
        """Add assistant response to conversation history.

        Args:
            answer: Assistant's answer
            sql_query: SQL query that was executed (if any)
            row_count: Number of rows returned
        """
        message = Message(role="assistant", content=answer)
        self.conversation_history.append(message)

        # Also add to query history if this was a query
        if sql_query and self.conversation_history:
            # Get the last user message
            user_messages = [m for m in self.conversation_history if m.role == "user"]
            if user_messages:
                last_question = user_messages[-1].content
                query_result = QueryResult(
                    question=last_question,
                    sql_query=sql_query,
                    answer=answer,
                    row_count=row_count,
                )
                self.query_history.append(query_result)

    def get_conversation_context(self) -> str:
        """Get formatted conversation context for agents.

        Returns:
            Formatted conversation history string
        """
        if not self.conversation_history:
            return ""

        context = "Previous conversation:\n"
        for msg in self.conversation_history[-10:]:  # Last 10 messages for context
            context += f"{msg.role.capitalize()}: {msg.content}\n"

        return context

    def get_recent_queries(self, limit: int = 5) -> list[QueryResult]:
        """Get recent query results.

        Args:
            limit: Maximum number of queries to return

        Returns:
            List of recent QueryResult objects
        """
        return self.query_history[-limit:]

    def clear_history(self) -> None:
        """Clear all conversation and query history."""
        self.conversation_history.clear()
        self.query_history.clear()

    def get_message_count(self) -> int:
        """Get total number of messages in conversation.

        Returns:
            Number of messages
        """
        return len(self.conversation_history)

    def get_query_count(self) -> int:
        """Get total number of queries executed.

        Returns:
            Number of queries
        """
        return len(self.query_history)
