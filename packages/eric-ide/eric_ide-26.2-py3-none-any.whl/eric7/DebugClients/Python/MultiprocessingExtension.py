#
# Copyright (c) 2020 - 2026 Detlev Offenbach <detlev@die-offenbachs.de>
#

"""
Module implementing a function to patch multiprocessing.Process to support
debugging of the process.
"""

import sys
import traceback

_debugClient = None
_originalProcess = None
_originalBootstrap = None


def patchMultiprocessing(module, debugClient):
    """
    Function to patch the multiprocessing module.

    @param module reference to the imported module to be patched
    @type module
    @param debugClient reference to the debug client object
    @type DebugClient
    """  # __IGNORE_WARNING_D-234__
    global _debugClient, _originalProcess, _originalBootstrap

    _debugClient = debugClient

    _originalProcess = module.process.BaseProcess
    _originalBootstrap = _originalProcess._bootstrap

    class ProcessWrapper(_originalProcess):
        """
        Wrapper class for multiprocessing.Process.
        """

        def _bootstrap(self, *args, **kwargs):
            """
            Wrapper around _bootstrap to start debugger.

            @param args function arguments
            @type list
            @param kwargs keyword only arguments
            @type dict
            @return exit code of the process
            @rtype int
            """
            _debugging = False
            if _debugClient.debugging and _debugClient.multiprocessSupport:
                scriptName = sys.argv[0]
                if not _debugClient.skipMultiProcessDebugging(scriptName):
                    _debugging = True
                    try:
                        (
                            _wd,
                            host,
                            port,
                            reportAllExceptions,
                            tracePython,
                            redirect,
                            _noencoding,
                            _useSettrace,
                        ) = _debugClient.startOptions[:8]
                        _debugClient.startDebugger(
                            sys.argv[0],
                            host=host,
                            port=port,
                            reportAllExceptions=reportAllExceptions,
                            tracePython=tracePython,
                            redirect=redirect,
                            passive=False,
                            multiprocessSupport=True,
                        )
                    except Exception:
                        print(  # noqa: T201, M-801
                            "Exception during multiprocessing bootstrap init:"
                        )
                        traceback.print_exc(file=sys.stdout)
                        sys.stdout.flush()
                        raise

            exitcode = _originalBootstrap(self, *args, **kwargs)

            if _debugging:
                _debugClient.progTerminated(exitcode, "process finished")

            return exitcode

    _originalProcess._bootstrap = ProcessWrapper._bootstrap

    class EricDefaultContext(module.context.DefaultContext):
        """
        Class replacing the original 'set_start_method()' method.

        This is done in order to prevent a script to be debugged changing the method
        to 'forkserver' because the debugger cannot handle this.
        """

        def set_start_method(self, method, force=False):  # noqa: ARG002
            """
            Public method to set the start method for starting new processes.

            @param method start method name
            @type str
            @param force flag indicating to set it even if one was set already
                (defaults to False)
            @type bool (optional)
            """
            if method == "forkserver":
                method = "spawn"

            super().set_start_method(method, force=True)

        def get_all_start_methods(self):
            """
            Public method to get a list of supported start methods.

            @return list of supported start methods
            @rtype list of str
            """
            methods = super().get_all_start_methods()
            return [m for m in methods if m != "forkserver"]

        def get_context(self, method=None):
            """
            Public method to get a context object of the given method.

            @param method start method of the new context (defaults to None)
            @type str | None (optional)
            @return created context object
            @rtype BaseContext
            """
            if method == "forkserver":
                method = "spawn"

            return super().get_context(method=method)

    # replace the original default class with our own
    module.context._default_context = EricDefaultContext(
        module.context._concrete_contexts["spawn"]
    )
    # replace some 'multiprocessing' functions by our own
    module.set_start_method = module.context._default_context.set_start_method
    module.get_start_method = module.context._default_context.get_start_method
    module.get_context = module.context._default_context.get_context
    module.get_all_start_methods = module.context._default_context.get_all_start_methods

    # Overwrite the start method to always be 'spawn' because the debugger does
    # not work with the 'forkserver' method and 'spawn' is the better method anyway.
    module.set_start_method("spawn")
