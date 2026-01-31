from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class JStocksConfig(AppConfig):
    name = "jstocks"
    verbose_name = _("Stocks")
    default_auto_field = "django.db.models.AutoField"
