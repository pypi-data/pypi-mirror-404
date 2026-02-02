#
# Copyright (c) 2025 Tobias Rzepka <tobias.rzepka@gmail.de>
#

"""
Module implementing a debugger / call tracer based on sys.monitoring.

Since Python 3.12 there is a new interface to implement debugger / call tracer
with much better performance compared to sys.set_trace.

If raising ImportError, the old debugger will be used.
"""

import _thread
import atexit
import contextlib
import ctypes
import dis
import os.path
import sys
import time

from collections import namedtuple
from types import CodeType
from weakref import WeakKeyDictionary

from BreakpointWatch import Breakpoint, Watch
from DebugUtilities import formatargvalues, getargvalues

_recursion_limit = 64

if sys.version_info < (3, 12):
    raise ImportError

monitoring = sys.monitoring
events = monitoring.events

# Syntetic Frame and Code objects for profiling C-code
Frame = namedtuple("Frame", "f_code, f_lineno")
Code = namedtuple("Code", "co_name, co_filename")


def printerr(s):
    """
    Module function used for debugging the debug client.

    @param s data to be printed
    @type str
    """
    sys.__stderr__.write(f"{s}\n")
    sys.__stderr__.flush()


def setRecursionLimit(limit):
    """
    Module function to set the recursion limit.

    @param limit recursion limit
    @type int
    """
    global _recursion_limit
    _recursion_limit = limit


class DebugBase:
    """
    Class implementing base class of the debugger.

    Provides methods for the 'owning' client to call to step etc.
    """

    lib = os.path.dirname(contextlib.__file__)
    # Tuple required because it's accessed a lot of times by startswith method
    paths_to_skip = ("<", os.path.dirname(__file__), lib)
    files_to_skip = {}

    code_has_breakpoints = WeakKeyDictionary()  # Drop code objects on reload
    # Prevent double initialization when debugging and using breakpoint()
    trace_active = False
    profile_active = False

    # Store information about next steps thread individual when stepping through
    # multithreaded code
    step_single_threads = set()
    step_over_frames = {}

    # Cache for fixed file names
    filename_cache = {}

    # Stop all timers, when greenlets are used
    pollTimerEnabled = True
    timer_thread = None

    def __init__(self, dbgClient=None):
        """
        Constructor of DebugBase.

        @param dbgClient the owning client
        @type DebugClient
        """
        self._dbgClient = dbgClient or self

        # Some information about the thread
        self.isMainThread = False
        self.quitting = False
        self.id = -1
        self.name = ""

        self.tracePythonLibs(False)

        # Special handling of a recursion error
        self.skipFrames = 0

        self.isBroken = False
        self.isException = False

        # Current frame we are at
        self.currentFrame = None
        self.current_exception_stack = None
        self.frame_list = []

        # Frame where opcode tracing could start
        self.enterframe = None
        self.traceOpcodes = False

        self.recursion_depth = -1
        self.setRecursionDepth(sys._getframe())

        self.special_breakpoint: Breakpoint = None

        # Don't step into bootstrapper when leaving the last user-code-frame
        # Don't make it a class attribute because ThreadExtension is not imported yet
        self.bootstrap_files = (__file__, sys.modules["ThreadExtension"].__file__)

        # Provide a hook to perform a hard breakpoint
        # Use it like this:
        # if hasattr(sys, 'breakpoint): sys.breakpoint()
        sys.breakpoint = self.set_trace
        sys.breakpointhook = self.set_trace

        # Define old main entry point for all debugging events and a profile method
        # for backward compatibility
        self.trace_dispatch = None
        self.profile = lambda _x, _y, _z: None

        # Background task to periodicaly check for client interactions
        if DebugBase.timer_thread is None:
            DebugBase.timer_thread = _thread.start_new_thread(
                self.__event_poll_timer, ()
            )

    def set_trace(self, start_line_trace=True):
        """
        Public method to enable debugging.

        @param start_line_trace start debugging with the next line
        @type bool
        """
        if DebugBase.trace_active is False:
            DebugBase.trace_active = True
            monitoring.use_tool_id(monitoring.DEBUGGER_ID, "eric")

            monitoring.register_callback(
                monitoring.DEBUGGER_ID, events.PY_START, self.__monitor_py_start
            )
            monitoring.register_callback(
                monitoring.DEBUGGER_ID, events.LINE, self.__monitor_line
            )
            monitoring.register_callback(
                monitoring.DEBUGGER_ID, events.PY_RETURN, self.__monitor_py_return
            )
            monitoring.register_callback(
                monitoring.DEBUGGER_ID, events.PY_YIELD, self.__monitor_py_return
            )
            monitoring.register_callback(
                monitoring.DEBUGGER_ID, events.RAISE, self.__monitor_exception
            )

            # Global events: PY_START to catch all Python-frames and RAISE for
            # exceptions
            monitoring.set_events(
                monitoring.DEBUGGER_ID, events.PY_START | events.RAISE
            )

        self.reset_debug_information()

        # Enable local event 'LINE' to start debugging with the next line
        if start_line_trace:
            code = sys._getframe(1).f_code
            monitoring.set_local_events(monitoring.DEBUGGER_ID, code, events.LINE)
            thread_id = _thread.get_ident()
            DebugBase.step_single_threads.add(thread_id)

    def reset_trace(self):
        """
        Public method to disable debugging.
        """
        if DebugBase.trace_active is False:
            return
        # Global events: Remove all events for debugging
        monitoring.set_events(monitoring.DEBUGGER_ID, 0)

        # Remove all callbacks
        monitoring.register_callback(monitoring.DEBUGGER_ID, events.PY_START, None)
        monitoring.register_callback(monitoring.DEBUGGER_ID, events.LINE, None)
        monitoring.register_callback(monitoring.DEBUGGER_ID, events.PY_RETURN, None)
        monitoring.register_callback(monitoring.DEBUGGER_ID, events.PY_YIELD, None)
        monitoring.register_callback(monitoring.DEBUGGER_ID, events.RAISE, None)

        # Release tool-id for next activation through, e.g. breakpoint()
        monitoring.free_tool_id(monitoring.DEBUGGER_ID)
        DebugBase.trace_active = False

    def __monitor_py_start(self, code: CodeType, _instruction_offset: int):
        """
        Private method to handle event when entering the next Python frame.

        Check if this code object could be of interest, e.g. is there a breakpoint or
        are we stepped in. In those cases enable line events to get __monitor_line
        called, otherwise just return monitoring.DISABLE and we don't visit this code
        object till reenabled by calling monitoring.restart_events().

        @param code current code object
        @type CodeType
        @param _instruction_offset where the call is performed next
        @type int
        @return monitoring.DISABLE if further calls from this code object should be
            suppressed
        @rtype None | monitoring.DISABLE
        """
        if self.__skip_file(code.co_filename):
            return monitoring.DISABLE

        # Don't evaluate _has_breakpoint before. Otherwise the main script is evaluated
        # before the breakpoints are set and therefore no stop is possible in the main
        # script
        if not DebugBase.step_single_threads and self._has_breakpoint(code) is False:
            return monitoring.DISABLE

        monitoring.set_local_events(monitoring.DEBUGGER_ID, code, events.LINE)
        return None

    def __monitor_line(self, code: CodeType, line_number: int):
        """
        Private method to handle line events.

        When stepping through the code, for each line we have to wait for the user.
        Otherwise we check, if current line has a breakpoint. If so, wait for user else
        just continue because in one of those code lines should be a breakpoint.
        Watchpoints are handled the same as breakpoints.

        @param code current code object
        @type CodeType
        @param line_number current line number
        @type int
        @return monitoring.DISABLE if further calls from this code object should be
            suppressed
        @rtype None | monitoring.DISABLE
        """
        frame = sys._getframe(1)
        thread_id = _thread.get_ident()
        # Check for breakpoints
        if (code.co_filename, line_number) in Breakpoint.breaks:
            bp, flag = Breakpoint.effectiveBreak(code.co_filename, line_number, frame)
            if bp:
                DebugBase.step_single_threads.add(thread_id)
                # Flag says ok to delete temporary breakpoint
                if flag and bp.temporary:
                    Breakpoint.clear_break(code.co_filename, line_number)
                    if self.special_breakpoint == bp:
                        self.special_breakpoint = None
                    else:
                        self.special_breakpoint = None
                        self._dbgClient.sendClearTemporaryBreakpoint(
                            code.co_filename, line_number
                        )

        # Check for watches
        if Watch.watches:
            watch, flag = Watch.effectiveWatch(frame)
            if watch:
                DebugBase.step_single_threads.add(thread_id)
                # Flag says ok to delete temporary watch
                if flag and watch.temporary:
                    Watch.clear_watch(watch.cond)
                    self._dbgClient.sendClearTemporaryWatch(watch.cond)

        # Evaluate if user wants to stop here
        if (
            thread_id not in DebugBase.step_single_threads
            and DebugBase.step_over_frames.get(thread_id) != frame
        ):
            return None

        # We never stop on line 0.
        if frame.f_lineno == 0:
            return None

        # Don't stop inside eric
        if self.__skip_file(code.co_filename):
            return monitoring.DISABLE

        self.user_line(thread_id, frame)  # User interaction
        return None

    def __monitor_py_return(
        self, _code: CodeType, _instruction_offset: int, _retval: object
    ):
        """
        Private method to handle return events.

        When leaving a Python frame this event is triggered if PY_RETURN is enabled.
        This is used to activate line events when leaving a frame with the command step
        over, because the step over command want to stop at the current frame.

        @param _code current code object
        @type CodeType
        @param _instruction_offset where the call is performed next
        @type int
        @param _retval first return value of the function / method or None
        @type object
        """
        thread_id = _thread.get_ident()
        try:
            step_over_frame = DebugBase.step_over_frames[thread_id]
            frame = test_frame = sys._getframe(2)
        except (KeyError, ValueError):
            return

        # Check if step_over_frame still exist, then we are in a recursive function and
        # doesn't need to update its value
        while test_frame is not None:
            if test_frame == step_over_frame:
                return
            test_frame = test_frame.f_back

        # Check if we enter the bootstrap frame == exit main
        if frame.f_code.co_filename in self.bootstrap_files:
            DebugBase.step_over_frames.pop(thread_id, None)
            local_events = events.NO_EVENTS
        elif self.special_breakpoint:
            local_events = events.LINE | events.PY_RETURN | events.PY_YIELD
        else:
            DebugBase.step_over_frames[thread_id] = frame
            local_events = events.LINE | events.PY_RETURN | events.PY_YIELD

        monitoring.set_local_events(monitoring.DEBUGGER_ID, frame.f_code, local_events)

    def __monitor_exception(
        self, code: CodeType, _instruction_offset: int, exception: BaseException
    ):
        """
        Private method to handle exception events.

        Every exception is handled here. It's not possible to disable it.

        Because user_exception() requires a triple like returned by sys.exc_info() but
        sys.exc_info() is returning None at this point, an artificial exc_info is
        created here.

        @param code current code object
        @type CodeType
        @param _instruction_offset where the call is performed next
        @type int
        @param exception the exception itself
        @type subclass of BaseException
        """
        if self.__skip_file(code.co_filename):
            return

        excinfo = type(exception), exception, sys._getframe(1)
        self.user_exception(excinfo, False)

    def set_profile(self):
        """
        Public method to enable call trace profiling.
        """
        if DebugBase.profile_active is False:
            DebugBase.profile_active = True
            monitoring.use_tool_id(monitoring.PROFILER_ID, "eric")

            monitoring.register_callback(
                monitoring.PROFILER_ID, events.CALL, self.__profile_call
            )

            # Global events: CALL and PY_RETURN to catch all Python-frames
            monitoring.set_events(
                monitoring.PROFILER_ID, events.CALL | events.PY_RETURN
            )
            monitoring.register_callback(
                monitoring.PROFILER_ID, events.PY_RETURN, self.__profile_py_return
            )

    def reset_profile(self):
        """
        Public method to disable call trace profiling.
        """
        if DebugBase.profile_active is False:
            return
        # Global events: Remove all events for profiling
        monitoring.set_events(monitoring.PROFILER_ID, 0)

        # Remove all callbacks
        monitoring.register_callback(monitoring.PROFILER_ID, events.CALL, None)
        monitoring.register_callback(monitoring.PROFILER_ID, events.C_RETURN, None)

        # Release tool-id for next activation
        monitoring.free_tool_id(monitoring.PROFILER_ID)
        DebugBase.profile_active = False

    def __profile_call(
        self,
        code: CodeType,
        _instruction_offset: int,
        callable_object: object,
        _arg0: object,
    ):
        """
        Private method to profile the next function / method call.

        @param code current code object
        @type CodeType
        @param _instruction_offset where the call is performed next
        @type int
        @param callable_object function / method which will be called
        @type object
        @param _arg0 First argument of the call
        @type object
        @return monitoring.DISABLE if further calls from this code object should be
            suppressed
        @rtype None | monitoring.DISABLE
        @exception RuntimeError when maximum recursion depth exceeded
        """
        if self.__skip_file(code.co_filename):
            return monitoring.DISABLE

        try:
            # Call into ordinary Python frame
            f_code = callable_object.__code__
            line_number = f_code.co_firstlineno
        except AttributeError:
            # Call into C-code
            return None

        current_frame = sys._getframe(1)
        self.__sendCallTrace("call", current_frame, Frame(f_code, line_number))

        self.recursion_depth += 1
        if self.recursion_depth > _recursion_limit:
            err = (
                "maximum recursion depth exceeded\n"
                "(offending frame is two down the stack)"
            )
            raise RuntimeError(err)
        return None

    def __profile_py_return(
        self, code: CodeType, _instruction_offset: int, _retval: object
    ):
        """
        Private method to profile the return from current Python frame.

        @param code current code object
        @type CodeType
        @param _instruction_offset offset of the return statement
        @type int
        @param _retval value of the return statement
        @type object
        @return monitoring.DISABLE if further calls from this code object should be
            suppressed
        @rtype None | monitoring.DISABLE
        """
        if self.__skip_file(code.co_filename):
            return monitoring.DISABLE

        current_frame = sys._getframe(1)
        self.__sendCallTrace("return", current_frame, sys._getframe(2))
        self.recursion_depth -= 1
        return None

    def __profile_c_return(
        self,
        code: CodeType,
        _instruction_offset: int,
        callable_object: object,
        _arg0: object,
    ):
        """
        Private method to profile the return from C-code frame. # NOTE: Maybe unused...

        @param code current code object
        @type CodeType
        @param _instruction_offset where the call is performed next
        @type int
        @param callable_object function / method which will be called
        @type object
        @param _arg0 First argument of the call
        @type object
        @return monitoring.DISABLE if further calls from this code object should be
            suppressed
        @rtype None | monitoring.DISABLE
        """
        if self.__skip_file(code.co_filename):
            return monitoring.DISABLE

        try:
            # Call into ordinary Python frame
            f_code = callable_object.__code__
            line_number = f_code.co_firstlineno
        except AttributeError:
            # Call into C-code
            f_code = Code("built-in", f" {callable_object}")
            line_number = -1

        current_frame = sys._getframe(1)
        self.__sendCallTrace("return", Frame(f_code, line_number), current_frame)
        self.recursion_depth -= 1
        return None

    def _has_breakpoint(self, code: CodeType):
        """
        Protected method to check if there is a breakpoint inside the code object.

        @param code current code object
        @type CodeType
        @return Flag if breakpoint in code object found
        @rtype bool
        """
        try:
            has_breakpoint = DebugBase.code_has_breakpoints[code]
        except KeyError:
            bp_lines = Breakpoint.breakInFile.get(code.co_filename, [])
            if bp_lines:
                line_numbers = set(list(zip(*code.co_lines(), strict=False))[2])
                has_breakpoint = bool(line_numbers & set(bp_lines))
            else:
                has_breakpoint = False

            DebugBase.code_has_breakpoints[code] = has_breakpoint

        return has_breakpoint

    def __sendCallTrace(self, event, from_frame, to_frame):
        """
        Private method to send a call/return trace.

        @param event trace event
        @type str
        @param from_frame originating frame
        @type frame object
        @param to_frame destination frame
        @type frame object
        """
        from_filename = from_frame.f_code.co_filename
        to_filename = to_frame.f_code.co_filename
        if not self.__skip_file(from_filename) and not self.__skip_file(to_filename):
            from_info = {
                "filename": from_filename,
                "linenumber": from_frame.f_lineno,
                "codename": from_frame.f_code.co_name,
            }
            to_info = {
                "filename": to_filename,
                "linenumber": to_frame.f_lineno,
                "codename": to_frame.f_code.co_name,
            }
            self._dbgClient.sendCallTrace(event, from_info, to_info)

    def bootstrap(self, target, args, kwargs):
        """
        Public method to bootstrap a thread.

        It wraps the call to the user function to enable tracing
        before hand.

        @param target function which is called in the new created thread
        @type function pointer
        @param args arguments to pass to target
        @type tuple
        @param kwargs keyword arguments to pass to target
        @type dict
        """
        self._dbgClient.threads[_thread.get_ident()] = self
        try:
            # Because in the initial run method the "base debug" function is
            # set up, it's also valid for the threads afterwards.
            if self._dbgClient.debugging:
                self.set_trace(False)

            # Inform eric about the new thread
            self._dbgClient.dumpThreadList()

            target(*args, **kwargs)
        except Exception:
            excinfo = sys.exc_info()
            self.user_exception(excinfo, True)
        finally:
            self._dbgClient.dumpThreadList(self.id)

    def run(
        self, cmd, globalsDict=None, localsDict=None, debug=True, closeSession=True
    ):
        """
        Public method to start a given command under debugger control.

        @param cmd command / code to execute under debugger control
        @type str or CodeType
        @param globalsDict dictionary of global variables for cmd
        @type dict
        @param localsDict dictionary of local variables for cmd
        @type dict
        @param debug flag if command should run under debugger control
        @type bool
        @return exit code of the program
        @rtype int
        @param closeSession flag indicating to close the debugger session
            at exit
        @type bool
        """
        if globalsDict is None:
            import __main__  # __IGNORE_WARNING_I-10__

            globalsDict = __main__.__dict__

        if localsDict is None:
            localsDict = globalsDict

        if not isinstance(cmd, CodeType):
            cmd = compile(cmd, "<string>", "exec")

        if debug:
            thread_id = _thread.get_ident()
            DebugBase.step_single_threads.add(thread_id)
            self.set_trace(False)

        try:
            exec(cmd, globalsDict, localsDict)  # secok
            atexit._run_exitfuncs()
            exitcode = 0
            message = ""
        except SystemExit:
            atexit._run_exitfuncs()
            excinfo = sys.exc_info()
            exitcode, message = self.__extractSystemExitMessage(excinfo)
        except Exception:
            excinfo = sys.exc_info()
            self.user_exception(excinfo, True)
            exitcode = -1
            message = "abort due to unhandled exception"
        finally:
            self.quitting = True
            self.reset_trace()
            self._dbgClient.progTerminated(
                exitcode, message=message, closeSession=closeSession
            )
        return exitcode

    def set_until(self, lineno):
        """
        Public method to stop when the line with the lineno greater than the
        current one is reached or when returning from current frame.

        The name "until" is borrowed from gdb.

        @param lineno line number to continue to
        @type int
        """
        # Create a temporary breakpoint for the requested line
        self.special_breakpoint = Breakpoint(
            self.currentFrame.f_code.co_filename, lineno, True
        )
        DebugBase.code_has_breakpoints.clear()
        self.go(events.LINE | events.PY_RETURN | events.PY_YIELD)

    def go(self, special=events.NO_EVENTS):
        """
        Public method to resume the thread.

        It resumes the thread stopping only at breakpoints or exceptions.

        @param special flag indicating a special continue operation
        @type bool | events
        """
        thread_id = _thread.get_ident()
        DebugBase.step_single_threads.discard(thread_id)
        DebugBase.step_over_frames.pop(thread_id, None)
        monitoring.restart_events()

        if self.currentFrame is None:
            return

        if self._has_breakpoint(self.currentFrame.f_code) is False or special:
            with contextlib.suppress(ValueError):
                # Raised if debugging stopped while in a BP or tiggered by a late thread
                monitoring.set_local_events(
                    monitoring.DEBUGGER_ID,
                    self.currentFrame.f_code,
                    events.NO_EVENTS | special,
                )

    def __set_stepinstr(self):
        """
        Private method to stop before the next instruction.
        """
        # Not implemented yet

    def step(self, step_into):
        """
        Public method to perform a step operation in this thread.

        @param step_into If it is True, then the step is a step into,
            otherwise it is a step over.
        @type bool
        """
        thread_id = _thread.get_ident()

        if step_into:
            DebugBase.step_single_threads.add(thread_id)  # Allow a step into
            DebugBase.step_over_frames[thread_id] = None
        else:
            DebugBase.step_single_threads.discard(thread_id)  # Avoid a step into
            DebugBase.step_over_frames[thread_id] = self.currentFrame

        monitoring.restart_events()

        # If stepped out, stop before returning from current frame to activate line
        # events
        with contextlib.suppress(ValueError):
            # Raised if debugging stopped while in a BP or tiggered by a late thread
            monitoring.set_local_events(
                monitoring.DEBUGGER_ID,
                self.currentFrame.f_code,
                events.LINE | events.PY_RETURN | events.PY_YIELD,
            )

    def stepOut(self):
        """
        Public method to perform a step out of the current call.
        """
        thread_id = _thread.get_ident()
        DebugBase.step_single_threads.discard(thread_id)
        step_over_frame = self.currentFrame.f_back
        DebugBase.step_over_frames[thread_id] = step_over_frame
        monitoring.restart_events()

        # Check if we enter the bootstrap frame => exit main
        if step_over_frame.f_code.co_filename in self.bootstrap_files:
            DebugBase.step_over_frames.pop(thread_id, None)
            step_over_code = None
        else:
            step_over_code = step_over_frame.f_code
            with contextlib.suppress(ValueError):
                # Raised if debugging stopped while in a BP or tiggered by a late thread
                monitoring.set_local_events(
                    monitoring.DEBUGGER_ID,
                    step_over_code,
                    events.LINE | events.PY_RETURN | events.PY_YIELD,
                )

        # Check if we are in a recusive function to prevent overwriting our settings
        if self.currentFrame.f_code != step_over_code:
            local_events = events.PY_RETURN | events.PY_YIELD
            # If breakpoints in code object, also activate line events
            if self._has_breakpoint(self.currentFrame.f_code):
                local_events |= events.LINE

            with contextlib.suppress(ValueError):
                # Raised if debugging stopped while in a BP or tiggered by a late thread
                monitoring.set_local_events(
                    monitoring.DEBUGGER_ID, self.currentFrame.f_code, local_events
                )

    def move_instruction_pointer(self, lineno):
        """
        Public method to move the instruction pointer to another line.

        @param lineno new line number
        @type int
        """
        try:
            self.currentFrame.f_lineno = lineno
            stack = self.getStack(self.currentFrame)
            self._dbgClient.sendResponseLine(stack, self.name)
        except Exception as e:
            printerr(e)

    def set_quit(self):
        """
        Public method to quit debugging.

        Disables the trace functions and resets all frame pointer.
        """
        for debugThread in self._dbgClient.threads.values():
            debugThread.quitting = True
            debugThread.step_single_threads.clear()
            debugThread.step_over_frames.clear()

        self.reset_trace()

    def reset_debug_information(self):
        """
        Public method to reset the cached debug information.

        This is needed to enable newly set breakpoints or watches, because the debugger
        might stepped already through some of those code objects and disabled further
        processing for speed optimization.
        """
        if DebugBase.trace_active is False:
            return

        current_frame = sys._getframe()
        DebugBase.code_has_breakpoints.clear()
        monitoring.restart_events()

        # Set line events for all threads
        for frame in sys._current_frames().values():
            if frame == current_frame:
                frame = frame.f_back.f_back  # Skip this and the 1st callers frame

            if not frame or not self._has_breakpoint(frame.f_code):
                continue

            with contextlib.suppress(ValueError):
                # Raised if debugging stopped while in a BP or tiggered by a late thread
                monitoring.set_local_events(
                    monitoring.DEBUGGER_ID, frame.f_code, events.LINE
                )

    def __event_poll_timer(self):
        """
        Private method to check every second for new commands.
        """
        self._dbgClient.ignore_thread_ids.add(_thread.get_ident())
        while DebugBase.pollTimerEnabled:
            # Just handle events from Eric direct in the thread
            delay = self._dbgClient.eventPoll()
            time.sleep(delay)  # Use a dynamic poll time to increase responsiveness

    def __fix_frame_filename(self, frame):
        """
        Private method used to fixup the filename for a given frame.

        The logic employed here is that if a module was loaded
        from a .pyc file, then the correct .py to operate with
        should be in the same path as the .pyc. The reason this
        logic is needed is that when a .pyc file is generated, the
        filename embedded and thus what is readable in the code object
        of the frame object is the fully qualified filepath when the
        pyc is generated. If files are moved from machine to machine
        this can break debugging as the .pyc will refer to the .py
        on the original machine. Another case might be sharing
        code over a network... This logic deals with that.

        @param frame the frame object
        @type frame object
        @return fixed up file name
        @rtype str
        """
        # Get module name from __file__
        fn = frame.f_globals.get("__file__")
        try:
            return self.filename_cache[fn]
        except KeyError:
            if fn is None:
                return frame.f_code.co_filename

            absolute_filename = os.path.abspath(fn)
            if absolute_filename.endswith((".pyc", ".pyo", ".pyd")):
                fixed_name = absolute_filename[:-1]
                # Keep original filename if it not exists
                if not os.path.exists(fixed_name):
                    fixed_name = absolute_filename
            else:
                fixed_name = absolute_filename
            # Update cache
            self.filename_cache[fn] = fixed_name
            return fixed_name

    def getFrame(self, frmnr=0):
        """
        Public method to return the frame "frmnr" down the stack.

        @param frmnr distance of frames down the stack. 0 is
            the current frame
        @type int
        @return the current frame
        @rtype frame object
        """
        try:
            return self.frame_list[frmnr]
        except IndexError:
            return None

    def getFrameLocals(self, frmnr=0):
        """
        Public method to return the locals dictionary of the current frame
        or a frame below.

        @param frmnr distance of frame to get locals dictionary of. 0 is
            the current frame
        @type int
        @return locals dictionary of the frame
        @rtype dict
        """
        try:
            f = self.frame_list[frmnr]
        except IndexError:
            return {}
        else:
            return f.f_locals

    def storeFrameLocals(self, frmnr=0):
        """
        Public method to store the locals into the frame, so an access to
        frame.f_locals returns the last data.

        @param frmnr distance of frame to store locals dictionary to. 0 is
            the current frame
        @type int
        """
        with contextlib.suppress(IndexError):
            cf = self.frame_list[frmnr]

            with contextlib.suppress(ImportError, AttributeError):
                if "__pypy__" in sys.builtin_module_names:
                    import __pypy__  # __IGNORE_WARNING_I-10__

                    __pypy__.locals_to_fast(cf)
                    return

            ctypes.pythonapi.PyFrame_LocalsToFast(ctypes.py_object(cf), ctypes.c_int(0))

    def getStack(self, frame=None, frame_list=None):
        """
        Public method to get the stack.

        @param frame frame object to inspect
        @type frame object or list
        @param frame_list where to store the frame information
        @type list or None
        @return list of lists with file name, line number, function name
            and function arguments
        @rtype list of list of [str, int, str, str]
        """
        current_thread = self._dbgClient.currentThread
        if current_thread and current_thread.current_exception_stack:
            return current_thread.current_exception_stack

        tb_lineno = None
        if frame is None:
            fr = self.currentFrame
        elif isinstance(frame, list):
            fr, tb_lineno = frame.pop(0)
        else:
            fr = frame

        if frame_list is None:
            frame_list = self.frame_list

        frame_list.clear()
        stack = []
        while fr is not None:
            fname = self._dbgClient.absPath(self.__fix_frame_filename(fr))
            basename = os.path.basename(fname)
            if basename == "DebugClient.py":
                return stack
            frame_list.append(fr)

            # Always show at least one stack frame, even if it's from eric.
            if stack and basename.startswith(
                (
                    "debug_monitor.py",
                    "debug_settrace.py",
                    "DebugBase.py",
                    "DebugClientBase.py",
                    "ThreadExtension.py",
                    "threading.py",
                )
            ):
                break

            fline = tb_lineno or fr.f_lineno
            ffunc = fr.f_code.co_name

            if ffunc == "?":
                ffunc = ""

            if ffunc and not ffunc.startswith("<"):
                argInfo = getargvalues(fr)
                try:
                    fargs = formatargvalues(
                        argInfo.args, argInfo.varargs, argInfo.keywords, argInfo.locals
                    )
                except Exception:
                    fargs = ""
            else:
                fargs = ""

            stack.append([fname, fline, ffunc, fargs])

            # Is it a stack frame or exception list?
            if isinstance(frame, list):
                if frame != []:
                    fr, tb_lineno = frame.pop(0)
                else:
                    fr = None
            else:
                fr = fr.f_back

        return stack

    def user_line(self, thread_id, frame):
        """
        Public method to handle the user interaction of a particular line.

        @param thread_id the current tread id
        @type int
        @param frame reference to the frame object
        @type frame object
        """
        current_thread = self._dbgClient.threads[thread_id]
        current_thread.currentFrame = frame
        current_thread.isBroken = True

        # Send updated thread list to GUI
        self._dbgClient.dumpThreadList()

        while True:
            # Acquire lock to show other threads that some thread is already running
            self._dbgClient.lockClient()

            # Check if it is the requested thread
            if thread_id not in self._dbgClient.exec_threads:
                # Mark this thread as already checked. If no other exists, execute this
                self._dbgClient.exec_threads.append(thread_id)
                # Release this thread and wait till switched to the next thread
                self._dbgClient.unlockClient()
                time.sleep(5 * sys.getswitchinterval())
                continue

            # Update internal pointers
            self.currentFrame = frame
            self._dbgClient.currentThread = current_thread
            self._dbgClient.currentThreadExec = current_thread

            # Send information about the current stack and thread
            stack = self.getStack(frame, current_thread.frame_list)
            self._dbgClient.sendResponseLine(stack, current_thread.name)

            # Execute event loop to get user response
            self._dbgClient.eventLoop(True)

            # Check why we have left the event loop: If debugging continues (thread_id
            # is in the list), just leave the loop and exit this method
            if thread_id in self._dbgClient.exec_threads:
                self._dbgClient.exec_threads.remove(thread_id)
                break

            # Allow switching to another thread
            self._dbgClient.unlockClient()
            time.sleep(5 * sys.getswitchinterval())

        current_thread.frame_list.clear()

        current_thread.isBroken = False
        self._dbgClient.unlockClient()
        self._dbgClient.dumpThreadList()

    def user_exception(self, excinfo, unhandled=False):
        """
        Public method to report an exception to the debug server and wait for user.

        @param excinfo details about the exception
        @type tuple(Exception, excval object, traceback frame object)
        @param unhandled flag indicating an uncaught exception
        @type bool
        """
        exctype, excval, exctb = excinfo

        if (
            not unhandled
            and (
                exctype in (GeneratorExit, StopIteration)
                or not self._dbgClient.reportAllExceptions
            )
        ) or exctype is SystemExit:
            # ignore these
            return

        thread_id = _thread.get_ident()
        current_thread = self._dbgClient.threads[thread_id]

        if exctype in (SyntaxError, IndentationError):
            try:
                if type(excval) is tuple:
                    message, details = excval
                    filename, lineno, charno, _text = details
                else:
                    message = excval.msg
                    filename = excval.filename
                    lineno = excval.lineno
                    charno = excval.offset

                if filename is None:
                    realSyntaxError = False
                else:
                    if charno is None:
                        charno = 0

                    filename = os.path.abspath(filename)
                    realSyntaxError = os.path.exists(filename)
            except (AttributeError, ValueError):
                message = ""
                filename = ""
                lineno = 0
                charno = 0
                realSyntaxError = True

            if realSyntaxError:
                self._dbgClient.sendSyntaxError(
                    message, filename, lineno, charno, current_thread.name
                )
                self._dbgClient.eventLoop()
                current_thread.frame_list.clear()
                return

        current_thread.skipFrames = 0
        if (
            exctype is RuntimeError
            and str(excval).startswith("maximum recursion depth exceeded")
        ) or exctype is RecursionError:
            excval = "maximum recursion depth exceeded"
            depth = 0
            tb = exctb
            while tb:
                tb = tb.tb_next

                if (
                    tb
                    and tb.tb_frame.f_code.co_name == "trace_dispatch"
                    and __file__.startswith(tb.tb_frame.f_code.co_filename)
                ):
                    depth = 1
                current_thread.skipFrames += depth

            # Always 1 if running without debugger
            current_thread.skipFrames = max(1, current_thread.skipFrames)

        exctypetxt = str(exctype).removeprefix("<class '").removesuffix("'>")
        if unhandled:
            exctypetxt = f"unhandled {exctypetxt}"

        if excval is None:
            excval = ""

        current_thread.isBroken = True
        current_thread.isException = True

        disassembly = None
        stack = []
        if exctb:
            frlist = self.__extract_stack(exctb)
            frlist.reverse()
            disassembly = self.__disassemble(frlist[0][0])

            current_thread.currentFrame = frlist[0][0]
            stack = self.getStack(frlist[self.skipFrames :], current_thread.frame_list)

        current_thread.current_exception_stack = stack
        self._dbgClient.currentThread = current_thread
        self._dbgClient.currentThreadExec = current_thread
        self._dbgClient.dumpThreadList()  # Update thread list before main window freeze
        self._dbgClient.sendException(
            exctypetxt, str(excval), stack, current_thread.name
        )

        # Avoid to accidentally jump into another thread
        self._dbgClient.exec_threads.clear()
        self._dbgClient.exec_threads.append(thread_id)

        init_done = False
        while True:
            # Acquire lock to show other threads that some thread is already running
            self._dbgClient.lockClient()

            # Check if it is the requested thread
            if thread_id not in self._dbgClient.exec_threads:
                # Mark this thread as already checked. If no other exists, execute this
                self._dbgClient.exec_threads.append(thread_id)
                # Release this thread and wait till switched to the next thread
                self._dbgClient.unlockClient()
                time.sleep(5 * sys.getswitchinterval())
                continue

            self._dbgClient.currentThread = current_thread
            self._dbgClient.currentThreadExec = current_thread
            self._dbgClient.dumpThreadList()
            self._dbgClient.setDisassembly(disassembly)

            if init_done:
                # Rehighlights but also makes yellow color when continue
                self._dbgClient.sendResponseLine(stack, current_thread.name)
            init_done = True

            if exctb is not None:
                # When polling kept enabled, it isn't possible to resume after an
                # unhandled exception without further user interaction.
                self._dbgClient.eventLoop(True)

            # Check why we have left the event loop: If debugging continues (thread_id
            # is in the list), just leave the loop and exit this method. If a switch to
            # another thread is requested, the exec_threads is cleared and we loop again
            if thread_id in self._dbgClient.exec_threads:
                self._dbgClient.exec_threads.remove(thread_id)
                break

            # Allow switching to another thread
            self._dbgClient.unlockClient()
            time.sleep(5 * sys.getswitchinterval())

        current_thread.current_exception_stack = None
        current_thread.frame_list.clear()
        current_thread.skipFrames = 0
        current_thread.currentFrame = None
        self._dbgClient.currentThread = None

        current_thread.isBroken = False
        current_thread.isException = False
        self._dbgClient.unlockClient()

        # Keep thread_id visible if it's a local exception only
        if not unhandled:
            thread_id = None
        self._dbgClient.dumpThreadList(thread_id)

    def __extract_stack(self, exctb):
        """
        Private member to return a list of stack frames.

        @param exctb exception traceback
        @type traceback
        @return list of stack frames
        @rtype list of frame
        """
        tb = exctb
        stack = []
        try:
            while tb is not None:
                stack.append((tb.tb_frame, tb.tb_lineno))
                tb = tb.tb_next
        except AttributeError:
            stack.append((exctb, exctb.f_lineno))

        # Follow first frame to bottom to catch special case if an exception
        # is thrown in a function with breakpoint in it.
        # eric's frames are filtered out later by self.getStack
        frame = stack[0][0].f_back
        while frame is not None:
            stack.insert(0, (frame, frame.f_lineno))
            frame = frame.f_back

        return stack

    def __disassemble(self, frame):
        """
        Private method to generate a disassembly of the given code object.

        @param frame frame object to be disassembled
        @type code
        @return dictionary containing the disassembly information
        @rtype dict
        """
        co = frame.f_code
        return {
            "lasti": frame.f_lasti,
            "firstlineno": co.co_firstlineno,
            # 1. disassembly info
            "instructions": [
                {
                    "lineno": instr.starts_line or 0,
                    "starts_line": instr.starts_line is not None,
                    "isJumpTarget": instr.is_jump_target,
                    "offset": instr.offset,
                    "opname": instr.opname,
                    "arg": instr.arg,
                    "argrepr": instr.argrepr,
                    "label": "dummy_label" if instr.is_jump_target else "",
                }
                if sys.version_info < (3, 13, 0)  # IDE might be 3.13.0+
                else {
                    "lineno": instr.line_number or 0,
                    "starts_line": instr.starts_line,
                    "isJumpTarget": instr.is_jump_target,
                    "offset": instr.offset,
                    "opname": instr.opname,
                    "arg": instr.arg,
                    "argrepr": instr.argrepr,
                    "label": "" if instr.label is None else instr.label,
                }
                for instr in dis.get_instructions(co)
            ],
            # 2. code info
            # Note: keep in sync with PythonDisViewer.__createCodeInfo()
            "codeinfo": {
                "name": co.co_name,
                "filename": co.co_filename,
                "firstlineno": co.co_firstlineno,
                "argcount": co.co_argcount,
                "kwonlyargcount": co.co_kwonlyargcount,
                "posonlyargcount": co.co_posonlyargcount,
                "nlocals": co.co_nlocals,
                "stacksize": co.co_stacksize,
                "flags": dis.pretty_flags(co.co_flags),
                "consts": [str(const) for const in co.co_consts],
                "names": [str(name) for name in co.co_names],
                "varnames": [str(name) for name in co.co_varnames],
                "freevars": [str(var) for var in co.co_freevars],
                "cellvars": [str(var) for var in co.co_cellvars],
            },
        }

    def __extractSystemExitMessage(self, excinfo):
        """
        Private method to get the SystemExit code and message.

        @param excinfo details about the SystemExit exception
        @type tuple(Exception, excval object, traceback frame object)
        @return SystemExit code and message
        @rtype int, str
        """
        _exctype, excval, _exctb = excinfo
        if excval is None:
            exitcode = 0
            message = ""
        elif isinstance(excval, str):
            exitcode = 1
            message = excval
        elif isinstance(excval, bytes):
            exitcode = 1
            message = excval.decode()
        elif isinstance(excval, int):
            exitcode = excval
            message = ""
        elif isinstance(excval, SystemExit):
            code = excval.code
            if isinstance(code, str):
                exitcode = 1
                message = code
            elif isinstance(code, bytes):
                exitcode = 1
                message = code.decode()
            elif isinstance(code, int):
                exitcode = code
                message = ""
            elif code is None:
                exitcode = 0
                message = ""
            else:
                exitcode = 1
                message = str(code)
        else:
            exitcode = 1
            message = str(excval)

        return exitcode, message

    def tracePythonLibs(self, enable):
        """
        Public method to update the settings to trace into Python libraries.

        @param enable flag to debug into Python libraries
        @type bool
        """
        paths_to_skip = list(self.paths_to_skip)
        # Don't trace into Python library?
        if enable:
            paths_to_skip = [
                x
                for x in paths_to_skip
                if not x.endswith(("site-packages", "dist-packages", self.lib))
            ]
        else:
            paths_to_skip.append(self.lib)
            localLib = [
                x
                for x in sys.path
                if x.endswith(("site-packages", "dist-packages"))
                and not x.startswith(self.lib)
            ]
            paths_to_skip.extend(localLib)

        self.paths_to_skip = tuple(set(paths_to_skip))

    def __skip_file(self, co_filename):
        """
        Private method to filter out debugger files.

        Tracing is turned off for files that are part of the
        debugger that are called from the application being debugged.

        @param co_filename the frame's filename
        @type co_filename str
        @return flag indicating whether the debugger should skip this file
        @rtype bool
        """
        try:
            return self.files_to_skip[co_filename]
        except KeyError:
            ret = co_filename.startswith(self.paths_to_skip)
            self.files_to_skip[co_filename] = ret
            return ret
        except AttributeError:
            # if co_filename is None
            return True

    def setRecursionDepth(self, frame):
        """
        Public method to determine the current recursion depth.

        @param frame The current stack frame.
        @type frame object
        """
        self.recursion_depth = 0
        while frame is not None:
            self.recursion_depth += 1
            frame = frame.f_back
