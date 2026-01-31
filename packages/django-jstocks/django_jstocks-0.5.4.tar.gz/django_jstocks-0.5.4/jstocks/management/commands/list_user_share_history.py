from datetime import date
from decimal import Decimal
from typing import Optional
from django.core.management.base import CommandParser
from jutil.command import SafeCommand
from jstocks.models import Tx, ShareSeq, Party, JournalEntry
from jstocks.services import get_next_share_journal_entry


class Command(SafeCommand):
    def add_arguments(self, parser: CommandParser):
        parser.add_argument("owner", type=str)
        parser.add_argument("--max-lines", type=int)

    def do(self, *args, **kwargs):  # pylint: disable=too-many-locals
        stdout = self.stdout
        owner = Party.objects.all().get(email=kwargs["owner"])
        assert isinstance(owner, Party)

        # list shares all time
        # note: same share can appear in tx history multiple times (buy/sell/buy/sell) so we need to keep track of that
        stdout.write("issuer,share_type,investment_id,stock_number,amount,issue_date,sold_date,state,username" + "\n")

        qs = JournalEntry.objects.all().filter(tx_set__owner=owner)
        lines = 0
        processed = set()
        for je in qs.order_by("timestamp", "seq_set__begin"):
            assert isinstance(je, JournalEntry)
            if je.id in processed:
                continue
            processed.add(je.id)
            if not je.tx_set.filter(account=Tx.ACC_STOCK, owner=owner, count__gt=0).exists():
                continue
            for ss in je.seq_set.all().order_by("begin"):
                assert isinstance(ss, ShareSeq)
                shares = ss.shares
                order_id = ss.shares.identifier
                for share_num in ss.seq:
                    share_id = "{}0000{}".format(order_id, share_num - shares.begin + 1)

                    sold_date: Optional[date] = None
                    share_state = "active"
                    e1 = get_next_share_journal_entry(ss.entry, ss.shares, share_num)
                    if e1 is not None:
                        share_state = "sold"
                        sold_date = e1.timestamp.date()

                    vals = [
                        shares.issuer.org_name,
                        shares.share_type.identifier,
                        order_id,
                        share_id,
                        Decimal("500.00"),
                        shares.timestamp.date(),
                        sold_date or "",
                        share_state,
                    ]
                    stdout.write(",".join([str(v) for v in vals]) + "\n")
                    lines += 1
                    if kwargs["max_lines"] and lines >= kwargs["max_lines"]:
                        return
