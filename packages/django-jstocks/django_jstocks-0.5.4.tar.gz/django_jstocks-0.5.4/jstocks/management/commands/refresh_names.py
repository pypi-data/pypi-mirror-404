import logging
from django.core.management.base import CommandParser
from jutil.admin import admin_log
from jutil.command import SafeCommand
from jstocks.models import Party

logger = logging.getLogger(__name__)


class Command(SafeCommand):
    def add_arguments(self, parser: CommandParser):
        pass

    def do(self, *args, **kwargs):
        for p in Party.objects.all().distinct():
            assert isinstance(p, Party)
            old = p.name
            name = p.get_name()
            if name != old:
                p.name = name
                p.save(update_fields=["name"])
                msg = f"Name updated from '{old}' to '{name}'"
                admin_log([p], msg)
                logger.info("%s: %s", p, msg)
