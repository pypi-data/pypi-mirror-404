"""
Types and enums for the Loop Discord SDK
"""

from enum import IntEnum
from typing import Any, Dict, List, Optional, TypedDict


class InteractionType(IntEnum):
    PING = 1
    APPLICATION_COMMAND = 2
    MESSAGE_COMPONENT = 3
    APPLICATION_COMMAND_AUTOCOMPLETE = 4
    MODAL_SUBMIT = 5


class InteractionResponseType(IntEnum):
    PONG = 1
    CHANNEL_MESSAGE_WITH_SOURCE = 4
    DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE = 5
    DEFERRED_UPDATE_MESSAGE = 6
    UPDATE_MESSAGE = 7
    APPLICATION_COMMAND_AUTOCOMPLETE_RESULT = 8
    MODAL = 9


class DiscordUser(TypedDict, total=False):
    id: str
    username: str
    discriminator: str
    avatar: Optional[str]
    bot: bool
    global_name: Optional[str]


class DiscordMember(TypedDict, total=False):
    user: DiscordUser
    nick: Optional[str]
    roles: List[str]
    joined_at: str
    permissions: str


class DiscordMessage(TypedDict, total=False):
    id: str
    channel_id: str
    content: str
    author: DiscordUser
    embeds: List[Dict[str, Any]]
    components: List[Dict[str, Any]]


class InteractionData(TypedDict, total=False):
    id: str
    name: str
    type: int
    options: List[Dict[str, Any]]
    custom_id: str
    component_type: int
    values: List[str]
    components: List[Dict[str, Any]]


class Interaction(TypedDict, total=False):
    id: str
    application_id: str
    type: int
    data: InteractionData
    guild_id: str
    channel_id: str
    member: DiscordMember
    user: DiscordUser
    token: str
    version: int
    message: DiscordMessage
    locale: str
