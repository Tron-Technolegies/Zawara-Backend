from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import Notification


def create_admin_notification(title, message):
    notification = Notification.objects.create(
        title=title,
        message=message 
    )

    unread_count = Notification.objects.filter(is_read=False).count()

    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        "admin_notifications",
        {
            "type": "send_notification",
            "notification_id": notification.id,
            "title": notification.title,
            "message": notification.message,
            "created_at": notification.created_at.isoformat(),
            "unread_count": unread_count,
        }
    )

    return notification