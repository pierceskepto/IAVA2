"""
ASGI config for IAVA project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import IAVA.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'IAVA.settings')

# We'll add the routing import after we create routing.py
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter([
            IAVA.routing.websocket_urlpatterns
        ])
    ),
})