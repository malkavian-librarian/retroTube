"""
ASGI config for retro_tool project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from channels.routing import ProtocolTypeRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "retro_tool.settings")

# Placeholder routing — WebSocket routes land in a later task (see
# _docs/arch.md's realtime event contract). HTTP falls through to Django.
application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
    }
)
