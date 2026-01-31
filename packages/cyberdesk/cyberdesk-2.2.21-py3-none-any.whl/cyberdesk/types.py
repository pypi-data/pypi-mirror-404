"""Type definitions for Cyberdesk run message history.

These types define the structure of the run_message_history field returned
in RunResponse objects. The run_message_history contains a conversation history
between the user, system, and AI assistant during a workflow execution.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MessageContentBlock(BaseModel):
    """Represents a content block within a message.
    
    A message can contain multiple blocks of different types (text, images, tool usage, etc).
    """
    
    type: str = Field(
        description="Type of content block: 'text', 'image', 'tool_use', 'tool_result'"
    )
    text: Optional[str] = Field(
        default=None,
        description="Text content for text blocks"
    )
    image_url: Optional[str] = Field(
        default=None,
        description="Supabase URL for image content (after processing)"
    )
    image_base64: Optional[str] = Field(
        default=None,
        description="Base64-encoded image data (temporary, during run execution)"
    )
    tool_use_id: Optional[str] = Field(
        default=None,
        description="Unique identifier for tool usage"
    )
    tool_name: Optional[str] = Field(
        default=None,
        description="Name of the tool being used (e.g., 'computer')"
    )
    tool_input: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Input parameters passed to the tool"
    )
    tool_result: Optional[str] = Field(
        default=None,
        description="Result returned from tool execution"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if the tool execution failed"
    )
    trajectory_id: Optional[str] = Field(
        default=None,
        description="ID of the trajectory used (for muscle memory/caching)"
    )
    trajectory_label: Optional[str] = Field(
        default=None,
        description="Human-readable label for the trajectory"
    )
    step_signature_hash: Optional[int] = Field(
        default=None,
        description="Hash of the step signature (for cache matching)"
    )
    step_index: Optional[int] = Field(
        default=None,
        description="Index of the step within the trajectory"
    )


class ChatMessage(BaseModel):
    """Represents a single message in the conversation history.
    
    Each message has a role (user, assistant, system) and contains one or more content blocks.
    """
    
    role: str = Field(
        description="Role of the message sender: 'user', 'assistant', or 'system'"
    )
    content: List[MessageContentBlock] = Field(
        description="List of content blocks in this message"
    )
    timestamp: Optional[str] = Field(
        default=None,
        description="ISO 8601 timestamp when the message was created"
    )
    trajectory_id: Optional[str] = Field(
        default=None,
        description="ID of the trajectory used for this entire message"
    )
    trajectory_label: Optional[str] = Field(
        default=None,
        description="Human-readable label for the trajectory"
    )
    step_index: Optional[int] = Field(
        default=None,
        description="Step index within the trajectory"
    )
    loop_uuid: Optional[str] = Field(
        default=None,
        description="UUID of the loop if this message is part of a loop"
    )
    iteration_index: Optional[int] = Field(
        default=None,
        description="Iteration index if this message is part of a loop"
    )


# Type alias for the full run message history
RunMessageHistory = List[ChatMessage]


__all__ = [
    "MessageContentBlock",
    "ChatMessage", 
    "RunMessageHistory",
]

