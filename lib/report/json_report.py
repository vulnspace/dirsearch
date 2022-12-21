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

import json

from lib.core.settings import COMMAND, START_TIME
from lib.report.factory import BaseReport, FileReportMixin, FormattingMixin, ResultsManagementMixin


class JSONReport(BaseReport, FileReportMixin, FormattingMixin, ResultsManagementMixin):
    __format__ = "json"
    __extension__ = "json"

    def generate(self, results):
        data = {
            "info": {"args": COMMAND, "time": START_TIME},
            "results": [],
        }

        for result in results:
            data["results"].append({
                "url": result.url,
                "status": result.status,
                "content-length": result.length,
                "content-type": result.type,
                "redirect": result.redirect,
            })

        return json.dumps(data, sort_keys=True, indent=4)
