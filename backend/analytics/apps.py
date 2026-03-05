from django.apps import AppConfig


class analyticsConfig(AppConfig):
    name = 'analytics'

    def ready(self):
        # 2026 Best Practice: Import definitions AND handlers
        import analytics.signals.definitions
        import analytics.signals.handlers
