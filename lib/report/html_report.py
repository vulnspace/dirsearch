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

import os

from jinja2 import Environment, FileSystemLoader

from lib.core.settings import COMMAND, START_TIME
from lib.report.factory import BaseReport, FileReportMixin, FormattingMixin, ResultsManagementMixin


class HTMLReport(FileReportMixin, FormattingMixin, ResultsManagementMixin, BaseReport):
    __format__ = "html"
    __extension__ = "html"

    def generate(self, results):
        file_loader = FileSystemLoader(
            os.path.dirname(os.path.realpath(__file__)) + "/templates/"
        )
        env = Environment(loader=file_loader)
        template = env.get_template("html_report_template.html")
        metadata = {"command": COMMAND, "date": START_TIME}
        results = []

        for result in results:
            status_color_class = ""
            if result.status >= 200 and result.status <= 299:
                status_color_class = "text-success"
            elif result.status >= 300 and result.status <= 399:
                status_color_class = "text-warning"
            elif result.status >= 400 and result.status <= 599:
                status_color_class = "text-danger"

            results.append(
                {
                    "url": result.url,
                    "status": result.status,
                    "contentLength": result.length,
                    "contentType": result.type,
                    "redirect": result.redirect,
                    "statusColorClass": status_color_class,
                }
            )

        return template.render(metadata=metadata, results=results)
