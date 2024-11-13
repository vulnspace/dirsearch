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

import difflib
import re

from lib.utils.common import lstrip_once
from lib.core.settings import MAX_MATCH_RATIO

class DynamicContentParser:
    def __init__(self, content1, content2):
        self._static_patterns = None
        self.responsesBySize = {}
        self._differ = difflib.Differ()
        self._is_static = content1 == content2
        self._base_content = content1

        if not self._is_static:
            self._static_patterns = self.get_static_patterns(
                self._differ.compare(content1.split(), content2.split())
            )

    def compare_to(self, content):
        """
        DynamicContentParser.compare_to() workflow

          1. Check if the wildcard response is static or not, if yes, compare two responses.
          2. If it's not static, get static patterns (split by space) and check if the response
            has all of them.
          3. In some cases, checking static patterns isn't reliable enough, so we check the similarity
            ratio of the two responses.
        """

        if self._is_static:
            return content == self._base_content

        i = -1
        splitted_content = content.split()
        # Allow one miss, see https://github.com/maurosoria/dirsearch/issues/1279
        misses = 0
        for pattern in self._static_patterns:
            try:
                i = splitted_content.index(pattern, i + 1)
            except ValueError:
                if misses or len(self._static_patterns) < 20:
                    return False

                misses += 1

        # Static patterns doesn't seem to be a reliable enough method
        if len(content.split()) > len(self._base_content.split()) and len(self._static_patterns) < 20:
            return difflib.SequenceMatcher(None, self._base_content, content).ratio() > 0.75

        return True

    def get_cluster_size(self, response):
        """
        Clusters the response based on its size. Returns the size rounded to the nearest thousand bytes.
        """
        size = DynamicContentParser.sizeBytes(response)
        return int(float(size) / 1000) * 1000

    def find_similar_page(self, response):
        """
        Checks if there are pages in the cluster with a similar size, and compares them with the current page.
        If a similar page is found, it returns True, otherwise False.
        """
        size = self.get_cluster_size(response)
        was_found = False
        if size in self.responsesBySize:
            for page in self.responsesBySize[size]:
                if page["path"] == response.full_path:
                    return False
                was_found = self.compare_pages(page, response)
                if was_found:
                    return True
        # If no similar pages are found, add a new one
        if not was_found:
            self.responsesBySize.setdefault(size, []).append({
                "response": response.content,
                "path": response.path
            })
        return was_found

    def compare_pages(self, page, response):
        """
        Compares the current page with a previously saved one. If the pages are similar, saves the comparison
        results in a page object. Returns True if the pages are similar, otherwise False.
        """
        match_ratio = difflib.SequenceMatcher(None, page["response"], response.content).ratio()
        if match_ratio > MAX_MATCH_RATIO:
            return True
        return False

    @staticmethod
    def sizeBytes(response):
        try:
            size = int(response.headers['Content-Length'])
        except (KeyError, ValueError):
            size = len(response.content)
        return size

    @staticmethod
    def get_static_patterns(patterns):
        # difflib.Differ.compare returns something like below:
        # ["  str1", "- str2", "+ str3", "  str4"]
        #
        # Get only stable patterns in the contents
        return [lstrip_once(pattern, "  ") for pattern in patterns if pattern.startswith("  ")]


def generate_matching_regex(string1: str, string2: str) -> str:
    start = "^"
    end = "$"

    for char1, char2 in zip(string1, string2):
        if char1 != char2:
            start += ".*"
            break

        start += re.escape(char1)

    if start.endswith(".*"):
        for char1, char2 in zip(string1[::-1], string2[::-1]):
            if char1 != char2:
                break

            end = re.escape(char1) + end

    return start + end
