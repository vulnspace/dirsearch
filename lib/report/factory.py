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

from abc import ABCMeta, abstractmethod
from urllib.parse import urlparse

from lib.core.decorators import locked
from lib.core.settings import STANDARD_PORTS


class BaseReport(ABCMeta):
    @abstractmethod
    def __init__(self):
        raise NotImplementedError

    @abstractmethod
    def append(self, result):
        raise NotImplementedError

    @abstractmethod
    def save(self, target):
        raise NotImplementedError

    @abstractmethod
    def close(self):
        raise NotImplementedError


class ResultsManagementMixin:
    _storage = {}

    def append(self, result):
        key = self.get_key(result.url)
        self._storage.setdefault(key, [])
        self._storage[key].append(result)

    def get_results(self, target):
        return self._storage.get(self.get_key(target))


class FormattingMixin:
    def format(self, string, target):
        parsed = urlparse(target)
        format_dict = dict(
            date=time.strftime("%Y-%m-%d"),
            host=parsed.hostname,
            scheme=parsed.scheme,
            port=parsed.port or STANDARD_PORTS[parsed.scheme],
            format=self.__format__,
            extension=self.__extension__,
        )

        return string.format(format_dict)


class FileReportMixin:
    def __init__(self, output_file):
        self.file = output_file

    def get_key(self, target):
        return self.format(self.file, target)

    @locked
    def save(self, target):
        with open(self.format(self.file, target)) as fh:
            fh.writelines(self.generate(self.get_results(target)))


class SQLReportMixin:
    def __init__(self, database, table_name):
        self.database = database
        self.table = table_name

    def get_key(self, target):
        return (
            self.format(self.database, target),
            self.format(self.table, target)
        )

    @property
    def delete_table_query(self, table):
        return (f'''DELETE TABLE IF EXISTS "{table}"''',)

    @property
    def create_table_query(self, table):
        return (f'''CREATE TABLE "{table}" (
            time TIMESTAMP,
            url TEXT,
            status_code INTEGER,
            content_length INTEGER,
            content_type TEXT,
            redirect TEXT
        );''',)

    def get_insert_query(self, values):
        return (f'''INSERT INTO "{self.table_name}" (time, url, status_code, content_length, content_type, redirect)
                    VALUES
                    (%s, %s, %s, %s, %s, %s)''', values)

    def get_queries(self, results, table):
        queries = []

        queries.append(self.get_drop_table_query(table))
        queries.append(self.get_create_table_query(table))

        for result in results:
            queries.append(
                self.get_insert_query(
                    result.time, result.url, result.status, result.length, result.type, result.redirect
                )
            )

        return queries

    @locked
    def save(self, target):
        conn = self.connect(self.format(self.database, target))
        cursor = conn.cursor()

        results = self.get_results(target)
        table = self.format(self.table, target)

        for query in self.get_queries(results, table):
            cursor.execute(*query)

        conn.commit()