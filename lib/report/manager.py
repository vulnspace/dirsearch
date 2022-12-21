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

from lib.core.data import options
from lib.core.settings import OUTPUT_FORMATS
from lib.report.csv_report import CSVReport
from lib.report.html_report import HTMLReport
from lib.report.json_report import JSONReport
from lib.report.markdown_report import MarkdownReport
from lib.report.mysql_report import MySQLReport
from lib.report.plain_text_report import PlainTextReport
from lib.report.postgresql_report import PostgreSQLReport
from lib.report.simple_report import SimpleReport
from lib.report.sqlite_report import SQLiteReport
from lib.report.xml_report import XMLReport

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
    def __init__(self):
        self.reports = []

        for format in options["output_formats"]:
            self.reports.append(
                self.get_output_handler(format)(
                    options["output_file"],
                    options["output_url"],
                    options["sql_table_name"],
                )
            )

    def update(self, result):
        for report in self.reports:
            report.append(result)

    def save(self, target):
        for report in self.reports:
            report.save(self.get_output_source(target))

    def get_output_handler(self, format):
        if format == "simple":
            return SimpleReport(options["output_file"])
        elif format == "plain":
            return PlainTextReport(options["output_file"])
        elif format == "json":
            return JSONReport(options["output_file"])
        elif format == "xml":
            return XMLReport(options["output_file"])
        elif format == "md":
            return MarkdownReport(options["output_file"])
        elif format == "csv":
            return CSVReport(options["output_file"])
        elif format == "html":
            return HTMLReport(options["output_file"])
        elif format == "sqlite":
            return SQLiteReport(options["output_file"], options["output_table"])
        elif format == "mysql":
            return MySQLReport(options["output_url"], options["output_table"])
        else:
            return PostgreSQLReport(options["output_url"], options["output_table"])
