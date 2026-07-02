import json
from channels.generic.websocket import AsyncWebsocketConsumer


class AdminNotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "admin_notifications"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def send_notification(self, event):
        await self.send(text_data=json.dumps({
            "title": event["title"],
            "message": event["message"],
            "date": event["date"],
            "unread_count": event["unread_count"]
        }))