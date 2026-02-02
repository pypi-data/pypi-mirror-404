#
# Copyright (c) 2025 - 2026 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to configure the documentation style check and show its
results.
"""

import collections
import fnmatch
import json
import os
import time

from PyQt6.QtCore import QTimer, Qt, pyqtSlot
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QAbstractButton,
    QApplication,
    QDialog,
    QDialogButtonBox,
    QTreeWidgetItem,
)

from eric7 import EricUtilities, Preferences, Utilities
from eric7.EricGui import EricPixmapCache
from eric7.EricWidgets.EricApplication import ericApp
from eric7.QScintilla.Editor import EditorWarningKind
from eric7.SystemUtilities import FileSystemUtilities

from .Ui_DocStyleCheckerDialog import Ui_DocStyleCheckerDialog


class DocStyleCheckerDialog(QDialog, Ui_DocStyleCheckerDialog):
    """
    Class implementing a dialog to configure the documentation style check and show its
    results.
    """

    filenameRole = Qt.ItemDataRole.UserRole + 1
    lineRole = Qt.ItemDataRole.UserRole + 2
    positionRole = Qt.ItemDataRole.UserRole + 3
    messageRole = Qt.ItemDataRole.UserRole + 4
    fixableRole = Qt.ItemDataRole.UserRole + 5
    codeRole = Qt.ItemDataRole.UserRole + 6
    ignoredRole = Qt.ItemDataRole.UserRole + 7
    argsRole = Qt.ItemDataRole.UserRole + 8

    noResults = 0
    noFiles = 1
    hasResults = 2

    def __init__(self, styleCheckService, project=None, parent=None):
        """
        Constructor

        @param styleCheckService reference to the service
        @type DocStyleCheckService
        @param project reference to the project if called on project or project
            browser level
        @type Project
        @param parent reference to the parent widget
        @type QWidget
        """
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.WindowType.Window)

        self.__project = project

        self.excludeMessagesSelectButton.setIcon(EricPixmapCache.getIcon("select"))
        self.includeMessagesSelectButton.setIcon(EricPixmapCache.getIcon("select"))
        self.fixIssuesSelectButton.setIcon(EricPixmapCache.getIcon("select"))
        self.noFixIssuesSelectButton.setIcon(EricPixmapCache.getIcon("select"))

        self.docTypeComboBox.addItem(self.tr("PEP-257"), "pep257")
        self.docTypeComboBox.addItem(self.tr("Eric"), "eric")
        self.docTypeComboBox.addItem(self.tr("Eric (Blacked)"), "eric_black")

        self.statisticsButton.setEnabled(False)
        self.showButton.setEnabled(False)
        self.cancelButton.setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Close).setEnabled(False)

        self.resultList.headerItem().setText(self.resultList.columnCount(), "")
        self.resultList.header().setSortIndicator(0, Qt.SortOrder.AscendingOrder)

        self.restartButton.setEnabled(False)
        self.fixButton.setEnabled(False)

        self.checkProgress.setVisible(False)

        self.styleCheckService = styleCheckService
        self.styleCheckService.styleChecked.connect(self.__processResult)
        self.styleCheckService.batchFinished.connect(self.__batchFinished)
        self.styleCheckService.error.connect(self.__processError)
        self.filename = None

        self.results = DocStyleCheckerDialog.noResults
        self.cancelled = False
        self.__lastFileItem = None
        self.__batch = False
        self.__finished = True
        self.__errorItem = None
        self.__timenow = time.monotonic()

        self.__fileOrFileList = ""
        self.__forProject = False
        self.__data = {}
        self.__statistics = collections.defaultdict(self.__defaultStatistics)
        self.__onlyFixes = {}
        self.__noFixCodesList = []
        self.__detectedCodes = []

        self.on_loadDefaultButton_clicked()

        self.mainWidget.setCurrentWidget(self.configureTab)

        self.__remotefsInterface = (
            ericApp().getObject("EricServer").getServiceInterface("FileSystem")
        )

    def __defaultStatistics(self):
        """
        Private method to return the default statistics entry.

        @return dictionary with default statistics entry
        @rtype dict
        """
        return {
            "total": 0,
            "ignored": 0,
        }

    def __resort(self):
        """
        Private method to resort the tree.
        """
        self.resultList.sortItems(
            self.resultList.sortColumn(), self.resultList.header().sortIndicatorOrder()
        )

    def __createErrorItem(self, filename, message):
        """
        Private slot to create a new error item in the result list.

        @param filename name of the file
        @type str
        @param message error message
        @type str
        """
        if self.__errorItem is None:
            self.__errorItem = QTreeWidgetItem(self.resultList, [self.tr("Errors")])
            self.__errorItem.setExpanded(True)
            self.__errorItem.setForeground(0, Qt.GlobalColor.red)

        msg = "{0} ({1})".format(self.__project.getRelativePath(filename), message)
        if not self.resultList.findItems(msg, Qt.MatchFlag.MatchExactly):
            itm = QTreeWidgetItem(self.__errorItem, [msg])
            itm.setForeground(0, Qt.GlobalColor.red)
            itm.setFirstColumnSpanned(True)

    def __createFileErrorItem(self, filename, message):
        """
        Private method to create an error entry for a given file.

        @param filename file name of the file
        @type str
        @param message error message text
        @type str
        """
        result = {
            "file": filename,
            "line": 1,
            "offset": 1,
            "code": "",
            "args": [],
            "display": self.tr("Error: {0}").format(message).rstrip(),
            "fixed": False,
            "autofixing": False,
            "ignored": False,
        }
        self.__createResultItem(filename, result)

    def __createResultItem(self, filename, result):
        """
        Private method to create an entry in the result list.

        @param filename file name of the file
        @type str
        @param result dictionary containing check result data
        @type dict
        @return reference to the created item
        @rtype QTreeWidgetItem
        """
        from .DocStyleFixer import FixableCodeStyleIssues

        if self.__lastFileItem is None:
            # It's a new file
            self.__lastFileItem = QTreeWidgetItem(
                self.resultList, [self.__project.getRelativePath(filename)]
            )
            self.__lastFileItem.setFirstColumnSpanned(True)
            self.__lastFileItem.setExpanded(True)
            self.__lastFileItem.setData(0, self.filenameRole, filename)

        msgCode = result["code"].split(".", 1)[0]
        self.__detectedCodes.append(msgCode)

        fixable = False
        itm = QTreeWidgetItem(
            self.__lastFileItem,
            ["{0:6}".format(result["line"]), msgCode, result["display"]],
        )

        itm.setIcon(1, EricPixmapCache.getIcon("docstringError"))

        if result["fixed"]:
            itm.setIcon(0, EricPixmapCache.getIcon("issueFixed"))
        elif (
            msgCode in FixableCodeStyleIssues
            and not result["autofixing"]
            and msgCode not in self.__noFixCodesList
        ):
            itm.setIcon(0, EricPixmapCache.getIcon("issueFixable"))
            fixable = True

        itm.setTextAlignment(0, Qt.AlignmentFlag.AlignRight)
        itm.setTextAlignment(1, Qt.AlignmentFlag.AlignHCenter)

        itm.setTextAlignment(0, Qt.AlignmentFlag.AlignVCenter)
        itm.setTextAlignment(1, Qt.AlignmentFlag.AlignVCenter)
        itm.setTextAlignment(2, Qt.AlignmentFlag.AlignVCenter)

        itm.setData(0, self.filenameRole, filename)
        itm.setData(0, self.lineRole, int(result["line"]))
        itm.setData(0, self.positionRole, int(result["offset"]))
        itm.setData(0, self.messageRole, result["display"])
        itm.setData(0, self.fixableRole, fixable)
        itm.setData(0, self.codeRole, msgCode)
        itm.setData(0, self.ignoredRole, result["ignored"])
        itm.setData(0, self.argsRole, result["args"])

        if result["ignored"]:
            font = itm.font(0)
            font.setItalic(True)
            for col in range(itm.columnCount()):
                itm.setFont(col, font)

        return itm

    def __modifyFixedResultItem(self, itm, result):
        """
        Private method to modify a result list entry to show its
        positive fixed state.

        @param itm reference to the item to modify
        @type QTreeWidgetItem
        @param result dictionary containing check result data
        @type dict
        """
        if result["fixed"]:
            itm.setText(2, result["display"])
            itm.setIcon(0, EricPixmapCache.getIcon("issueFixed"))

            itm.setData(0, self.messageRole, result["display"])
        else:
            itm.setIcon(0, QIcon())
        itm.setData(0, self.fixableRole, False)

    def __updateStatistics(self, statisticData, fixer, ignoredErrors):
        """
        Private method to update the collected statistics.

        @param statisticData dictionary of statistical data with
            message code as key and message count as value
        @type dict
        @param fixer reference to the code style fixer
        @type DocStyleFixer
        @param ignoredErrors number of ignored errors
        @type int
        """
        self.__statistics["_FilesCount"] += 1
        stats = [k for k in statisticData if k[0].isupper()]
        if stats:
            self.__statistics["_FilesIssues"] += 1
            for key in stats:
                self.__statistics[key]["total"] += statisticData[key]
            for key in ignoredErrors:
                self.__statistics[key]["ignored"] += ignoredErrors[key]
        self.__statistics["_IssuesFixed"] += fixer

    def __updateFixerStatistics(self, fixer):
        """
        Private method to update the collected fixer related statistics.

        @param fixer reference to the code style fixer
        @type DocStyleFixer
        """
        self.__statistics["_IssuesFixed"] += fixer

    def __resetStatistics(self):
        """
        Private slot to reset the statistics data.
        """
        self.__statistics.clear()
        self.__statistics["_FilesCount"] = 0
        self.__statistics["_FilesIssues"] = 0
        self.__statistics["_IssuesFixed"] = 0

    def getDefaults(self):
        """
        Public method to get a dictionary containing the default values.

        @return dictionary containing the default values
        @rtype dict
        """
        return {
            "DocstringType": "pep257",
            "MaxLineLength": 88,
            # better code formatting than pycodestyle.MAX_LINE_LENGTH
            # see the Black tool
            "ExcludeFiles": "",
            "ExcludeMessages": "",
            "IncludeMessages": "",
            "RepeatMessages": False,
            "ShowIgnored": False,
            "FixCodes": "",
            "NoFixCodes": "",
            "FixIssues": False,
        }

    def prepare(self, fileList, project):
        """
        Public method to prepare the dialog with a list of filenames.

        @param fileList list of filenames
        @type list of str
        @param project reference to the project object
        @type Project
        """
        self.__fileOrFileList = fileList[:]
        self.__project = project
        self.__forProject = True

        self.buttonBox.button(QDialogButtonBox.StandardButton.Close).setEnabled(True)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Close).setDefault(True)
        self.cancelButton.setEnabled(False)

        defaultParameters = self.getDefaults()
        self.__data = self.__project.getData("CHECKERSPARMS", "DocStyleChecker")
        if self.__data is None or len(self.__data) < 6:
            # initialize the data structure
            self.__data = defaultParameters
        else:
            for key in defaultParameters:
                if key not in self.__data:
                    self.__data[key] = defaultParameters[key]

        self.docTypeComboBox.setCurrentText(self.__data["DocstringType"])
        self.lineLengthSpinBox.setValue(self.__data["MaxLineLength"])
        self.excludeFilesEdit.setText(self.__data["ExcludeFiles"])
        self.excludeMessagesEdit.setText(self.__data["ExcludeMessages"])
        self.includeMessagesEdit.setText(self.__data["IncludeMessages"])
        self.repeatCheckBox.setChecked(self.__data["RepeatMessages"])
        self.ignoredCheckBox.setChecked(self.__data["ShowIgnored"])
        self.fixIssuesEdit.setText(self.__data["FixCodes"])
        self.noFixIssuesEdit.setText(self.__data["NoFixCodes"])
        self.fixIssuesCheckBox.setChecked(self.__data["FixIssues"])

    def __prepareProgress(self):
        """
        Private method to prepare the progress tab for the next run.
        """
        self.progressList.clear()
        if len(self.files) > 0:
            self.checkProgress.setMaximum(len(self.files))
            self.checkProgress.setVisible(len(self.files) > 1)
            if len(self.files) > 1:
                if self.__project:
                    self.progressList.addItems(
                        [
                            os.path.join("...", self.__project.getRelativePath(f))
                            for f in self.files
                        ]
                    )
                else:
                    self.progressList.addItems(self.files)

        QApplication.processEvents()

    def start(self, fn, save=False, repeat=None):
        """
        Public slot to start the code style check.

        @param fn file or list of files or directory to be checked
        @type str or list of str
        @param save flag indicating to save the given file/file list/directory
        @type bool
        @param repeat state of the repeat check box if it is not None
        @type None or bool
        """
        if self.__project is None:
            self.__project = ericApp().getObject("Project")

        self.mainWidget.setCurrentWidget(self.progressTab)

        self.cancelled = False
        self.buttonBox.button(QDialogButtonBox.StandardButton.Close).setEnabled(False)
        self.cancelButton.setEnabled(True)
        self.cancelButton.setDefault(True)
        self.statisticsButton.setEnabled(False)
        self.showButton.setEnabled(False)
        self.fixButton.setEnabled(False)
        self.startButton.setEnabled(False)
        self.restartButton.setEnabled(False)
        if repeat is not None:
            self.repeatCheckBox.setChecked(repeat)
        self.checkProgress.setVisible(True)
        QApplication.processEvents()

        if save:
            self.__fileOrFileList = fn

        if isinstance(fn, list):
            self.files = fn[:]
        elif FileSystemUtilities.isRemoteFileName(
            fn
        ) and self.__remotefsInterface.isdir(fn):
            extensions = set(Preferences.getPython("Python3Extensions"))
            self.files = self.__remotefsInterface.direntries(
                fn, True, [f"*{ext}" for ext in extensions], False
            )
        elif FileSystemUtilities.isPlainFileName(fn) and os.path.isdir(fn):
            extensions = set(Preferences.getPython("Python3Extensions"))
            self.files = FileSystemUtilities.direntries(
                fn, True, [f"*{ext}" for ext in extensions], False
            )
        else:
            self.files = [fn]

        # filter the list depending on the filter string
        if self.files:
            filterString = self.excludeFilesEdit.text()
            filterList = [f.strip() for f in filterString.split(",") if f.strip()]
            for fileFilter in filterList:
                self.files = [
                    f for f in self.files if not fnmatch.fnmatch(f, fileFilter.strip())
                ]

        self.__errorItem = None
        self.__resetStatistics()
        self.__clearErrors(self.files)
        self.__prepareProgress()

        # disable updates of the list for speed
        self.resultList.setUpdatesEnabled(False)
        self.resultList.setSortingEnabled(False)

        if len(self.files) > 0:
            # extract the configuration values
            excludeMessages = self.excludeMessagesEdit.text()
            includeMessages = self.includeMessagesEdit.text()
            repeatMessages = self.repeatCheckBox.isChecked()
            fixCodes = self.fixIssuesEdit.text()
            noFixCodes = self.noFixIssuesEdit.text()
            self.__noFixCodesList = [
                c.strip() for c in noFixCodes.split(",") if c.strip()
            ]
            fixIssues = self.fixIssuesCheckBox.isChecked() and repeatMessages
            self.showIgnored = self.ignoredCheckBox.isChecked() and repeatMessages
            maxLineLength = self.lineLengthSpinBox.value()
            docType = self.docTypeComboBox.currentData()

            self.__options = [
                excludeMessages,
                includeMessages,
                repeatMessages,
                fixCodes,
                noFixCodes,
                fixIssues,
                maxLineLength,
                docType,
            ]

            # now go through all the files
            self.progress = 0
            self.files.sort()
            self.__timenow = time.monotonic()

            if len(self.files) == 1:
                self.__batch = False
                self.mainWidget.setCurrentWidget(self.resultsTab)
                self.check()
            else:
                self.__batch = True
                self.checkBatch()
        else:
            self.results = DocStyleCheckerDialog.noFiles
            self.__finished = False
            self.__finish()

    def check(self, codestring=""):
        """
        Public method to start a style check for one file.

        The results are reported to the __processResult slot.

        @param codestring optional sourcestring
        @type str
        """
        if not self.files:
            self.checkProgress.setMaximum(1)
            self.checkProgress.setValue(1)
            self.__finish()
            return

        self.filename = self.files.pop(0)
        self.checkProgress.setValue(self.progress)
        QApplication.processEvents()

        if self.cancelled:
            self.__resort()
            return

        self.__lastFileItem = None
        self.__finished = False

        if codestring:
            source = codestring.splitlines(True)
            encoding = Utilities.get_coding(source)
        else:
            try:
                if FileSystemUtilities.isRemoteFileName(self.filename):
                    source, encoding = self.__remotefsInterface.readEncodedFile(
                        self.filename
                    )
                else:
                    source, encoding = Utilities.readEncodedFile(self.filename)
                source = source.splitlines(True)
            except (OSError, UnicodeError) as msg:
                self.results = DocStyleCheckerDialog.hasResults
                self.__createFileErrorItem(self.filename, str(msg))
                self.progress += 1
                # Continue with next file
                self.check()
                return
        if encoding.endswith(("-selected", "-default", "-guessed", "-ignore")):
            encoding = encoding.rsplit("-", 1)[0]

        errors = []
        self.__itms = []
        for error, itm in self.__onlyFixes.pop(self.filename, []):
            errors.append(error)
            self.__itms.append(itm)

        eol = self.__getEol(self.filename)
        args = [
            *self.__options,
            errors,
            eol,
            encoding,
            Preferences.getEditor("CreateBackupFile"),
        ]
        self.styleCheckService.styleCheck(None, self.filename, source, args)

    def checkBatch(self):
        """
        Public method to start a style check batch job.

        The results are reported to the __processResult slot.
        """
        self.__lastFileItem = None
        self.__finished = False

        argumentsList = []
        for progress, filename in enumerate(self.files, start=1):
            self.checkProgress.setValue(progress)
            if time.monotonic() - self.__timenow > 0.01:
                QApplication.processEvents()
                self.__timenow = time.monotonic()

            try:
                if FileSystemUtilities.isRemoteFileName(filename):
                    source, encoding = self.__remotefsInterface.readEncodedFile(
                        filename
                    )
                else:
                    source, encoding = Utilities.readEncodedFile(filename)
                source = source.splitlines(True)
            except (OSError, UnicodeError) as msg:
                self.results = DocStyleCheckerDialog.hasResults
                self.__createFileErrorItem(filename, str(msg))
                continue

            if encoding.endswith(("-selected", "-default", "-guessed", "-ignore")):
                encoding = encoding.rsplit("-", 1)[0]

            errors = []
            self.__itms = []
            for error, itm in self.__onlyFixes.pop(filename, []):
                errors.append(error)
                self.__itms.append(itm)

            eol = self.__getEol(filename)
            args = [
                *self.__options,
                errors,
                eol,
                encoding,
                Preferences.getEditor("CreateBackupFile"),
            ]
            argumentsList.append((filename, source, args))

        # reset the progress bar to the checked files
        self.checkProgress.setValue(self.progress)
        QApplication.processEvents()

        self.styleCheckService.styleBatchCheck(argumentsList)

    def __batchFinished(self):
        """
        Private slot handling the completion of a batch job.
        """
        self.checkProgress.setMaximum(1)
        self.checkProgress.setValue(1)
        self.__finish()

    def __processError(self, fn, msg):
        """
        Private slot to process an error indication from the service.

        @param fn filename of the file
        @type str
        @param msg error message
        @type str
        """
        self.__createErrorItem(fn, msg)

        if not self.__batch:
            self.check()

    def __processResult(self, fn, docStyleCheckerStats, fixes, results):
        """
        Private slot called after perfoming a style check on one file.

        @param fn filename of the just checked file
        @type str
        @param docStyleCheckerStats stats of style and name check
        @type dict
        @param fixes number of applied fixes
        @type int
        @param results dictionary containing check result data
        @type dict
        """
        if self.__finished:
            return

        # Check if it's the requested file, otherwise ignore signal if not
        # in batch mode
        if not self.__batch and fn != self.filename:
            return

        fixed = None
        ignoredErrors = collections.defaultdict(int)
        if self.__itms:
            for itm, result in zip(self.__itms, results, strict=False):
                self.__modifyFixedResultItem(itm, result)
            self.__updateFixerStatistics(fixes)
        else:
            self.__lastFileItem = None

            for result in results:
                if result["ignored"]:
                    ignoredErrors[result["code"]] += 1
                    if self.showIgnored:
                        result["display"] = self.tr("{0} (ignored)").format(
                            result["display"]
                        )
                    else:
                        continue

                self.results = DocStyleCheckerDialog.hasResults
                self.__createResultItem(fn, result)

            self.__updateStatistics(docStyleCheckerStats, fixes, ignoredErrors)

        if fixed:
            vm = ericApp().getObject("ViewManager")
            editor = vm.getOpenEditor(fn)
            if editor:
                editor.refresh()

        self.progress += 1
        self.__updateProgress(fn)

        if not self.__batch:
            self.check()

    def __updateProgress(self, fn):
        """
        Private method to update the progress tab.

        @param fn filename of the just checked file
        @type str
        """
        if self.__project:
            fn = os.path.join("...", self.__project.getRelativePath(fn))

        self.checkProgress.setValue(self.progress)

        # remove file from the list of jobs to do
        fileItems = self.progressList.findItems(fn, Qt.MatchFlag.MatchExactly)
        if fileItems:
            row = self.progressList.row(fileItems[0])
            self.progressList.takeItem(row)

        if time.monotonic() - self.__timenow > 0.01:
            QApplication.processEvents()
            self.__timenow = time.monotonic()

    def __finish(self):
        """
        Private slot called when the code style check finished or the user
        pressed the cancel button.
        """
        if not self.__finished:
            self.__finished = True

            self.cancelled = True
            self.buttonBox.button(QDialogButtonBox.StandardButton.Close).setEnabled(
                True
            )
            self.buttonBox.button(QDialogButtonBox.StandardButton.Close).setDefault(
                True
            )
            self.cancelButton.setEnabled(False)
            self.statisticsButton.setEnabled(True)
            self.showButton.setEnabled(True)
            self.startButton.setEnabled(True)
            self.restartButton.setEnabled(True)

            if self.results != DocStyleCheckerDialog.hasResults:
                if self.results == DocStyleCheckerDialog.noResults:
                    QTreeWidgetItem(self.resultList, [self.tr("No issues found.")])
                else:
                    QTreeWidgetItem(
                        self.resultList,
                        [self.tr("No files found (check your ignore list).")],
                    )
                QApplication.processEvents()
                self.showButton.setEnabled(False)
            else:
                self.showButton.setEnabled(True)
            for col in range(self.resultList.columnCount()):
                self.resultList.resizeColumnToContents(col)
            self.resultList.header().setStretchLastSection(True)

            if self.__detectedCodes:
                self.filterComboBox.addItem("")
                self.filterComboBox.addItems(sorted(set(self.__detectedCodes)))
                self.filterComboBox.setEnabled(True)
                self.filterButton.setEnabled(True)

            self.checkProgress.setVisible(False)

            self.__resort()
            self.resultList.setUpdatesEnabled(True)
            self.resultList.setSortingEnabled(True)

            self.mainWidget.setCurrentWidget(self.resultsTab)

    def __getEol(self, fn):
        """
        Private method to get the applicable eol string.

        @param fn filename where to determine the line ending
        @type str
        @return eol string
        @rtype str
        """
        return (
            self.__project.getEolString()
            if self.__project.isOpen() and self.__project.isProjectFile(fn)
            else Utilities.linesep()
        )

    @pyqtSlot()
    def on_startButton_clicked(self):
        """
        Private slot to start a documentation style check run.
        """
        if self.__forProject:
            data = {
                "DocstringType": self.docTypeComboBox.itemData(
                    self.docTypeComboBox.currentIndex()
                ),
                "MaxLineLength": self.lineLengthSpinBox.value(),
                "ExcludeFiles": self.excludeFilesEdit.text(),
                "ExcludeMessages": self.excludeMessagesEdit.text(),
                "IncludeMessages": self.includeMessagesEdit.text(),
                "RepeatMessages": self.repeatCheckBox.isChecked(),
                "ShowIgnored": self.ignoredCheckBox.isChecked(),
                "FixCodes": self.fixIssuesEdit.text(),
                "NoFixCodes": self.noFixIssuesEdit.text(),
                "FixIssues": self.fixIssuesCheckBox.isChecked(),
            }

            if json.dumps(data, sort_keys=True) != json.dumps(
                self.__data, sort_keys=True
            ):
                self.__data = data
                self.__project.setData("CHECKERSPARMS", "DocStyleChecker", self.__data)

        self.resultList.clear()
        self.results = DocStyleCheckerDialog.noResults
        self.cancelled = False
        self.__detectedCodes.clear()
        self.filterComboBox.clear()
        self.filterComboBox.setEnabled(False)
        self.filterButton.setEnabled(False)

        self.start(self.__fileOrFileList)

    @pyqtSlot()
    def on_restartButton_clicked(self):
        """
        Private slot to restart a code style check run.
        """
        self.on_startButton_clicked()

    def __selectCodes(self, edit, showFixCodes):
        """
        Private method to select message codes via a selection dialog.

        @param edit reference of the line edit to be populated
        @type QLineEdit
        @param showFixCodes flag indicating to show a list of fixable
            issues
        @type bool
        """
        from .DocStyleCodeSelectionDialog import DocStyleCodeSelectionDialog

        dlg = DocStyleCodeSelectionDialog(edit.text(), showFixCodes, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            edit.setText(dlg.getSelectedCodes())

    @pyqtSlot()
    def on_excludeMessagesSelectButton_clicked(self):
        """
        Private slot to select the message codes to be excluded via a
        selection dialog.
        """
        self.__selectCodes(self.excludeMessagesEdit, False)

    @pyqtSlot()
    def on_includeMessagesSelectButton_clicked(self):
        """
        Private slot to select the message codes to be included via a
        selection dialog.
        """
        self.__selectCodes(self.includeMessagesEdit, False)

    @pyqtSlot()
    def on_fixIssuesSelectButton_clicked(self):
        """
        Private slot to select the issue codes to be fixed via a
        selection dialog.
        """
        self.__selectCodes(self.fixIssuesEdit, True)

    @pyqtSlot()
    def on_noFixIssuesSelectButton_clicked(self):
        """
        Private slot to select the issue codes not to be fixed via a
        selection dialog.
        """
        self.__selectCodes(self.noFixIssuesEdit, True)

    @pyqtSlot(QTreeWidgetItem, int)
    def on_resultList_itemActivated(self, item, _column):
        """
        Private slot to handle the activation of an item.

        @param item reference to the activated item
        @type QTreeWidgetItem
        @param _column column the item was activated in (unused)
        @type int
        """
        if (
            self.results != DocStyleCheckerDialog.hasResults
            or item.data(0, self.filenameRole) is None
        ):
            return

        if item.parent():
            fn = item.data(0, self.filenameRole)
            lineno = item.data(0, self.lineRole)
            position = item.data(0, self.positionRole)
            message = item.data(0, self.messageRole)
            issueCode = item.data(0, self.codeRole)

            vm = ericApp().getObject("ViewManager")
            vm.openSourceFile(fn, lineno=lineno, pos=position + 1)
            editor = vm.getOpenEditor(fn)

            if issueCode in ["E-901", "E-902"]:
                editor.toggleSyntaxError(lineno, 0, True, message, True)
            else:
                editor.toggleWarning(
                    lineno,
                    0,
                    True,
                    self.tr("{0} - {1}", "issue code, message").format(
                        issueCode, message
                    ),
                    warningType=EditorWarningKind.Style,
                )

            editor.updateVerticalScrollBar()

    @pyqtSlot()
    def on_resultList_itemSelectionChanged(self):
        """
        Private slot to change the dialog state depending on the selection.
        """
        self.fixButton.setEnabled(len(self.__getSelectedFixableItems()) > 0)

    @pyqtSlot()
    def on_showButton_clicked(self):
        """
        Private slot to handle the "Show" button press.
        """
        vm = ericApp().getObject("ViewManager")

        selectedIndexes = [
            index
            for index in range(self.resultList.topLevelItemCount())
            if self.resultList.topLevelItem(index).isSelected()
        ]
        if len(selectedIndexes) == 0:
            selectedIndexes = list(range(self.resultList.topLevelItemCount()))
        for index in selectedIndexes:
            itm = self.resultList.topLevelItem(index)
            if itm.data(0, self.filenameRole) is not None:
                fn = itm.data(0, self.filenameRole)
                vm.openSourceFile(fn, 1)
                editor = vm.getOpenEditor(fn)
                editor.clearStyleWarnings()
                for cindex in range(itm.childCount()):
                    citm = itm.child(cindex)
                    editor.toggleWarning(
                        citm.data(0, self.lineRole),
                        0,
                        True,
                        self.tr("{0} - {1}", "issue code, message").format(
                            citm.data(0, self.codeRole),
                            citm.data(0, self.messageRole),
                        ),
                        warningType=EditorWarningKind.Style,
                    )

        # go through the list again to clear warning markers for files,
        # that are ok
        openFiles = vm.getOpenFilenames()
        errorFiles = []
        for index in range(self.resultList.topLevelItemCount()):
            itm = self.resultList.topLevelItem(index)
            errorFiles.append(itm.data(0, self.filenameRole))
        for file in openFiles:
            if file not in errorFiles:
                editor = vm.getOpenEditor(file)
                editor.clearStyleWarnings()

        editor = vm.activeWindow()
        editor.updateVerticalScrollBar()

    @pyqtSlot()
    def on_statisticsButton_clicked(self):
        """
        Private slot to show the statistics dialog.
        """
        from .DocStyleStatisticsDialog import DocStyleStatisticsDialog

        dlg = DocStyleStatisticsDialog(self.__statistics, parent=self)
        dlg.exec()

    @pyqtSlot()
    def on_loadDefaultButton_clicked(self):
        """
        Private slot to load the default configuration values.
        """
        defaultParameters = self.getDefaults()
        settings = Preferences.getSettings()

        self.docTypeComboBox.setCurrentIndex(
            self.docTypeComboBox.findData(
                settings.value(
                    "DocStyle/DocstringType", defaultParameters["DocstringType"]
                )
            )
        )
        self.lineLengthSpinBox.setValue(
            int(
                settings.value(
                    "DocStyle/MaxLineLength", defaultParameters["MaxLineLength"]
                )
            )
        )
        self.excludeFilesEdit.setText(
            settings.value(
                "DocStyle/ExcludeFilePatterns", defaultParameters["ExcludeFiles"]
            )
        )
        self.excludeMessagesEdit.setText(
            settings.value(
                "DocStyle/ExcludeMessages", defaultParameters["ExcludeMessages"]
            )
        )
        self.includeMessagesEdit.setText(
            settings.value(
                "DocStyle/IncludeMessages", defaultParameters["IncludeMessages"]
            )
        )
        self.repeatCheckBox.setChecked(
            EricUtilities.toBool(
                settings.value(
                    "DocStyle/RepeatMessages", defaultParameters["RepeatMessages"]
                )
            )
        )
        self.ignoredCheckBox.setChecked(
            EricUtilities.toBool(
                settings.value("DocStyle/ShowIgnored", defaultParameters["ShowIgnored"])
            )
        )
        self.fixIssuesEdit.setText(
            settings.value("DocStyle/FixCodes", defaultParameters["FixCodes"])
        )
        self.noFixIssuesEdit.setText(
            settings.value("DocStyle/NoFixCodes", defaultParameters["NoFixCodes"])
        )
        self.fixIssuesCheckBox.setChecked(
            EricUtilities.toBool(
                settings.value("DocStyle/FixIssues", defaultParameters["FixIssues"])
            )
        )

    @pyqtSlot()
    def on_storeDefaultButton_clicked(self):
        """
        Private slot to store the current configuration values as
        default values.
        """
        settings = Preferences.getSettings()

        settings.setValue(
            "DocStyle/DocstringType",
            self.docTypeComboBox.itemData(self.docTypeComboBox.currentIndex()),
        )
        settings.setValue("DocStyle/MaxLineLength", self.lineLengthSpinBox.value())
        settings.setValue("DocStyle/ExcludeFilePatterns", self.excludeFilesEdit.text())
        settings.setValue("DocStyle/ExcludeMessages", self.excludeMessagesEdit.text())
        settings.setValue("DocStyle/IncludeMessages", self.includeMessagesEdit.text())
        settings.setValue("DocStyle/RepeatMessages", self.repeatCheckBox.isChecked())
        settings.setValue("DocStyle/MaxLineLength", self.lineLengthSpinBox.value())
        settings.setValue("DocStyle/FixCodes", self.fixIssuesEdit.text())
        settings.setValue("DocStyle/NoFixCodes", self.noFixIssuesEdit.text())
        settings.setValue("DocStyle/FixIssues", self.fixIssuesCheckBox.isChecked())
        settings.setValue("DocStyle/ShowIgnored", self.ignoredCheckBox.isChecked())

    @pyqtSlot()
    def on_resetDefaultButton_clicked(self):
        """
        Private slot to reset the configuration values to their default values.
        """
        defaultParameters = self.getDefaults()
        settings = Preferences.getSettings()

        settings.setValue("DocStyle/DocstringType", defaultParameters["DocstringType"])
        settings.setValue("DocStyle/MaxLineLength", defaultParameters["MaxLineLength"])
        settings.setValue(
            "DocStyle/ExcludeFilePatterns", defaultParameters["ExcludeFiles"]
        )
        settings.setValue(
            "DocStyle/ExcludeMessages", defaultParameters["ExcludeMessages"]
        )
        settings.setValue(
            "DocStyle/IncludeMessages", defaultParameters["IncludeMessages"]
        )
        settings.setValue(
            "DocStyle/RepeatMessages", defaultParameters["RepeatMessages"]
        )
        settings.setValue("DocStyle/ShowIgnored", defaultParameters["ShowIgnored"])
        settings.setValue("DocStyle/FixCodes", defaultParameters["FixCodes"])
        settings.setValue("DocStyle/NoFixCodes", defaultParameters["NoFixCodes"])
        settings.setValue("DocStyle/FixIssues", defaultParameters["FixIssues"])

        # Update UI with default values
        self.on_loadDefaultButton_clicked()

    def closeEvent(self, _evt):
        """
        Protected method to handle a close event.

        @param _evt reference to the close event (unused)
        @type QCloseEvent
        """
        self.on_cancelButton_clicked()

    @pyqtSlot()
    def on_cancelButton_clicked(self):
        """
        Private slot to handle the "Cancel" button press.
        """
        if self.__batch:
            self.styleCheckService.cancelStyleBatchCheck()
            QTimer.singleShot(1000, self.__finish)
        else:
            self.__finish()

    @pyqtSlot(QAbstractButton)
    def on_buttonBox_clicked(self, button):
        """
        Private slot called by a button of the button box clicked.

        @param button button that was clicked
        @type QAbstractButton
        """
        if button == self.buttonBox.button(QDialogButtonBox.StandardButton.Close):
            self.close()

    def __clearErrors(self, files):
        """
        Private method to clear all warning markers of open editors to be
        checked.

        @param files list of files to be checked
        @type list of str
        """
        vm = ericApp().getObject("ViewManager")
        openFiles = vm.getOpenFilenames()
        for file in [f for f in openFiles if f in files]:
            editor = vm.getOpenEditor(file)
            editor.clearStyleWarnings()

    @pyqtSlot()
    def on_fixButton_clicked(self):
        """
        Private slot to fix selected issues.

        Build a dictionary of issues to fix. Update the initialized __options.
        Then call check with the dict as keyparam to fix selected issues.
        """
        fixableItems = self.__getSelectedFixableItems()
        # dictionary of lists of tuples containing the issue and the item
        fixesDict = {}
        for itm in fixableItems:
            filename = itm.data(0, self.filenameRole)
            if filename not in fixesDict:
                fixesDict[filename] = []
            fixesDict[filename].append(
                (
                    {
                        "file": filename,
                        "line": itm.data(0, self.lineRole),
                        "offset": itm.data(0, self.positionRole),
                        "code": itm.data(0, self.codeRole),
                        "display": itm.data(0, self.messageRole),
                        "args": itm.data(0, self.argsRole),
                    },
                    itm,
                )
            )

        # update the configuration values (3: fixCodes, 4: noFixCodes,
        # 5: fixIssues, 6: maxLineLength)
        self.__options[3] = self.fixIssuesEdit.text()
        self.__options[4] = self.noFixIssuesEdit.text()
        self.__options[5] = True
        self.__options[6] = self.lineLengthSpinBox.value()

        self.files = list(fixesDict)
        # now go through all the files
        self.progress = 0
        self.files.sort()
        self.cancelled = False
        self.__onlyFixes = fixesDict
        self.check()

    def __getSelectedFixableItems(self):
        """
        Private method to extract all selected items for fixable issues.

        @return selected items for fixable issues
        @rtype list of QTreeWidgetItem
        """
        fixableItems = []
        for itm in self.resultList.selectedItems():
            if itm.childCount() > 0:
                for index in range(itm.childCount()):
                    citm = itm.child(index)
                    if self.__itemFixable(citm) and citm not in fixableItems:
                        fixableItems.append(citm)
            elif self.__itemFixable(itm) and itm not in fixableItems:
                fixableItems.append(itm)

        return fixableItems

    def __itemFixable(self, itm):
        """
        Private method to check, if an item has a fixable issue.

        @param itm item to be checked
        @type QTreeWidgetItem
        @return flag indicating a fixable issue
        @rtype bool
        """
        return itm.data(0, self.fixableRole) and not itm.data(0, self.ignoredRole)

    @pyqtSlot()
    def on_filterButton_clicked(self):
        """
        Private slot to filter the list of messages based on selected message
        code.
        """
        selectedMessageCode = self.filterComboBox.currentText()

        for topRow in range(self.resultList.topLevelItemCount()):
            topItem = self.resultList.topLevelItem(topRow)
            topItem.setExpanded(True)
            visibleChildren = topItem.childCount()
            for childIndex in range(topItem.childCount()):
                childItem = topItem.child(childIndex)
                hideChild = (
                    childItem.data(0, self.codeRole) != selectedMessageCode
                    if selectedMessageCode
                    else False
                )
                childItem.setHidden(hideChild)
                if hideChild:
                    visibleChildren -= 1
            topItem.setHidden(visibleChildren == 0)
