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

from lib.core.settings import (
    COMMAND,
    NEW_LINE,
    START_TIME,
)
from lib.report.factory import BaseReport, FileReportMixin, FormattingMixin, ResultsManagementMixin
from lib.utils.common import human_size


class PlainTextReport(BaseReport, FileReportMixin, FormattingMixin, ResultsManagementMixin):
    __format__ = "plain"
    __extension__ = "txt"

    def get_header(self):
        return f"# Dirsearch started {START_TIME} as: {COMMAND}" + NEW_LINE * 2

    def generate(self, results):
        data = self.get_header()

        for result in results:
            readable_size = human_size(result.length)
            data += f"{result.status} {readable_size.rjust(6, chr(32))} {result.url}"

            if result.redirect:
                data += f"  ->  {result.redirect}"

            data += NEW_LINE

        return data
