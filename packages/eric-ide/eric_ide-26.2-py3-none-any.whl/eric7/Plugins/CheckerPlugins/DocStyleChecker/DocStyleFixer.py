#
# Copyright (c) 2025 - 2026 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a class to fix certain documentation style issues.
"""

import codecs
import contextlib
import os
import re

FixableCodeStyleIssues = [  # noqa: U-200
    "D-111",
    "D-112",
    "D-121",
    "D-131",
    "D-141",
    "D-142",
    "D-143",
    "D-144",
    "D-145",
    "D-221",
    "D-222",
    "D-231",
    "D-242",
    "D-243",
    "D-244",
    "D-245",
    "D-246",
    "D-247",
]


class DocStyleFixer:
    """
    Class implementing a fixer for certain documentation style issues.
    """

    def __init__(
        self,
        filename,
        sourceLines,
        fixCodes,
        noFixCodes,
        maxLineLength,
        inPlace,
        eol,
        backup=False,
    ):
        """
        Constructor

        @param filename name of the file to be fixed
        @type str
        @param sourceLines list of source lines including eol marker
        @type list of str
        @param fixCodes list of codes to be fixed as a comma separated
            string
        @type str
        @param noFixCodes list of codes not to be fixed as a comma
            separated string
        @type str
        @param maxLineLength maximum allowed line length
        @type int
        @param inPlace flag indicating to modify the file in place
        @type bool
        @param eol end of line character(s)
        @type str
        @param backup flag indicating to create a backup before fixing
            anything
        @type bool
        """
        super().__init__()

        self.__filename = filename
        self.__origName = ""
        self.__source = sourceLines[:]  # save a copy
        self.__fixCodes = [c.strip() for c in fixCodes.split(",") if c.strip()]
        self.__noFixCodes = [c.strip() for c in noFixCodes.split(",") if c.strip()]
        self.__maxLineLength = maxLineLength
        self.fixed = 0

        if inPlace:
            self.__createBackup = backup
        else:
            self.__origName = self.__filename
            self.__filename = os.path.join(
                os.path.dirname(self.__filename),
                "fixed_" + os.path.basename(self.__filename),
            )
            self.__createBackup = False
        self.__eol = eol

        self.__fixes = {
            "D-111": self.__fixD111,
            "D-112": self.__fixD112,
            "D-121": self.__fixD121,
            "D-131": self.__fixD131_D231,
            "D-141": self.__fixD141,
            "D-142": self.__fixD142,
            "D-143": self.__fixD143,
            "D-144": self.__fixD144_D246,
            "D-145": self.__fixD145,
            "D-221": self.__fixD221_D222,
            "D-222": self.__fixD221_D222,
            "D-231": self.__fixD131_D231,
            "D-242": self.__fixD242_D244,
            "D-243": self.__fixD243_D245,
            "D-244": self.__fixD242_D244,
            "D-245": self.__fixD243_D245,
            "D-246": self.__fixD144_D246,
            "D-247": self.__fixD247,
        }
        self.__modified = False
        self.__stack = []
        # These need to be fixed before the file is saved but after all
        # inline fixes.

        self.__multiLineNumbers = None
        self.__docLineNumbers = None

        self.__lastID = 0

    def saveFile(self, encoding):
        """
        Public method to save the modified file.

        @param encoding encoding of the source file
        @type str
        @return error message on failure
        @rtype tuple of (str, [str])
        """
        if not self.__modified:
            # no need to write
            return None

        if self.__createBackup:
            # create a backup file before writing any changes
            if os.path.islink(self.__filename):
                bfn = "{0}~".format(os.path.realpath(self.__filename))
            else:
                bfn = "{0}~".format(self.__filename)
            with contextlib.suppress(OSError):
                os.remove(bfn)
            with contextlib.suppress(OSError):
                os.rename(self.__filename, bfn)

        txt = "".join(self.__source)
        try:
            enc = "utf-8" if encoding == "utf-8-bom" else encoding
            txt = txt.encode(enc)
            if encoding == "utf-8-bom":
                txt = codecs.BOM_UTF8 + txt

            with open(self.__filename, "wb") as fp:
                fp.write(txt)
        except (OSError, UnicodeError) as err:
            # Could not save the file! Skipping it. Reason: {0}
            return ("FIX-WRITE_ERROR", [str(err)])

        return None

    def __codeMatch(self, code):
        """
        Private method to check, if the code should be fixed.

        @param code to check
        @type str
        @return flag indicating it should be fixed
        @rtype bool
        """

        def mutualStartswith(a, b):
            """
            Local helper method to compare the beginnings of two strings
            against each other.

            @return flag indicating that one string starts with the other
            @rtype bool
            """
            return b.startswith(a) or a.startswith(b)

        if self.__noFixCodes and any(
            mutualStartswith(code.lower(), noFixCode.lower())
            for noFixCode in [c.strip() for c in self.__noFixCodes]
        ):
            return False

        if self.__fixCodes:
            return any(
                mutualStartswith(code.lower(), fixCode.lower())
                for fixCode in [c.strip() for c in self.__fixCodes]
            )

        return True

    def fixIssue(self, line, pos, code):
        """
        Public method to fix the fixable issues.

        @param line line number of the issue
        @type int
        @param pos position inside line
        @type int
        @param code code of the issue
        @type str
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message code for the fix, arguments list for the message
            and an ID for a deferred fix
        @rtype tuple of (int, str, list, int)
        """
        if (
            line <= len(self.__source)
            and self.__codeMatch(code)
            and code in self.__fixes
        ):
            res = self.__fixes[code](code, line, pos)
            if res[0] == 1:
                self.__modified = True
                self.fixed += 1
        else:
            res = (0, "", [], 0)

        return res

    def finalize(self):
        """
        Public method to apply all deferred fixes.

        @return dictionary containing the fix results
        @rtype dict
        """
        results = {}

        # do fixes that change the number of lines
        for id_, code, line, pos in reversed(self.__stack):
            res, msg, args, _ = self.__fixes[code](code, line, pos, apply=True)
            if res == 1:
                self.__modified = True
                self.fixed += 1
            results[id_] = (res, msg, args)

        return results

    def __getID(self):
        """
        Private method to get the ID for a deferred fix.

        @return ID for a deferred fix
        @rtype int
        """
        self.__lastID += 1
        return self.__lastID

    def __getIndent(self, line):
        """
        Private method to get the indentation string.

        @param line line to determine the indentation string from
        @type str
        @return indentation string
        @rtype str
        """
        return line.replace(line.lstrip(), "")

    def __fixD111(self, _code, line, _pos):
        """
        Private method to fix docstring enclosed in wrong quotes.

        Codes: D111

        @param _code code of the issue (unused)
        @type str
        @param line line number of the issue
        @type int
        @param _pos position inside line (unused)
        @type int
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message code for the fix, a list of arguments for the
            message and an ID for a deferred fix
        @rtype tuple of (int, str, list or int, int)
        """
        line -= 1
        quotes = re.match(r"""\s*[ru]?('''|'|\")""", self.__source[line]).group(1)
        left, right = self.__source[line].split(quotes, 1)
        self.__source[line] = left + '"""' + right
        while line < len(self.__source):
            if self.__source[line].rstrip().endswith(quotes):
                left, right = self.__source[line].rsplit(quotes, 1)
                self.__source[line] = left + '"""' + right
                break
            line += 1

        # Triple single quotes converted to triple double quotes.
        return (1, "FIX-D-111", [], 0)

    def __fixD112(self, code, line, _pos):
        """
        Private method to fix docstring 'r' in leading quotes.

        Codes: D112

        @param code code of the issue
        @type str
        @param line line number of the issue
        @type int
        @param _pos position inside line (unused)
        @type int
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message code for the fix, a list of arguments for the
            message and an ID for a deferred fix
        @rtype tuple of (int, str, list or int, int)
        """
        line -= 1
        if code == "D-112":
            insertChar = "r"
        else:
            return (0, "", 0)

        newText = (
            self.__getIndent(self.__source[line])
            + insertChar
            + self.__source[line].lstrip()
        )
        self.__source[line] = newText
        # Introductory quotes corrected to be {0}"""
        return (1, "FIX-D-112", [insertChar], 0)

    def __fixD121(self, code, line, pos, apply=False):
        """
        Private method to fix a single line docstring on multiple lines.

        Codes: D121

        @param code code of the issue
        @type str
        @param line line number of the issue
        @type int
        @param pos position inside line
        @type int
        @param apply flag indicating, that the fix should be applied
        @type bool
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message code for the fix, a list of arguments for the
            message and an ID for a deferred fix
        @rtype tuple of (int, str, list or int, int)
        """
        if apply:
            line -= 1
            if not self.__source[line].lstrip().startswith(('"""', 'r"""', 'u"""')):
                # only correctly formatted docstrings will be fixed
                return (0, "", [], 0)

            docstring = self.__source[line].rstrip() + self.__source[line + 1].strip()
            if docstring.endswith('"""'):
                docstring += self.__eol
            else:
                docstring += self.__source[line + 2].lstrip()
                self.__source[line + 2] = ""

            self.__source[line] = docstring
            self.__source[line + 1] = ""
            # Single line docstring put on one line.
            return (1, "FIX-D-121", [], 0)
        fixId = self.__getID()
        self.__stack.append((fixId, code, line, pos))
        return (-1, "", [], fixId)

    def __fixD131_D231(self, code, line, _pos):
        """
        Private method to fix a docstring summary not ending with a
        period.

        Codes: D131, D231

        @param code code of the issue (unused)
        @type str
        @param line line number of the issue
        @type int
        @param _pos position inside line (unused)
        @type int
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message code for the fix, a list of arguments for the
            message and an ID for a deferred fix
        @rtype tuple of (int, str, list or int, int)
        """
        line -= 1
        newText = ""
        if self.__source[line].rstrip().endswith(('"""', "'''")) and self.__source[
            line
        ].lstrip().startswith(('"""', 'r"""', 'u"""', 'ru"""', 'ur"""')):
            # it is a one-liner
            newText = (
                self.__source[line].rstrip()[:-3].rstrip()
                + "."
                + self.__source[line].rstrip()[-3:]
                + self.__eol
            )
        else:
            if line < len(self.__source) - 1 and (
                not self.__source[line + 1].strip()
                or self.__source[line + 1].lstrip().startswith("@")
                or (
                    self.__source[line + 1].strip() in ('"""', "'''")
                    and not self.__source[line].lstrip().startswith("@")
                )
            ):
                newText = self.__source[line].rstrip() + "." + self.__eol

        if newText:
            self.__source[line] = newText
            # Period added to summary line.
            return (1, f"FIX-{code}", [], 0)
        return (0, "", [], 0)

    def __fixD141(self, code, line, pos, apply=False):
        """
        Private method to fix a function/method docstring preceded by a
        blank line.

        Codes: D141

        @param code code of the issue
        @type str
        @param line line number of the issue
        @type int
        @param pos position inside line
        @type int
        @param apply flag indicating, that the fix should be applied
        @type bool
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message code for the fix, a list of arguments for the
            message and an ID for a deferred fix
        @rtype tuple of (int, str, list or int, int)
        """
        if apply:
            line -= 1
            self.__source[line - 1] = ""
            # Blank line before function/method docstring removed.
            return (1, "FIX-D-141", [], 0)
        fixId = self.__getID()
        self.__stack.append((fixId, code, line, pos))
        return (-1, "", [], fixId)

    def __fixD142(self, code, line, pos, apply=False):
        """
        Private method to fix a class docstring not preceded by a
        blank line.

        Codes: D142

        @param code code of the issue
        @type str
        @param line line number of the issue
        @type int
        @param pos position inside line
        @type int
        @param apply flag indicating, that the fix should be applied
        @type bool
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message code for the fix, a list of arguments for the
            message and an ID for a deferred fix
        @rtype tuple of (int, str, list or int, int)
        """
        if apply:
            line -= 1
            self.__source[line] = self.__eol + self.__source[line]
            # Blank line inserted before class docstring.
            return (1, "FIX-D-142", [], 0)
        fixId = self.__getID()
        self.__stack.append((fixId, code, line, pos))
        return (-1, "", [], fixId)

    def __fixD143(self, code, line, pos, apply=False):
        """
        Private method to fix a class docstring not followed by a
        blank line.

        Codes: D143

        @param code code of the issue
        @type str
        @param line line number of the issue
        @type int
        @param pos position inside line
        @type int
        @param apply flag indicating, that the fix should be applied
        @type bool
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message code for the fix, a list of arguments for the
            message and an ID for a deferred fix
        @rtype tuple of (int, str, list or int, int)
        """
        if apply:
            line -= 1
            self.__source[line] += self.__eol
            # Blank line inserted after class docstring.
            return (1, "FIX-D-143", [], 0)
        fixId = self.__getID()
        self.__stack.append((fixId, code, line, pos))
        return (-1, "", [], fixId)

    def __fixD144_D246(self, code, line, pos, apply=False):
        """
        Private method to fix a docstring summary not followed by a
        blank line.

        Codes: D144, D246

        @param code code of the issue
        @type str
        @param line line number of the issue
        @type int
        @param pos position inside line
        @type int
        @param apply flag indicating, that the fix should be applied
        @type bool
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message code for the fix, a list of arguments for the
            message and an ID for a deferred fix
        @rtype tuple of (int, str, list or int, int)
        """
        if apply:
            line -= 1
            if not self.__source[line].rstrip().endswith("."):
                # only correct summary lines can be fixed here
                return (0, "", 0)

            self.__source[line] += self.__eol
            # Blank line inserted after docstring summary.
            return (1, f"FIX-{code}", [], 0)
        fixId = self.__getID()
        self.__stack.append((fixId, code, line, pos))
        return (-1, "", [], fixId)

    def __fixD145(self, code, line, pos, apply=False):
        """
        Private method to fix the last paragraph of a multi-line docstring
        not followed by a blank line.

        Codes: D143

        @param code code of the issue
        @type str
        @param line line number of the issue
        @type int
        @param pos position inside line
        @type int
        @param apply flag indicating, that the fix should be applied
        @type bool
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message code for the fix, a list of arguments for the
            message and an ID for a deferred fix
        @rtype tuple of (int, str, list or int, int)
        """
        if apply:
            line -= 1
            self.__source[line] = self.__eol + self.__source[line]
            # Blank line inserted after last paragraph of docstring.
            return (1, "FIX-D-145", [], 0)
        fixId = self.__getID()
        self.__stack.append((fixId, code, line, pos))
        return (-1, "", [], fixId)

    def __fixD221_D222(self, code, line, pos, apply=False):
        """
        Private method to fix leading and trailing quotes of docstring
        not on separate lines.

        Codes: D221, D222

        @param code code of the issue
        @type str
        @param line line number of the issue
        @type int
        @param pos position inside line
        @type int
        @param apply flag indicating, that the fix should be applied
        @type bool
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message code for the fix, a list of arguments for the
            message and an ID for a deferred fix
        @rtype tuple of (int, str, list or int, int)
        """
        if apply:
            line -= 1
            indent = self.__getIndent(self.__source[line])
            source = self.__source[line].strip()
            if code == "D-221":
                # leading
                if source.startswith(("r", "u")):
                    first, second = source[:4], source[4:].strip()
                else:
                    first, second = source[:3], source[3:].strip()
            else:
                # trailing
                first, second = source[:-3].strip(), source[-3:]
            newText = indent + first + self.__eol + indent + second + self.__eol
            self.__source[line] = newText
            # Leading quotes put on separate line.
            # Trailing quotes put on separate line.
            return (1, f"FIX-{code}", [], 0)
        fixId = self.__getID()
        self.__stack.append((fixId, code, line, pos))
        return (-1, "", [], fixId)

    def __fixD242_D244(self, code, line, pos, apply=False):
        """
        Private method to fix a class or function/method docstring preceded
        by a blank line.

        Codes: D242, D244

        @param code code of the issue
        @type str
        @param line line number of the issue
        @type int
        @param pos position inside line
        @type int
        @param apply flag indicating, that the fix should be applied
        @type bool
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message code for the fix, a list of arguments for the
            message and an ID for a deferred fix
        @rtype tuple of (int, str, list or int, int)
        """
        if apply:
            line -= 1
            self.__source[line - 1] = ""
            # Blank line before class docstring removed.
            # Blank line before function/method docstring removed.
            return (1, f"FIX-{code}", [], 0)
        fixId = self.__getID()
        self.__stack.append((fixId, code, line, pos))
        return (-1, "", [], fixId)

    def __fixD243_D245(self, code, line, pos, apply=False):
        """
        Private method to fix a class or function/method docstring followed
        by a blank line.

        Codes: D243, D245

        @param code code of the issue
        @type str
        @param line line number of the issue
        @type int
        @param pos position inside line
        @type int
        @param apply flag indicating, that the fix should be applied
        @type bool
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message code for the fix, a list of arguments for the
            message and an ID for a deferred fix
        @rtype tuple of (int, str, list or int, int)
        """
        if apply:
            line -= 1
            self.__source[line + 1] = ""
            # Blank line after class docstring removed.
            # Blank line after function/method docstring removed.
            return (1, f"FIX-{code}", [], 0)
        fixId = self.__getID()
        self.__stack.append((fixId, code, line, pos))
        return (-1, "", [], fixId)

    def __fixD247(self, code, line, pos, apply=False):
        """
        Private method to fix a last paragraph of a docstring followed
        by a blank line.

        Codes: D247

        @param code code of the issue
        @type str
        @param line line number of the issue
        @type int
        @param pos position inside line
        @type int
        @param apply flag indicating, that the fix should be applied
        @type bool
        @return value indicating an applied/deferred fix (-1, 0, 1),
            a message code for the fix, a list of arguments for the
            message and an ID for a deferred fix
        @rtype tuple of (int, str, list or int, int)
        """
        if apply:
            line -= 1
            self.__source[line - 1] = ""
            # Blank line after last paragraph removed.
            return (1, "FIX-D-247", [], 0)
        fixId = self.__getID()
        self.__stack.append((fixId, code, line, pos))
        return (-1, "", [], fixId)
