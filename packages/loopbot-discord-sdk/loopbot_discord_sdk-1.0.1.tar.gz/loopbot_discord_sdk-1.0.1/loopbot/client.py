"""
HTTP/SSE Client for Loop Discord SDK
"""

import asyncio
import json
from typing import Any, Callable, Dict, List, Optional

import aiohttp
from aiohttp_sse_client import client as sse_client


class Client:
    """HTTP client for communicating with the Loop API"""

    def __init__(self, token: str, base_url: str = "https://gatewayloop.discloud.app"):
        self.token = token
        self.base_url = base_url.rstrip("/")
        self._session: Optional[aiohttp.ClientSession] = None
        self._sse_task: Optional[asyncio.Task] = None
        self._connected = False

    @property
    def headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def request(
        self,
        method: str,
        endpoint: str,
        body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an HTTP request to the API"""
        session = await self._get_session()
        url = f"{self.base_url}/api{endpoint}"

        async with session.request(
            method,
            url,
            headers=self.headers,
            json=body,
        ) as response:
            if not response.ok:
                error_text = await response.text()
                raise Exception(f"API error {response.status}: {error_text}")

            if response.status == 204:
                return {}

            return await response.json()

    async def connect(self, commands: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Connect to the API and deploy commands"""
        result = await self.request("POST", "/sdk/connect", {"commands": commands})
        self._connected = True
        return result

    async def connect_sse(self, on_interaction: Callable[[Dict[str, Any]], None]) -> None:
        """Connect to SSE for receiving interactions"""
        url = f"{self.base_url}/api/sdk/events"

        async with sse_client.EventSource(
            url,
            headers=self.headers,
        ) as event_source:
            async for event in event_source:
                if event.type == "connected":
                    print("[Loop SDK] SSE connected")
                elif event.type == "interaction":
                    try:
                        interaction = json.loads(event.data)
                        on_interaction(interaction)
                    except json.JSONDecodeError as e:
                        print(f"[Loop SDK] Failed to parse interaction: {e}")
                elif event.type == "ping":
                    pass  # Heartbeat

    async def respond(self, interaction_id: str, response: Dict[str, Any]) -> None:
        """Send interaction response"""
        await self.request("POST", "/sdk/respond", {
            "interactionId": interaction_id,
            "response": response,
        })

    async def follow_up(
        self,
        application_id: str,
        interaction_token: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Send follow-up message"""
        return await self.request("POST", "/sdk/followup", {
            "applicationId": application_id,
            "interactionToken": interaction_token,
            "data": data,
        })

    async def edit_original(
        self,
        application_id: str,
        interaction_token: str,
        data: Dict[str, Any],
    ) -> None:
        """Edit original response"""
        await self.request("POST", "/sdk/edit", {
            "applicationId": application_id,
            "interactionToken": interaction_token,
            "data": data,
        })

    async def disconnect(self) -> None:
        """Disconnect from API"""
        if self._connected:
            try:
                await self.request("POST", "/sdk/disconnect", {})
            except Exception:
                pass
            self._connected = False

        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    @property
    def is_connected(self) -> bool:
        return self._connected

    # ==================== MESSAGING ====================

    async def send_message(
        self,
        application_id: str,
        channel_id: str,
        content: Optional[str] = None,
        embeds: Optional[List[Dict[str, Any]]] = None,
        components: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Send a message to a channel"""
        data = {"applicationId": application_id, "channelId": channel_id}
        if content:
            data["content"] = content
        if embeds:
            data["embeds"] = embeds
        if components:
            data["components"] = components
        result = await self.request("POST", "/sdk/messages/send", data)
        return result.get("message", {})

    async def edit_message(
        self,
        application_id: str,
        channel_id: str,
        message_id: str,
        content: Optional[str] = None,
        embeds: Optional[List[Dict[str, Any]]] = None,
        components: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Edit a message"""
        data = {"applicationId": application_id, "channelId": channel_id, "messageId": message_id}
        if content is not None:
            data["content"] = content
        if embeds:
            data["embeds"] = embeds
        if components:
            data["components"] = components
        result = await self.request("POST", "/sdk/messages/edit", data)
        return result.get("message", {})

    async def delete_message(
        self,
        application_id: str,
        channel_id: str,
        message_id: str,
    ) -> None:
        """Delete a message"""
        await self.request("POST", "/sdk/messages/delete", {
            "applicationId": application_id,
            "channelId": channel_id,
            "messageId": message_id,
        })

    async def get_messages(
        self,
        application_id: str,
        channel_id: str,
        limit: Optional[int] = None,
        before: Optional[str] = None,
        after: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get messages from a channel"""
        params = []
        if limit:
            params.append(f"limit={limit}")
        if before:
            params.append(f"before={before}")
        if after:
            params.append(f"after={after}")
        endpoint = f"/sdk/messages/{application_id}/{channel_id}"
        if params:
            endpoint += "?" + "&".join(params)
        result = await self.request("GET", endpoint)
        return result.get("messages", [])

    async def get_message(
        self,
        application_id: str,
        channel_id: str,
        message_id: str,
    ) -> Dict[str, Any]:
        """Get a single message"""
        result = await self.request("GET", f"/sdk/messages/{application_id}/{channel_id}/{message_id}")
        return result.get("message", {})

    # ==================== CHANNELS ====================

    async def get_channel(self, application_id: str, channel_id: str) -> Dict[str, Any]:
        """Get a channel"""
        result = await self.request("GET", f"/sdk/channels/{application_id}/{channel_id}")
        return result.get("channel", {})

    async def create_channel(
        self,
        application_id: str,
        guild_id: str,
        name: str,
        channel_type: Optional[int] = None,
        topic: Optional[str] = None,
        permission_overwrites: Optional[List[Dict[str, Any]]] = None,
        parent_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a channel in a guild"""
        data: Dict[str, Any] = {
            "applicationId": application_id,
            "guildId": guild_id,
            "name": name,
        }
        if channel_type is not None:
            data["type"] = channel_type
        if topic:
            data["topic"] = topic
        if permission_overwrites:
            data["permission_overwrites"] = permission_overwrites
        if parent_id:
            data["parent_id"] = parent_id
        result = await self.request("POST", "/sdk/channels/create", data)
        return result.get("channel", {})

    async def modify_channel(
        self,
        application_id: str,
        channel_id: str,
        name: Optional[str] = None,
        topic: Optional[str] = None,
        permission_overwrites: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Modify a channel"""
        data: Dict[str, Any] = {"applicationId": application_id, "channelId": channel_id}
        if name:
            data["name"] = name
        if topic is not None:
            data["topic"] = topic
        if permission_overwrites:
            data["permission_overwrites"] = permission_overwrites
        result = await self.request("POST", "/sdk/channels/modify", data)
        return result.get("channel", {})

    async def delete_channel(self, application_id: str, channel_id: str) -> None:
        """Delete a channel"""
        await self.request("POST", "/sdk/channels/delete", {
            "applicationId": application_id,
            "channelId": channel_id,
        })

    # ==================== GUILDS ====================

    async def get_guild(self, application_id: str, guild_id: str) -> Dict[str, Any]:
        """Get guild info"""
        result = await self.request("GET", f"/sdk/guilds/{application_id}/{guild_id}")
        return result.get("guild", {})

    async def get_guild_channels(self, application_id: str, guild_id: str) -> List[Dict[str, Any]]:
        """Get guild channels"""
        result = await self.request("GET", f"/sdk/guilds/{application_id}/{guild_id}/channels")
        return result.get("channels", [])

    async def get_guild_roles(self, application_id: str, guild_id: str) -> List[Dict[str, Any]]:
        """Get guild roles"""
        result = await self.request("GET", f"/sdk/guilds/{application_id}/{guild_id}/roles")
        return result.get("roles", [])

    # ==================== MEMBERS ====================

    async def get_guild_member(
        self,
        application_id: str,
        guild_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """Get a guild member"""
        result = await self.request("GET", f"/sdk/members/{application_id}/{guild_id}/{user_id}")
        return result.get("member", {})

    async def list_guild_members(
        self,
        application_id: str,
        guild_id: str,
        limit: Optional[int] = None,
        after: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List guild members"""
        params = []
        if limit:
            params.append(f"limit={limit}")
        if after:
            params.append(f"after={after}")
        endpoint = f"/sdk/members/{application_id}/{guild_id}"
        if params:
            endpoint += "?" + "&".join(params)
        result = await self.request("GET", endpoint)
        return result.get("members", [])

    async def add_member_role(
        self,
        application_id: str,
        guild_id: str,
        user_id: str,
        role_id: str,
    ) -> None:
        """Add role to member"""
        await self.request("POST", "/sdk/members/roles/add", {
            "applicationId": application_id,
            "guildId": guild_id,
            "userId": user_id,
            "roleId": role_id,
        })

    async def remove_member_role(
        self,
        application_id: str,
        guild_id: str,
        user_id: str,
        role_id: str,
    ) -> None:
        """Remove role from member"""
        await self.request("POST", "/sdk/members/roles/remove", {
            "applicationId": application_id,
            "guildId": guild_id,
            "userId": user_id,
            "roleId": role_id,
        })

    async def kick_member(
        self,
        application_id: str,
        guild_id: str,
        user_id: str,
    ) -> None:
        """Kick member"""
        await self.request("POST", "/sdk/members/kick", {
            "applicationId": application_id,
            "guildId": guild_id,
            "userId": user_id,
        })

    async def ban_member(
        self,
        application_id: str,
        guild_id: str,
        user_id: str,
        delete_message_seconds: Optional[int] = None,
    ) -> None:
        """Ban member"""
        data: Dict[str, Any] = {
            "applicationId": application_id,
            "guildId": guild_id,
            "userId": user_id,
        }
        if delete_message_seconds:
            data["deleteMessageSeconds"] = delete_message_seconds
        await self.request("POST", "/sdk/members/ban", data)

    async def unban_member(
        self,
        application_id: str,
        guild_id: str,
        user_id: str,
    ) -> None:
        """Unban member"""
        await self.request("POST", "/sdk/members/unban", {
            "applicationId": application_id,
            "guildId": guild_id,
            "userId": user_id,
        })

    # ==================== REACTIONS ====================

    async def add_reaction(
        self,
        application_id: str,
        channel_id: str,
        message_id: str,
        emoji: str,
    ) -> None:
        """Add reaction to message"""
        await self.request("POST", "/sdk/reactions/add", {
            "applicationId": application_id,
            "channelId": channel_id,
            "messageId": message_id,
            "emoji": emoji,
        })

    async def remove_reaction(
        self,
        application_id: str,
        channel_id: str,
        message_id: str,
        emoji: str,
    ) -> None:
        """Remove reaction from message"""
        await self.request("POST", "/sdk/reactions/remove", {
            "applicationId": application_id,
            "channelId": channel_id,
            "messageId": message_id,
            "emoji": emoji,
        })

    # ==================== PINS ====================

    async def pin_message(
        self,
        application_id: str,
        channel_id: str,
        message_id: str,
    ) -> None:
        """Pin a message"""
        await self.request("POST", "/sdk/pins/add", {
            "applicationId": application_id,
            "channelId": channel_id,
            "messageId": message_id,
        })

    async def unpin_message(
        self,
        application_id: str,
        channel_id: str,
        message_id: str,
    ) -> None:
        """Unpin a message"""
        await self.request("POST", "/sdk/pins/remove", {
            "applicationId": application_id,
            "channelId": channel_id,
            "messageId": message_id,
        })

    async def get_pinned_messages(
        self,
        application_id: str,
        channel_id: str,
    ) -> List[Dict[str, Any]]:
        """Get pinned messages"""
        result = await self.request("GET", f"/sdk/pins/{application_id}/{channel_id}")
        return result.get("messages", [])

    # ==================== USERS ====================

    async def get_user(self, application_id: str, user_id: str) -> Dict[str, Any]:
        """Get user info"""
        result = await self.request("GET", f"/sdk/users/{application_id}/{user_id}")
        return result.get("user", {})

    # ==================== THREADS ====================

    async def create_thread(
        self,
        application_id: str,
        channel_id: str,
        name: str,
        message_id: Optional[str] = None,
        thread_type: Optional[int] = None,
        auto_archive_duration: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Create a thread"""
        data: Dict[str, Any] = {
            "applicationId": application_id,
            "channelId": channel_id,
            "name": name,
        }
        if message_id:
            data["messageId"] = message_id
        if thread_type:
            data["type"] = thread_type
        if auto_archive_duration:
            data["auto_archive_duration"] = auto_archive_duration
        result = await self.request("POST", "/sdk/threads/create", data)
        return result.get("thread", {})

    # ==================== FORUM CHANNELS ====================

    async def create_forum_post(
        self,
        application_id: str,
        channel_id: str,
        name: str,
        message: Dict[str, Any],
        applied_tags: Optional[List[str]] = None,
        auto_archive_duration: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Create a forum post"""
        data: Dict[str, Any] = {
            "applicationId": application_id,
            "channelId": channel_id,
            "name": name,
            "message": message,
        }
        if applied_tags:
            data["applied_tags"] = applied_tags
        if auto_archive_duration:
            data["auto_archive_duration"] = auto_archive_duration
        result = await self.request("POST", "/sdk/forum/post", data)
        return result.get("post", {})

    async def get_forum_tags(
        self, application_id: str, channel_id: str
    ) -> List[Dict[str, Any]]:
        """Get forum tags"""
        result = await self.request("GET", f"/sdk/forum/{application_id}/{channel_id}/tags")
        return result.get("tags", [])

    async def modify_forum_tags(
        self,
        application_id: str,
        channel_id: str,
        tags: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Modify forum tags"""
        result = await self.request("POST", "/sdk/forum/tags/modify", {
            "applicationId": application_id,
            "channelId": channel_id,
            "tags": tags,
        })
        return result.get("channel", {})

    async def archive_thread(
        self,
        application_id: str,
        thread_id: str,
        archived: bool = True,
    ) -> Dict[str, Any]:
        """Archive thread"""
        result = await self.request("POST", "/sdk/forum/archive", {
            "applicationId": application_id,
            "threadId": thread_id,
            "archived": archived,
        })
        return result.get("thread", {})

    async def lock_thread(
        self,
        application_id: str,
        thread_id: str,
        locked: bool = True,
    ) -> Dict[str, Any]:
        """Lock thread"""
        result = await self.request("POST", "/sdk/forum/lock", {
            "applicationId": application_id,
            "threadId": thread_id,
            "locked": locked,
        })
        return result.get("thread", {})

    # ==================== ROLES ====================

    async def get_roles(
        self, application_id: str, guild_id: str
    ) -> List[Dict[str, Any]]:
        """Get roles"""
        result = await self.request("GET", f"/sdk/roles/{application_id}/{guild_id}")
        return result.get("roles", [])

    async def create_role(
        self,
        application_id: str,
        guild_id: str,
        name: Optional[str] = None,
        permissions: Optional[str] = None,
        color: Optional[int] = None,
        hoist: Optional[bool] = None,
        mentionable: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Create role"""
        data: Dict[str, Any] = {
            "applicationId": application_id,
            "guildId": guild_id,
        }
        if name:
            data["name"] = name
        if permissions:
            data["permissions"] = permissions
        if color is not None:
            data["color"] = color
        if hoist is not None:
            data["hoist"] = hoist
        if mentionable is not None:
            data["mentionable"] = mentionable
        result = await self.request("POST", "/sdk/roles/create", data)
        return result.get("role", {})

    async def modify_role(
        self,
        application_id: str,
        guild_id: str,
        role_id: str,
        name: Optional[str] = None,
        permissions: Optional[str] = None,
        color: Optional[int] = None,
        hoist: Optional[bool] = None,
        mentionable: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Modify role"""
        data: Dict[str, Any] = {
            "applicationId": application_id,
            "guildId": guild_id,
            "roleId": role_id,
        }
        if name:
            data["name"] = name
        if permissions:
            data["permissions"] = permissions
        if color is not None:
            data["color"] = color
        if hoist is not None:
            data["hoist"] = hoist
        if mentionable is not None:
            data["mentionable"] = mentionable
        result = await self.request("POST", "/sdk/roles/modify", data)
        return result.get("role", {})

    async def delete_role(
        self, application_id: str, guild_id: str, role_id: str
    ) -> None:
        """Delete role"""
        await self.request("POST", "/sdk/roles/delete", {
            "applicationId": application_id,
            "guildId": guild_id,
            "roleId": role_id,
        })

    async def reorder_roles(
        self,
        application_id: str,
        guild_id: str,
        positions: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Reorder roles"""
        result = await self.request("POST", "/sdk/roles/reorder", {
            "applicationId": application_id,
            "guildId": guild_id,
            "positions": positions,
        })
        return result.get("roles", [])

    # ==================== WEBHOOKS ====================

    async def create_webhook(
        self,
        application_id: str,
        channel_id: str,
        name: str,
        avatar: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create webhook"""
        data: Dict[str, Any] = {
            "applicationId": application_id,
            "channelId": channel_id,
            "name": name,
        }
        if avatar:
            data["avatar"] = avatar
        result = await self.request("POST", "/sdk/webhooks/create", data)
        return result.get("webhook", {})

    async def get_channel_webhooks(
        self, application_id: str, channel_id: str
    ) -> List[Dict[str, Any]]:
        """Get channel webhooks"""
        result = await self.request(
            "GET", f"/sdk/webhooks/channel/{application_id}/{channel_id}"
        )
        return result.get("webhooks", [])

    async def get_guild_webhooks(
        self, application_id: str, guild_id: str
    ) -> List[Dict[str, Any]]:
        """Get guild webhooks"""
        result = await self.request(
            "GET", f"/sdk/webhooks/guild/{application_id}/{guild_id}"
        )
        return result.get("webhooks", [])

    async def get_webhook(
        self, application_id: str, webhook_id: str
    ) -> Dict[str, Any]:
        """Get webhook"""
        result = await self.request(
            "GET", f"/sdk/webhooks/{application_id}/{webhook_id}"
        )
        return result.get("webhook", {})

    async def modify_webhook(
        self,
        application_id: str,
        webhook_id: str,
        name: Optional[str] = None,
        avatar: Optional[str] = None,
        channel_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Modify webhook"""
        data: Dict[str, Any] = {
            "applicationId": application_id,
            "webhookId": webhook_id,
        }
        if name:
            data["name"] = name
        if avatar:
            data["avatar"] = avatar
        if channel_id:
            data["channel_id"] = channel_id
        result = await self.request("POST", "/sdk/webhooks/modify", data)
        return result.get("webhook", {})

    async def delete_webhook(
        self, application_id: str, webhook_id: str
    ) -> None:
        """Delete webhook"""
        await self.request("POST", "/sdk/webhooks/delete", {
            "applicationId": application_id,
            "webhookId": webhook_id,
        })

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
        data: Dict[str, Any] = {
            "webhookId": webhook_id,
            "webhookToken": webhook_token,
            "wait": wait,
        }
        if content:
            data["content"] = content
        if username:
            data["username"] = username
        if avatar_url:
            data["avatar_url"] = avatar_url
        if embeds:
            data["embeds"] = embeds
        result = await self.request("POST", "/sdk/webhooks/execute", data)
        return result.get("message")

    async def edit_webhook_message(
        self,
        webhook_id: str,
        webhook_token: str,
        message_id: str,
        content: Optional[str] = None,
        embeds: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Edit webhook message"""
        data: Dict[str, Any] = {
            "webhookId": webhook_id,
            "webhookToken": webhook_token,
            "messageId": message_id,
        }
        if content:
            data["content"] = content
        if embeds:
            data["embeds"] = embeds
        result = await self.request("POST", "/sdk/webhooks/message/edit", data)
        return result.get("message", {})

    async def delete_webhook_message(
        self, webhook_id: str, webhook_token: str, message_id: str
    ) -> None:
        """Delete webhook message"""
        await self.request("POST", "/sdk/webhooks/message/delete", {
            "webhookId": webhook_id,
            "webhookToken": webhook_token,
            "messageId": message_id,
        })

