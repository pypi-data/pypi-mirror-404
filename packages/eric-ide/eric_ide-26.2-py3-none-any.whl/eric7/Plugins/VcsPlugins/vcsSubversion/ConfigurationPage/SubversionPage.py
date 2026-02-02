#
# Copyright (c) 2007 - 2026 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Subversion configuration page.
"""

from PyQt6.QtCore import pyqtSlot

from eric7.Plugins.PluginVcsSubversion import VcsSubversionPlugin
from eric7.Preferences.ConfigurationPages.ConfigurationPageBase import (
    ConfigurationPageBase,
)

from ..SvnUtilities import getConfigPath, getServersPath
from .Ui_SubversionPage import Ui_SubversionPage


class SubversionPage(ConfigurationPageBase, Ui_SubversionPage):
    """
    Class implementing the Subversion configuration page.
    """

    def __init__(self):
        """
        Constructor
        """
        super().__init__()
        self.setupUi(self)
        self.setObjectName("SubversionPage")

        # set initial values
        self.logSpinBox.setValue(VcsSubversionPlugin.getPreferences("LogLimit"))

    def save(self):
        """
        Public slot to save the Subversion configuration.
        """
        VcsSubversionPlugin.setPreferences("LogLimit", self.logSpinBox.value())

    @pyqtSlot()
    def on_configButton_clicked(self):
        """
        Private slot to edit the Subversion config file.
        """
        from eric7.QScintilla.MiniEditor import MiniEditor

        cfgFile = getConfigPath()
        editor = MiniEditor(cfgFile, "Properties", self)
        editor.show()

    @pyqtSlot()
    def on_serversButton_clicked(self):
        """
        Private slot to edit the Subversion servers file.
        """
        from eric7.QScintilla.MiniEditor import MiniEditor

        serversFile = getServersPath()
        editor = MiniEditor(serversFile, "Properties", self)
        editor.show()
