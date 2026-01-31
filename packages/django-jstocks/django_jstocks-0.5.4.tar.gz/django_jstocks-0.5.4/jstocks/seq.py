from typing import Tuple, List, Any, Sequence
from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from django.db.models.query_utils import Q
from django.utils.translation import gettext as _


class Seq:
    """Helper class representing sequence [begin, end)."""

    begin: int
    end: int
    parent: Any  # Not used in comparisons

    def __init__(self, begin: int, end: int, parent: Any = None):
        assert isinstance(begin, int)
        assert isinstance(end, int)
        self.begin = begin
        self.end = end
        self.parent = parent

    def __str__(self) -> str:
        return "Seq({}, {})".format(self.begin, self.end)

    def __repr__(self):
        return "Seq({}, {})".format(self.begin, self.end)

    def __iter__(self):
        return iter(range(self.begin, self.end))

    def __getitem__(self, index):
        assert 0 <= index <= 1
        return self.tuple[index]

    def __hash__(self):
        return self.begin

    def __and__(self, other):
        return Seq(max(self.begin, other.begin), min(self.end, other.end), self.parent or other.parent)

    def __or__(self, other):
        return Seq(min(self.begin, other.begin), max(self.end, other.end), self.parent or other.parent)

    def __eq__(self, other) -> bool:
        return self.begin == other.begin and self.end == other.end

    def __ne__(self, other) -> bool:
        return self.begin != other.begin or self.end != other.end

    def __lt__(self, other) -> bool:
        return self.begin < other.begin or self.begin == other.begin and self.end < other.end

    def __gt__(self, other) -> bool:
        return self.begin > other.begin or self.begin == other.begin and self.end > other.end

    def __le__(self, other) -> bool:
        return self.begin < other.begin or self.begin == other.begin and self.end <= other.end

    def __ge__(self, other) -> bool:
        return self.begin > other.begin or self.begin == other.begin and self.end >= other.end

    @property
    def tuple(self) -> Tuple[int, int]:
        return self.begin, self.end

    @property
    def count(self) -> int:
        return self.end - self.begin

    @property
    def last(self) -> int:
        return self.end - 1

    def __contains__(self, item):
        if isinstance(item, Seq):
            return self.contains_seq(item)
        if isinstance(item, int):
            return self.contains_value(item)
        raise ValueError("Seq.__contains__({}) not valid type ({})".format(item, type(item)))

    def contains_seq(self, sub) -> bool:
        """Returns True if this Seq fully contains sub sequence."""
        assert isinstance(sub, Seq)
        return (self & sub) == sub

    def contains_value(self, x: int) -> bool:
        """Returns True if this Seq contains x."""
        assert isinstance(x, int)
        return self.begin <= x < self.end

    @staticmethod
    def sum_count(iterable) -> int:
        """Iterates over Seq objects and returns their summed counts."""
        s = 0
        for e in iterable:
            assert isinstance(e, Seq)
            s += e.count
        return s


def split_seq(parent: Seq, sub: Seq) -> List[Seq]:
    """Splits sub sequence from the parent.
    Returns remaining sequence in parent.
    """
    if not parent.contains_seq(sub):
        raise ValueError("Parent sequence {} must contain sub sequence {} before the split".format(parent, sub))

    out: List[Seq] = []

    # case 1: parent starts before sub
    if parent.begin < sub.begin:
        out.append(Seq(parent.begin, sub.begin, parent.parent))

    # case 2: parent ends after sub
    if parent.end > sub.end:
        out.append(Seq(sub.end, parent.end, parent.parent))

    assert sub.count + Seq.sum_count(out) == parent.count
    return out


def make_seqs(items: Sequence[int], parent: Any = None) -> List[Seq]:
    """Returns list of maximum length sequences from arbitrary list of ints."""
    items = sorted(items)
    seqs: List[Seq] = []
    if items:
        seq = Seq(items[0], items[0] + 1, parent)
        for item in items[1:]:
            assert isinstance(item, int)
            if item == seq.end:
                seq.end += 1
            else:
                seqs.append(seq)
                seq = Seq(item, item + 1, parent)
        seqs.append(seq)
    return seqs


def merge_seqs(seqs: Sequence[Seq]) -> List[Seq]:
    """Returns a new list of sequences with continuous sequences merged together."""
    out: List[Seq] = []
    if seqs:
        seqs = sorted(list(seqs))
        prev: Seq = seqs[0]
        for seq in seqs[1:]:
            if prev.end == seq.begin and prev.parent == seq.parent:  # seq directly after prev?
                prev.end = seq.end
                continue
            if seq.begin <= prev.end < seq.end and prev.parent == seq.parent:  # seq partly within prev?
                prev.end = seq.end
                continue
            if prev.end >= seq.end and prev.parent == seq.parent:  # seq fully within prev?
                continue
            out.append(prev)
            prev = seq
        out.append(prev)
    return out


def parse_seqs(ranges_str: str, parent: Any = None) -> List[Seq]:
    """Parses "4000001-4000120, 4000121-4000130" style list of [first,last] ranges.
    Note that ranges are INCLUSIVE, but Seq() object uses exclusive range end.
    """
    out: List[Seq] = []
    for range_str in ranges_str.split(","):
        r = range_str.split("-")
        if len(r) != 2:
            raise ValidationError(_("Failed to parse sequence range."))
        begin, last = r[0].strip(), r[1].strip()
        out.append(Seq(int(begin), int(last) + 1, parent))
    if not out:
        raise ValidationError(_("Failed to parse sequence range."))
    return out


def format_seqs(seqs: Sequence[Seq]) -> str:
    return ", ".join(["{}-{}".format(seq.begin, seq.last) for seq in seqs])


def filter_seq_overlap(qs: QuerySet, seq: Seq) -> QuerySet:
    b, e = seq.begin, seq.end
    return qs.exclude(Q(begin__gte=e) | Q(last__lt=b))
