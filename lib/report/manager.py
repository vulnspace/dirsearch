# -*- coding: utf-8 -*-
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#  Author: Mauro Soria

import time

from urllib.parse import urlparse

from lib.core.data import options
from lib.core.settings import OUTPUT_FORMATS
from lib.reports.csv_report import CSVReport
from lib.reports.html_report import HTMLReport
from lib.reports.json_report import JSONReport
from lib.reports.markdown_report import MarkdownReport
from lib.reports.mysql_report import MySQLReport
from lib.reports.plain_text_report import PlainTextReport
from lib.reports.postgresql_report import PostgreSQLReport
from lib.reports.simple_report import SimpleReport
from lib.reports.sqlite_report import SQLiteReport
from lib.reports.xml_report import XMLReport

reporters = dict(
    zip(
        OUTPUT_FORMATS,
        (
            SimpleReport,
            PlainTextReport,
            JSONReport,
            XMLReport,
            MarkdownReport,
            CSVReport,
            HTMLReport,
            SQLiteReport,
            MySQLReport,
            PostgreSQLReport,
        ),
    )
)


class ReportManager:
    def __init__(self, url):
        self.results = []
        self.reports = []
        self.url = url

        for format in options["output_formats"]:
            self.reports.append(
                self.get_output_handler(format)(self.get_output_source())
            )

    def update(self, result):
        self.results.append(result)

    def save(self):
        for report in self.reports:
            self.report.save(self.results)

    def get_output_extension(self, format):
        if format in ("plain", "simple"):
            return "txt"
        elif format in ("mysql", "postgresql"):
            return ""

        return format

    def get_output_source(self, format):
        if format in ("mysql", "postgresql"):
            return options["output_url"]

        return self.format(options["output_file"], format)

    def get_output_handler(self, format):
        return reporters[format]

    def format(string, format):
        parsed = urlparse(self.url)
        return string.format({
            "date": time.strftime("%Y-%m-%d"),
            "host": parsed.hostname,
            "scheme": parsed.scheme,
            "port": parsed.port or STANDARD_PORTS[parsed.scheme],
            "extension": self.get_output_extension(format),
        })
