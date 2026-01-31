import heapq
import logging
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Tuple, Sequence
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.timezone import now
from django.utils.translation import gettext as _
from jutil.format import dec2
from jstocks.models import ShareType, Shares, Tx, ShareSeq, Party, JournalEntry, ShareTransfer, ShareAllocation
from jstocks.seq import Seq, format_seqs, split_seq, merge_seqs
from jutil.admin import admin_log

logger = logging.getLogger(__name__)


def debit_tx(  # pylint: disable=too-many-arguments
    entry: JournalEntry,
    owner: Party,
    account: str,
    amount: Optional[Decimal] = None,
    count: Optional[int] = None,
    share_type: Optional[ShareType] = None,
    commit: bool = True,
) -> Tx:
    if amount is not None:
        if amount < Decimal("0.00"):
            raise ValidationError({"amount": _("Value cannot be negative.")})
        amount = dec2(amount)
    if count is not None:
        if count < 0:
            raise ValidationError({"count": _("Value cannot be negative.")})
    tx = Tx(entry=entry, share_type=share_type, owner=owner, account=account, amount=amount, count=count)
    tx.full_clean()
    if commit:
        tx.save()
    return tx


def credit_tx(  # pylint: disable=too-many-arguments
    entry: JournalEntry,
    owner: Party,
    account: str,
    amount: Optional[Decimal] = None,
    count: Optional[int] = None,
    share_type: Optional[ShareType] = None,
    commit: bool = True,
) -> Tx:
    if amount is not None:
        if amount < Decimal("0.00"):
            raise ValidationError({"amount": _("Value cannot be negative.")})
        amount = -dec2(amount)
    if count is not None:
        assert isinstance(count, int)
        if count < 0:
            raise ValidationError({"count": _("Value cannot be negative.")})
        count = -count  # pylint: disable=invalid-unary-operand-type
    tx = Tx(entry=entry, share_type=share_type, owner=owner, account=account, amount=amount, count=count)
    tx.full_clean()
    if commit:
        tx.save()
    return tx


@transaction.atomic
def allocate_shares(  # pylint: disable=too-many-arguments,too-many-locals
    owner: Party,
    shares: Shares,
    begin: int,
    end: int,
    amount: Optional[Decimal],
    timestamp: datetime,
    parent: Optional[JournalEntry] = None,
    description: str = "",
) -> List[Tx]:
    """Allocate shares to owner.
    Debit tx to user's stock account.
    Credit tx to user's cash account.
    Returns [debit, credit] transactions list.
    """
    logger.info("allocate_shares(%s, %s, %s, %s, %s, %s)", owner, shares, begin, end, amount, timestamp)
    count = end - begin
    last = end - 1
    share_type = shares.share_type
    issuer = shares.issuer

    # journal entry
    msg = "{action} {share_type} {begin}-{last}".format(share_type=share_type.name, action=description or _("share allocation"), begin=begin, last=last)
    entry = JournalEntry(description=msg, timestamp=timestamp, parent=parent)
    entry.full_clean()
    entry.save()

    # share #s related to entry
    ss = ShareSeq(entry=entry, shares=shares, begin=begin, last=last)
    ss.full_clean()
    ss.save()

    # debit tx to user's stock account
    txs: List[Tx] = []
    tx = debit_tx(entry, owner, Tx.ACC_STOCK, None, count, share_type)
    txs.append(tx)

    # credit issuer's stock account
    tx = credit_tx(entry, issuer, Tx.ACC_STOCK, None, count, share_type)
    txs.append(tx)

    if amount is not None and amount != Decimal("0.00"):
        # credit tx to user's cash account
        tx = credit_tx(entry, owner, Tx.ACC_CASH, amount, None, None)
        txs.append(tx)

        # debit tx to issuer's cash account
        tx = debit_tx(entry, issuer, Tx.ACC_CASH, amount, None, None)
        txs.append(tx)

    # update (cached) owned_share_count
    owner.refresh_owned_share_count()
    return txs


@transaction.atomic
def authorize_and_allocate_shares(  # pylint: disable=too-many-arguments
    owner: Party,
    share_type: ShareType,
    count: int,
    amount: Decimal,
    timestamp: datetime,
    issuing_identifier: Optional[int] = 0,
    begin: Optional[int] = None,
    description: str = "",
) -> Tuple[Shares, List[Tx]]:
    """Authorize and allocate shares to owner.
    Debit tx to user's stock account.
    Credit tx to user's cash account.
    Returns authorized shares and [debit, credit] transactions list.
    """
    logger.info(
        "issue_shares(%s, %s, %s, %s, %s, %s, %s)",
        owner,
        share_type,
        count,
        amount,
        timestamp,
        issuing_identifier,
        begin,
    )

    # issue shares
    issuer = share_type.issuer
    if issuing_identifier is None:
        issuing_identifier = Shares.objects.get_next_identifier(issuer)
    if begin is None:
        begin = Shares.objects.get_next_share_number(issuer)
    end = begin + count
    last = end - 1
    logger.info("%s %s %s-shares shares at %s", count, share_type.issuer, share_type.identifier, timestamp.date())
    shares = Shares(share_type=share_type, begin=begin, last=last, timestamp=timestamp, identifier=issuing_identifier)
    shares.full_clean()
    shares.save()

    tx_list = allocate_shares(owner, shares, begin, end, amount, timestamp, description=description)
    return shares, tx_list


@transaction.atomic
def transfer_shares(  # pylint: disable=too-many-locals,too-many-arguments
    seller: Party,
    buyer: Party,
    share_type: ShareType,
    seq_list: Sequence[Seq],
    amount: Optional[Decimal],
    timestamp: datetime,
    msg: str = "",
) -> List[Tx]:
    logger.info("transfer_shares(%s, %s, %s, %s, %s, %s)", seller, buyer, share_type, seq_list, amount, timestamp)

    # validate
    if amount is None:
        amount = Decimal("0.00")
    count = sum(s.count for s in seq_list)  #
    if count <= 0:
        raise ValidationError(_("Nothing to transfer"))
    for seq in seq_list:
        if not isinstance(seq.parent, Shares):
            raise ValueError(_("Sequence parent field is assumed to be AuthorizedShares instance"))

    # list current share sequences
    sharelist = merge_seqs(list_shares(seller, share_type, timestamp))
    logger.info("Seller %s owns following shares: %s", seller, sharelist)
    if Seq.sum_count(sharelist) < count:
        raise ValidationError(_("Not enough {share_type} shares").format(share_type=share_type))

    # journal entry
    if not msg:
        msg = "{action} {share_type} x{count}".format(share_type=share_type.name, action=_("share transfer"), count=Seq.sum_count(seq_list))
    entry = JournalEntry(description=msg, timestamp=timestamp)
    entry.full_clean()
    entry.save()

    txs: List[Tx] = []
    if amount:
        # debit tx to user's cash account
        tx = debit_tx(entry, seller, Tx.ACC_CASH, amount, None, None)
        txs.append(tx)

        # credit tx to issuer's cash account
        tx = credit_tx(entry, buyer, Tx.ACC_CASH, amount, None, None)
        txs.append(tx)

    # credit tx to user's stock account
    tx = credit_tx(entry, seller, Tx.ACC_STOCK, None, count, share_type)
    txs.append(tx)

    # debit tx to issuer's stock account
    tx = debit_tx(entry, buyer, Tx.ACC_STOCK, None, count, share_type)
    txs.append(tx)

    # share # related to entry
    for seq in seq_list:
        shares = seq.parent
        if not isinstance(shares, Shares):
            raise ValueError("Seq.parent is assumed to be AuthorizedShares type by buy_back_shares_by_seq_list()")
        found = False
        for owned_seq in sharelist:
            if owned_seq.contains_seq(seq):
                found = True
                break
        if not found:
            raise ValueError("Tried to sell shares {} but user does not own specified shares".format(seq))
        ss = ShareSeq(entry=entry, shares=shares, begin=seq.begin, last=seq.last)
        ss.full_clean()
        ss.save()

    # update (cached) owned_share_count
    seller.refresh_owned_share_count()
    buyer.refresh_owned_share_count()
    return txs


@transaction.atomic
def execute_share_transfer(obj: ShareTransfer):
    if obj.record_date:
        raise ValidationError(_("help.text.recorded.share.transfers.cannot.be.modified"))

    obj.full_clean()
    share_type = obj.share_type
    seqs = list_shares_fifo(obj.seller, share_type, obj.count, obj.timestamp)
    logger.info("%s list_shares_fifo: %s", obj, seqs)
    txs = transfer_shares(obj.seller, obj.buyer, share_type, seqs, obj.price, obj.timestamp)

    obj.record_date = now()
    obj.entry = txs[0].entry
    obj.save()
    admin_log([obj], "Share transfer executed: {}".format(format_seqs(seqs)))


@transaction.atomic
def execute_share_allocation(obj: ShareAllocation, parent_entry: Optional[JournalEntry] = None):
    if obj.record_date:
        raise ValidationError(_("help.text.recorded.share.transfers.cannot.be.modified"))

    obj.full_clean()
    txs = allocate_shares(obj.subscriber, obj.shares, obj.begin, obj.end, obj.price, obj.timestamp, parent=parent_entry)  # type: ignore

    obj.record_date = now()
    obj.entry = txs[0].entry
    obj.save()
    admin_log([obj], "Share allocation executed")


def list_shares(owner: Party, share_type: ShareType, timestamp: Optional[datetime] = None) -> List[Seq]:
    """List current shares after executing all transactions in the queryset."""
    if timestamp is None:
        timestamp = now()
    txs = Tx.objects.filter(owner=owner, share_type=share_type, account=Tx.ACC_STOCK, timestamp__lte=timestamp)
    shares: List[Seq] = []
    for tx in txs.order_by("timestamp", "id"):
        assert isinstance(tx, Tx)
        assert tx.count is not None
        if tx.count > 0:
            for seq in tx.seqs:
                heapq.heappush(shares, seq)
        elif tx.count < 0:
            left = -tx.count
            while left > 0:
                # no shares left, so we have negative balance on shares
                if not shares:
                    return []
                owned_seq = heapq.heappop(shares)
                assert isinstance(owned_seq, Seq)
                n = min(left, owned_seq.count)
                sold_seq = Seq(owned_seq.begin, owned_seq.begin + n, owned_seq.parent)
                for rem_seq in split_seq(owned_seq, sold_seq):
                    heapq.heappush(shares, rem_seq)
                left -= n
    return shares


def get_share_count(owner: Party, share_type: ShareType, timestamp: Optional[datetime] = None, timestamp_gte: Optional[datetime] = None) -> int:
    if timestamp is None:
        timestamp = now()
    qs = Tx.objects.filter(owner=owner, account=Tx.ACC_STOCK, share_type=share_type, timestamp__lte=timestamp)
    if timestamp_gte is not None:
        qs = qs.filter(timestamp__gte=timestamp_gte)
    return Tx.objects.sum_count(qs)  # type: ignore


def get_share_list(share_type: ShareType, begin: int, end: int) -> List[Seq]:
    """Returns shares share sequences by share type and [begin, end) range.
    AuthorizedShares instance is returned in parent field of the Seq-objects.
    """
    sub = Seq(begin, end)
    out: List[Seq] = []
    for shares in list(Shares.objects.filter(share_type=share_type).order_by("begin")):
        assert isinstance(shares, Shares)
        sec = shares.seq & sub
        if sec.count > 0:
            sec.parent = shares
            out.append(sec)
    return sorted(out)


def get_next_share_journal_entry(entry: JournalEntry, shares: Shares, share_num: int) -> Optional[JournalEntry]:
    return (
        JournalEntry.objects.filter(
            timestamp__gte=entry.timestamp,
            id__gt=entry.id,
            seq_set__shares=shares,
            seq_set__begin__lte=share_num,
            seq_set__last__gte=share_num,
        )
        .order_by("timestamp", "id")
        .first()
    )


def list_shares_fifo(owner: Party, share_type: ShareType, count: int, timestamp: Optional[datetime] = None) -> List[Seq]:
    """Lists n first shares (as sequences)."""
    sharelist = list_shares(owner, share_type, timestamp)
    fifo: List[Seq] = []
    left = count
    while left > 0:
        if not sharelist:
            raise ValidationError(_("Not enough {share_type} shares").format(share_type=share_type))
        owned_seq = heapq.heappop(sharelist)
        assert isinstance(owned_seq, Seq)
        n = min(left, owned_seq.count)
        sold_seq = Seq(owned_seq.begin, owned_seq.begin + n, owned_seq.parent)
        fifo.append(sold_seq)
        for rem_seq in split_seq(owned_seq, sold_seq):
            assert isinstance(rem_seq, Seq)
            heapq.heappush(sharelist, rem_seq)
        left -= n
    return merge_seqs(fifo)


def list_share_types(owner: Party) -> List[ShareType]:
    """Lists all share types owned (currently or before) by this owner."""
    qs = Tx.objects.filter(owner=owner, account=Tx.ACC_STOCK, count__gt=0).exclude(share_type=None)
    qs = qs.order_by("share_type").distinct("share_type")
    return [e.share_type for e in list(qs)]  # type: ignore
