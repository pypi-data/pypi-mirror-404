#
# Copyright (c) 2014 - 2026 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Translation Services configuration page.
"""

from PyQt6.QtCore import pyqtSlot

from eric7.EricGui import EricPixmapCache
from eric7.EricUtilities.crypto import pwConvert
from eric7.Plugins.PluginTranslator import TranslatorPlugin
from eric7.Preferences.ConfigurationPages.ConfigurationPageBase import (
    ConfigurationPageBase,
)

try:
    from OllamaInterface.OllamaServerProfile import OllamaServerProfile
except ImportError:
    OllamaServerProfile = None

from .. import TranslatorEngines
from .Ui_TranslationServicesPage import Ui_TranslationServicesPage


class TranslationServicesPage(ConfigurationPageBase, Ui_TranslationServicesPage):
    """
    Class implementing the Translation Services configuration page.
    """

    def __init__(self):
        """
        Constructor
        """
        super().__init__()
        self.setupUi(self)
        self.setObjectName("TranslationServicesPage")

        self.deeplLabel.setText(
            self.tr(
                """<p>A key is <b>required</b> to use this service."""
                """ <a href="{0}">Get a commercial or free API key.</a></p>"""
            ).format(TranslatorEngines.getKeyUrl("deepl"))
        )
        self.googlev2Label.setText(
            self.tr(
                """<p>A key is <b>required</b> to use this service."""
                """ <a href="{0}">Get a commercial API key.</a></p>"""
            ).format(TranslatorEngines.getKeyUrl("googlev2"))
        )
        self.ibmLabel.setText(
            self.tr(
                """<p>A key is <b>required</b> to use this service."""
                """ <a href="{0}">Register with IBM Cloud.</a></p>"""
            ).format(TranslatorEngines.getKeyUrl("ibm_watson"))
        )
        self.libreLabel.setText(
            self.tr(
                """<p>A key is <b>optional</b> to use this service and depends on the"""
                """ server configuration. Contact your server admin for details.</p>"""
            )
        )
        self.msLabel.setText(
            self.tr(
                """<p>A registration of the text translation service is"""
                """ <b>required</b>. <a href="{0}">Register with Microsoft"""
                """ Azure.</a></p>"""
            ).format(TranslatorEngines.getKeyUrl("microsoft"))
        )
        self.mymemoryLabel.setText(
            self.tr(
                """<p>A key is <b>optional</b> to use this service."""
                """ <a href="{0}">Get a free API key.</a></p>"""
            ).format(TranslatorEngines.getKeyUrl("mymemory"))
        )
        self.yandexLabel.setText(
            self.tr(
                """<p>A key is <b>required</b> to use this service."""
                """ <a href="{0}">Get a free API key.</a></p>"""
            ).format(TranslatorEngines.getKeyUrl("yandex"))
        )

        self.reloadModelsButton.setIcon(EricPixmapCache.getIcon("reload"))

        # set initial values
        # DeepL settings
        self.deeplKeyEdit.setText(TranslatorPlugin.getPreferences("DeeplKey"))

        # Google settings
        self.dictionaryCheckBox.setChecked(
            TranslatorPlugin.getPreferences("GoogleEnableDictionary")
        )
        self.googlev2KeyEdit.setText(TranslatorPlugin.getPreferences("GoogleV2Key"))

        # IBM Watson settings
        self.ibmUrlEdit.setText(TranslatorPlugin.getPreferences("IbmUrl"))
        self.ibmKeyEdit.setText(TranslatorPlugin.getPreferences("IbmKey"))

        # LibreTranslate settings
        self.libreUrlEdit.setText(TranslatorPlugin.getPreferences("LibreTranslateUrl"))
        self.libreKeyEdit.setText(TranslatorPlugin.getPreferences("libreTranslateKey"))

        # Microsoft settings
        self.msSubscriptionKeyEdit.setText(
            TranslatorPlugin.getPreferences("MsTranslatorKey")
        )
        self.msSubscriptionRegionEdit.setText(
            TranslatorPlugin.getPreferences("MsTranslatorRegion")
        )

        # MyMemory settings
        self.mymemoryKeyEdit.setText(TranslatorPlugin.getPreferences("MyMemoryKey"))
        self.mymemoryEmailEdit.setText(TranslatorPlugin.getPreferences("MyMemoryEmail"))

        # Ollama (translategemma) settings
        if OllamaServerProfile:
            ollamaProfile = OllamaServerProfile.fromJSON(
                TranslatorPlugin.getPreferences("OllamaServerProfile")
            )
            self.serverSchemeComboBox.setCurrentText(ollamaProfile.scheme)
            self.serverHostEdit.setText(ollamaProfile.hostname)
            self.serverPortSpinBox.setValue(ollamaProfile.port)
            self.authTokenEdit.setText(ollamaProfile.authtoken)
            self.usernameEdit.setText(ollamaProfile.username)
            self.passwordEdit.setText(pwConvert(ollamaProfile.password, encode=False))
            if ollamaProfile.authtoken:
                self.authTokenButton.setChecked(True)
            elif ollamaProfile.username:
                self.basicAuthButton.setChecked(True)
            else:
                self.noAuthButton.setChecked(True)

            self.modelComboBox.addItems(
                TranslatorPlugin.getPreferences("OllamaModelNames")
            )
            self.modelComboBox.setCurrentText(
                TranslatorPlugin.getPreferences("OllamaRecentlyUsedModelName")
            )
            self.contextWindowSpinBox.setValue(
                TranslatorPlugin.getPreferences("OllamaContextSize")
            )
            self.responseTimeoutSpinBox.setValue(
                TranslatorPlugin.getPreferences("OllamaResponseTimeout") // 1000
            )
        else:
            self.ollamaGroup.setEnabled(False)

        # Yandex settings
        self.yandexKeyEdit.setText(TranslatorPlugin.getPreferences("YandexKey"))

    def save(self):
        """
        Public slot to save the translators configuration.
        """
        # DeepL settings
        TranslatorPlugin.setPreferences("DeeplKey", self.deeplKeyEdit.text())

        # Google settings
        TranslatorPlugin.setPreferences(
            "GoogleEnableDictionary", self.dictionaryCheckBox.isChecked()
        )
        TranslatorPlugin.setPreferences("GoogleV2Key", self.googlev2KeyEdit.text())

        # IBM Watson settings
        TranslatorPlugin.setPreferences("IbmUrl", self.ibmUrlEdit.text())
        TranslatorPlugin.setPreferences("IbmKey", self.ibmKeyEdit.text())

        # LibreTranslate settings
        TranslatorPlugin.setPreferences("LibreTranslateUrl", self.libreUrlEdit.text())
        TranslatorPlugin.setPreferences("libreTranslateKey", self.libreKeyEdit.text())

        # Microsoft settings
        TranslatorPlugin.setPreferences(
            "MsTranslatorKey", self.msSubscriptionKeyEdit.text()
        )
        TranslatorPlugin.setPreferences(
            "MsTranslatorRegion", self.msSubscriptionRegionEdit.text()
        )

        # MyMemory settings
        TranslatorPlugin.setPreferences("MyMemoryKey", self.mymemoryKeyEdit.text())

        # Ollama (translategemma) settings
        if OllamaServerProfile is not None:
            scheme = self.serverSchemeComboBox.currentText()
            port = self.serverPortSpinBox.value()
            if port == 0:
                if scheme == "http":
                    self.serverPortSpinBox.setValue(80)
                elif scheme == "https":
                    self.serverPortSpinBox.setValue(443)

            ollamaProfile = OllamaServerProfile(
                scheme=scheme,
                hostname=self.serverHostEdit.text(),
                port=self.serverPortSpinBox.value(),
                authtoken=self.authTokenEdit.text(),
                username=self.usernameEdit.text(),
                password=pwConvert(self.passwordEdit.text(), encode=True),
            )

            # clear not used authentication entries
            if self.noAuthButton.isChecked():
                ollamaProfile.authtoken = ""
                ollamaProfile.username = ""
                ollamaProfile.password = ""
            elif self.authTokenButton.isChecked():
                ollamaProfile.username = ""
                ollamaProfile.password = ""
            elif self.basicAuthButton.isChecked():
                ollamaProfile.authtoken = ""

            TranslatorPlugin.setPreferences(
                "OllamaServerProfile", ollamaProfile.toJSON()
            )
            TranslatorPlugin.setPreferences(
                "OllamaRecentlyUsedModelName", self.modelComboBox.currentText()
            )
            TranslatorPlugin.setPreferences(
                "OllamaContextSize", self.contextWindowSpinBox.value()
            )
            TranslatorPlugin.setPreferences(
                "OllamaResponseTimeout", self.responseTimeoutSpinBox.value()
            )

        # Yandex settings
        TranslatorPlugin.setPreferences("YandexKey", self.yandexKeyEdit.text())

    @pyqtSlot()
    def on_reloadModelsButton_clicked(self):
        """
        Private slot to reload the list of available translation models.
        """
        self.modelComboBox.clear()
        self.modelComboBox.addItems(TranslatorPlugin.getPreferences("OllamaModelNames"))
        self.modelComboBox.setCurrentText(
            TranslatorPlugin.getPreferences("OllamaRecentlyUsedModelName")
        )
