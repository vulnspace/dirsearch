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

    def stop(self):
        self.running = False
        self.play()

    def scan(self, path):
        response = self.requester.request(path)
        result = None
        parsers = [res["parser"] for res in list(self.responsesBySize.values()) if "parser" in res]

        reason = self.getScannerFor(path).scan(path, response, parsers)
        if reason:
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
                    status, response, reason = self.scan(path)
                    result = Path(path=path, status=status, response=response, ratio=reason)

                    if status is not None:
                        size = Response.sizeBytes(response)
                        was_found = False

                        self.ratioCheckLock.acquire()
                        if size in self.responsesBySize:
                            if not "parser" in self.responsesBySize[size]:
                                old_response = self.responsesBySize[size]["response"]
                                self.responsesBySize[size]["parser"] = DynamicContentParser(self.requester, path, old_response.body, response.body)
                                ratio = self.responsesBySize[size]["parser"].comparisonRatio
                                self.responsesBySize[size]["ratio"] = ratio
                                if ratio >= 0.90:
                                    # сверяем схожесть второй найденной страницы такого же размера
                                    was_found = True
                        else:
                            # впервые найденная страница такого размера
                            self.responsesBySize[size] = {
                                "response": response
                            }
                        self.ratioCheckLock.release()

                        if not was_found:
                            self.matches.append(result)

                            for callback in self.matchCallbacks:
                                callback(result)
                    else:
                        for callback in self.notFoundCallbacks:
                            callback(result)
                    del status
                    del response

                except RequestException as e:

                    for callback in self.errorCallbacks:
                        callback(path, e.args[0]['message'])

                    continue

                finally:
                    if not self.playEvent.isSet():
                        self.pausedSemaphore.release()
                        self.playEvent.wait()

                    path = next(self.dictionary)  # Raises StopIteration when finishes

                    if not self.running:
                        break

        except StopIteration:
            return

        finally:
            self.stopThread()
