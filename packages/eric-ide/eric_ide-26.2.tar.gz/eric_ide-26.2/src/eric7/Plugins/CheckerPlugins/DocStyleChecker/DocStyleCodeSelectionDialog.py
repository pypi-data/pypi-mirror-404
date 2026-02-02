#
# Copyright (c) 2025 - 2026 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a dialog to select documentation style message codes.
"""

import textwrap

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QTreeWidgetItem

from eric7.EricGui import EricPixmapCache

from .DocStyleFixer import FixableDocStyleIssues
from .Ui_DocStyleCodeSelectionDialog import Ui_DocStyleCodeSelectionDialog
from .translations import getMessageCodes, getTranslatedMessage


class DocStyleCodeSelectionDialog(QDialog, Ui_DocStyleCodeSelectionDialog):
    """
    Class implementing a dialog to select documentation style message codes.
    """

    def __init__(self, codes, showFixCodes, parent=None):
        """
        Constructor

        @param codes comma separated list of selected codes
        @type str
        @param showFixCodes flag indicating to show a list of fixable
            issues
        @type bool
        @param parent reference to the parent widget
        @type QWidget
        """
        super().__init__(parent)
        self.setupUi(self)

        textWrapper = textwrap.TextWrapper(width=60)

        self.codeTable.headerItem().setText(self.codeTable.columnCount(), "")
        codeList = [c.strip() for c in codes.split(",") if c.strip()]

        if showFixCodes:
            selectableCodes = FixableDocStyleIssues
        else:
            selectableCodes = [x for x in getMessageCodes() if not x.startswith("FIX")]
        for msgCode in sorted(selectableCodes):
            message = getTranslatedMessage(msgCode, [], example=True)
            if message is None:
                # try with extension
                for ext in ("1", "2"):
                    message = getTranslatedMessage(
                        "{0}.{1}".format(msgCode, ext), [], example=True
                    )
                    if message is not None:
                        break
                else:
                    continue
            itm = QTreeWidgetItem(
                self.codeTable, [msgCode, "\n".join(textWrapper.wrap(message))]
            )
            itm.setIcon(0, EricPixmapCache.getIcon("docstringError"))
            itm.setFlags(itm.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            if msgCode in codeList:
                itm.setCheckState(0, Qt.CheckState.Checked)
                codeList.remove(msgCode)
            else:
                itm.setCheckState(0, Qt.CheckState.Unchecked)
        self.codeTable.resizeColumnToContents(0)
        self.codeTable.resizeColumnToContents(1)
        self.codeTable.header().setStretchLastSection(True)

        self.__extraCodes = codeList[:]

    def getSelectedCodes(self):
        """
        Public method to get a comma separated list of codes selected.

        @return comma separated list of selected codes
        @rtype str
        """
        selectedCodes = []

        for index in range(self.codeTable.topLevelItemCount()):
            itm = self.codeTable.topLevelItem(index)
            if itm.checkState(0) == Qt.CheckState.Checked:
                selectedCodes.append(itm.text(0))

        return ", ".join(self.__extraCodes + selectedCodes)
