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

import psycopg

from lib.core.exceptions import InvalidURLException
from lib.report.factory import BaseReport, FormattingMixin, ResultsManagementMixin, SQLReportMixin


class PostgreSQLReport(BaseReport, FormattingMixin, ResultsManagementMixin, SQLReportMixin):
    __format__ = "sql"
    __extension__ = None

    # Cache connection
    _conn = None

    def is_valid(self, url):
        return url.startswith(("postgres://", "postgresql://"))

    def connect(self, url):
        if not self._conn:
            if not self.is_valid(url):
                raise InvalidURLException("Provided PostgreSQL URL does not start with postgresql://")

            self._conn = psycopg.connect(url)

        return self._conn