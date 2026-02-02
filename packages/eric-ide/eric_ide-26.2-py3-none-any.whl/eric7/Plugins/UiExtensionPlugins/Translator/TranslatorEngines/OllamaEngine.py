#
# Copyright (c) 2026 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the 'ollama' translation engine.
"""

import importlib

from PyQt6.QtCore import QCoreApplication, QEventLoop, QTimer, pyqtSlot
from PyQt6.QtWidgets import QInputDialog

from eric7.EricWidgets import EricMessageBox
from eric7.Plugins.PluginTranslator import TranslatorPlugin

from .TranslationEngine import TranslationEngine


class TranslationModelUnavailableError(BaseException):
    """
    Class defining an exception for unavailable translation models.
    """


class TranslationModelSelectionError(BaseException):
    """
    Class defining an exception for no selected translation models.
    """


class OllamaEngine(TranslationEngine):
    """
    Class implementing the translation engine for the 'translategemma' model
    of an 'ollama' server.
    """

    TranslatorModelName = "translategemma"

    CodeLanguageMapping = {
        "af": "Afrikaans",
        "ar": "Arabic",
        "be": "Belarusian",
        "bg": "Bulgarian",
        "bs": "Bosnian",
        "ca": "Catalan",
        "cs": "Czech",
        "da": "Danish",
        "de": "German",
        "el": "Greek",
        "en": "English",
        "es": "Spanish",
        "et": "Estonian",
        "fi": "Finnish",
        "fr": "French",
        "ga": "Irish",
        "gl": "Galician",
        "he": "Hebrew",
        "hi": "Hindi",
        "hr": "Croatian",
        "hu": "Hungarian",
        "id": "Indonesian",
        "is": "Icelandic",
        "it": "Italian",
        "ja": "Japanese",
        "ka": "Georgian",
        "ko": "Korean",
        "lt": "Lithuanian",
        "lv": "Latvian",
        "mk": "Macedonian",
        "mt": "Maltese",
        "nb": "Norwegian Bokmål",
        "nl": "Dutch",
        "no": "Norwegian",
        "pl": "Polish",
        "pt": "Portuguese",
        "ro": "Romanian",
        "ru": "Russian",
        "sk": "Slovak",
        "sl": "Slovenian",
        "sq": "Albanian",
        "sr": "Serbian",
        "sv": "Swedish",
        "th": "Thai",
        "tl": "Tagalog",
        "tr": "Turkish",
        "uk": "Ukrainian",
        "vi": "Vietnamese",
        "zh": "Chinese",
        "zh-CN": "Chinese",
        "zh-TW": "Chinese",
    }

    MessageTemplate = (
        "You are a professional {SOURCE_LANG} ({SOURCE_CODE}) to {TARGET_LANG}\n"
        "({TARGET_CODE}) translator. Your goal is to accurately convey the meaning\n"
        "and nuances of the original {SOURCE_LANG} text while adhering to\n"
        "{TARGET_LANG} grammar, vocabulary, and cultural sensitivities.\n"
        "Produce only the {TARGET_LANG} translation, without any additional\n"
        "explanations or commentary.\n"
        "Please translate the following {SOURCE_LANG} text into {TARGET_LANG}:\n"
        "\n"
        "\n"
        "{TEXT}"
    )

    def __init__(self, plugin, parent=None):
        """
        Constructor

        @param plugin reference to the plugin object
        @type TranslatorPlugin
        @param parent reference to the parent object
        @type QObject
        @exception TranslationModelUnavailableError raised to signal the unavailability
            of any 'translategemma' model
        @exception TranslationModelSelectionError raised when the user did not select
            any 'translategemma' model variant
        """
        from OllamaInterface.OllamaClient import OllamaClient
        from OllamaInterface.OllamaServerProfile import OllamaServerProfile

        super().__init__(plugin, parent)

        self.__translationResponse = None
        self.__translationError = None

        self.__loop = QEventLoop()

        self.__client = OllamaClient(plugin=plugin, parent=self)
        self.__client.serverStateChanged.connect(self.__handleServerStateChanged)
        self.__client.generateReplyReceived.connect(self.__handleTranslationResponse)
        self.__client.errorOccurred.connect(self.__handleServerError)

        self.__profile = OllamaServerProfile.fromJSON(
            TranslatorPlugin.getPreferences("OllamaServerProfile")
        )
        self.__client.connectToServer(self.__profile)

        models = self.__client.listDetails()
        availableModels = [
            m["name"]
            for m in models
            if m["name"].split(":")[0] == OllamaEngine.TranslatorModelName
        ]
        TranslatorPlugin.setPreferences("OllamaModelNames", availableModels)
        if len(availableModels) == 0:
            raise TranslationModelUnavailableError(
                self.tr(
                    "<p>The translation model <b>{0}</b> is not available. Load it"
                    " via the 'ollama AI Interface' tool.</p>"
                ).format(OllamaEngine.TranslatorModelName)
            )
        if len(availableModels) == 1:
            translationModel = availableModels[0]
        else:
            recentModel = TranslatorPlugin.getPreferences("OllamaRecentlyUsedModelName")
            if recentModel in availableModels:
                translationModel = recentModel
            else:
                model, ok = QInputDialog.getItem(
                    None,
                    self.tr("'ollama' Translation Model"),
                    self.tr("Select the translation model to be used:"),
                    availableModels,
                    0,
                    False,
                )
                if not ok:
                    raise TranslationModelSelectionError(
                        self.tr("No model selected by user.")
                    )
                translationModel = model
        TranslatorPlugin.setPreferences("OllamaRecentlyUsedModelName", translationModel)

        QTimer.singleShot(0, self.availableTranslationsLoaded.emit)

    def engineName(self):
        """
        Public method to return the name of the engine.

        @return engine name
        @rtype str
        """
        return "ollama"

    def supportedLanguages(self):
        """
        Public method to get the supported languages.

        @return list of supported language codes
        @rtype list of str
        """
        return [
            "af",
            "ar",
            "be",
            "bg",
            "bs",
            "ca",
            "cs",
            "da",
            "de",
            "el",
            "en",
            "es",
            "et",
            "fi",
            "fr",
            "ga",
            "gl",
            "he",
            "hi",
            "hr",
            "hu",
            "id",
            "is",
            "it",
            "ja",
            "ka",
            "ko",
            "lt",
            "lv",
            "mk",
            "mt",
            "nb",
            "nl",
            "no",
            "pl",
            "pt",
            "ro",
            "ru",
            "sk",
            "sl",
            "sq",
            "sr",
            "sv",
            "th",
            "tl",
            "tr",
            "uk",
            "vi",
            "zh",
            "zh-CN",
            "zh-TW",
        ]

    def getTranslation(
        self,
        requestObject,  # noqa: ARG002
        text,
        originalLanguage,
        translationLanguage,
    ):
        """
        Public method to translate the given text.

        @param requestObject reference to the request object
        @type TranslatorRequest
        @param text text to be translated
        @type str
        @param originalLanguage language code of the original
        @type str
        @param translationLanguage language code of the translation
        @type str
        @return tuple of translated text and flag indicating success
        @rtype tuple of (str, bool)
        """
        prompt = OllamaEngine.MessageTemplate.format(
            SOURCE_LANG=OllamaEngine.CodeLanguageMapping[originalLanguage],
            SOURCE_CODE=originalLanguage,
            TARGET_LANG=OllamaEngine.CodeLanguageMapping[translationLanguage],
            TARGET_CODE=translationLanguage,
            TEXT=text,
        )
        self.__translationResponse = None
        self.__translationError = None

        self.__client.generate(
            model=TranslatorPlugin.getPreferences("OllamaRecentlyUsedModelName"),
            prompt=prompt,
            timeout=TranslatorPlugin.getPreferences("OllamaResponseTimeout"),
            streaming=False,
        )

        if not self.__loop.isRunning():
            self.__loop.exec()

        if self.__translationError is not None:
            return self.__translationError, False

        if self.__translationResponse is None:
            return self.tr("No translation possible."), False

        return self.__translationResponse, True

    @pyqtSlot(str)
    def __handleTranslationResponse(self, translation):
        """
        Private slot handling the server translation response.

        @param translation translated text
        @type str
        """
        self.__translationResponse = translation
        if self.__loop.isRunning():
            self.__loop.quit()

    @pyqtSlot(str)
    def __handleServerError(self, message):
        """
        Private slot handling an issue reported by the 'ollama' server or the
        server interface.

        @param message error message
        @type str
        """
        if self.__loop.isRunning():
            # waiting for a translation response
            self.__translationError = message
            self.__loop.quit()
            return

        EricMessageBox.critical(
            None,
            self.tr("'ollama' Error"),
            self.tr(
                "<p>There was an issue when accessing the 'ollama' server.</p>"
                "<p>Error: {0}</p>"
            ).format(message),
        )

    def shutdown(self):
        """
        Public method to perform shutdown actions before the engine is discarded.
        """
        self.__client.disconnectFromServer()

    @pyqtSlot(bool, str)
    def __handleServerStateChanged(self, connected, msg):
        """
        Private slot handling a change in the 'ollama' server connected state.

        @param connected flag indicating the connected state of an 'ollama' server
        @type bool
        @param msg status message
        @type str
        """
        if not connected and msg:
            EricMessageBox.critical(
                None,
                self.tr("'ollama' Server State"),
                self.tr(
                    "<p>The 'ollama' server was disconnected due to an issue.</p>"
                    "<p>Reason: {0}</p>"
                ).format(msg),
            )


def createEngine(plugin, parent=None):
    """
    Function to instantiate a translator engine object.

    @param plugin reference to the plugin object
    @type TranslatorPlugin
    @param parent reference to the parent object (defaults to None)
    @type QObject (optional)
    @return reference to the instantiated translator engine object
    @rtype DeepLEngine
    """
    if importlib.util.find_spec("OllamaInterface") is None:
        EricMessageBox.critical(
            None,
            QCoreApplication.translate("OllamaEngine", "Ollama Translation Interface"),
            QCoreApplication.translate(
                "OllamaEngine",
                "<p>The Ollama interface plugin is not installed. Install it via the"
                " <b>Plugin Repository</b> tool.</p>",
            ),
        )
        return None

    try:
        return OllamaEngine(plugin, parent=parent)
    except TranslationModelUnavailableError as err:
        EricMessageBox.critical(
            None,
            QCoreApplication.translate("OllamaEngine", "Ollama Translation Interface"),
            str(err),
        )
    except (AttributeError, KeyError):
        EricMessageBox.critical(
            None,
            QCoreApplication.translate("OllamaEngine", "Ollama Translation Interface"),
            QCoreApplication.translate(
                "OllamaEngine",
                "<p>The <b>Ollama Interface</b> plugin is not compatible. Ensure the"
                " latest version is installed.</p>",
            ),
        )

    return None
