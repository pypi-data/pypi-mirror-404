"""
Bot class - Main entry point for the Loop Discord SDK
"""

import asyncio
import signal
from typing import Any, Callable, Dict, List, Optional, Union

from .client import Client
from .context.command import CommandContext
from .context.button import ButtonContext
from .context.modal import ModalContext
from .context.select import SelectContext
from .types import InteractionType


CommandHandler = Callable[[CommandContext], None]
ButtonHandler = Callable[[ButtonContext], None]
ModalHandler = Callable[[ModalContext], None]
SelectHandler = Callable[[SelectContext], None]


class Command:
    """Represents a slash command"""

    def __init__(
        self,
        name: str,
        description: str,
        handler: CommandHandler,
        options: Optional[List[Dict[str, Any]]] = None,
    ):
        self.name = name
        self.description = description
        self.handler = handler
        self.options = options or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "options": self.options,
        }


class Bot:
    """Main class for creating a Loop Discord bot"""

    def __init__(
        self,
        token: str,
        api_url: str = "https://api.loopbot.app",
    ):
        self.token = token
        self.api_url = api_url
        self._client = Client(token, api_url)
        self._commands: Dict[str, Command] = {}
        self._button_handlers: Dict[str, ButtonHandler] = {}
        self._modal_handlers: Dict[str, ModalHandler] = {}
        self._select_handlers: Dict[str, SelectHandler] = {}
        self._application_id: str = ""
        self._running = False

    def command(
        self,
        name: str,
        description: str,
        options: Optional[List[Dict[str, Any]]] = None,
    ) -> Callable[[CommandHandler], CommandHandler]:
        """Decorator to register a command handler"""
        def decorator(func: CommandHandler) -> CommandHandler:
            self._commands[name] = Command(name, description, func, options)
            return func
        return decorator

    def on_button(self, custom_id: str) -> Callable[[ButtonHandler], ButtonHandler]:
        """Decorator to register a button handler"""
        def decorator(func: ButtonHandler) -> ButtonHandler:
            self._button_handlers[custom_id] = func
            return func
        return decorator

    def on_modal(self, custom_id: str) -> Callable[[ModalHandler], ModalHandler]:
        """Decorator to register a modal handler"""
        def decorator(func: ModalHandler) -> ModalHandler:
            self._modal_handlers[custom_id] = func
            return func
        return decorator

    def on_select(self, custom_id: str) -> Callable[[SelectHandler], SelectHandler]:
        """Decorator to register a select menu handler"""
        def decorator(func: SelectHandler) -> SelectHandler:
            self._select_handlers[custom_id] = func
            return func
        return decorator

    def _handle_interaction(self, interaction: Dict[str, Any]) -> None:
        """Handle incoming interaction"""
        interaction_type = interaction.get("type")
        data = interaction.get("data", {})

        response: Optional[Dict[str, Any]] = None

        if interaction_type == InteractionType.APPLICATION_COMMAND:
            command_name = data.get("name", "")
            command = self._commands.get(command_name)
            
            if command:
                ctx = CommandContext(interaction, self._client, self._application_id)
                command.handler(ctx)
                response = ctx.response

        elif interaction_type == InteractionType.MESSAGE_COMPONENT:
            custom_id = data.get("custom_id", "")
            component_type = data.get("component_type")

            # Button (type 2)
            if component_type == 2:
                handler = self._button_handlers.get(custom_id)
                if handler:
                    ctx = ButtonContext(interaction, self._client, self._application_id)
                    handler(ctx)
                    response = ctx.response

            # Select Menu (type 3)
            elif component_type == 3:
                handler = self._select_handlers.get(custom_id)
                if handler:
                    ctx = SelectContext(interaction, self._client, self._application_id)
                    handler(ctx)
                    response = ctx.response

        elif interaction_type == InteractionType.MODAL_SUBMIT:
            custom_id = data.get("custom_id", "")
            handler = self._modal_handlers.get(custom_id)
            
            if handler:
                ctx = ModalContext(interaction, self._client, self._application_id)
                handler(ctx)
                response = ctx.response

        # Send response
        if response:
            asyncio.create_task(
                self._client.respond(interaction.get("id", ""), response)
            )

    async def _start_async(self) -> None:
        """Start the bot (async)"""
        print("[Loop SDK] Starting bot...")

        # Get command schemas
        commands = [cmd.to_dict() for cmd in self._commands.values()]

        # Connect to API
        result = await self._client.connect(commands)
        self._application_id = result.get("applicationId", "")
        
        print(f"[Loop SDK] Connected to application {self._application_id}")
        print(f"[Loop SDK] Deployed {len(commands)} commands")
        print("[Loop SDK] Bot is running. Waiting for interactions...")

        self._running = True

        try:
            # Start SSE connection
            await self._client.connect_sse(self._handle_interaction)
        except asyncio.CancelledError:
            pass
        finally:
            await self.stop()

    async def stop(self) -> None:
        """Stop the bot"""
        if self._running:
            print("[Loop SDK] Stopping bot...")
            self._running = False
            await self._client.disconnect()

    def start(self) -> None:
        """Start the bot (blocking)"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Handle signals
        def signal_handler() -> None:
            loop.create_task(self.stop())

        try:
            loop.add_signal_handler(signal.SIGINT, signal_handler)
            loop.add_signal_handler(signal.SIGTERM, signal_handler)
        except NotImplementedError:
            # Windows doesn't support add_signal_handler
            pass

        try:
            loop.run_until_complete(self._start_async())
        except KeyboardInterrupt:
            loop.run_until_complete(self.stop())
        finally:
            loop.close()

    def run(self) -> None:
        """Alias for start()"""
        self.start()

    # ==================== MESSAGING ====================

    async def send(
        self,
        channel_id: str,
        content: Optional[str] = None,
        embeds: Optional[List[Dict[str, Any]]] = None,
        components: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Send a message to a channel"""
        return await self._client.send_message(
            self._application_id, channel_id, content, embeds, components
        )

    async def edit_message(
        self,
        channel_id: str,
        message_id: str,
        content: Optional[str] = None,
        embeds: Optional[List[Dict[str, Any]]] = None,
        components: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Edit a message"""
        return await self._client.edit_message(
            self._application_id, channel_id, message_id, content, embeds, components
        )

    async def delete_message(self, channel_id: str, message_id: str) -> None:
        """Delete a message"""
        await self._client.delete_message(self._application_id, channel_id, message_id)

    async def get_messages(
        self,
        channel_id: str,
        limit: Optional[int] = None,
        before: Optional[str] = None,
        after: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get messages from a channel"""
        return await self._client.get_messages(
            self._application_id, channel_id, limit, before, after
        )

    async def get_message(self, channel_id: str, message_id: str) -> Dict[str, Any]:
        """Get a single message"""
        return await self._client.get_message(
            self._application_id, channel_id, message_id
        )

    # ==================== CHANNELS ====================

    async def get_channel(self, channel_id: str) -> Dict[str, Any]:
        """Get a channel"""
        return await self._client.get_channel(self._application_id, channel_id)

    async def create_channel(
        self,
        guild_id: str,
        name: str,
        channel_type: Optional[int] = None,
        topic: Optional[str] = None,
        permission_overwrites: Optional[List[Dict[str, Any]]] = None,
        parent_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a channel in a guild"""
        return await self._client.create_channel(
            self._application_id, guild_id, name, channel_type, topic,
            permission_overwrites, parent_id
        )

    async def modify_channel(
        self,
        channel_id: str,
        name: Optional[str] = None,
        topic: Optional[str] = None,
        permission_overwrites: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Modify a channel"""
        return await self._client.modify_channel(
            self._application_id, channel_id, name, topic, permission_overwrites
        )

    async def delete_channel(self, channel_id: str) -> None:
        """Delete a channel"""
        await self._client.delete_channel(self._application_id, channel_id)

    # ==================== GUILDS ====================

    async def get_guild(self, guild_id: str) -> Dict[str, Any]:
        """Get guild info"""
        return await self._client.get_guild(self._application_id, guild_id)

    async def get_guild_channels(self, guild_id: str) -> List[Dict[str, Any]]:
        """Get guild channels"""
        return await self._client.get_guild_channels(self._application_id, guild_id)

    async def get_guild_roles(self, guild_id: str) -> List[Dict[str, Any]]:
        """Get guild roles"""
        return await self._client.get_guild_roles(self._application_id, guild_id)

    # ==================== MEMBERS ====================

    async def get_guild_member(self, guild_id: str, user_id: str) -> Dict[str, Any]:
        """Get a guild member"""
        return await self._client.get_guild_member(
            self._application_id, guild_id, user_id
        )

    async def list_guild_members(
        self,
        guild_id: str,
        limit: Optional[int] = None,
        after: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List guild members"""
        return await self._client.list_guild_members(
            self._application_id, guild_id, limit, after
        )

    async def add_member_role(
        self, guild_id: str, user_id: str, role_id: str
    ) -> None:
        """Add role to member"""
        await self._client.add_member_role(
            self._application_id, guild_id, user_id, role_id
        )

    async def remove_member_role(
        self, guild_id: str, user_id: str, role_id: str
    ) -> None:
        """Remove role from member"""
        await self._client.remove_member_role(
            self._application_id, guild_id, user_id, role_id
        )

    async def kick_member(self, guild_id: str, user_id: str) -> None:
        """Kick member"""
        await self._client.kick_member(self._application_id, guild_id, user_id)

    async def ban_member(
        self,
        guild_id: str,
        user_id: str,
        delete_message_seconds: Optional[int] = None,
    ) -> None:
        """Ban member"""
        await self._client.ban_member(
            self._application_id, guild_id, user_id, delete_message_seconds
        )

    async def unban_member(self, guild_id: str, user_id: str) -> None:
        """Unban member"""
        await self._client.unban_member(self._application_id, guild_id, user_id)

    # ==================== REACTIONS ====================

    async def add_reaction(
        self, channel_id: str, message_id: str, emoji: str
    ) -> None:
        """Add reaction to message"""
        await self._client.add_reaction(
            self._application_id, channel_id, message_id, emoji
        )

    async def remove_reaction(
        self, channel_id: str, message_id: str, emoji: str
    ) -> None:
        """Remove reaction from message"""
        await self._client.remove_reaction(
            self._application_id, channel_id, message_id, emoji
        )

    # ==================== PINS ====================

    async def pin_message(self, channel_id: str, message_id: str) -> None:
        """Pin a message"""
        await self._client.pin_message(
            self._application_id, channel_id, message_id
        )

    async def unpin_message(self, channel_id: str, message_id: str) -> None:
        """Unpin a message"""
        await self._client.unpin_message(
            self._application_id, channel_id, message_id
        )

    async def get_pinned_messages(self, channel_id: str) -> List[Dict[str, Any]]:
        """Get pinned messages"""
        return await self._client.get_pinned_messages(
            self._application_id, channel_id
        )

    # ==================== USERS ====================

    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get user info"""
        return await self._client.get_user(self._application_id, user_id)

    # ==================== THREADS ====================

    async def create_thread(
        self,
        channel_id: str,
        name: str,
        message_id: Optional[str] = None,
        thread_type: Optional[int] = None,
        auto_archive_duration: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Create a thread"""
        return await self._client.create_thread(
            self._application_id, channel_id, name, message_id,
            thread_type, auto_archive_duration
        )

    # ==================== FORUM CHANNELS ====================

    async def create_forum_post(
        self,
        channel_id: str,
        name: str,
        message: Dict[str, Any],
        applied_tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create a forum post"""
        return await self._client.create_forum_post(
            self._application_id, channel_id, name, message, applied_tags
        )

    async def get_forum_tags(self, channel_id: str) -> List[Dict[str, Any]]:
        """Get forum tags"""
        return await self._client.get_forum_tags(self._application_id, channel_id)

    async def modify_forum_tags(
        self, channel_id: str, tags: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Modify forum tags"""
        return await self._client.modify_forum_tags(
            self._application_id, channel_id, tags
        )

    async def archive_thread(
        self, thread_id: str, archived: bool = True
    ) -> Dict[str, Any]:
        """Archive thread"""
        return await self._client.archive_thread(
            self._application_id, thread_id, archived
        )

    async def lock_thread(
        self, thread_id: str, locked: bool = True
    ) -> Dict[str, Any]:
        """Lock thread"""
        return await self._client.lock_thread(
            self._application_id, thread_id, locked
        )

    # ==================== ROLES ====================

    async def get_roles(self, guild_id: str) -> List[Dict[str, Any]]:
        """Get roles"""
        return await self._client.get_roles(self._application_id, guild_id)

    async def create_role(
        self,
        guild_id: str,
        name: Optional[str] = None,
        permissions: Optional[str] = None,
        color: Optional[int] = None,
        hoist: Optional[bool] = None,
        mentionable: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Create role"""
        return await self._client.create_role(
            self._application_id, guild_id, name, permissions, color, hoist, mentionable
        )

    async def modify_role(
        self,
        guild_id: str,
        role_id: str,
        name: Optional[str] = None,
        permissions: Optional[str] = None,
        color: Optional[int] = None,
        hoist: Optional[bool] = None,
        mentionable: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Modify role"""
        return await self._client.modify_role(
            self._application_id, guild_id, role_id, name, permissions, color, hoist, mentionable
        )

    async def delete_role(self, guild_id: str, role_id: str) -> None:
        """Delete role"""
        await self._client.delete_role(self._application_id, guild_id, role_id)

    async def reorder_roles(
        self, guild_id: str, positions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Reorder roles"""
        return await self._client.reorder_roles(
            self._application_id, guild_id, positions
        )

    # ==================== WEBHOOKS ====================

    async def create_webhook(
        self, channel_id: str, name: str, avatar: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create webhook"""
        return await self._client.create_webhook(
            self._application_id, channel_id, name, avatar
        )

    async def get_channel_webhooks(self, channel_id: str) -> List[Dict[str, Any]]:
        """Get channel webhooks"""
        return await self._client.get_channel_webhooks(
            self._application_id, channel_id
        )

    async def get_guild_webhooks(self, guild_id: str) -> List[Dict[str, Any]]:
        """Get guild webhooks"""
        return await self._client.get_guild_webhooks(self._application_id, guild_id)

    async def get_webhook(self, webhook_id: str) -> Dict[str, Any]:
        """Get webhook"""
        return await self._client.get_webhook(self._application_id, webhook_id)

    async def modify_webhook(
        self,
        webhook_id: str,
        name: Optional[str] = None,
        avatar: Optional[str] = None,
        channel_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Modify webhook"""
        return await self._client.modify_webhook(
            self._application_id, webhook_id, name, avatar, channel_id
        )

    async def delete_webhook(self, webhook_id: str) -> None:
        """Delete webhook"""
        await self._client.delete_webhook(self._application_id, webhook_id)

    async def execute_webhook(
        self,
        webhook_id: str,
        webhook_token: str,
        content: Optional[str] = None,
        username: Optional[str] = None,
        avatar_url: Optional[str] = None,
        embeds: Optional[List[Dict[str, Any]]] = None,
        wait: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """Execute webhook (send message)"""
        return await self._client.execute_webhook(
            webhook_id, webhook_token, content, username, avatar_url, embeds, wait
        )

    async def edit_webhook_message(
        self,
        webhook_id: str,
        webhook_token: str,
        message_id: str,
        content: Optional[str] = None,
        embeds: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Edit webhook message"""
        return await self._client.edit_webhook_message(
            webhook_id, webhook_token, message_id, content, embeds
        )

    async def delete_webhook_message(
        self, webhook_id: str, webhook_token: str, message_id: str
    ) -> None:
        """Delete webhook message"""
        await self._client.delete_webhook_message(
            webhook_id, webhook_token, message_id
        )
