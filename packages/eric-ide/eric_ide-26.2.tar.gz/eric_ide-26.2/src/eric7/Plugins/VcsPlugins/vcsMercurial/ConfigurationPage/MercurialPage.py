#
# Copyright (c) 2010 - 2026 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Mercurial configuration page.
"""

import os

from PyQt6.QtCore import pyqtSlot

from eric7.EricWidgets.EricApplication import ericApp
from eric7.EricWidgets.EricPathPicker import EricPathPickerModes
from eric7.Plugins.PluginVcsMercurial import VcsMercurialPlugin
from eric7.Preferences.ConfigurationPages.ConfigurationPageBase import (
    ConfigurationPageBase,
)
from eric7.SystemUtilities import OSUtilities, PythonUtilities
from eric7.Utilities import supportedCodecs

from .. import HgUtilities
from .Ui_MercurialPage import Ui_MercurialPage


class MercurialPage(ConfigurationPageBase, Ui_MercurialPage):
    """
    Class implementing the Mercurial configuration page.
    """

    def __init__(self):
        """
        Constructor
        """
        super().__init__()
        self.setupUi(self)
        self.setObjectName("MercurialPage")

        self.hgPicker.setMode(EricPathPickerModes.OPEN_FILE_MODE)
        if OSUtilities.isWindowsPlatform():
            self.hgPicker.setFilters(self.tr("Executable Files (*.exe);;All Files (*)"))
        else:
            self.hgPicker.setFilters(self.tr("All Files (*)"))

        self.encodingComboBox.addItems(sorted(supportedCodecs))
        self.encodingModeComboBox.addItems(["strict", "ignore", "replace"])

        self.installButton.setEnabled(not self.__mercurialInstalled())

        # set initial values
        # executable override
        self.hgPicker.setText(
            VcsMercurialPlugin.getPreferences("MercurialExecutablePath")
        )

        # global options
        index = self.encodingComboBox.findText(
            VcsMercurialPlugin.getPreferences("Encoding")
        )
        self.encodingComboBox.setCurrentIndex(index)
        index = self.encodingModeComboBox.findText(
            VcsMercurialPlugin.getPreferences("EncodingMode")
        )
        self.encodingModeComboBox.setCurrentIndex(index)
        self.hiddenChangesetsCheckBox.setChecked(
            VcsMercurialPlugin.getPreferences("ConsiderHidden")
        )
        # log
        self.logSpinBox.setValue(VcsMercurialPlugin.getPreferences("LogLimit"))
        self.logWidthSpinBox.setValue(
            VcsMercurialPlugin.getPreferences("LogMessageColumnWidth")
        )
        self.startFullLogCheckBox.setChecked(
            VcsMercurialPlugin.getPreferences("LogBrowserShowFullLog")
        )
        # commit
        self.commitAuthorsSpinBox.setValue(
            VcsMercurialPlugin.getPreferences("CommitAuthorsLimit")
        )
        # pull
        self.pullUpdateCheckBox.setChecked(
            VcsMercurialPlugin.getPreferences("PullUpdate")
        )
        self.preferUnbundleCheckBox.setChecked(
            VcsMercurialPlugin.getPreferences("PreferUnbundle")
        )
        # cleanup
        self.cleanupPatternEdit.setText(
            VcsMercurialPlugin.getPreferences("CleanupPatterns")
        )
        # revert
        self.backupCheckBox.setChecked(
            VcsMercurialPlugin.getPreferences("CreateBackup")
        )
        # merge
        self.internalMergeCheckBox.setChecked(
            VcsMercurialPlugin.getPreferences("InternalMerge")
        )

    def save(self):
        """
        Public slot to save the Mercurial configuration.
        """
        # executable override
        VcsMercurialPlugin.setPreferences(
            "MercurialExecutablePath", self.hgPicker.text()
        )
        # global options
        VcsMercurialPlugin.setPreferences(
            "Encoding", self.encodingComboBox.currentText()
        )
        VcsMercurialPlugin.setPreferences(
            "EncodingMode", self.encodingModeComboBox.currentText()
        )
        VcsMercurialPlugin.setPreferences(
            "ConsiderHidden", self.hiddenChangesetsCheckBox.isChecked()
        )
        # log
        VcsMercurialPlugin.setPreferences("LogLimit", self.logSpinBox.value())
        VcsMercurialPlugin.setPreferences(
            "LogMessageColumnWidth", self.logWidthSpinBox.value()
        )
        VcsMercurialPlugin.setPreferences(
            "LogBrowserShowFullLog", self.startFullLogCheckBox.isChecked()
        )
        # commit
        VcsMercurialPlugin.setPreferences(
            "CommitAuthorsLimit", self.commitAuthorsSpinBox.value()
        )
        # pull
        VcsMercurialPlugin.setPreferences(
            "PullUpdate", self.pullUpdateCheckBox.isChecked()
        )
        VcsMercurialPlugin.setPreferences(
            "PreferUnbundle", self.preferUnbundleCheckBox.isChecked()
        )
        # cleanup
        VcsMercurialPlugin.setPreferences(
            "CleanupPatterns", self.cleanupPatternEdit.text()
        )
        # revert
        VcsMercurialPlugin.setPreferences(
            "CreateBackup", self.backupCheckBox.isChecked()
        )
        # merge
        VcsMercurialPlugin.setPreferences(
            "InternalMerge", self.internalMergeCheckBox.isChecked()
        )

    @pyqtSlot()
    def on_configButton_clicked(self):
        """
        Private slot to edit the (per user) Mercurial configuration file.
        """
        from ..HgUserConfigDialog import HgUserConfigDialog
        from ..HgUtilities import hgVersion

        dlg = HgUserConfigDialog(version=hgVersion(self.__plugin)[1], parent=self)
        dlg.exec()

    @pyqtSlot()
    def on_installButton_clicked(self):
        """
        Private slot to install Mercurial alongside eric7.
        """
        pip = ericApp().getObject("Pip")
        pip.installPackages(
            ["mercurial"], interpreter=PythonUtilities.getPythonExecutable()
        )
        self.installButton.setEnabled(not self.__mercurialInstalled())

    def __mercurialInstalled(self):
        """
        Private method to check, if Mercurial is installed alongside eric7.

        @return flag indicating an installed Mercurial executable
        @rtype bool
        """
        hg = HgUtilities.getHgExecutable()
        # assume local installation, if the path is absolute
        return os.path.isabs(hg)
