import heapq
from typing import Tuple, Dict, Optional, Any
from pprint import pprint
from django.test import TestCase  # pylint: disable=unused-import
from jstocks.models import ShareType, Issuer, Party, Shares
from jstocks.seq import Seq, split_seq, make_seqs, parse_seqs, merge_seqs
from jstocks.services import get_share_list
from jutil.testing import TestSetupMixin


class Tests(TestCase, TestSetupMixin):
    def test_seq_ops(self):
        self.assertEqual(Seq(0, 10).tuple, (0, 10))
        self.assertEqual(Seq(0, 10) & Seq(3, 5), Seq(3, 5))
        self.assertEqual(Seq(3, 5) | Seq(8, 9), Seq(3, 9))

    def test_split_seq(self):
        test_cases = [
            {
                "parent": Seq(0, 100),
                "sub": Seq(0, 50),
                "result": [Seq(50, 100)],
            },
            {
                "parent": Seq(0, 100),
                "sub": Seq(1, 50),
                "result": [Seq(0, 1), Seq(50, 100)],
            },
            {
                "parent": Seq(0, 100),
                "sub": Seq(0, 100),
                "result": [],
            },
            {
                "parent": Seq(0, 100),
                "sub": Seq(99, 100),
                "result": [Seq(0, 99)],
            },
        ]
        for tc in test_cases:
            ref_res = tc["result"]
            res = split_seq(tc["parent"], tc["sub"])
            if ref_res != res:
                print("ref_res:")
                pprint(ref_res)
                print("res:")
                pprint(res)
            self.assertEqual(ref_res, res)

        fails = [
            (Seq(1, 10), Seq(1, 11)),
            (Seq(1, 1), Seq(1, 11)),
        ]
        for parent, sub in fails:
            try:
                split_seq(parent, sub)
                self.fail("split_seq({}, {})".format(parent, sub))
            except ValueError:
                pass

    def test_seq_cmp(self):
        self.assertLess(Seq(0, 10), Seq(1, 10))
        self.assertLess(Seq(-1, 0), Seq(1, 10))
        self.assertGreater(Seq(2, 10), Seq(1, 10))
        self.assertGreater(Seq(2, 9), Seq(1, 10))
        self.assertGreater(Seq(11, 12), Seq(1, 10))
        self.assertGreaterEqual(Seq(11, 12), Seq(1, 10))
        self.assertLessEqual(Seq(1, 10), Seq(11, 12))
        self.assertGreaterEqual(Seq(1, 12), Seq(1, 10))
        self.assertLessEqual(Seq(1, 10), Seq(1, 12))
        self.assertIn(Seq(1, 10), Seq(1, 12))
        self.assertNotIn(Seq(1, 12), Seq(1, 10))
        self.assertIn(1, Seq(1, 12))
        self.assertNotIn(0, Seq(1, 10))

        a = set()
        for s in [Seq(0, 10), Seq(2, 5), Seq(0, 10), Seq(10, 20)]:
            a.add(s)
        self.assertListEqual(list([str(e) for e in a]), ["Seq(0, 10)", "Seq(2, 5)", "Seq(10, 20)"])

        h = list(a)
        heapq.heapify(h)
        self.assertEqual(heapq.heappop(h), Seq(0, 10))
        self.assertEqual(heapq.heappop(h), Seq(2, 5))
        self.assertEqual(heapq.heappop(h), Seq(10, 20))

    def test_make_seqs(self):
        a = (1, 2, 3, 6, 7, 8, 9, 10, 11, 15, 16, 19)
        ref_res = [Seq(1, 4), Seq(6, 12), Seq(15, 17), Seq(19, 20)]
        test_inputs = [
            (1, 2, 3, 6, 11, 16, 7, 9, 19, 10, 15, 8),
            (1, 2, 3, 6, 11, 15, 19, 10, 8, 7, 9, 16),
            (1, 2, 3, 6, 7, 16, 10, 9, 8, 19, 15, 11),
            (1, 2, 3, 8, 7, 19, 16, 10, 15, 11, 6, 9),
            (1, 2, 3, 7, 8, 19, 11, 6, 10, 9, 16, 15),
            (1, 2, 3, 6, 10, 9, 11, 19, 7, 8, 16, 15),
            (1, 2, 3, 7, 15, 6, 8, 11, 19, 16, 9, 10),
            (1, 2, 3, 6, 11, 15, 19, 16, 9, 8, 7, 10),
            (1, 2, 3, 7, 19, 6, 8, 16, 9, 10, 15, 11),
            (1, 2, 3, 7, 11, 8, 9, 10, 19, 16, 15, 6),
        ] + [a]

        for p_a in test_inputs:
            self.assertEqual(make_seqs(p_a), ref_res)

    def create_issuer_and_share_type(self, company: str, stock_name: str) -> Tuple[Issuer, ShareType]:
        user = self.add_test_user()
        issuer = Issuer.objects.get_or_create(name=company, defaults={"party_type": Party.PARTY_ORG, "created_by": user})[0]
        share_type = ShareType.objects.get_or_create(issuer=issuer, name=stock_name, identifier=stock_name)[0]
        assert isinstance(issuer, Issuer)
        assert isinstance(share_type, ShareType)
        return issuer, share_type

    def test_shares_seqs(self):
        issuer, share_type = self.create_issuer_and_share_type("Test Co 4", "A")

        # Issue 2 sets of shares and make sure both are returned in various combinations
        a = Shares(share_type=share_type, begin=1, last=100)
        a.full_clean()
        a.save()
        assert isinstance(a, Shares)
        b = Shares(share_type=share_type, begin=101, last=200)
        b.full_clean()
        b.save()
        assert isinstance(b, Shares)

        test_cases = [
            [(1, 50), [Seq(1, 50, a)]],
            [(1, 101), [Seq(1, 101, a)]],
            [(99, 102), [Seq(99, 101, a), Seq(101, 102, b)]],
            [(101, 101), []],
            [(101, 200), [Seq(101, 200, b)]],
        ]
        for inp, ref in test_cases:
            print("jstocks.tests.Tests.test_shares_seqs: case", inp)
            res = get_share_list(share_type, inp[0], inp[1])
            self.assertEqual(len(res), len(ref))
            self.assertListEqual(res, ref)
            self.assertListEqual([e.parent for e in res], [e.parent for e in ref])

    def test_merge_seqs(self):
        parent = "dummy"
        test_cases = [
            ("4000001-4000120, 4000121-4000130", [Seq(4000001, 4000131, parent)]),
            ("4000001-4000120, 4000122-4000130", [Seq(4000001, 4000121, parent), Seq(4000122, 4000131, parent)]),
            ("4000001-4000125, 4000122-4000130", [Seq(4000001, 4000131, parent)]),
            ("4000001-4000125, 4000001-4000125", [Seq(4000001, 4000126, parent)]),
        ]
        for seqs_str, ref in test_cases:
            res1 = parse_seqs(seqs_str, parent)
            res2 = merge_seqs(res1)
            self.assertListEqual(ref, res2)

    def client_get(self, path: str, data: Optional[Dict[str, Any]] = None):
        print("HTTP GET {}".format(path))
        res = self.client.get(path, data=data or {})
        print("  res.status_code", res.status_code)
        return res

    def client_post(self, path: str, data: Dict[str, Any]):
        print(f"HTTP POST {path}")
        res = self.client.post(path, data=data or {})
        print("res.status_code", res.status_code)
        return res

    def test_admin(self):
        user = self.add_test_user(username="jani", password="jani1234")
        user.is_staff = True
        user.is_superuser = True
        user.save()
        old_shares_count = Shares.objects.all().count()
        self.client_get("/admin/login/", data={})
        self.client_post("/admin/login/", data={"username": "jani", "password": "jani1234", "next": "/admin/"})
        self.client_get("/admin/", data={})
        self.client_get("/admin/jstocks/issuer/add/", data={})
        self.client_post(
            "/admin/jstocks/issuer/add/",
            data={
                "org_name": "GF Money Consumer Finance Oy",
                "org_id": "2382033-5",
                "email": "",
                "phone": "",
                "address": "",
                "city": "",
                "zip_code": "",
                "country": "FI",
                "notes": "",
                "_save": "Save",
            },
        )
        issuer = Issuer.objects.order_by("created").last()
        self.assertTrue(isinstance(issuer, Issuer))
        assert isinstance(issuer, Issuer)
        self.client_get("/admin/jstocks/issuer/", data={})
        self.client_get("/admin/jstocks/", data={})
        self.client_get("/admin/jstocks/sharetype/add/", data={})
        self.client_post(
            "/admin/jstocks/sharetype/add/",
            data={"name": "A-sarja", "identifier": "A", "issuer": issuer.id, "notes": "", "_save": "Save"},
        )
        share_type = ShareType.objects.order_by("created").last()
        self.assertTrue(isinstance(share_type, ShareType))
        assert isinstance(share_type, ShareType)
        self.client_get("/admin/jstocks/sharetype/", data={})
        self.client_get("/admin/jstocks/", data={})
        self.client_get("/admin/jstocks/shares/add/", data={})
        self.client_post(
            "/admin/jstocks/shares/add/",
            data={
                "share_type": share_type.id,
                "begin": "1",
                "last": "4000000",
                "timestamp_0": "2020-09-13",
                "timestamp_1": "21:12:18",
                "initial-timestamp_0": "2020-09-13",
                "initial-timestamp_1": "21:12:18",
                "identifier": "",
                "notes": "",
                "_save": "Save",
            },
        )
        self.client_get("/admin/jstocks/shares/", data={})
        new_shares_count = Shares.objects.all().count()
        self.assertEqual(new_shares_count, old_shares_count + 1)
