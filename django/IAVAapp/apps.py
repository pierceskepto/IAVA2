from django.apps import AppConfig


class IavaappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'IAVAapp'

def ready(self):
        import IAVAapp.models