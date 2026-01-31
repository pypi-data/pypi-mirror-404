import logging
from django.conf import settings
from django.core.management.base import CommandParser
from jutil.command import SafeCommand
from jstocks.models import Tx


logger = logging.getLogger(__name__)


class Command(SafeCommand):
    def add_arguments(self, parser: CommandParser):
        parser.add_argument("--begin-id", type=int)
        parser.add_argument("--last-id", type=int)
        parser.add_argument("--id", type=int)
        parser.add_argument("--all", action="store_true")

    def do(self, *args, **kwargs):
        qs = Tx.objects.all()
        if kwargs["id"]:
            qs = qs.filter(id=kwargs["id"])
        elif kwargs["last_id"] and kwargs["begin_id"]:
            qs = qs.filter(id__gte=kwargs["begin_id"], id__lte=kwargs["last_id"])
        elif kwargs["all"]:
            if not settings.DEBUG:
                print("--all not available in production")
        else:
            print("Range not defined, see --help")
            return

        for obj in qs.distinct():
            logger.warning("Deleting %s", obj.__dict__)
        res = qs.delete()
        logger.warning("Deleted %s", res)
