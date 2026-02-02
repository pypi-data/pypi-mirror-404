#
# Copyright (c) 2014 - 2026 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Translator configuration page.
"""

import sys

from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import QListWidgetItem

from eric7.EricWidgets import EricMessageBox
from eric7.Plugins.PluginTranslator import TranslatorPlugin
from eric7.Preferences.ConfigurationPages.ConfigurationPageBase import (
    ConfigurationPageBase,
)

from ..TranslatorLanguagesDb import TranslatorLanguagesDb
from .Ui_TranslatorPage import Ui_TranslatorPage


class TranslatorPage(ConfigurationPageBase, Ui_TranslatorPage):
    """
    Class implementing the Translator configuration page.
    """

    def __init__(self):
        """
        Constructor
        """
        super().__init__()
        self.setupUi(self)
        self.setObjectName("TranslatorPage")

        self.__enableLanguageWarning = True

        # set initial values
        enabledLanguages = TranslatorPlugin.getPreferences("EnabledLanguages")
        languages = TranslatorLanguagesDb()
        for languageCode in languages.getAllLanguages():
            itm = QListWidgetItem()
            itm.setText(languages.getLanguage(languageCode))
            itm.setIcon(languages.getLanguageIcon(languageCode))
            itm.setData(Qt.ItemDataRole.UserRole, languageCode)
            if languageCode in enabledLanguages or not enabledLanguages:
                itm.setCheckState(Qt.CheckState.Checked)
            else:
                itm.setCheckState(Qt.CheckState.Unchecked)
            self.languagesList.addItem(itm)
        self.languagesList.sortItems()

        if "--no-multimedia" in sys.argv:
            self.pronounceCheckBox.setChecked(False)
            self.pronounceCheckBox.setEnabled(False)
        else:
            self.pronounceCheckBox.setChecked(
                TranslatorPlugin.getPreferences("MultimediaEnabled")
            )

    def save(self):
        """
        Public slot to save the translators configuration.
        """
        enabledLanguages = [
            itm.data(Qt.ItemDataRole.UserRole) for itm in self.__checkedLanguageItems()
        ]
        TranslatorPlugin.setPreferences("EnabledLanguages", enabledLanguages)

        TranslatorPlugin.setPreferences(
            "MultimediaEnabled", self.pronounceCheckBox.isChecked()
        )

    def __checkedLanguageItems(self):
        """
        Private method to get a list of checked language items.

        @return list of checked language items
        @rtype list of QListWidgetItem
        """
        items = []
        for index in range(self.languagesList.count()):
            itm = self.languagesList.item(index)
            if itm.checkState() == Qt.CheckState.Checked:
                items.append(itm)

        return items

    @pyqtSlot()
    def on_setButton_clicked(self):
        """
        Private slot to set or unset all items.
        """
        self.__enableLanguageWarning = False

        unset = len(self.__checkedLanguageItems()) > 0
        for index in range(self.languagesList.count()):
            itm = self.languagesList.item(index)
            if unset:
                itm.setCheckState(Qt.CheckState.Unchecked)
            else:
                itm.setCheckState(Qt.CheckState.Checked)

        self.__enableLanguageWarning = True

    @pyqtSlot()
    def on_defaultButton_clicked(self):
        """
        Private slot to set the default languages.
        """
        self.__enableLanguageWarning = False

        defaults = TranslatorPlugin.getPreferencesDefault("EnabledLanguages")
        for index in range(self.languagesList.count()):
            itm = self.languagesList.item(index)
            if itm.data(Qt.ItemDataRole.UserRole) in defaults:
                itm.setCheckState(Qt.CheckState.Checked)
            else:
                itm.setCheckState(Qt.CheckState.Unchecked)

        self.__enableLanguageWarning = True

    @pyqtSlot(QListWidgetItem)
    def on_languagesList_itemChanged(self, _item):
        """
        Private slot to handle the selection of an item.

        @param _item reference to the changed item
        @type QListWidgetItem
        """
        if self.__enableLanguageWarning and len(self.__checkedLanguageItems()) < 2:
            EricMessageBox.warning(
                self,
                self.tr("Enabled Languages"),
                self.tr(
                    """At least two languages should be selected to"""
                    """ work correctly."""
                ),
            )
