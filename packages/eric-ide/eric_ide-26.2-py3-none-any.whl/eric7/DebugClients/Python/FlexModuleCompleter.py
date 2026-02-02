"""
Module word completion for the eric-ide shell.

<h4>NOTE for eric-ide variant</h4>

    This version is a re-implementation of _module_completer as found in the Python3
    library. It is modified to work with the eric-ide debug client.
"""

import pkgutil
import sys
import token
import tokenize

from contextlib import contextmanager
from dataclasses import dataclass
from io import StringIO
from itertools import chain
from tokenize import TokenInfo


class ModuleCompleter:
    """
    Class implementing a completer for Python import statements.

    Examples:
        - import <tab>
        - import foo<tab>
        - import foo.<tab>
        - import foo as bar, baz<tab>

        - from <tab>
        - from foo<tab>
        - from foo import <tab>
        - from foo import bar<tab>
        - from foo import (bar as baz, qux<tab>
    """

    def __init__(self, namespace=None):
        """
        Constructor

        @param namespace namespace for the completer (defaults to None)
        @type dict or FrameLocalsProxy (optional)
        """
        self.namespace = namespace or {}
        self._global_cache = []
        self._curr_sys_path = sys.path[:]

    def get_completions(self, line):
        """
        Public method to get the next possible import completions for 'line'.

        @param line line of code to get completions for
        @type str
        @return list of potential completions
        @rtype list of str
        """
        result = ImportParser(line).parse()
        if not result:
            # Parsing of the import statement failed, make it look like
            # no completions are available.
            return []

        try:
            return self.complete(*result)
        except Exception:
            # Some unexpected error occurred, make it look like
            # no completions are available.
            return []

    def complete(self, from_name, name):
        """
        Public method to complete module or submodule names.

        @param from_name name of modules to import from
        @type str
        @param name name part to be completed
        @type str
        @return list of completions
        @rtype list of str
        """
        if from_name is None:
            # import x.y.z<tab>
            if name is not None:
                path, prefix = self.get_path_and_prefix(name)
                modules = self.find_modules(path, prefix)
                return [self.format_completion(path, module) for module in modules]

            return []

        if name is None:
            # from x.y.z<tab>
            path, prefix = self.get_path_and_prefix(from_name)
            modules = self.find_modules(path, prefix)
            return [self.format_completion(path, module) for module in modules]

        # from x.y import z<tab>
        return self.find_modules(from_name, name)

    def find_modules(self, path, prefix):
        """
        Public method to find all modules under 'path' that start with 'prefix'.

        @param path path to find modules in
        @type str
        @param prefix module prefix to look for
        @type str
        @return list of modules
        @rtype list of str
        """
        modules = self._find_modules(path, prefix)
        # Filter out invalid module names
        # (for example those containing dashes that cannot be imported with 'import')
        return [mod for mod in modules if mod.isidentifier()]

    def _find_modules(self, path, prefix):
        """
        Protected method to find all modules under 'path' that start with 'prefix'
        (even invalid module names).

        @param path path to find modules in
        @type str
        @param prefix module prefix to look for
        @type str
        @return list of modules
        @rtype list of str
        """
        if not path:
            # Top-level import (e.g. `import foo<tab>`` or `from foo<tab>`)`
            builtin_modules = [
                name
                for name in sys.builtin_module_names
                if self.is_suggestion_match(name, prefix)
            ]
            third_party_modules = [
                module.name
                for module in self.global_cache
                if self.is_suggestion_match(module.name, prefix)
            ]
            return sorted(builtin_modules + third_party_modules)

        if path.startswith("."):
            # Convert relative path to absolute path
            package = self.namespace.get("__package__", "")
            path = self.resolve_relative_name(path, package)
            if path is None:
                return []

        modules = self.global_cache
        for segment in path.split("."):
            modules = [
                mod_info
                for mod_info in modules
                if mod_info.ispkg and mod_info.name == segment
            ]
            modules = self.iter_submodules(modules)
        return [
            module.name
            for module in modules
            if self.is_suggestion_match(module.name, prefix)
        ]

    def is_suggestion_match(self, module_name, prefix):
        """
        Public method to ckeck, if 'module_name' is a valid suggestion.

        @param module_name module name to be checked
        @type str
        @param prefix module name prefix to check against
        @type str
        @return flag indicating a valid suggestion
        @rtype bool
        """
        if prefix:
            return module_name.startswith(prefix)

        # For consistency with attribute completion, which
        # does not suggest private attributes unless requested.
        return not module_name.startswith("_")

    def iter_submodules(self, parent_modules):
        """
        Public method to iterate over all submodules of the given parent modules.

        @param parent_modules list of module info objects to be processed
        @type list of pkgutil.ModuleInfo
        @return iterator of all submodules
        @rtype iterator of pkgutil.ModuleInfo
        """
        specs = [
            info.module_finder.find_spec(info.name, None)
            for info in parent_modules
            if info.ispkg
        ]
        search_locations = set(
            chain.from_iterable(
                getattr(spec, "submodule_search_locations", [])
                for spec in specs
                if spec
            )
        )
        return pkgutil.iter_modules(search_locations)

    def get_path_and_prefix(self, dotted_name):
        """
        Public method to split a dotted name into an import path and a
        final prefix that is to be completed.

        Examples:
            'foo.bar' -> 'foo', 'bar'
            'foo.' -> 'foo', ''
            '.foo' -> '.', 'foo'

        @param dotted_name dotted modules name to be split
        @type str
        @return tuple containing the import path and the final prefix
        @rtype tuple of (str, str)
        """
        if "." not in dotted_name:
            return "", dotted_name

        if dotted_name.startswith("."):
            stripped = dotted_name.lstrip(".")
            dots = "." * (len(dotted_name) - len(stripped))
            if "." not in stripped:
                return dots, stripped

            path, prefix = stripped.rsplit(".", 1)
            return dots + path, prefix

        path, prefix = dotted_name.rsplit(".", 1)
        return path, prefix

    def format_completion(self, path, module):
        """
        Public method to format a valid module path.

        @param path path component
        @type str
        @param module module name
        @type str
        @return formatted module name
        @rtype str
        """
        if path == "" or path.endswith("."):
            return f"{path}{module}"

        return f"{path}.{module}"

    def resolve_relative_name(self, name, package):
        """
        Public method to resolve a relative module name to an absolute name.

        Example: resolve_relative_name('.foo', 'bar') -> 'bar.foo'

        @param name relative module name
        @type str
        @param package package name
        @type str
        @return absolute module name
        @rtype str or None
        """
        # taken from importlib._bootstrap
        level = 0  # noqa: Y-113
        for character in name:
            if character != ".":
                break
            level += 1
        bits = package.rsplit(".", level - 1)
        if len(bits) < level:
            return None

        base = bits[0]
        name = name[level:]
        return f"{base}.{name}" if name else base

    @property
    def global_cache(self):
        """
        Public method implementing the global module cache.

        @return reference to the global cache object
        @rtype list of pkgutil.ModuleInfo
        """
        if not self._global_cache or self._curr_sys_path != sys.path:
            self._curr_sys_path = sys.path[:]
            self._global_cache = list(pkgutil.iter_modules())

        return self._global_cache


class ImportParser:
    """
    Class to Parse incomplete import statements that are suitable for autocomplete
    suggestions.

    Examples:
        - import foo          -> Result(from_name=None, name='foo')
        - import foo.         -> Result(from_name=None, name='foo.')
        - from foo            -> Result(from_name='foo', name=None)
        - from foo import bar -> Result(from_name='foo', name='bar')
        - from .foo import (  -> Result(from_name='.foo', name='')

    Note that the parser works in reverse order, starting from the
    last token in the input string. This makes the parser more robust
    when parsing multiple statements.
    """

    _ignored_tokens = {
        token.INDENT,
        token.DEDENT,
        token.COMMENT,
        token.NL,
        token.NEWLINE,
        token.ENDMARKER,
    }
    _keywords = {"import", "from", "as"}

    def __init__(self, code_line):
        """
        Constructor

        @param code_line line of code to be parsed
        @type str
        """
        self.code_line = code_line
        tokens = []
        try:
            tokens.extend(
                t
                for t in tokenize.generate_tokens(StringIO(code_line).readline)
                if t.type not in self._ignored_tokens
            )
        except tokenize.TokenError as e:
            if "unexpected EOF" not in str(e):
                # unexpected EOF is fine, since we're parsing an
                # incomplete statement, but other errors are not
                # because we may not have all the tokens so it's
                # safer to bail out
                tokens = []
        except SyntaxError:
            tokens = []
        self.tokens = TokenQueue(tokens[::-1])

    def parse(self):
        """
        Public method to parse the code line.

        @return tuple containing the package name and the module name
        @rtype tuple of (str, str)
        """
        res = self._parse()
        if not res:
            return None

        return res.from_name, res.name

    def _parse(self):
        """
        Protected method parse the supported import variants.

        @return result of the parse operation
        @rtype Result
        """
        with self.tokens.save_state():
            return self.parse_from_import()

        with self.tokens.save_state():
            return self.parse_import()

    def parse_import(self):
        """
        Public method to parse a simple import statement.

        @return result of the parse operation
        @rtype Result
        @exception ParseError DESCRIPTION
        """
        if self.code_line.rstrip().endswith("import") and self.code_line.endswith(" "):
            return Result(name="")

        if self.tokens.peek_string(","):
            name = ""
        else:
            if self.code_line.endswith(" "):
                err = "parse_import"
                raise ParseError(err)
            name = self.parse_dotted_name()

        if name.startswith("."):
            err = "parse_import"
            raise ParseError(err)

        while self.tokens.peek_string(","):
            self.tokens.pop()
            self.parse_dotted_as_name()

        if self.tokens.peek_string("import"):
            return Result(name=name)

        err = "parse_import"
        raise ParseError(err)

    def parse_from_import(self):
        """
        Public method to parse a from...import statement.

        @return result of the parse operation
        @rtype Result
        @exception ParseError DESCRIPTION
        """
        stripped = self.code_line.rstrip()
        if stripped.endswith("import") and self.code_line.endswith(" "):
            return Result(from_name=self.parse_empty_from_import(), name="")

        if stripped.endswith("from") and self.code_line.endswith(" "):
            return Result(from_name="")

        if self.tokens.peek_string("(") or self.tokens.peek_string(","):
            return Result(from_name=self.parse_empty_from_import(), name="")

        if self.code_line.endswith(" "):
            err = "parse_from_import"
            raise ParseError(err)

        name = self.parse_dotted_name()
        if "." in name:
            self.tokens.pop_string("from")
            return Result(from_name=name)

        if self.tokens.peek_string("from"):
            return Result(from_name=name)

        from_name = self.parse_empty_from_import()
        return Result(from_name=from_name, name=name)

    def parse_empty_from_import(self):
        """
        Public method to parse an empty from...import statement.

        @return package name
        @rtype str
        """
        if self.tokens.peek_string(","):
            self.tokens.pop()
            self.parse_as_names()
        if self.tokens.peek_string("("):
            self.tokens.pop()
        self.tokens.pop_string("import")
        return self.parse_from()

    def parse_from(self):
        """
        Public method to parse the from part.

        @return package name
        @rtype str
        """
        from_name = self.parse_dotted_name()
        self.tokens.pop_string("from")
        return from_name

    def parse_dotted_as_name(self):
        """
        Public method to parse a dotted as name.

        @return module name
        @rtype str
        """
        self.tokens.pop_name()
        if self.tokens.peek_string("as"):
            self.tokens.pop()
        with self.tokens.save_state():
            return self.parse_dotted_name()

    def parse_dotted_name(self):
        """
        Public method to parse a dotted name.

        @return dotted module name
        @rtype str
        @exception ParseError DESCRIPTION
        """
        name = []
        if self.tokens.peek_string("."):
            name.append(".")
            self.tokens.pop()
        if (
            self.tokens.peek_name()
            and (tok := self.tokens.peek())
            and tok.string not in self._keywords
        ):
            name.append(self.tokens.pop_name())
        if not name:
            err = "parse_dotted_name"
            raise ParseError(err)

        while self.tokens.peek_string("."):
            name.append(".")
            self.tokens.pop()
            if (
                self.tokens.peek_name()
                and (tok := self.tokens.peek())
                and tok.string not in self._keywords
            ):
                name.append(self.tokens.pop_name())
            else:
                break

        while self.tokens.peek_string("."):
            name.append(".")
            self.tokens.pop()

        return "".join(name[::-1])

    def parse_as_names(self):
        """
        Public method to parse the as parts.
        """
        self.parse_as_name()
        while self.tokens.peek_string(","):
            self.tokens.pop()
            self.parse_as_name()

    def parse_as_name(self):
        """
        Public method to parse the as part.
        """
        self.tokens.pop_name()
        if self.tokens.peek_string("as"):
            self.tokens.pop()
            self.tokens.pop_name()


class ParseError(Exception):
    """
    Class representing a parsing issue.
    """


@dataclass(frozen=True)
class Result:
    """
    Class implementing the result data structure.
    """

    from_name: str | None = None
    name: str | None = None


class TokenQueue:
    """
    Class implementing helper functions for working with a sequence of tokens.
    """

    def __init__(self, tokens):
        """
        Constructor

        @param tokens list of token info objects
        @type list of TokenInfo
        """
        self.tokens: list[TokenInfo] = tokens
        self.index: int = 0
        self.stack: list[int] = []

    @contextmanager
    def save_state(self):
        """
        Public method implementing a context manager to save the current state.
        """
        try:
            self.stack.append(self.index)
            yield
        except ParseError:
            self.index = self.stack.pop()
        else:
            self.stack.pop()

    def __bool__(self):
        """
        Special method implementing the 'bool' logic.

        @return flag indicating the boolean state
        @rtype bool
        """
        return self.index < len(self.tokens)

    def peek(self):
        """
        Public method to get the next token without popping it.

        @return next token
        @rtype TokenInfo
        """
        if not self:
            return None
        return self.tokens[self.index]

    def peek_name(self):
        """
        Public method to check, if the next token is a name token without popping it.

        @return flag indicating that the next token is a name token
        @rtype TokenInfo
        """
        if not (tok := self.peek()):
            return False
        return tok.type == token.NAME

    def pop_name(self):
        """
        Public method to pop a name token off the token stack.

        @return value of the name token
        @rtype str
        @exception ParseError raised to indicate that the popped token is not a
            name token
        """
        tok = self.pop()
        if tok.type != token.NAME:
            err = "pop_name"
            raise ParseError(err)
        return tok.string

    def peek_string(self, token_string):
        """
        Public method check, if the next token has a specific value.

        @param token_string string to test against
        @type str
        @return flag indicating that the next token has the specified value
        @rtype bool
        """
        if not (tok := self.peek()):
            return False
        return tok.string == token_string

    def pop_string(self, token_string):
        """
        Public method to pop the next token and return its value, if it is of a
        specific name.

        @param token_string string to test against
        @type str
        @return token value
        @rtype str
        @exception ParseError raised to indicate an invalid or unexpected token
        """
        tok = self.pop()
        if tok.string != token_string:
            err = "pop_string"
            raise ParseError(err)
        return tok.string

    def pop(self) -> TokenInfo:
        """
        Public method to pop the next token off the stack.

        @return next token
        @rtype TokenInfo
        @exception ParseError raised to indicate an empty token queue.
        """
        if not self:
            err = "pop"
            raise ParseError(err)
        tok = self.tokens[self.index]
        self.index += 1
        return tok


#
# ~ eflag: noqa = M-111
