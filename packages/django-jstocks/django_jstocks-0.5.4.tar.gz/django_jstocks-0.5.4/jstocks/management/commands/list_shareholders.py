import logging
from typing import Optional
from uuid import UUID
from django.core.management.base import CommandParser
from django.utils.timezone import now
from django.utils.translation import gettext as _
from jutil.command import SafeCommand
from jstocks.models import Party, Issuer
from jstocks.reports import add_report_default_output_options, generate_report_output
from jstocks.seq import merge_seqs
from jstocks.services import list_shares, list_share_types, get_share_count

logger = logging.getLogger(__name__)


class Command(SafeCommand):
    def add_arguments(self, parser: CommandParser):
        parser.add_argument("--owner", type=str)
        parser.add_argument("--issuer-id", type=str)
        add_report_default_output_options(parser)

    def do(self, *args, **kwargs):  # pylint: disable=too-many-locals
        report_time = now()
        owners_qs = Party.objects.all()
        if kwargs["owner"]:
            query = kwargs["owner"]
            owners_qs = owners_qs.filter(id=Party.objects.get_by_search(query).id)
        issuer: Optional[Issuer] = None
        if kwargs["issuer_id"]:
            issuer = Issuer.objects.get(id=UUID(kwargs["issuer_id"]))
        assert issuer is None or isinstance(issuer, Issuer)

        keys = [
            _("name"),
            _("party type"),
            _("email"),
            _("phone number"),
            _("address"),
            _("city"),
            _("zip code"),
            _("country"),
            _("issuer"),
            _("share type"),
            _("share count"),
        ]
        report_name = _("shareholder list")
        rows = []
        total_all_users = 0
        for owner in owners_qs:
            assert isinstance(owner, Party)
            owner.refresh_owned_share_count()
            if owner.owned_share_count == 0:
                continue
            for share_type in list_share_types(owner):
                if issuer and share_type.issuer.id != issuer.id:
                    continue
                share_count = get_share_count(owner, share_type)
                list_shares_count = 0
                for seq in merge_seqs(list_shares(owner, share_type)):
                    list_shares_count += seq.count
                if list_shares_count != share_count:
                    raise Exception("{} (Party id={}) list_shares_count={} vs get_share_count={}".format(owner, owner.id, list_shares_count, share_count))
                total_all_users += share_count
                rows.append(
                    [
                        owner.get_name(),
                        owner.party_type_label,
                        owner.email,
                        owner.phone,
                        owner.address,
                        owner.city,
                        owner.zip_code,
                        owner.country,
                        share_type.issuer.name,
                        share_type.name,
                        share_count,
                    ]
                )

        header = [
            [_("shareholder list").title(), report_time.date()],
            [],
            keys,
        ]
        generate_report_output(report_name, header + rows, **kwargs)
        print("Total {total_all_users} shares".format(total_all_users=total_all_users))
