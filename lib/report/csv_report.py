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

from defusedcsv import csv

from lib.core.settings import NEW_LINE
from lib.report.factory import BaseReport, FileReportMixin, FormattingMixin, ResultsManagementMixin


class CSVReport(BaseReport, FileReportMixin, FormattingMixin, ResultsManagementMixin):
    __format__ = "csv"
    __extension__ = "csv"

    def get_header(self):
        return ["URL", "Status", "Size", "Content Type", "Redirection"]

    def save(self, target):
        with open(self.format(self.file, target), "w") as fd:
            writer = csv.writer(fd, delimiter=',', quotechar='"')
            writer.writerow(self.get_header())

            for result in self.get_results(target):
                writer.writerow(result.url, result.status, result.length, result.type, result.redirect)
