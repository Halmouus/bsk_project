import os
from django.apps import AppConfig
from django.conf import settings

class TestappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'testapp'

    def ready(self):
        import testapp.signals
        # Create media directories on app startup
        media_dirs = [
            os.path.join(settings.MEDIA_ROOT, 'documents'),
            os.path.join(settings.MEDIA_ROOT, 'documents/deliverynote'),
            os.path.join(settings.MEDIA_ROOT, 'documents/receptionnote'),
        ]
        for dir_path in media_dirs:
            os.makedirs(dir_path, exist_ok=True)
