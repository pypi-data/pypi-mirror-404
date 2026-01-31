import csv
import logging
import sys
from typing import List, Any, Optional
from django.core.management.base import CommandParser
from django.utils.formats import localize
from django.utils.timezone import now
from django.utils.translation import gettext as _
from jutil.email import send_email
from openpyxl import Workbook  # type: ignore

from jstocks.xlsx import create_workbook_from_rows

logger = logging.getLogger(__name__)


def add_report_default_output_options(parser: CommandParser):
    parser.add_argument("--stdout", action="store_true")
    parser.add_argument("--xlsx", type=str)
    parser.add_argument("--email", type=str)


def generate_report_output(report_name: str, rows: List[List[Any]], wb: Optional[Workbook] = None, **kwargs):
    done = False
    xlsx_filename = kwargs["xlsx"]
    if wb is None:
        wb = create_workbook_from_rows(rows)
    if kwargs["email"] and not xlsx_filename:
        xlsx_filename = "/tmp/" + report_name + ".xlsx"
    if xlsx_filename:
        wb.save(xlsx_filename)
        logger.info("%s written", xlsx_filename)
        done = True
    if kwargs["email"]:
        emails = kwargs["email"].split(",")
        subject = "{} {}".format(report_name, localize(now().date()))
        text = _("report attached")
        send_email(emails, subject, text, files=[xlsx_filename])
        done = True
    if kwargs["stdout"] or not done:
        w = csv.writer(sys.stdout)
        for row in rows:
            w.writerow(row)
