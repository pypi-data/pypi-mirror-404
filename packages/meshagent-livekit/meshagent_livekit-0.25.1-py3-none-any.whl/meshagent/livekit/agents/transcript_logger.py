import logging
from typing import Literal
from datetime import datetime, timezone
from livekit.agents import Agent, llm, StopResponse
from livekit.agents.llm import ChatMessage
from livekit.agents.voice import ConversationItemAddedEvent
from meshagent.api import MeshDocument, Participant
from meshagent.api.room_server_client import RoomClient
from meshagent.agents.schemas.transcript import transcript_schema

logger = logging.getLogger("transcript_logger")


class Transcriber(Agent):
    def __init__(
        self,
        *,
        user: Participant,
        agent: Participant,
        events: set[Literal["user_turn_completed", "conversation_item_added"]],
        transcript_path: str,
        room: RoomClient,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.user = user
        self.agent = agent
        self.events = events
        self.transcript_path = transcript_path
        self.room = room
        self.doc: MeshDocument | None = None

    def _append_segment(self, *, role: str, text: str, created_at: float):
        if not text:
            return

        if not self.doc:
            logger.warning("Cannot append segment, document not opened")
            return

        if role == "user":
            participant_id = self.user.id
            participant_name = self.user.get_attribute("name")
        elif role == "assistant":
            participant_id = self.agent.id
            participant_name = self.agent.get_attribute("name")
        else:
            # skip system / developer / function_call, etc
            return

        try:
            segments = self.doc.root
            segments.append_child(
                "segment",
                {
                    "text": text,
                    "participant_name": participant_name,
                    "participant_id": participant_id,
                    "time": datetime.fromtimestamp(created_at, tz=timezone.utc)
                    .isoformat()
                    .replace("+00:00", "Z"),
                },
            )
        except Exception as e:
            logger.error(f"Failed to write sgement: {e}", exc_info=e)

    def _on_conversation_item(self, event: ConversationItemAddedEvent):
        item = event.item
        # Only care about ChatMessages (ignore tool calls, etc.)
        if not isinstance(item, ChatMessage):
            return

        text = item.text_content
        if text is None:
            return

        # item.role is Literal["developer", "system", "user", "assistant"]
        self._append_segment(role=item.role, text=text, created_at=item.created_at)

    async def on_enter(self):
        """Open MeshDocument and attach handler for voicebot transcriptions"""
        try:
            self.doc = await self.room.sync.open(
                path=self.transcript_path, create=True, schema=transcript_schema
            )
        except Exception as e:
            logger.warning(
                f"Failed to open transcript doc: {e}. This meeting will not be transcribed."
            )
            return

        if "conversation_item_added" in self.events:
            self.session.on("conversation_item_added", self._on_conversation_item)

    async def on_exit(self):
        """Cleanup handler when voicebot transcription ends and close MeshDocument"""
        if "conversation_item_added" in self.events:
            try:
                self.session.off("conversation_item_added", self._on_conversation_item)
            except Exception as e:
                logger.warning(f"Failed to remove handler: {e}")
        # only close doc if it was successfully opened
        if self.doc:
            try:
                await self.room.sync.close(path=self.transcript_path)
                logger.info("transcript saved at %s", self.transcript_path)
            except Exception as e:
                logger.warning("failed to close transcript doc: %s", e)

    async def on_user_turn_completed(
        self, turn_ctx: llm.ChatContext, new_message: llm.ChatMessage
    ):
        if "user_turn_completed" in self.events:
            self._append_segment(
                role="user",
                text=new_message.text_content,
                created_at=new_message.created_at,
            )
            raise StopResponse()
