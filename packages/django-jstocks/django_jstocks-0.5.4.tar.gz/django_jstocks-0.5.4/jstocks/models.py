import logging
from decimal import Decimal
from typing import Optional, Tuple, List
from uuid import uuid1, UUID
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models, transaction  # noqa
from django.db.models import QuerySet
from django.db.models.aggregates import Sum, Max
from django.db.models.query_utils import Q
from django.utils.formats import number_format
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from jutil.modelfields import SafeCharField
from jutil.format import dec2, choices_label, dec4
from jutil.validators import phone_filter

from jstocks.countries import COUNTRY_CHOICES
from jstocks.seq import Seq, filter_seq_overlap
from django_cryptography.fields import encrypt  # type: ignore

logger = logging.getLogger(__name__)


class PartyManager(models.Manager):
    def get_by_search(self, q: str):
        """
        Finds Party instance by trying following:
        1) exact id match
        2) case-insensitive name match
        3) exact email match
        4) exact phone match
        5) case-insensitive last name match
        Raises jstocks.models.Party.DoesNotExist if not found,
        and jstocks.models.Tx.MultipleObjectsReturned if multiple matches.
        """
        for k in ["pk", "name__iexact", "email", "phone", "last_name__iexact"]:
            if k == "pk":
                try:
                    qs = self.filter(pk=UUID(hex=q))
                except ValueError:
                    continue
            else:
                qs = self.filter(**{k: q})
            if qs.count() > 1:
                raise Party.MultipleObjectsReturned("{}={}".format(k, q))
            obj = qs.first()
            if obj is not None:
                return obj
        raise Party.DoesNotExist("{}".format(q))


class Party(models.Model):
    PARTY_PERSON = "I"
    PARTY_ORG = "O"
    PARTY_CHOICES = [
        (PARTY_PERSON, _("person")),
        (PARTY_ORG, _("organization")),
    ]

    objects = PartyManager()
    id = models.UUIDField(_("unique identifier"), primary_key=True, editable=False, default=uuid1)
    party_type = models.CharField(_("party type"), choices=PARTY_CHOICES, default=PARTY_PERSON, max_length=1, blank=True, db_index=True)
    user = models.ForeignKey(
        User,
        verbose_name=_("user"),
        null=True,
        default=None,
        blank=True,
        on_delete=models.PROTECT,
        related_name="party_set",
    )  # noqa
    first_name = SafeCharField(_("first name"), max_length=64, blank=True, db_index=True, help_text=_("if the party is a person"))  # noqa
    last_name = SafeCharField(_("last name"), max_length=64, blank=True, db_index=True, help_text=_("if the party is a person"))  # noqa
    ssn = encrypt(models.CharField(_("person number"), max_length=32, blank=True, default=""))
    ssn_masked = models.CharField(_("person number (masked)"), max_length=32, blank=True, default="", editable=False, db_index=True)
    org_name = SafeCharField(_("organization name"), max_length=64, blank=True, db_index=True, help_text=_("if the party is an organization"))
    org_id = SafeCharField(
        _("organization identifier"),
        max_length=32,
        blank=True,
        db_index=True,
        help_text=_("if the party is an organization"),
    )
    email = models.EmailField(_("email"), blank=True, db_index=True)
    phone = SafeCharField(_("phone number"), blank=True, max_length=32, default="", db_index=True)
    address = SafeCharField(_("address"), max_length=128, blank=True, default="", db_index=True)
    city = SafeCharField(_("city"), max_length=128, blank=True, default="", db_index=True)
    zip_code = SafeCharField(_("zip code"), max_length=32, blank=True, default="", db_index=True)
    country = SafeCharField(_("country"), max_length=2, choices=COUNTRY_CHOICES, blank=True, db_index=True)
    created = models.DateTimeField(_("created"), default=now, db_index=True, editable=False, blank=True)
    last_modified = models.DateTimeField(_("last modified"), auto_now=True, editable=False, blank=True)
    notes = models.TextField(_("notes"), blank=True)
    # cached fields
    name = SafeCharField(_("name"), max_length=128, db_index=True, blank=True, editable=False)
    owned_share_count = models.IntegerField(_("owned shares"), null=True, default=None, blank=True, editable=False, db_index=True)

    class Meta:
        verbose_name = _("party")
        verbose_name_plural = _("parties")
        ordering = ["name"]

    def __str__(self):
        return str(self.get_name())

    @property
    def party_type_label(self) -> str:
        return choices_label(self.PARTY_CHOICES, self.party_type)

    @property
    def is_org(self) -> bool:
        return self.party_type == self.PARTY_ORG

    @property
    def is_person(self) -> bool:
        return self.party_type == self.PARTY_PERSON

    def get_owned_share_count(self) -> int:
        return Tx.objects.filter(owner=self, account=Tx.ACC_STOCK).aggregate(c=Sum("count"))["c"] or 0

    def refresh_owned_share_count(self):
        self.owned_share_count = self.get_owned_share_count()
        self.save(update_fields=["owned_share_count"])

    @property
    def full_name(self) -> str:
        return " ".join([str(self.first_name), str(self.last_name)]).strip()

    def get_name(self) -> str:
        if self.is_org:
            return str(self.org_name)
        name = self.full_name
        if name:
            return name
        if self.is_org:
            raise ValidationError(f"{self} is organization but name missing")
        user = self.user
        if user is not None:
            return str(user.get_full_name())  # type: ignore
        return ""

    def clean(self) -> None:
        self.name = self.get_name()
        if not self.name:
            err_msg = _("This field is required.")
            if self.is_person:
                err = {"first_name": err_msg, "last_name": err_msg}
            else:
                err = {"org_name": err_msg}
            raise ValidationError(err)
        self.phone = phone_filter(self.phone) if self.phone else ""
        self.ssn_masked = self.ssn.split("-")[0] if self.ssn else ""


class Issuer(Party):
    created_by = models.ForeignKey(User, verbose_name=_("created by"), on_delete=models.PROTECT, related_name="+", editable=False)

    class Meta:
        verbose_name = _("issuer")
        verbose_name_plural = _("issuers")

    def clean(self) -> None:
        self.party_type = Party.PARTY_ORG
        return super().clean()


class ShareType(models.Model):
    id = models.UUIDField(_("unique identifier"), primary_key=True, editable=False, default=uuid1)
    issuer = models.ForeignKey(Issuer, verbose_name=_("issuer"), on_delete=models.CASCADE, related_name="stocktype_set")
    name = SafeCharField(_("name"), max_length=64, db_index=True, help_text=_("For example: Series A"))
    identifier = SafeCharField(_("identifier"), max_length=16, db_index=True, help_text=_("For example: A"))
    created = models.DateTimeField(_("created"), default=now, db_index=True, editable=False, blank=True)
    last_modified = models.DateTimeField(_("last modified"), auto_now=True, editable=False, blank=True)
    notes = models.TextField(_("notes"), blank=True)

    class Meta:
        verbose_name = _("share type")
        verbose_name_plural = _("share types")
        constraints = [
            models.UniqueConstraint(fields=["issuer", "identifier"], name="unique_issuer_identifier"),
        ]

    def __str__(self) -> str:
        return "{} ({})".format(self.name, self.issuer)


class SharesManager(models.Manager):
    def get_next_identifier(self, issuer: Issuer) -> int:
        max_value = self.all().filter(share_type__issuer=issuer).aggregate(v=Max("identifier"))["v"] or 0
        return max_value + 1

    def get_next_share_number(self, issuer: Issuer) -> int:
        max_value = self.all().filter(share_type__issuer=issuer).aggregate(v=Max("last"))["v"] or 0
        return max_value + 1


class Shares(models.Model):
    objects = SharesManager()
    share_type = models.ForeignKey(ShareType, verbose_name=_("share type"), related_name="AuthorizedShares_set", on_delete=models.CASCADE)
    identifier = models.BigIntegerField(_("numeric identifier"), blank=True, db_index=True, help_text=_("optional"))
    begin = models.BigIntegerField(_("first share number"), db_index=True)
    last = models.BigIntegerField(_("last share number"), db_index=True)
    timestamp = models.DateTimeField(_("timestamp"), default=now, db_index=True, blank=True)
    created = models.DateTimeField(_("created"), default=now, db_index=True, editable=False, blank=True)
    last_modified = models.DateTimeField(_("last modified"), auto_now=True, editable=False, blank=True)
    notes = models.TextField(_("notes"), blank=True)

    class Meta:
        verbose_name = _("authorized shares")
        verbose_name_plural = _("authorized shares")

    def __str__(self):
        return "{}-{} ({} {})".format(self.begin, self.last, self.share_type.issuer.org_name, self.share_type.name) if self.begin and self.end else ""

    @property
    def seq(self) -> Seq:
        return Seq(self.begin, self.end, self)

    @property
    def end(self) -> int:
        """Returns end (exclusive) of the sequence."""
        return self.last + 1 if self.last else None  # type: ignore

    end.fget.short_description = _("end")  # type: ignore

    @property
    def count(self) -> int:
        return self.end - self.begin if self.begin and self.end else 0  # type: ignore

    count.fget.short_description = _("number of shares")  # type: ignore

    @property
    def count_str(self) -> str:
        return number_format(self.end - self.begin, force_grouping=True) if self.begin and self.end else ""  # type: ignore

    count_str.fget.short_description = _("count")  # type: ignore

    @property
    def issuer(self) -> Issuer:
        return self.share_type.issuer

    issuer.fget.short_description = _("issuer")  # type: ignore

    def clean_identifier(self) -> None:
        if not hasattr(self, "share_type") or not self.share_type:
            return
        issuer = self.issuer
        if not self.identifier:
            self.identifier = Shares.objects.get_next_identifier(issuer)
        qs = Shares.objects.all()
        if hasattr(self, "id") and self.id:
            qs = qs.exclude(id=self.id)
        if issuer and qs.filter(share_type__issuer=issuer, identifier=self.identifier).exists():
            identifier_msg = " ({})".format(self.identifier)
            raise ValidationError({"identifier": _("Stock issuing identifier must be unique") + identifier_msg})

    def clean_seq(self) -> None:
        if not hasattr(self, "share_type") or not self.share_type:
            return
        qs = Shares.objects.filter(share_type=self.share_type)
        if hasattr(self, "id"):
            qs = qs.exclude(id=self.id)
        if filter_seq_overlap(qs, self.seq).exists():
            raise ValidationError(_("Shares in specified numeric range have already been authorized"))

    def clean(self) -> None:
        self.clean_identifier()
        self.clean_seq()


class ShareSeq(models.Model):
    entry = models.ForeignKey("JournalEntry", verbose_name=_("journal entry"), on_delete=models.CASCADE, related_name="seq_set")
    shares = models.ForeignKey(Shares, verbose_name=_("shares"), related_name="shareseq_set", on_delete=models.PROTECT)
    begin = models.BigIntegerField(_("first share number"), db_index=True)
    last = models.BigIntegerField(_("last share number"), db_index=True)

    class Meta:
        verbose_name = _("share sequence")
        verbose_name_plural = _("share sequences")

    def __str__(self):
        return "{}-{}".format(self.begin, self.last) if self.begin and self.end else ""

    @property
    def seq(self) -> Seq:
        assert isinstance(self.begin, int)
        assert isinstance(self.end, int)
        return Seq(self.begin, self.end, self.shares)

    @property
    def end(self) -> int:
        """Returns end (exclusive) of the sequence."""
        return self.last + 1 if self.last else None  # type: ignore

    end.fget.short_description = _("end")  # type: ignore

    @property
    def count(self) -> int:
        return self.end - self.begin if self.begin and self.end else 0  # type: ignore

    count.fget.short_description = _("count")  # type: ignore

    @property
    def count_str(self) -> str:
        return number_format(self.end - self.begin, force_grouping=True) if self.begin and self.end else ""  # type: ignore

    count_str.fget.short_description = _("count")  # type: ignore

    def clean(self):
        if self.seq & self.shares.seq != self.seq:
            raise ValidationError(_("Share sequence cannot exceed authorized shares range"))


class TxManager(models.Manager):
    def sum_amount(self, qs: Optional[QuerySet] = None) -> Decimal:
        if qs is None:
            qs = self  # type: ignore
        return qs.aggregate(a=Sum("amount"))["a"] or Decimal("0.00")  # type: ignore

    def sum_count(self, qs: Optional[QuerySet] = None) -> int:
        if qs is None:
            qs = self  # type: ignore
        return int(qs.aggregate(c=Sum("count"))["c"] or 0)  # type: ignore

    def sum_amount_and_count(self, qs: Optional[QuerySet] = None) -> Tuple[Decimal, int]:
        if qs is None:
            qs = self  # type: ignore
        res = qs.aggregate(a=Sum("amount"), c=Sum("count"))  # type: ignore
        return dec2(res["a"] or "0.00"), int(res["c"] or 0)

    def filter_balance(self, tx) -> QuerySet:
        """Filters all same-owner-same-account txs leading to this tx, including this one."""
        return self.filter(owner=tx.owner, account=tx.account).filter(Q(timestamp__lt=tx.timestamp) | Q(timestamp=tx.timestamp) & Q(id__lte=tx.id))


class Tx(models.Model):
    ACC_STOCK = "S"
    ACC_DIVIDEND = "D"
    ACC_CASH = "C"

    ACC_CHOICES = (
        (ACC_STOCK, _("stock")),
        (ACC_DIVIDEND, _("dividend")),
        (ACC_CASH, _("cash")),
    )
    ACC_TYPES: List[str] = [k for k, label in ACC_CHOICES]  # noqa

    objects = TxManager()
    entry = models.ForeignKey("JournalEntry", verbose_name=_("journal entry"), on_delete=models.CASCADE, related_name="tx_set")
    owner = models.ForeignKey(Party, verbose_name=_("owner"), related_name="tx_set", on_delete=models.PROTECT)
    account = models.CharField(_("account"), choices=ACC_CHOICES, max_length=2, db_index=True)
    amount = models.DecimalField(_("amount"), max_digits=10, decimal_places=2, db_index=True, null=True, default=None, blank=True)
    share_type = models.ForeignKey(
        ShareType,
        verbose_name=_("share type"),
        blank=True,
        default=None,
        null=True,
        related_name="tx_set",
        on_delete=models.CASCADE,
    )  # noqa
    count = models.IntegerField(_("count"), null=True, default=None, blank=True, db_index=True)
    timestamp = models.DateTimeField(_("timestamp"), default=now, db_index=True, blank=True)
    _total: Optional[int]
    _balance: Optional[Decimal]

    class Meta:
        verbose_name = _("transaction")
        verbose_name_plural = _("transactions")

    @property
    def description(self) -> str:
        return self.entry.description

    description.fget.short_description = _("description")  # type: ignore

    @property
    def account_name(self) -> str:
        return choices_label(self.ACC_CHOICES, self.account)

    @property
    def seqs(self) -> List[Seq]:
        return self.entry.seqs

    @property
    def unit_price(self) -> Decimal:
        return dec4(self.amount / Decimal(self.count)) if self.amount and self.count else Decimal("0.00")

    unit_price.fget.short_description = _("unit price")  # type: ignore

    def clean(self) -> None:
        if self.account not in Tx.ACC_TYPES:
            raise ValidationError({"account": _("This field is required.")})
        self.timestamp = self.entry.timestamp
        if self.count is None and self.share_type:
            raise ValidationError({"count": _("This field is required.")})
        if self.count and self.share_type is None:
            raise ValidationError({"share_type": _("This field is required.")})

    def get_balance_and_total_count(self) -> Tuple[Decimal, int]:
        """Returns balance and accumulated share count up to this transaction (including this one)."""
        return Tx.objects.sum_amount_and_count(Tx.objects.filter_balance(self))  # type: ignore

    @property
    def balance(self):
        """Returns sum of amount up to this (including this) transaction."""
        if not hasattr(self, "_balance") or self._balance is None:
            self._balance, self._total = self.get_balance_and_total_count()
        return self._balance

    balance.fget.short_description = _("balance")  # type: ignore

    @property
    def total(self):
        """
        Returns sum of count up to this (including this) transaction.
        """
        if not hasattr(self, "_total") or self._total is None:
            self.balance_amount, self._total = self.get_balance_and_total_count()
        return self._total  # type: ignore

    total.fget.short_description = _("total")  # type: ignore


class JournalEntry(models.Model):
    description = models.CharField(_("description"), max_length=256, blank=True)
    timestamp = models.DateTimeField(_("timestamp"), default=now, db_index=True, blank=True)
    created = models.DateTimeField(_("created"), default=now, db_index=True, editable=False, blank=True)
    last_modified = models.DateTimeField(_("last modified"), auto_now=True, editable=False, blank=True)
    parent = models.ForeignKey(
        "JournalEntry",
        verbose_name=_("parent journal entry"),
        blank=True,
        null=True,
        default=None,
        related_name="child_set",
        on_delete=models.CASCADE,
    )  # noqa

    class Meta:
        verbose_name = _("journal entry")
        verbose_name_plural = _("journal entries")

    def __str__(self):
        return "[{}] {}".format(self.timestamp.date().isoformat() if self.timestamp else "", self.description)

    @property
    def seqs(self) -> List[Seq]:
        return [ss.seq for ss in list(self.seq_set.all().order_by("begin"))]

    @property
    def root(self):
        parent = self.parent
        if parent is None:
            return self
        return parent.root


class OwnedStockManager(models.Manager):
    def filter_distinct_share_type(self, owner: Party) -> QuerySet:
        qs = self.filter(owner=owner, account=OwnedStock.ACC_STOCK).exclude(share_type=None)
        return qs.order_by("share_type").distinct("share_type")


class OwnedStock(Tx):
    objects = OwnedStockManager()  # type: ignore

    class Meta:
        proxy = True
        verbose_name = _("owned stock")
        verbose_name_plural = _("owned stocks")

    @property
    def issuer_name(self) -> str:
        return self.share_type.issuer.name if self.share_type else ""

    issuer_name.fget.short_description = _("issuer")  # type: ignore

    @property
    def share_type_name(self) -> str:
        return self.share_type.name if self.share_type else ""

    share_type_name.fget.short_description = _("share type")  # type: ignore


class ShareOwnershipChangeManager(models.Manager):
    def get_next_identifier(self, issuer: Issuer) -> int:
        max_value = self.all().filter(share_type__issuer=issuer).aggregate(v=Max("identifier"))["v"] or 0
        return max_value + 1


class ShareOwnershipChange(models.Model):
    identifier = models.BigIntegerField(_("numeric identifier"), blank=True, db_index=True, help_text=_("optional"))
    share_type = models.ForeignKey(ShareType, verbose_name=_("share type"), blank=True, related_name="+", on_delete=models.PROTECT)
    count = models.BigIntegerField(_("number of shares"), db_index=True)
    begin = models.BigIntegerField(_("first share number"), db_index=True, blank=True, default=None, null=True)
    last = models.BigIntegerField(_("last share number"), db_index=True, blank=True, default=None, null=True)
    price = models.DecimalField(_("price"), max_digits=10, decimal_places=2, null=True, default=None, blank=True, db_index=True)  # noqa
    unit_price = models.DecimalField(_("unit price"), max_digits=10, decimal_places=4, null=True, default=None, blank=True, db_index=True)  # noqa
    record_date = models.DateTimeField(_("record date"), default=None, null=True, editable=False, db_index=True, blank=True)
    timestamp = models.DateTimeField(_("timestamp"), default=now, db_index=True, blank=True)
    entry = models.ForeignKey(
        "JournalEntry", verbose_name=_("journal entry"), blank=True, default=None, null=True, editable=False, on_delete=models.PROTECT, related_name="+"
    )
    created = models.DateTimeField(_("created"), default=now, db_index=True, editable=False, blank=True)
    last_modified = models.DateTimeField(_("last modified"), auto_now=True, editable=False, blank=True)
    notes = models.TextField(_("notes"), blank=True)

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        logger.info("Deleting %s and %s", self, self.entry)
        with transaction.atomic():
            if self.entry is not None:
                self.entry.delete()
                self.entry = None
                self.save(update_fields=["entry"])
            super().delete(using, keep_parents)

    @property
    def count_str(self) -> str:
        return number_format(self.count, force_grouping=True)

    count_str.fget.short_description = _("number of shares")  # type: ignore

    @property
    def end(self) -> Optional[int]:
        return self.last + 1 if self.last is not None else None

    @property
    def issuer(self) -> Issuer:
        return self.share_type.issuer

    issuer.fget.short_description = _("issuer")  # type: ignore

    def clean_ownership_change(self):
        # make sure all transfers are recorded before adding new ones
        if not hasattr(self, "share_type"):
            return
        qs = ShareTransfer.objects.all()
        if hasattr(self, "id") and self.id:
            qs = qs.exclude(id=self.id)
        rec = qs.filter(share_type=self.share_type, record_date=None).first()
        if rec:
            raise ValidationError(_("Share ownership change {} must be recorded before new transfers are added").format(rec))

        # allow use to set either unit price or total price
        if self.count:
            n = Decimal(self.count)
            if self.unit_price is not None:
                self.price = dec2(self.unit_price * n)
            elif self.price is not None:
                if self.unit_price is None:
                    self.unit_price = dec4(self.price / n)


class ShareTransferAttachment(models.Model):
    context = models.ForeignKey("ShareTransfer", verbose_name=_("context object"), related_name="attachment_set", on_delete=models.CASCADE)
    file = models.FileField(verbose_name=_("file"), upload_to="uploads", blank=True)

    class Meta:
        verbose_name = _("attachment")
        verbose_name_plural = _("attachments")


class ShareTransfer(ShareOwnershipChange):
    objects = ShareOwnershipChangeManager()
    seller = models.ForeignKey(Party, verbose_name=_("seller"), related_name="as_seller", on_delete=models.PROTECT)
    buyer = models.ForeignKey(Party, verbose_name=_("buyer"), related_name="as_buyer", on_delete=models.PROTECT)

    class Meta:
        verbose_name = _("share transfer")
        verbose_name_plural = _("share transfers")
        constraints = [
            models.UniqueConstraint(fields=["share_type", "identifier"], name="unique_sharetransfer_share_type_identifier"),
        ]

    def clean(self) -> None:  # noqa
        from jstocks.services import (  # pylint: disable=cyclic-import,import-outside-toplevel
            get_share_count,
            list_shares,
        )
        from jstocks.services import list_shares_fifo  # pylint: disable=cyclic-import,import-outside-toplevel

        if hasattr(self, "record_date") and self.record_date:
            return
        if not hasattr(self, "seller") or not hasattr(self, "buyer") or not self.seller or not self.buyer:
            return
        if not hasattr(self, "share_type") or not self.share_type:
            return
        if self.timestamp is None:
            self.timestamp = now()

        self.clean_ownership_change()

        # make sure this is the latest transfer for this seller
        latest = ShareTransfer.objects.filter(seller=self.seller).order_by("-timestamp").last()
        if latest:
            assert isinstance(latest, ShareTransfer)
            if latest.timestamp > self.timestamp:
                raise ValidationError(_("Share ownership transfers must be recorded in order"))

        if not self.count:
            raise ValidationError(_("No shares to transfer"))
        list_shares_fifo(self.seller, self.share_type, self.count, self.timestamp)

        if not self.identifier:
            self.identifier = ShareTransfer.objects.get_next_identifier(self.issuer)
        if self.begin is not None and self.last is None:
            raise ValidationError({"last": _("This field is required.")})
        if self.begin is None and self.last is not None:
            raise ValidationError({"begin": _("This field is required.")})
        if hasattr(self, "buyer") and hasattr(self, "share_type"):
            share_type = self.share_type
            assert isinstance(share_type, ShareType)

            if self.seller == self.buyer:
                msg = _("Buyer and seller cannot be the same")
                raise ValidationError({"buyer": msg, "seller": msg})
            if get_share_count(self.seller, share_type, self.timestamp) < self.count:
                msg = _("Not enough {share_type} shares").format(share_type=share_type.name)
                raise ValidationError({"count": msg})

            # find out share numbers (if one sequence)
            if self.begin is None and self.last is None:
                shares = list_shares(self.seller, share_type, self.timestamp)
                seq = shares[0]
                if seq.count >= self.count:
                    self.begin = seq.begin
                    self.last = seq.begin + self.count - 1

            # make sure count matches share numbers
            if self.begin is not None and self.last is not None:
                assert isinstance(self.begin, int)
                assert isinstance(self.end, int)
                if self.begin and self.last and self.last - self.begin + 1 != self.count:
                    msg = _(
                        "Count does not match first and last share numbers. You can also leave first and last share "
                        "numbers empty to automatically figure out share numbers in first-in-first-out order."
                    )
                    raise ValidationError({"begin": msg, "last": msg, "count": msg})


class ShareAllocationAttachment(models.Model):
    context = models.ForeignKey("ShareAllocation", verbose_name=_("context object"), related_name="attachment_set", on_delete=models.CASCADE)
    file = models.FileField(verbose_name=_("file"), upload_to="uploads", blank=True)

    class Meta:
        verbose_name = _("attachment")
        verbose_name_plural = _("attachments")


class ShareAllocation(ShareOwnershipChange):
    objects = ShareOwnershipChangeManager()
    shares = models.ForeignKey(Shares, verbose_name=_("authorized shares"), related_name="allocation_set", on_delete=models.PROTECT)
    subscriber = models.ForeignKey(Party, verbose_name=_("subscriber"), related_name="as_subscriber", on_delete=models.PROTECT)

    class Meta:
        verbose_name = _("share allocation")
        verbose_name_plural = _("share allocations")
        constraints = [
            models.UniqueConstraint(fields=["share_type", "identifier"], name="unique_shareallocation_share_type_identifier"),
        ]

    def clean(self) -> None:
        if hasattr(self, "record_date") and self.record_date:
            return
        if not hasattr(self, "shares") or self.shares is None:
            return
        if self.timestamp is None:
            self.timestamp = now()

        self.share_type = self.shares.share_type
        self.clean_ownership_change()

        if not self.identifier:
            self.identifier = ShareAllocation.objects.get_next_identifier(self.issuer)
        if self.begin is not None and self.last is None:
            raise ValidationError({"last": _("This field is required.")})
        if self.begin is None and self.last is not None:
            raise ValidationError({"begin": _("This field is required.")})

        # make sure this is the latest transfer for this issuer
        latest = ShareAllocation.objects.filter(shares=self.shares).order_by("-timestamp").last()
        if latest:
            assert isinstance(latest, ShareAllocation)
            if latest.timestamp > self.timestamp:
                raise ValidationError(_("Share ownership transfers must be recorded in order"))

        # find out share numbers (if one sequence)
        if self.begin is None and self.last is None:
            last = ShareAllocation.objects.all().filter(shares=self.shares).aggregate(last=Max("last"))["last"] or self.shares.begin - 1
            self.begin = last + 1
            self.last = self.begin + self.count - 1

        # make sure we are within limits of authorized shares
        if Seq(self.begin, self.end) & self.shares.seq != Seq(self.begin, self.end):  # type: ignore
            msg = _("Cannot allocate shares beyond authorized share range")
            raise ValidationError({"begin": msg, "last": msg, "count": msg})

        # make sure count matches share numbers
        if self.begin is not None and self.last is not None:
            assert isinstance(self.begin, int)
            assert isinstance(self.end, int)
            if self.begin and self.last and self.last - self.begin + 1 != self.count:
                msg = _(
                    "Count does not match first and last share numbers. You can also leave first and last share "
                    "numbers empty to automatically figure out share numbers in first-in-first-out order."
                )
                raise ValidationError({"begin": msg, "last": msg, "count": msg})
