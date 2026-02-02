#
# Copyright (c) 2014 - 2026 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Translator plugin.
"""

import os

from PyQt6.QtCore import QCoreApplication, QObject, pyqtSignal

from eric7 import EricUtilities, Preferences
from eric7.EricWidgets.EricApplication import ericApp
from eric7.Plugins.UiExtensionPlugins.Translator.Translator import Translator
from eric7.__version__ import VersionOnly

# Start-Of-Header
__header__ = {
    "name": "Translator Plugin",
    "author": "Detlev Offenbach <detlev@die-offenbachs.de>",
    "autoactivate": True,
    "deactivateable": True,
    "version": VersionOnly,
    "className": "TranslatorPlugin",
    "packageName": "__core__",
    "shortDescription": "Translation utility using various translators.",
    "longDescription": (
        """This plug-in implements a utility to translate text using"""
        """ various online translation services."""
    ),
    "needsRestart": False,
    "pyqtApi": 2,
}
# End-Of-Header

error = ""  # noqa: U-200

translatorPluginObject = None


def createTranslatorPage(_configDlg):
    """
    Module function to create the Translator configuration page.

    @param _configDlg reference to the configuration dialog (unused)
    @type ConfigurationWidget
    @return reference to the configuration page
    @rtype TranslatorPage
    """
    from eric7.Plugins.UiExtensionPlugins.Translator.ConfigurationPage import (
        TranslatorPage,
    )

    return TranslatorPage.TranslatorPage()


def createTranslationServicesPage(_configDlg):
    """
    Module function to create the Translation Services configuration page.

    @param _configDlg reference to the configuration dialog (unused)
    @type ConfigurationWidget
    @return reference to the configuration page
    @rtype TranslatorPage
    """
    from eric7.Plugins.UiExtensionPlugins.Translator.ConfigurationPage import (
        TranslationServicesPage,
    )

    return TranslationServicesPage.TranslationServicesPage()


def getConfigData():
    """
    Module function returning data as required by the configuration dialog.

    @return dictionary containing the relevant data
    @rtype dict
    """
    iconMode = "dark" if ericApp().usesDarkPalette() else "light"

    return {
        "0translatorPages": [
            QCoreApplication.translate("TranslatorPlugin", "Translator"),
            os.path.join(
                "UiExtensionPlugins", "Translator", "icons", f"flag-{iconMode}"
            ),
            None,
            None,
            None,
        ],
        "translatorPage": [
            QCoreApplication.translate("TranslatorPlugin", "Translator"),
            os.path.join(
                "UiExtensionPlugins", "Translator", "icons", f"flag-{iconMode}"
            ),
            createTranslatorPage,
            "0translatorPages",
            None,
        ],
        "translationServicesPage": [
            QCoreApplication.translate("TranslatorPlugin", "Translation Services"),
            os.path.join(
                "UiExtensionPlugins", "Translator", "icons", f"services-{iconMode}"
            ),
            createTranslationServicesPage,
            "0translatorPages",
            None,
        ],
    }


def prepareUninstall():
    """
    Module function to prepare for an uninstallation.
    """
    Preferences.getSettings().remove(TranslatorPlugin.PreferencesKey)


class TranslatorPlugin(QObject):
    """
    Class implementing the Translator plug-in.

    @signal preferencesChanged() emitted to signal a change of preferences. This
        signal is simply relayed from the main UI.
    @signal updateLanguages() emitted to indicate a languages update
    """

    PreferencesKey = "Translator"
    DefaultPreferences = {
        "OriginalLanguage": "en",
        "TranslationLanguage": "de",
        "SelectedEngine": "deepl",
        "EnabledLanguages": [
            "en",
            "de",
            "fr",
            "cs",
            "es",
            "pt",
            "ru",
            "tr",
            "zh-CN",
            "zh-TW",
        ],
        "MultimediaEnabled": False,
        # service specific settings below
        # DeepL
        "DeeplKey": "",
        # Google V1
        "GoogleEnableDictionary": False,
        # Google V2
        "GoogleV2Key": "",
        # IBM Watson
        "IbmUrl": "",
        "IbmKey": "",
        # LibreTranslate
        "LibreTranslateUrl": "http://localhost:5000",
        "libreTranslateKey": "",
        # Microsoft
        "MsTranslatorKey": "",
        "MsTranslatorRegion": "",
        # MyMemory
        "MyMemoryKey": "",
        "MyMemoryEmail": "",
        # Ollama
        "OllamaResponseTimeout": 30_000,  # 30 seconds response timeout given in ms
        "OllamaServerProfile": "{}",  # JSON formatted empty dict of server profile
        "OllamaRecentlyUsedModelName": "",
        "OllamaModelNames": [],  # list of available translation models
        "OllamaContextSize": 0,  # default context window
        # Yandex
        "YandexKey": "",
    }
    preferencesChanged = pyqtSignal()
    updateLanguages = pyqtSignal()

    def __init__(self, ui):
        """
        Constructor

        @param ui reference to the user interface object
        @type UI.UserInterface
        """
        super().__init__(ui)
        self.__ui = ui
        self.__initialize()

    def __initialize(self):
        """
        Private slot to (re)initialize the plugin.
        """
        self.__object = None

    def activate(self):
        """
        Public method to activate this plugin.

        @return tuple of None and activation status
        @rtype tuple of (None, bool)
        """
        global error
        error = ""  # clear previous error

        global translatorPluginObject
        translatorPluginObject = self

        self.__object = Translator(self, ericApp().usesDarkPalette(), self.__ui)
        self.__object.activate()
        ericApp().registerPluginObject("Translator", self.__object)

        self.__ui.preferencesChanged.connect(self.preferencesChanged)

        return None, True

    def deactivate(self):
        """
        Public method to deactivate this plugin.
        """
        self.__ui.preferencesChanged.disconnect(self.preferencesChanged)

        ericApp().unregisterPluginObject("Translator")
        self.__object.deactivate()

        self.__initialize()

    @classmethod
    def getPreferencesDefault(cls, key):
        """
        Class method to retrieve the various default settings.

        @param key the key of the value to get
        @type str
        @return the requested setting
        @rtype Any
        """
        return TranslatorPlugin.DefaultPreferences[key]

    @classmethod
    def getPreferences(cls, key):
        """
        Class method to retrieve the various settings.

        @param key the key of the value to get
        @type str
        @return the requested setting
        @rtype Any
        """
        if key in ("EnabledLanguages", "OllamaModelNames"):
            return EricUtilities.toList(
                Preferences.getSettings().value(
                    f"{TranslatorPlugin.PreferencesKey}/{key}",
                    TranslatorPlugin.DefaultPreferences[key],
                )
            )

        if key in ("GoogleEnableDictionary", "MultimediaEnabled"):
            return EricUtilities.toBool(
                Preferences.getSettings().value(
                    f"{TranslatorPlugin.PreferencesKey}/{key}",
                    TranslatorPlugin.DefaultPreferences[key],
                )
            )

        if key in ("OllamaResponseTimeout", "OllamaContextSize"):
            return int(
                Preferences.getSettings().value(
                    f"{TranslatorPlugin.PreferencesKey}/{key}",
                    TranslatorPlugin.DefaultPreferences[key],
                )
            )
        return Preferences.getSettings().value(
            f"{TranslatorPlugin.PreferencesKey}/{key}",
            TranslatorPlugin.DefaultPreferences[key],
        )

    @classmethod
    def setPreferences(cls, key, value):
        """
        Class method to store the various settings.

        @param key the key of the setting to be set
        @type str
        @param value the value to be set
        @type Any
        """
        Preferences.getSettings().setValue(
            f"{TranslatorPlugin.PreferencesKey}/{key}", value
        )

        if key in ["EnabledLanguages"] and translatorPluginObject is not None:
            translatorPluginObject.updateLanguages.emit()
