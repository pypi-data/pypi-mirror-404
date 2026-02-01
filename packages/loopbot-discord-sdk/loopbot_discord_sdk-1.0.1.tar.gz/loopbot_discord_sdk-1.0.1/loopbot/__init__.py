"""
Loop Discord SDK for Python
Build Discord bots without websockets using HTTP Interactions
"""

from .bot import Bot
from .client import Client
from .builders import (
    EmbedBuilder,
    ButtonBuilder,
    ButtonStyle,
    ActionRowBuilder,
    SelectMenuBuilder,
    ModalBuilder,
    ContainerBuilder,
    SeparatorBuilder,
    TextDisplayBuilder,
    MediaGalleryBuilder,
    SectionBuilder,
    FileBuilder,
)
from .context import (
    CommandContext,
    ButtonContext,
    ModalContext,
    SelectContext,
)
from .types import (
    InteractionType,
    InteractionResponseType,
)

__version__ = "1.0.0"
__all__ = [
    # Core
    "Bot",
    "Client",
    # Builders
    "EmbedBuilder",
    "ButtonBuilder",
    "ButtonStyle",
    "ActionRowBuilder",
    "SelectMenuBuilder",
    "ModalBuilder",
    # Components V2
    "ContainerBuilder",
    "SeparatorBuilder",
    "TextDisplayBuilder",
    "MediaGalleryBuilder",
    "SectionBuilder",
    "FileBuilder",
    # Context
    "CommandContext",
    "ButtonContext",
    "ModalContext",
    "SelectContext",
    # Types
    "InteractionType",
    "InteractionResponseType",
]
