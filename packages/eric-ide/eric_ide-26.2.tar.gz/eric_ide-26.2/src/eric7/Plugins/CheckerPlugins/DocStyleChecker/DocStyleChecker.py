#
# Copyright (c) 2025 - 2026 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the documentation style checker.
"""

import ast
import contextlib
import multiprocessing
import queue
import sys

from DocStyleFixer import DocStyleFixer
from StyleChecker import StyleChecker


def initService():
    """
    Initialize the service and return the entry point.

    @return the entry point for the background client
    @rtype function
    """
    return docStyleCheck


def initBatchService():
    """
    Initialize the batch service and return the entry point.

    @return the entry point for the background client
    @rtype function
    """
    return docStyleBatchCheck


def extractLineFlags(line, startComment="#", endComment="", flagsLine=False):
    """
    Function to extract flags starting and ending with '__' or being introduced with
    'noqa:' from a line comment.

    @param line line to extract flags from
    @type str
    @param startComment string identifying the start of the comment
    @type str
    @param endComment string identifying the end of a comment
    @type str
    @param flagsLine flag indicating to check for a flags only line
    @type bool
    @return list containing the extracted flags
    @rtype list of str
    """
    flags = []

    if not flagsLine or (flagsLine and line.strip().startswith(startComment)):
        pos = line.rfind(startComment)
        if pos >= 0:
            comment = line[pos + len(startComment) :].strip()
            if endComment:
                endPos = line.rfind(endComment)
                if endPos >= 0:
                    comment = comment[:endPos]
            if comment.startswith(("noqa:", "NOQA:")):
                flags = [
                    "noqa:{0}".format(f.strip())
                    for f in comment[len("noqa:") :].split(",")
                ]
            else:
                flags = [
                    f
                    for f in comment.split()
                    if (f.startswith("__") and f.endswith("__"))
                ]
                flags += [f.lower() for f in comment.split() if f in ("noqa", "NOQA")]
    return flags


def ignoreCode(errorCode, lineFlags):
    """
    Function to check, if the given code should be ignored as per line flags.

    @param errorCode error code to be checked
    @type str
    @param lineFlags list of line flags to check against
    @type list of str
    @return flag indicating to ignore the error code
    @rtype bool
    """
    if lineFlags:
        if "__IGNORE_WARNING__" in lineFlags or "noqa" in lineFlags:
            # ignore all warning codes
            return True

        for flag in lineFlags:
            # check individual warning code
            if flag.startswith("__IGNORE_WARNING_"):
                ignoredCode = flag[2:-2].rsplit("_", 1)[-1]
                if errorCode.startswith(ignoredCode):
                    return True
            elif flag.startswith("noqa:"):
                ignoredCode = flag[len("noqa:") :].strip()
                if errorCode.startswith(ignoredCode):
                    return True

    return False


def docStyleCheck(filename, source, args):
    """
    Do the source code documentation style check and/or fix found errors.

    @param filename source filename
    @type str
    @param source list of code lines to be checked
    @type list of str
    @param args arguments used by the docStyleCheck function (list of
        excludeMessages, includeMessages, repeatMessages, fixCodes,
        noFixCodes, fixIssues, maxLineLength, docType, errors, eol, encoding, backup)
    @type list of (str, str, bool, str, str, bool, int, str, list of str, str, str,
        bool)
    @return tuple of statistics (dict) and list of results (tuple for each
        found violation of documentation style (lineno, position, text, ignored, fixed,
        autofixing, fixedMsg))
    @rtype tuple of (dict, list of tuples of (int, int, str, bool, bool, bool, str))
    """
    return __checkDocStyle(filename, source, args)


def docStyleBatchCheck(argumentsList, send, fx, cancelled, maxProcesses=0):
    """
    Module function to check source code documentation style for a batch of files.

    @param argumentsList list of arguments tuples as given for docStyleCheck
    @type list
    @param send reference to send function
    @type func
    @param fx registered service name
    @type str
    @param cancelled reference to function checking for a cancellation
    @type func
    @param maxProcesses number of processes to be used
    @type int
    """
    if maxProcesses == 0:
        # determine based on CPU count
        try:
            NumberOfProcesses = multiprocessing.cpu_count()
            if NumberOfProcesses >= 1:
                NumberOfProcesses -= 1
        except NotImplementedError:
            NumberOfProcesses = 1
    else:
        NumberOfProcesses = maxProcesses

    # Create queues
    taskQueue = multiprocessing.Queue()
    doneQueue = multiprocessing.Queue()

    # Submit tasks (initially two times the number of processes)
    tasks = len(argumentsList)
    initialTasks = min(2 * NumberOfProcesses, tasks)
    for _ in range(initialTasks):
        taskQueue.put(argumentsList.pop(0))

    # Start worker processes
    workers = [
        multiprocessing.Process(target=workerTask, args=(taskQueue, doneQueue))
        for _ in range(NumberOfProcesses)
    ]
    for worker in workers:
        worker.start()

    # Get and send results
    for _ in range(tasks):
        resultSent = False
        wasCancelled = False

        while not resultSent:
            try:
                # get result (waiting max. 3 seconds and send it to frontend
                filename, result = doneQueue.get(timeout=3)
                send(fx, filename, result)
                resultSent = True
            except queue.Empty:
                # ignore empty queue, just carry on
                if cancelled():
                    wasCancelled = True
                    break

        if wasCancelled or cancelled():
            # just exit the loop ignoring the results of queued tasks
            break

        if argumentsList:
            taskQueue.put(argumentsList.pop(0))

    # Tell child processes to stop
    for _ in range(NumberOfProcesses):
        taskQueue.put("STOP")

    for worker in workers:
        worker.join()
        worker.close()

    taskQueue.close()
    doneQueue.close()


def workerTask(inputQueue, outputQueue):
    """
    Module function acting as the parallel worker for the style check.

    @param inputQueue input queue
    @type multiprocessing.Queue
    @param outputQueue output queue
    @type multiprocessing.Queue
    """
    for filename, source, args in iter(inputQueue.get, "STOP"):
        result = __checkDocStyle(filename, source, args)
        outputQueue.put((filename, result))


def __checkSyntax(filename, source):
    """
    Private module function to perform a syntax check.

    @param filename source filename
    @type str
    @param source list of code lines to be checked
    @type list of str
    @return tuple containing the error dictionary with syntax error details,
        a statistics dictionary and None or a tuple containing two None and
        the generated AST tree
    @rtype tuple of (dict, dict, None) or tuple of (None, None, ast.Module)
    """
    src = "".join(source)

    try:
        tree = ast.parse(src, filename, "exec")
    except (SyntaxError, TypeError):
        exc_type, exc = sys.exc_info()[:2]
        if len(exc.args) > 1:
            offset = exc.args[1]
            if len(offset) > 2:
                offset = offset[1:3]
        else:
            offset = (1, 0)
        return (
            {
                "file": filename,
                "line": offset[0],
                "offset": offset[1],
                "code": "E-901",
                "args": [exc_type.__name__, exc.args[0]],
            },
            {
                "E-901": 1,
            },
            None,
        )
    else:
        return None, None, tree


def __checkDocStyle(filename, source, args):
    """
    Private module function to perform the source code documentation style check
    and/or fix found errors.

    @param filename source filename
    @type str
    @param source list of code lines to be checked
    @type list of str
    @param args arguments used by the docStyleCheck function (list of
        excludeMessages, includeMessages, repeatMessages, fixCodes,
        noFixCodes, fixIssues, maxLineLength, docType, errors, eol, encoding, backup)
    @type list of (str, str, bool, str, str, bool, int, str, list of str, str, str,
        bool)
    @return tuple of statistics data and list of result dictionaries with
        keys:
        <ul>
        <li>file: file name</li>
        <li>line: line_number</li>
        <li>offset: offset within line</li>
        <li>code: error message code</li>
        <li>args: list of arguments to format the message</li>
        <li>ignored: flag indicating this issue was ignored</li>
        <li>fixed: flag indicating this issue was fixed</li>
        <li>autofixing: flag indicating that a fix can be done</li>
        <li>fixcode: message code for the fix</li>
        <li>fixargs: list of arguments to format the fix message</li>
        </ul>
    @rtype tuple of (dict, list of dict)
    """
    (
        excludeMessages,
        includeMessages,
        repeatMessages,
        fixCodes,
        noFixCodes,
        fixIssues,
        maxLineLength,
        docType,
        errors,
        eol,
        encoding,
        backup,
    ) = args

    stats = {}

    fixer = (
        DocStyleFixer(
            filename,
            source,
            fixCodes,
            noFixCodes,
            maxLineLength,
            True,
            eol,
            backup,
        )
        if fixIssues
        else None
    )

    if not errors:
        if includeMessages:
            selected = [s.strip() for s in includeMessages.split(",") if s.strip()]
        else:
            selected = []
        if excludeMessages:
            ignored = [i.strip() for i in excludeMessages.split(",") if i.strip()]
        else:
            ignored = []

        syntaxError, syntaxStats, tree = __checkSyntax(filename, source)

        # perform the checks only, if syntax is ok and AST tree was generated
        if tree:
            # check documentation style
            styleChecker = StyleChecker(
                source,
                filename,
                selected,
                ignored,
                repeatMessages,
                maxLineLength=maxLineLength,
                docType=docType,
            )
            styleChecker.run()
            stats.update(styleChecker.counters)
            errors.extend(styleChecker.errors)

        elif syntaxError:
            errors = [syntaxError]
            stats.update(syntaxStats)

    errorsDict = {}
    for error in errors:
        if error["line"] > len(source):
            error["line"] = len(source)
        # inverse processing of messages and fixes
        errorLine = errorsDict.setdefault(error["line"], [])
        errorLine.append((error["offset"], error))
    deferredFixes = {}
    results = []
    for lineno, errorsList in errorsDict.items():
        errorsList.sort(key=lambda x: x[0], reverse=True)
        for _, error in errorsList:
            error.update(
                {
                    "ignored": False,
                    "fixed": False,
                    "autofixing": False,
                    "fixcode": "",
                    "fixargs": [],
                    "securityOk": False,
                }
            )

            if source:
                errorCode = error["code"]
                lineFlags = extractLineFlags(source[lineno - 1].strip())
                with contextlib.suppress(IndexError):
                    lineFlags += extractLineFlags(
                        source[lineno].strip(), flagsLine=True
                    )

                if ignoreCode(errorCode, lineFlags):
                    error["ignored"] = True
                else:
                    if fixer:
                        res, fixcode, fixargs, fixId = fixer.fixIssue(
                            lineno, error["offset"], errorCode
                        )
                        if res == -1:
                            deferredFixes[fixId] = error
                        else:
                            error.update(
                                {
                                    "fixed": res == 1,
                                    "autofixing": True,
                                    "fixcode": fixcode,
                                    "fixargs": fixargs,
                                }
                            )

            results.append(error)

    if fixer:
        deferredResults = fixer.finalize()
        for resultId in deferredResults:
            fixed, fixcode, fixargs = deferredResults[resultId]
            error = deferredFixes[resultId]
            error.update(
                {
                    "ignored": False,
                    "fixed": fixed == 1,
                    "autofixing": True,
                    "fixcode": fixcode,
                    "fixargs": fixargs,
                }
            )

        saveError = fixer.saveFile(encoding)
        if saveError:
            for error in results:
                error.update(
                    {
                        "fixcode": saveError[0],
                        "fixargs": saveError[1],
                    }
                )

    return stats, results
