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

import threading

from lib.connection.RequestException import RequestException
from lib.utils import Response
from .Path import *
from .Scanner import *


class Fuzzer(object):
    def __init__(self, requester, dictionary, testFailPath=None, threads=1, matchCallbacks=[], notFoundCallbacks=[],
                 errorCallbacks=[]):

        self.requester = requester
        self.dictionary = dictionary
        self.testFailPath = testFailPath
        self.basePath = self.requester.basePath
        self.threads = []
        self.threadsCount = threads if len(self.dictionary) >= threads else len(self.dictionary)
        self.running = False
        self.scanners = {}
        self.defaultScanner = None
        self.matchCallbacks = matchCallbacks
        self.notFoundCallbacks = notFoundCallbacks
        self.errorCallbacks = errorCallbacks
        self.matches = []
        self.errors = []
        self.responsesBySize = {}

    def wait(self, timeout=None):
        for thread in self.threads:
            thread.join(timeout)

            if timeout is not None and thread.is_alive():
                return False

        return True

    def setupScanners(self):
        if len(self.scanners) != 0:
            self.scanners = {}

        self.defaultScanner = Scanner(self.requester, self.testFailPath, "")
        self.scanners['/'] = Scanner(self.requester, self.testFailPath, "/")

        for extension in self.dictionary.extensions:
            self.scanners[extension] = Scanner(self.requester, self.testFailPath, "." + extension)

    def setupThreads(self):
        if len(self.threads) != 0:
            self.threads = []

        for thread in range(self.threadsCount):
            newThread = threading.Thread(target=self.thread_proc)
            newThread.daemon = True
            self.threads.append(newThread)

    def getScannerFor(self, path):
        if path.endswith('/'):
            return self.scanners['/']

        for extension in list(self.scanners.keys()):
            if path.endswith(extension):
                return self.scanners[extension]

        # By default, returns empty tester
        return self.defaultScanner

    def start(self):
        # Setting up testers
        self.setupScanners()
        # Setting up threads
        self.setupThreads()
        self.index = 0
        self.dictionary.reset()
        self.runningThreadsCount = len(self.threads)
        self.running = True
        self.playEvent = threading.Event()
        self.pausedSemaphore = threading.Semaphore(0)
        self.ratioCheckLock = threading.Lock()
        self.playEvent.clear()
        self.exit = False

        for thread in self.threads:
            thread.start()

        self.play()

    def play(self):
        self.playEvent.set()

    def pause(self):
        self.playEvent.clear()
        for thread in self.threads:
            if thread.is_alive():
                self.pausedSemaphore.acquire()

        print("\nResponses diff info")
        for size in sorted(self.responsesBySize.keys()):
            for page in self.responsesBySize[size]:
                print("%d: %s - %s - %s - %s - %s" % (size, page['path'],
                    page['thread'], page.get('ratio'), page.get('second_path'),
                    page.get('second_thread')))

    def stop(self):
        self.running = False
        self.play()

    def scan(self, path):
        response = self.requester.request(path)
        result = None
        page_clusters = list(self.responsesBySize.values())
        parsers = [page["parser"] for pages in page_clusters for page in pages if "parser" in page]
        reason = self.getScannerFor(path).scan(path, response, parsers)
        if reason is not False:
            result = (None if response.status == 404 else response.status)

        return result, response, reason

    def isRunning(self):
        return self.running

    def finishThreads(self):
        self.running = False
        self.finishedEvent.set()

    def isFinished(self):
        return self.runningThreadsCount == 0

    def stopThread(self):
        self.runningThreadsCount -= 1

    def thread_proc(self):
        self.playEvent.wait()
        try:
            path = next(self.dictionary)
            while path is not None:
                try:
                    result = self.process_scan(path)

                    if result.status is not None:
                        size = self.cluster_response_by_size(result.response)
                        was_found = self.check_similar_pages(size, result)

                        if not was_found:
                            self.add_new_match(result)

                    else:
                        self.invoke_callbacks(self.notFoundCallbacks, result)

                except RequestException as e:
                    self.invoke_error_callbacks(path, e)

                finally:
                    del result.status
                    del result.response

                    path = self.handle_pause_and_continue()

                    if not self.running:
                        break

        except StopIteration:
            return

        finally:
            self.stopThread()

    def process_scan(self, path):
        status, response, reason = self.scan(path)
        return Path(path=path, status=status, response=response, ratio=reason)

    def cluster_response_by_size(self, response):
        size = Response.sizeBytes(response)
        return int(float(size) / 1000) * 1000

    def check_similar_pages(self, size, result):
        was_found = False

        with self.ratioCheckLock:
            if size in self.responsesBySize:
                for page in self.responsesBySize[size]:
                    was_found = self.compare_pages(page, result.path, result.response)
                    if was_found:
                        break

            if not was_found:
                self.responsesBySize.setdefault(size, []).append({
                    "response": result.response,
                    "path": result.path,
                    "thread": threading.get_ident()
                })

        return was_found

    def compare_pages(self, page, path, response):
        if "parser" not in page:
            prev_response = page["response"]
            parser = DynamicContentParser(self.requester, path, prev_response.body, response.body)
            ratio = parser.comparisonRatio

            if ratio >= Scanner.RATIO:
                page.update({
                    "parser": parser,
                    "ratio": ratio,
                    "second_path": path,
                    "second_thread": threading.get_ident()
                })
                return True
        else:
            if page["parser"].compareTo(response.body) >= Scanner.RATIO:
                return True

        return False

    def add_new_match(self, result):
        self.matches.append(result)
        self.invoke_callbacks(self.matchCallbacks, result)

    def invoke_callbacks(self, callbacks, result):
        for callback in callbacks:
            callback(result)

    def invoke_error_callbacks(self, path, e):
        for callback in self.errorCallbacks:
            callback(path, e.args[0]['message'])

    def handle_pause_and_continue(self):
        if not self.playEvent.isSet():
            self.pausedSemaphore.release()
            self.playEvent.wait()

        return next(self.dictionary)  # Raises StopIteration when finishes
