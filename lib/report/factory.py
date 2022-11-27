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

from abc import ABCMeta, abstractmethod

from lib.core.decorators import locked


class BaseTextReport(ABCMeta):
    @abstractmethod
    def open(self, output_file):
        raise NotImplementedError

    @abstractmethod
    def save(self, result):
        raise NotImplementedError

    @abstractmethod
    def close(self):
        raise NotImplementedError


class BaseSQLReport(ABCMeta):
    @abstractmethod
    def connect(self, database):
        raise NotImplementedError

    @abstractmethod
    def open(self, table):
        raise NotImplementedError

    @abstractmethod
    def save(self, results):
        raise NotImplementedError

    @abstractmethod
    def close(self):
        raise NotImplementedError


class TextReportAdapter(BaseTextReport):
    def __init__(self, report):
        self.__report = report

    def connect(self):
        pass


class TextReportMixin:
    _file_handler = None
    ouput_file = None

    def open(self, output_file):
        if output_file == self.output_file:
            self.close()

        self._file_handler = open(output_file, "w")

    def close(self):
        self._file_handler.close()

    @locked
    def write_to_file(self, results):
        self._file_handler.truncate(0)
        self._file_handler.writelines(text)
        self._file_handler.flush()


class SQLReportMixin:
    _conn = None
    _cursor = None
    table_name = None

    def select_table(self, table_name):
        self.table_name = table_name

    def get_drop_table_query(self):
        return (f'DROP TABLE IF EXISTS "{self.table_name}"',)

    def get_create_table_query(self):
        return (f'''CREATE TABLE "{self.table_name}" (
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

    def get_queries(self, entries):
        queries = []

        queries.append(self.get_drop_table_query())
        queries.append(self.get_create_table_query())

        for result in results:
            queries.append(
                self.get_insert_query(
                    entry.time, entry.url, entry.status, entry.length, entry.type, entry.redirect
                )
            )

        return queries

    @locked
    def insert(self, entries):
        for query in self.get_queries(entries):
            self._cursor.execute(*query)

        self._conn.commit()
