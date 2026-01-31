import logging
from datetime import timedelta
from decimal import Decimal
from typing import Optional, List, Any
from django.contrib import admin, messages  # noqa
from django.contrib.admin.options import TabularInline
from django.contrib.auth.models import User
from django.db.models import QuerySet
from django.db.models.aggregates import Sum
from django.http.request import HttpRequest
from django.shortcuts import redirect
from django.urls import ResolverMatch, path
from django.utils.formats import date_format, number_format, localize
from django.utils.html import format_html
from django.utils.text import capfirst
from jutil.format import capfirst_lazy
from django.utils.translation import gettext_lazy as _
from jutil.admin import (
    ModelAdminBase,
    admin_obj_link,
    admin_obj_url,
    InlineModelAdminParentAccessMixin,
)
from jutil.auth import get_auth_user_or_none
from jstocks.models import (
    Issuer,
    ShareType,
    Shares,
    Tx,
    ShareTransfer,
    Party,
    OwnedStock,
    ShareTransferAttachment,
    ShareAllocationAttachment,
    ShareAllocation,
    JournalEntry,
)
from jstocks.seq import format_seqs, merge_seqs, Seq
from jstocks.services import list_shares_fifo, execute_share_transfer, execute_share_allocation

logger = logging.getLogger(__name__)


class JStocksAdminBase(ModelAdminBase):
    save_on_top = False
    ordering = ("-created",)

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """
        By default, returns empty queryset for normal is_staff user.
        Access filter can be configured using issuer_staff_user_filter.
        For is_superuser, whole queryset is returned.
        """
        user = request.user
        qs = super().get_queryset(request)
        if user.is_authenticated and user.is_staff:
            if user.is_superuser:
                return qs
        return qs.none()


class IssuerAdmin(JStocksAdminBase):
    ordering = ("org_name",)
    fields = [
        "org_name",
        "org_id",
        "email",
        "phone",
        "address",
        "city",
        "zip_code",
        "country",
        "notes",
        "created",
        "last_modified",
        "id",
    ]
    readonly_fields = [
        "id",
        "created",
        "last_modified",
    ]
    list_display = (
        "org_name",
        "org_id",
        "country",
    )

    def save_model(self, request, obj, form, change):
        assert isinstance(request, HttpRequest)
        assert isinstance(obj, Issuer)
        user = request.user
        assert isinstance(user, User)
        if not change:
            obj.party_type = Issuer.PARTY_ORG
            obj.created_by = user
        obj.save()


class OwnedStockInlineAdmin(TabularInline, InlineModelAdminParentAccessMixin):
    model = OwnedStock
    fk_name = "owner"
    fields = [
        "owner_since",
        "issuer_name",
        "share_type_name",
        "share_count",
    ]
    readonly_fields = fields
    extra = 0
    can_delete = False

    def get_owner(self, request: HttpRequest) -> Optional[Party]:
        owner = self.get_parent_object(request)
        assert owner is None or isinstance(owner, Party)
        return owner

    def has_add_permission(self, request, obj=None):
        return False

    def owner_since(self, obj):
        assert isinstance(obj, OwnedStock)
        owner, share_type = obj.owner, obj.share_type
        t = Tx.objects.filter(owner=owner, account=Tx.ACC_STOCK, share_type=share_type).order_by("timestamp").first()
        assert t is None or isinstance(t, Tx)
        return localize(t.timestamp.date()) if t else ""

    owner_since.short_description = _("owner since")  # type: ignore

    def share_count(self, obj):
        assert isinstance(obj, OwnedStock)
        owner, share_type = obj.owner, obj.share_type
        n = Tx.objects.sum_count(Tx.objects.filter(owner=owner, share_type=share_type, account=Tx.ACC_STOCK))
        return localize(n)

    share_count.short_description = _("count")  # type: ignore

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        owner = self.get_owner(request)
        if owner is None:
            return OwnedStock.objects.none()
        return OwnedStock.objects.filter_distinct_share_type(owner)


class PartyAdmin(JStocksAdminBase):
    ordering = ("name",)
    inlines = (OwnedStockInlineAdmin,)
    raw_id_fields = ("user",)
    fields = [
        "user",
        "party_type",
        "first_name",
        "last_name",
        "ssn",
        "org_name",
        "org_id",
        "email",
        "phone",
        "address",
        "city",
        "zip_code",
        "country",
        "notes",
        "created",
        "last_modified",
        "id",
        "shares",
    ]
    list_display = (
        "name_link",
        "email",
        "phone",
        "user_link",
        "user_is_staff",
        "shares",
    )
    readonly_fields = (
        "id",
        "name",
        "created",
        "last_modified",
        "shares",
        "user_link",
    )
    list_filter = (
        "party_type",
        "user__is_staff",
    )
    search_fields = (
        "name__icontains",
        "=user__email",
        "=user__username",
        "ssn_masked__startswith",
    )

    def name_link(self, obj):
        assert isinstance(obj, Party)
        return obj.get_name()

    name_link.short_description = _("name")  # type: ignore
    name_link.admin_order_field = ""  # type: ignore

    def user_link(self, obj):
        return admin_obj_link(obj.user) if obj.user else ""

    user_link.short_description = _("user")  # type: ignore
    user_link.admin_order_field = "user"  # type: ignore

    def shares(self, owner):
        assert isinstance(owner, Party)
        if owner.owned_share_count is None:
            return ""
        return localize(owner.owned_share_count)

    shares.short_description = _("shares")  # type: ignore

    def change_view(self, request, object_id, form_url="", extra_context=None):
        issuer = Issuer.objects.filter(pk=object_id).first()
        if issuer:
            return redirect(admin_obj_url(issuer))
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def user_is_staff(self, obj: Party) -> bool:
        return obj.user.is_staff if obj.user else False

    user_is_staff.boolean = True  # type: ignore
    user_is_staff.short_description = _("staff status")  # type: ignore

    def user_is_superuser(self, obj: Party) -> bool:
        return obj.user.is_superuser if obj.user else False

    user_is_superuser.boolean = True  # type: ignore
    user_is_superuser.short_description = _("superuser status")  # type: ignore


class StockTypeAdmin(JStocksAdminBase):
    exclude = ()
    ordering = ("identifier",)
    fields = (
        "name",
        "identifier",
        "issuer",
        "notes",
        "created",
        "last_modified",
        "id",
    )
    readonly_fields = (
        "created",
        "last_modified",
        "id",
    )
    list_display = (
        "name",
        "identifier",
        "issuer_link",
    )
    raw_id_fields = ()
    list_filter = ("issuer",)

    def issuer_link(self, obj: Party) -> str:
        return admin_obj_link(obj.issuer)

    issuer_link.short_description, issuer_link.admin_order_field = _("issuer"), "issuer"  # type: ignore


class AuthorizedSharesAdmin(JStocksAdminBase):
    ordering = (
        "share_type",
        "begin",
    )  # type: ignore
    fields = (
        "share_type",
        "begin",
        "last",
        "count_str",
        "timestamp",
        "identifier",
        "notes",
    )
    list_display = (
        "timestamp",
        "issuer_link",
        "share_type_link",
        "begin",
        "last",
        "count_str",
    )
    raw_id_fields = ()
    readonly_fields = (
        "share_type_link",
        "issuer_link",
        "count_str",
    )
    list_filter = (
        "share_type",
        "share_type__issuer",
    )

    def share_type_link(self, obj: Shares):
        return admin_obj_link(obj.share_type, label=obj.share_type.name)

    share_type_link.short_description = _("share")  # type: ignore

    def issuer_link(self, obj: Shares):
        return admin_obj_link(obj.share_type.issuer)

    issuer_link.short_description = _("issuer")  # type: ignore


def summarize_txs(modeladmin, request, qs):  # pylint: disable=unused-argument
    res_dr_amount = qs.filter(amount__gt=0).aggregate(a=Sum("amount"), c=Sum("count"))
    res_cr_amount = qs.filter(amount__lt=0).aggregate(a=Sum("amount"), c=Sum("count"))
    res_dr_count = qs.filter(count__gt=0).aggregate(a=Sum("amount"), c=Sum("count"))
    res_cr_count = qs.filter(count__lt=0).aggregate(a=Sum("amount"), c=Sum("count"))
    res_sum = qs.aggregate(a=Sum("amount"), c=Sum("count"))
    dr_label = _("debit.tx")
    cr_label = _("credit.tx")
    html = format_html(
        "{}: {} {} {} {} = {}<br/>{}: {} {} {} {} = {}",
        _("amount"),
        number_format(res_dr_amount["a"] or Decimal("0.00"), force_grouping=True),
        dr_label,
        number_format(res_cr_amount["a"] or Decimal("0.00"), force_grouping=True),
        cr_label,
        number_format(res_sum["a"] or Decimal("0.00"), force_grouping=True),
        capfirst(_("count")),
        number_format(res_dr_count["c"] or 0, force_grouping=True),
        dr_label,
        number_format(res_cr_count["c"] or 0, force_grouping=True),
        cr_label,
        number_format(res_sum["c"] or 0, force_grouping=True),
    )
    messages.info(request, html)


class TxInlineAdmin(TabularInline):
    model = Tx
    extra = 0
    fields = [
        "timestamp_link",
        "description",
        "share_type",
        "owner_link",
        "account",
        "count_str",
        "amount_str",
    ]
    readonly_fields = fields

    def owner_link(self, obj):
        assert isinstance(obj, Tx)
        return admin_obj_link(obj.owner)

    owner_link.short_description = _("owner")  # type: ignore
    owner_link.admin_order_field = "order"  # type: ignore

    def timestamp_link(self, obj):
        assert isinstance(obj, Tx)
        return admin_obj_link(obj, label=localize(obj.timestamp))

    timestamp_link.short_description = _("timestamp")  # type: ignore
    timestamp_link.admin_order_field = "timestamp"  # type: ignore

    def count_str(self, obj) -> str:
        assert isinstance(obj, Tx)
        return number_format(obj.count, force_grouping=True) if obj.count is not None else ""

    count_str.short_description = _("count")  # type: ignore
    count_str.admin_order_field = "count"  # type: ignore

    def amount_str(self, obj) -> str:
        assert isinstance(obj, Tx)
        return number_format(obj.amount, force_grouping=True) if obj.amount is not None else ""

    amount_str.short_description = _("amount")  # type: ignore
    amount_str.admin_order_field = "amount"  # type: ignore


class JournalEntryAdmin(JStocksAdminBase):
    date_hierarchy = "timestamp"
    inlines = [
        TxInlineAdmin,
    ]
    search_fields = [
        "description",
    ]
    fields = [
        "id",
        "description",
        "timestamp",
        "created",
        "last_modified",
        "parent_link",
    ]
    readonly_fields = [
        "id",
        "description",
        "created",
        "last_modified",
        "parent_link",
    ]
    list_display = [
        "id",
        "timestamp",
        "description",
        "parent_link",
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        user = get_auth_user_or_none(request)
        return user and user.is_superuser and super().has_delete_permission(request, obj)

    def parent_link(self, obj):
        assert isinstance(obj, JournalEntry)
        return admin_obj_link(obj.parent) if obj.parent else ""

    parent_link.short_description = _("parent journal entry")  # type: ignore
    parent_link.admin_order_field = "parent"  # type: ignore


class TxAdmin(JStocksAdminBase):
    ordering = ("-timestamp", "-id")  # type: ignore
    date_hierarchy = "timestamp"
    actions: List[Any] = [
        summarize_txs,
    ]
    inlines: List[Any] = []
    list_display = [
        "timestamp_date",
        "description",
        "share_type",
        "owner_link",
        "account",
        "count_str",
        "amount_str",
    ]
    raw_id_fields: List[str] = []
    fields = [
        "id",
        "journal_entry",
        "description",
        "share_type",
        "owner_link",
        "account",
        "count_str",
        "amount",
        "timestamp",
        "sequences",
    ]
    readonly_fields = [
        "id",
        "journal_entry",
        "description",
        "share_type",
        "owner_link",
        "account",
        "count_str",
        "sequences",
    ]
    list_filter = [
        "account",
        "share_type",
        "share_type__issuer",
    ]
    search_fields = [
        "owner__name",
        "=owner__email",
    ]

    def get_list_display(self, request):
        rm = request.resolver_match
        assert isinstance(rm, ResolverMatch)
        owner_filter = "owner_pk" in rm.kwargs
        account_filter = request.GET.get("account__exact") or ""
        if owner_filter and account_filter == Tx.ACC_STOCK:
            return self.list_display[:-2] + ["count", "total"]
        if owner_filter and account_filter in [Tx.ACC_CASH, Tx.ACC_DIVIDEND]:
            return self.list_display[:-2] + ["amount", "balance"]
        return self.list_display

    def owner_link(self, obj) -> str:
        assert isinstance(obj, Tx)
        return admin_obj_link(obj.owner)

    owner_link.short_description = _("owner")  # type: ignore
    owner_link.admin_order_field = "order"  # type: ignore

    def journal_entry(self, obj) -> str:
        assert isinstance(obj, Tx)
        return admin_obj_link(obj.entry.root)

    journal_entry.short_description = _("journal entry")  # type: ignore
    journal_entry.admin_order_field = "entry"  # type: ignore

    def sequences(self, obj) -> str:
        assert isinstance(obj, Tx)
        return format_seqs(merge_seqs(obj.entry.seqs))

    sequences.short_description = _("share sequences")  # type: ignore

    def count_str(self, obj) -> str:
        assert isinstance(obj, Tx)
        return number_format(obj.count, force_grouping=True) if obj.count is not None else ""

    count_str.short_description = _("count")  # type: ignore
    count_str.admin_order_field = "count"  # type: ignore

    def amount_str(self, obj) -> str:
        assert isinstance(obj, Tx)
        return number_format(obj.amount, force_grouping=True) if obj.amount is not None else ""

    amount_str.short_description = _("amount")  # type: ignore
    amount_str.admin_order_field = "amount"  # type: ignore

    def timestamp_date(self, obj) -> str:
        assert isinstance(obj, Tx)
        return date_format(obj.timestamp.date(), "SHORT_DATE_FORMAT")

    timestamp_date.short_description = _("timestamp")  # type: ignore
    timestamp_date.admin_order_field = "timestamp"  # type: ignore

    def has_add_permission(self, request) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return request.user.is_superuser

    def get_queryset(self, request) -> QuerySet:
        assert isinstance(request, HttpRequest)
        rm = request.resolver_match
        assert isinstance(rm, ResolverMatch)
        qs = super().get_queryset(request)
        owner_pk = rm.kwargs.get("owner_pk", None)
        if owner_pk is not None:
            qs = qs.filter(owner_id=owner_pk)
        return qs

    def get_urls(self):
        app, model = self.model._meta.app_label, self.model._meta.model_name  # type: ignore
        return [
            path(
                "by-owner/<path:owner_pk>/",
                self.admin_site.admin_view(self.kw_changelist_view),
                name="{}_{}_party_changelist".format(app, model),
            ),
        ] + super().get_urls()


class ShareTransferAttachmentInlineAdmin(TabularInline):
    model = ShareTransferAttachment
    fields = ["file"]


def admin_record_share_transfer(modelsadmin, request, queryset):  # pylint: disable=unused-argument
    try:
        for obj in queryset:
            assert isinstance(obj, ShareAllocation)
            execute_share_transfer(obj)
    except Exception as e:
        messages.error(request, str(e))


class ShareOwnershipChangeAdmin(JStocksAdminBase):
    date_hierarchy = "timestamp"
    fields_recorded: List[str] = []

    editable_recorded_fields = [
        "notes",
        "unit_price",
        "price",
        "timestamp",
    ]

    def is_recorded(self, obj):
        assert isinstance(obj, (ShareTransfer, ShareAllocation))
        return obj.record_date is not None

    is_recorded.short_description = _("recorded")  # type: ignore
    is_recorded.admin_order_field = "record_date"  # type: ignore
    is_recorded.boolean = True  # type: ignore

    def count_str(self, obj) -> str:
        assert isinstance(obj, (ShareTransfer, ShareAllocation))
        return number_format(obj.count, force_grouping=True) if obj.count is not None else ""

    count_str.short_description = _("count")  # type: ignore

    def timestamp_date(self, obj) -> str:
        assert isinstance(obj, (ShareTransfer, ShareAllocation))
        return date_format(obj.timestamp.date(), "SHORT_DATE_FORMAT")

    timestamp_date.short_description = _("date")  # type: ignore
    timestamp_date.admin_order_field = "timestamp"  # type: ignore

    def entry_link(self, obj):
        assert isinstance(obj, (ShareTransfer, ShareAllocation))
        return admin_obj_link(obj.entry)

    entry_link.short_description = _("journal entry")  # type: ignore
    entry_link.admin_order_field = "entry"  # type: ignore

    def get_fields(self, request: HttpRequest, obj=None):
        if obj:
            assert isinstance(obj, (ShareTransfer, ShareAllocation))
            if obj.record_date:
                return self.fields_recorded  # type: ignore
        return self.fields

    def get_readonly_fields(self, request: HttpRequest, obj=None):
        if obj:
            assert isinstance(obj, (ShareTransfer, ShareAllocation))
            if obj.record_date:
                return [k for k in self.get_fields(request, obj) if k not in self.editable_recorded_fields]
        return self.readonly_fields


class ShareTransferAdmin(ShareOwnershipChangeAdmin):  # JStocksAdminBase
    actions = [
        admin_record_share_transfer,
    ]
    inlines = [
        ShareTransferAttachmentInlineAdmin,
    ]
    fields = [
        "timestamp",
        "share_type",
        "seller",
        "buyer",
        "count",
        "begin",
        "last",
        "sequences",
        "unit_price",
        "price",
        "notes",
        "identifier",
        "record_date",
    ]
    fields_recorded = [
        "timestamp",
        "share_type",
        "seller_link",
        "buyer_link",
        "count",
        "sequences",
        "unit_price",
        "price",
        "notes",
        "identifier",
        "record_date",
        "entry_link",
    ]
    raw_id_fields = [
        "seller",
        "buyer",
    ]
    readonly_fields = [
        "count_str",
        "record_date",
        "sequences",
        "entry_link",
    ]
    search_fields = [
        "seller__name",
        "buyer__name",
    ]
    list_display = [
        "identifier",
        "timestamp_date",
        "share_type",
        "seller_link",
        "buyer_link",
        "count_str",
        "price",
        "unit_price",
        "is_recorded",
    ]

    def delete_queryset(self, request: HttpRequest, queryset: QuerySet) -> None:
        for obj in list(queryset.order_by("id").distinct()):
            assert isinstance(obj, ShareTransfer)
            obj.delete()

    def seller_link(self, obj):
        assert isinstance(obj, ShareTransfer)
        return admin_obj_link(obj.seller)

    seller_link.short_description = _("seller")  # type: ignore
    seller_link.admin_order_field = "seller"  # type: ignore

    def buyer_link(self, obj):
        assert isinstance(obj, ShareTransfer)
        return admin_obj_link(obj.buyer)

    buyer_link.short_description = _("buyer")  # type: ignore
    buyer_link.admin_order_field = "buyer"  # type: ignore

    def sequences(self, obj) -> str:
        assert isinstance(obj, ShareTransfer)
        if not obj.record_date:
            return ""
        seqs = list_shares_fifo(obj.seller, obj.share_type, obj.count, obj.timestamp - timedelta(microseconds=1))
        return format_seqs(seqs)

    sequences.short_description = _("share sequences")  # type: ignore


class ShareAllocationAttachmentInlineAdmin(TabularInline):
    model = ShareAllocationAttachment
    fields = ["file"]


def admin_record_share_allocation(modelsadmin, request, queryset):  # pylint: disable=unused-argument
    try:
        for obj in queryset:
            assert isinstance(obj, ShareAllocation)
            execute_share_allocation(obj)
    except Exception as e:
        messages.error(request, str(e))


class ShareAllocationAdmin(ShareOwnershipChangeAdmin):  # JStocksAdminBase
    date_hierarchy = "timestamp"
    actions = [
        admin_record_share_allocation,
    ]
    inlines = [
        ShareAllocationAttachmentInlineAdmin,
    ]
    fields = [
        "timestamp",
        "shares",
        "subscriber",
        "count",
        "begin",
        "last",
        "sequences",
        "unit_price",
        "price",
        "notes",
        "identifier",
        "record_date",
    ]
    fields_recorded = [
        "timestamp",
        "shares",
        "subscriber_link",
        "count",
        "sequences",
        "unit_price",
        "price",
        "notes",
        "identifier",
        "record_date",
        "entry_link",
    ]
    raw_id_fields = [
        "shares",
        "subscriber",
    ]
    readonly_fields = [
        "count_str",
        "record_date",
        "sequences",
        "entry_link",
    ]
    search_fields = [
        "share_type__issuer__name",
        "subscriber__name",
    ]
    list_display = [
        "identifier",
        "timestamp_date",
        "share_type",
        "subscriber_link",
        "count_str",
        "price",
        "unit_price",
        "is_recorded",
    ]

    def sequences(self, obj) -> str:
        assert isinstance(obj, ShareAllocation)
        return format_seqs([Seq(obj.begin, obj.end)]) if obj.begin and obj.end else ""

    sequences.short_description = _("share sequences")  # type: ignore

    def subscriber_link(self, obj):
        assert isinstance(obj, ShareAllocation)
        return admin_obj_link(obj.subscriber)

    subscriber_link.short_description = _("subscriber")  # type: ignore
    subscriber_link.admin_order_field = "subscriber"  # type: ignore


admin_record_share_transfer.short_description = capfirst_lazy(_("record share transfer"))  # type: ignore
admin_record_share_allocation.short_description = capfirst_lazy(_("record share allocation"))  # type: ignore
summarize_txs.short_description = capfirst_lazy(_("summarize transactions"))  # type: ignore

admin.site.register(Tx, TxAdmin)
admin.site.register(Issuer, IssuerAdmin)
admin.site.register(Party, PartyAdmin)
admin.site.register(ShareType, StockTypeAdmin)
admin.site.register(Shares, AuthorizedSharesAdmin)
admin.site.register(ShareTransfer, ShareTransferAdmin)
admin.site.register(ShareAllocation, ShareAllocationAdmin)
admin.site.register(JournalEntry, JournalEntryAdmin)
