#
# Copyright (c) 2010 - 2026 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing the Mercurial version control plugin.
"""

import contextlib
import os

from PyQt6.QtCore import QByteArray, QCoreApplication, QObject

from eric7 import EricUtilities, Preferences
from eric7.EricWidgets.EricApplication import ericApp
from eric7.Plugins.VcsPlugins.vcsMercurial.HgUtilities import (
    getHgExecutable,
)
from eric7.Preferences.Shortcuts import readShortcuts
from eric7.SystemUtilities import FileSystemUtilities
from eric7.__version__ import VersionOnly

# Start-Of-Header
__header__ = {
    "name": "Mercurial Plugin",
    "author": "Detlev Offenbach <detlev@die-offenbachs.de>",
    "autoactivate": False,
    "deactivateable": True,
    "version": VersionOnly,
    "pluginType": "version_control",
    "pluginTypename": "Mercurial",
    "className": "VcsMercurialPlugin",
    "packageName": "__core__",
    "shortDescription": "Implements the Mercurial version control interface.",
    "longDescription": (
        """This plugin provides the Mercurial version control interface."""
    ),
    "pyqtApi": 2,
}
# End-Of-Header

error = ""  # noqa: U-200


def exeDisplayData():
    """
    Public method to support the display of some executable info.

    @return dictionary containing the data to query the presence of
        the executable
    @rtype dict
    """
    return {
        "programEntry": True,
        "header": QCoreApplication.translate(
            "VcsMercurialPlugin", "Version Control - Mercurial"
        ),
        "exe": getHgExecutable(),
        "versionCommand": "version",
        "versionStartsWith": "Mercurial",
        "versionPosition": -1,
        "version": "",
        "versionCleanup": (0, -1),
    }


def getVcsSystemIndicator():
    """
    Public function to get the indicators for this version control system.

    @return dictionary with indicator as key and a tuple with the vcs name
        and vcs display string
    @rtype dict
    """
    data = {}
    exe = getHgExecutable()
    if FileSystemUtilities.isinpath(exe):
        data[".hg"] = (__header__["pluginTypename"], displayString())
        data["_hg"] = (__header__["pluginTypename"], displayString())
    return data


def displayString():
    """
    Public function to get the display string.

    @return display string
    @rtype str
    """
    exe = getHgExecutable()
    if FileSystemUtilities.isinpath(exe):
        return QCoreApplication.translate("VcsMercurialPlugin", "Mercurial")
    return ""


def createConfigurationPage(_configDlg):
    """
    Module function to create the configuration page.

    @param _configDlg reference to the configuration dialog (unused)
    @type QDialog
    @return reference to the configuration page
    @rtype MercurialPage
    """
    from eric7.Plugins.VcsPlugins.vcsMercurial.ConfigurationPage.MercurialPage import (
        MercurialPage,
    )

    return MercurialPage()


def getConfigData():
    """
    Module function returning data as required by the configuration dialog.

    @return dictionary with key "zzz_mercurialPage" containing the relevant data
    @rtype dict
    """
    return {
        "zzz_mercurialPage": [
            QCoreApplication.translate("VcsMercurialPlugin", "Mercurial"),
            os.path.join(
                "VcsPlugins", "vcsMercurial", "icons", "preferences-mercurial.svg"
            ),
            createConfigurationPage,
            "vcsPage",
            None,
        ],
    }


def prepareUninstall():
    """
    Module function to prepare for an uninstallation.
    """
    if not ericApp().getObject("PluginManager").isPluginLoaded("PluginVcsMercurial"):
        Preferences.getSettings().remove("Mercurial")


def clearPrivateData():
    """
    Module function to clear the private data of the plug-in.
    """
    for key in ["RepositoryUrlHistory"]:
        VcsMercurialPlugin.setPreferences(key, [])


class VcsMercurialPlugin(QObject):
    """
    Class implementing the Mercurial version control plugin.
    """

    MercurialDefaults = {
        "StopLogOnCopy": True,  # used in log browser
        "LogLimit": 20,
        "Commits": [],
        "CommitAuthorsLimit": 20,
        "CommitAuthors": [],
        "PullUpdate": False,
        "PreferUnbundle": False,
        "ServerPort": 8000,
        "ServerStyle": "",
        "CleanupPatterns": "*.orig *.rej *~",
        "CreateBackup": False,
        "InternalMerge": False,
        "Encoding": "utf-8",
        "EncodingMode": "strict",
        "ConsiderHidden": False,
        "LogMessageColumnWidth": 30,
        "LogBrowserShowFullLog": True,
        "LogBrowserGeometry": QByteArray(),
        "LogBrowserSplitterStates": [QByteArray(), QByteArray(), QByteArray()],
        # mainSplitter, detailsSplitter, diffSplitter
        "StatusDialogGeometry": QByteArray(),
        "StatusDialogSplitterState": QByteArray(),
        "MqStatusDialogGeometry": QByteArray(),
        "MqStatusDialogSplitterState": QByteArray(),
        "RepositoryUrlHistory": [],
        "MercurialExecutablePath": "",
    }

    def __init__(self, ui):
        """
        Constructor

        @param ui reference to the user interface object
        @type UserInterface
        """
        from eric7.Plugins.VcsPlugins.vcsMercurial.ProjectHelper import HgProjectHelper

        super().__init__(ui)
        self.__ui = ui

        self.__projectHelperObject = HgProjectHelper(None, None, parent=ui)
        with contextlib.suppress(KeyError):
            ericApp().registerPluginObject(
                __header__["pluginTypename"],
                self.__projectHelperObject,
                __header__["pluginType"],
            )
        readShortcuts(pluginName=__header__["pluginTypename"])

    def getProjectHelper(self):
        """
        Public method to get a reference to the project helper object.

        @return reference to the project helper object
        @rtype HgProjectHelper
        """
        return self.__projectHelperObject

    def initToolbar(self, ui, toolbarManager):
        """
        Public slot to initialize the VCS toolbar.

        @param ui reference to the main window
        @type UserInterface
        @param toolbarManager reference to a toolbar manager object
        @type EricToolBarManager
        """
        if self.__projectHelperObject:
            self.__projectHelperObject.initToolbar(ui, toolbarManager)

    def activate(self):
        """
        Public method to activate this plugin.

        @return tuple of reference to instantiated viewmanager and
            activation status
        @rtype tuple of (Hg, bool)
        """
        from eric7.Plugins.VcsPlugins.vcsMercurial.hg import Hg

        self.__object = Hg(self, self.__ui)

        tb = self.__ui.getToolbar("vcs")[1]
        tb.setVisible(False)
        tb.setEnabled(False)

        tb = self.__ui.getToolbar("mercurial")[1]
        tb.setVisible(Preferences.getVCS("ShowVcsToolbar"))
        tb.setEnabled(True)

        return self.__object, True

    def deactivate(self):
        """
        Public method to deactivate this plugin.
        """
        self.__object = None

        tb = self.__ui.getToolbar("mercurial")[1]
        tb.setVisible(False)
        tb.setEnabled(False)

        tb = self.__ui.getToolbar("vcs")[1]
        tb.setVisible(Preferences.getVCS("ShowVcsToolbar"))
        tb.setEnabled(True)

    @classmethod
    def getPreferences(cls, key):
        """
        Class method to retrieve the various settings.

        @param key the key of the value to get
        @type str
        @return the requested setting
        @rtype Any
        """
        if key in (
            "StopLogOnCopy",
            "PullUpdate",
            "PreferUnbundle",
            "CreateBackup",
            "InternalMerge",
            "ConsiderHidden",
            "LogBrowserShowFullLog",
        ):
            return EricUtilities.toBool(
                Preferences.getSettings().value(
                    "Mercurial/" + key, cls.MercurialDefaults[key]
                )
            )
        if key in (
            "LogLimit",
            "CommitAuthorsLimit",
            "ServerPort",
            "LogMessageColumnWidth",
        ):
            return int(
                Preferences.getSettings().value(
                    "Mercurial/" + key, cls.MercurialDefaults[key]
                )
            )
        if key in ("Commits", "CommitAuthors", "RepositoryUrlHistory"):
            return EricUtilities.toList(
                Preferences.getSettings().value(
                    "Mercurial/" + key, cls.MercurialDefaults[key]
                )
            )
        if key in (
            "LogBrowserGeometry",
            "StatusDialogGeometry",
            "StatusDialogSplitterState",
            "MqStatusDialogGeometry",
            "MqStatusDialogSplitterState",
        ):
            # QByteArray values
            v = Preferences.getSettings().value("Mercurial/" + key)
            if v is not None:
                return v
            return cls.MercurialDefaults[key]
        if key in ["LogBrowserSplitterStates"]:
            # list of QByteArray values
            states = Preferences.getSettings().value("Mercurial/" + key)
            if states is not None:
                return states
            return cls.MercurialDefaults[key]
        return Preferences.getSettings().value(
            "Mercurial/" + key, cls.MercurialDefaults[key]
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
        Preferences.getSettings().setValue("Mercurial/" + key, value)

    @classmethod
    def getGlobalOptions(self):
        """
        Class method to build a list of global options.

        @return list of global options
        @rtype list of str
        """
        args = []
        if (
            VcsMercurialPlugin.getPreferences("Encoding")
            != VcsMercurialPlugin.MercurialDefaults["Encoding"]
        ):
            args.append("--encoding")
            args.append(VcsMercurialPlugin.getPreferences("Encoding"))
        if (
            VcsMercurialPlugin.getPreferences("EncodingMode")
            != VcsMercurialPlugin.MercurialDefaults["EncodingMode"]
        ):
            args.append("--encodingmode")
            args.append(VcsMercurialPlugin.getPreferences("EncodingMode"))
        if VcsMercurialPlugin.getPreferences("ConsiderHidden"):
            args.append("--hidden")
        return args

    def prepareUninstall(self):
        """
        Public method to prepare for an uninstallation.
        """
        ericApp().unregisterPluginObject(__header__["pluginTypename"])

    def prepareUnload(self):
        """
        Public method to prepare for an unload.
        """
        if self.__projectHelperObject:
            self.__projectHelperObject.removeToolbar(
                self.__ui, ericApp().getObject("ToolbarManager")
            )
        ericApp().unregisterPluginObject(__header__["pluginTypename"])
