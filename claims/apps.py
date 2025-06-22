from django.apps import AppConfig  # ✅ Required import

class ClaimsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'claims'

    def ready(self):
        import claims.signals  # ✅ This enables the automatic signal connection
