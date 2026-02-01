from django.apps import AppConfig

class DjangotenbergConfig(AppConfig):
    name = "djangotenberg"
    verbose_name = "Django Gotenberg"

    def ready(self):
        from djangotenberg import conf
        conf.validate_settings()