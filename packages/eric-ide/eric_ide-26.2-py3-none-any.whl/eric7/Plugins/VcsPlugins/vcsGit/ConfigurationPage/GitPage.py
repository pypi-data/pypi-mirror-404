#
# Copyright (c) 2014 - 2026 Detlev Offenbach <detlev@die-offenbachs.de>
#


"""
Module implementing the Git configuration page.
"""

import contextlib
import os

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QDialog

from eric7.Plugins.PluginVcsGit import VcsGitPlugin
from eric7.Preferences.ConfigurationPages.ConfigurationPageBase import (
    ConfigurationPageBase,
)

from .Ui_GitPage import Ui_GitPage


class GitPage(ConfigurationPageBase, Ui_GitPage):
    """
    Class implementing the Git configuration page.
    """

    def __init__(self):
        """
        Constructor
        """
        super().__init__()
        self.setupUi(self)
        self.setObjectName("GitPage")

        # set initial values
        # log
        self.logSpinBox.setValue(VcsGitPlugin.getPreferences("LogLimit"))
        self.logWidthSpinBox.setValue(
            VcsGitPlugin.getPreferences("LogSubjectColumnWidth")
        )
        self.findHarderCheckBox.setChecked(
            VcsGitPlugin.getPreferences("FindCopiesHarder")
        )
        # commit
        self.commitIdSpinBox.setValue(VcsGitPlugin.getPreferences("CommitIdLength"))
        # branch naming
        self.politicalCorrectnessCheckBox.setChecked(
            VcsGitPlugin.getPreferences("PoliticalCorrectness")
        )
        # cleanup
        self.cleanupPatternEdit.setText(VcsGitPlugin.getPreferences("CleanupPatterns"))
        # repository optimization
        self.aggressiveCheckBox.setChecked(VcsGitPlugin.getPreferences("AggressiveGC"))

    def save(self):
        """
        Public slot to save the Git configuration.
        """
        # log
        VcsGitPlugin.setPreferences("LogLimit", self.logSpinBox.value())
        VcsGitPlugin.setPreferences(
            "LogSubjectColumnWidth", self.logWidthSpinBox.value()
        )
        VcsGitPlugin.setPreferences(
            "FindCopiesHarder", self.findHarderCheckBox.isChecked()
        )
        # commit
        VcsGitPlugin.setPreferences("CommitIdLength", self.commitIdSpinBox.value())
        # branch naming
        VcsGitPlugin.setPreferences(
            "PoliticalCorrectness", self.politicalCorrectnessCheckBox.isChecked()
        )
        # cleanup
        VcsGitPlugin.setPreferences("CleanupPatterns", self.cleanupPatternEdit.text())
        # repository optimization
        VcsGitPlugin.setPreferences("AggressiveGC", self.aggressiveCheckBox.isChecked())

    @pyqtSlot()
    def on_configButton_clicked(self):
        """
        Private slot to edit the (per user) Git configuration file.
        """
        from eric7.QScintilla.MiniEditor import MiniEditor

        from ..GitUserConfigDataDialog import GitUserConfigDataDialog
        from ..GitUtilities import getConfigPath

        cfgFile = getConfigPath()
        if not os.path.exists(cfgFile):
            dlg = GitUserConfigDataDialog(parent=self)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                firstName, lastName, email = dlg.getData()
            else:
                firstName, lastName, email = ("Firstname", "Lastname", "email_address")
            with contextlib.suppress(OSError), open(cfgFile, "w") as f:
                f.write("[user]\n")
                f.write("    name = {0} {1}\n".format(firstName, lastName))
                f.write("    email = {0}\n".format(email))
        editor = MiniEditor(cfgFile, "Properties", self)
        editor.show()
