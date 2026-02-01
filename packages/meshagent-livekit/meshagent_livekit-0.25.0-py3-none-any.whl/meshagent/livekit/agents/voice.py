import logging
import asyncio
from asyncio import CancelledError
from dataclasses import dataclass

from meshagent.api import (
    RoomMessage,
    ErrorResponse,
    Requirement,
    Participant,
    JsonResponse,
    EmptyResponse,
    TextResponse,
)
from meshagent.api.room_server_client import RoomClient

from meshagent.agents import ToolResponseAdapter
from meshagent.tools import ToolContext, Toolkit
from livekit.agents import Agent, AgentSession, ChatContext
from livekit.agents.llm import RawFunctionTool, ToolError, function_tool

from meshagent.openai.proxy import get_client
from meshagent.agents import AgentChatContext
from meshagent.livekit.agents.transcript_logger import Transcriber
from livekit.agents import (
    BackgroundAudioPlayer,
    AudioConfig,
    BuiltinAudioClip,
    RoomInputOptions,
    RoomOutputOptions,
)

from livekit.plugins import openai, silero
# from livekit.plugins.turn_detector.multilingual import MultilingualModel

import json

from typing import Any, Optional
from livekit import rtc
from meshagent.agents import SingleRoomAgent
import re

logger = logging.getLogger("voice")


def _replace_non_matching(text: str, allowed_chars: str, replacement: str) -> str:
    """
    Replaces every character in `text` that does not match the given
    `allowed_chars` regex set with `replacement`.

    Parameters:
    -----------
    text : str
        The input string on which the replacement is to be done.
    allowed_chars : str
        A string defining the set of allowed characters (part of a character set).
        For example, "a-zA-Z0-9" will keep only letters and digits.
    replacement : str
        The string to replace non-matching characters with.

    Returns:
    --------
    str
        A new string where all characters not in `allowed_chars` are replaced.
    """
    # Build a regex that matches any character NOT in allowed_chars
    pattern = rf"[^{allowed_chars}]"
    return re.sub(pattern, replacement, text)


def safe_tool_name(name: str):
    return _replace_non_matching(name, "a-zA-Z0-9_-", "_")


class VoiceConnection:
    def __init__(self, *, room: RoomClient, breakout_room: str):
        self.room = room
        self.breakout_room = breakout_room

    async def __aenter__(self):
        client = self.room

        room_options = rtc.RoomOptions(auto_subscribe=True)

        room = rtc.Room()

        self.livekit_room = room

        connection_info = await client.livekit.get_connection_info(
            breakout_room=self.breakout_room
        )

        await room.connect(
            url=connection_info.url, token=connection_info.token, options=room_options
        )

        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.livekit_room.disconnect()


@dataclass
class VoiceBotContext:
    room: RoomClient
    caller: Participant
    connection: VoiceConnection
    transcript_path: Optional[str] = None


class VoiceBot(SingleRoomAgent):
    def __init__(
        self,
        name: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        labels: Optional[list[str]] = None,
        rules: Optional[list[str]] = None,
        auto_greet_message: Optional[str] = None,
        auto_greet_prompt: Optional[str] = None,
        tool_adapter: ToolResponseAdapter = None,
        toolkits: list[Toolkit] = None,
        requires: list[Requirement] = None,
        client_rules: Optional[dict[str, list[str]]] = None,
    ):
        if toolkits is None:
            toolkits = []

        self.toolkits = toolkits

        if rules is None:
            rules = ["You are a helpful assistant communicating through voice."]

        self.tool_adapter = tool_adapter
        self.auto_greet_message = auto_greet_message
        self.auto_greet_prompt = auto_greet_prompt

        self.rules = rules

        self.client_rules = client_rules

        super().__init__(
            name=name,
            description=description,
            title=title,
            labels=labels,
            requires=requires,
        )

    async def start(self, *, room):
        await super().start(room=room)
        await room.local_participant.set_attribute("supports_voice", True)
        await room.messaging.enable()
        room.messaging.on("message", self.on_message)

    def on_message(self, message: RoomMessage):
        if message.type == "voice_call":
            breakout_room = message.message["breakout_room"]
            transcript_path = message.message.get(
                "transcript_path"
            )  # get the transcript_path if the client sends one

            logger.info(f"joining breakout room {breakout_room}")

            def on_done(task: asyncio.Task):
                try:
                    task.result()
                except CancelledError:
                    pass
                except Exception as e:
                    logger.error(f"{e}", exc_info=e)

            for participant in self.room.messaging.remote_participants:
                if (
                    participant.id == message.message.get("participant_id")
                    or participant.id == message.from_participant_id
                ):
                    task = asyncio.create_task(
                        self.run_voice_agent(
                            participant=participant,
                            breakout_room=breakout_room,
                            transcript_path=transcript_path,
                        )
                    )
                    task.add_done_callback(on_done)
                    return

            logger.error(f"unable to find participant {message.from_participant_id}")

    async def _wait_for_disconnect(self, room: rtc.Room):
        disconnected = asyncio.Future()

        def on_disconnected(_):
            disconnected.set_result(True)

        room.on("disconnected", on_disconnected)

        logger.info("waiting for disconnection")
        await disconnected

    async def make_function_tools(self, *, context: ToolContext):
        toolkits = [*await self.get_required_toolkits(context=context), *self.toolkits]

        tools = []

        for toolkit in toolkits:
            for tool in toolkit.tools:
                tools.append(
                    self._make_function_tool(
                        toolkits,
                        context,
                        tool.name,
                        tool.description,
                        tool.input_schema,
                    )
                )

        return tools

    def _make_function_tool(
        self,
        toolkits: list[Toolkit],
        context: ToolContext,
        name: str,
        description: str | None,
        input_schema: dict,
    ) -> RawFunctionTool:
        name = safe_tool_name(name)

        async def _tool_called(raw_arguments: dict) -> Any:
            try:
                tool = None
                for toolkit in toolkits:
                    for t in toolkit.tools:
                        if safe_tool_name(t.name) == name:
                            tool = t

                if tool is None:
                    raise ToolError(f"Could not find tool {name}")

                try:
                    logger.info(f"executing tool {name}: {raw_arguments}")
                    tool_result = await tool.execute(context=context, **raw_arguments)
                except Exception as e:
                    logger.error(f"failed to call tool {tool.name}: {e}")
                    return ToolError(f"{e}")
                if self.tool_adapter is None:
                    if isinstance(tool_result, ErrorResponse):
                        raise ToolError(tool_result.text)

                    if isinstance(tool_result, JsonResponse):
                        return json.dumps(tool_result.json)

                    if isinstance(tool_result, TextResponse):
                        return tool_result.text

                    if isinstance(tool_result, EmptyResponse):
                        return "success"

                    if tool_result is None:
                        return "success"

                    raise ToolError(
                        f"Tool '{name}' returned an unexpected result {type(tool_result)}, attach a tool response adapter"
                    )

                else:
                    text = await self.tool_adapter.to_plain_text(
                        room=context.room, response=tool_result
                    )
                    if text is None:
                        text = "success"
                    return text

            except Exception as e:
                logger.error("unable to call tool", exc_info=e)
                raise

        return function_tool(
            _tool_called,
            raw_schema={
                "name": name,
                "description": description,
                "strict": True,
                "parameters": input_schema,
            },
        )

    async def create_agent(
        self,
        *,
        context: VoiceBotContext,
        session: AgentSession,
    ):
        ctx = ChatContext()

        initial_context = await self.init_chat_context()

        tool_context = ToolContext(
            room=context.room,
            caller=context.room.local_participant,
            on_behalf_of=context.caller,
        )

        rules = await self.get_rules(participant=context.room.local_participant)

        initial_context.replace_rules(rules)

        for message in initial_context.messages:
            ctx.add_message(role=message["role"], content=message["content"])

        if context.transcript_path:
            return Transcriber(
                room=context.room,
                transcript_path=context.transcript_path,
                events={"conversation_item_added"},
                user=context.caller,
                agent=context.room.local_participant,
                chat_ctx=ctx,
                instructions=initial_context.get_system_instructions(),
                allow_interruptions=True,
                tools=[*await self.make_function_tools(context=tool_context)],
            )
        else:
            return Agent(
                chat_ctx=ctx,
                instructions=initial_context.get_system_instructions(),
                allow_interruptions=True,
                tools=[*await self.make_function_tools(context=tool_context)],
            )

    async def get_rules(self, *, participant: Participant):
        rules = [*self.rules]
        client = participant.get_attribute("client")

        if self.client_rules is not None and client is not None:
            cr = self.client_rules.get(client)
            if cr is not None:
                rules.extend(cr)

        return rules

    async def init_chat_context(self) -> AgentChatContext:
        return AgentChatContext()

    def create_session(self, *, context: VoiceBotContext) -> AgentSession:
        oaiclient = get_client(room=self.room)

        session = AgentSession(
            max_tool_steps=50,
            allow_interruptions=True,
            vad=silero.VAD.load(),
            stt=openai.STT(client=oaiclient),
            tts=openai.TTS(client=oaiclient),
            llm=openai.LLM(client=oaiclient),
            # turn_detection=MultilingualModel(),
        )
        return session

    async def on_session_created(
        self, *, context: VoiceBotContext, session: AgentSession
    ) -> None:
        return

    async def on_session_started(
        self, *, context: VoiceBotContext, session: AgentSession
    ) -> None:
        return

    async def on_session_ended(
        self, *, context: VoiceBotContext, session: AgentSession
    ) -> None:
        return

    async def run_voice_agent(
        self,
        *,
        participant: Participant,
        breakout_room: str,
        transcript_path: Optional[str] = None,
    ):
        async with VoiceConnection(
            room=self.room, breakout_room=breakout_room
        ) as connection:
            logger.info("starting voice agent")

            context = VoiceBotContext(
                room=self.room,
                caller=participant,
                connection=connection,
                transcript_path=transcript_path,
            )

            session = self.create_session(context=context)

            try:
                await self.on_session_created(context=context, session=session)

                agent = await self.create_agent(context=context, session=session)

                background_audio = BackgroundAudioPlayer(
                    thinking_sound=[
                        # AudioConfig(
                        #    os.path.dirname(os.path.abspath(__file__)) +"/sfx/thinking.mp3", volume=0.2),
                        AudioConfig(BuiltinAudioClip.KEYBOARD_TYPING, volume=0.3),
                        AudioConfig(BuiltinAudioClip.KEYBOARD_TYPING2, volume=0.4),
                    ],
                )
                await background_audio.start(
                    room=connection.livekit_room, agent_session=session
                )

                await session.start(
                    agent=agent,
                    room=connection.livekit_room,
                    room_input_options=RoomInputOptions(
                        text_enabled=False,
                        delete_room_on_close=False,
                    ),
                    room_output_options=RoomOutputOptions(
                        transcription_enabled=True,
                        audio_enabled=True,
                    ),
                )

                await self.on_session_started(context=context, session=session)
                if self.auto_greet_prompt is not None:
                    session.generate_reply(user_input=self.auto_greet_prompt)

                if self.auto_greet_message is not None:
                    session.say(self.auto_greet_message)

                logger.info("started voice agent")
                await self._wait_for_disconnect(room=connection.livekit_room)

            except Exception as e:
                logger.error(f"Error during voice session: {e}", exc_info=e)

            await self.on_session_ended(context=context, session=session)
