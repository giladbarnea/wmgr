# * This file shouldn't import anything at root level!
"""
--no-notif                  default True
--no-print                  default True
--ignore-scripts[=false]    default True
--stdout-result             default False

No-op if --no-print:
    info  = console_info
    warn  = console_warn
    error = console_error
    debug = console_debug
    fatal = console_fatal
    good  = console_good

if --no-notif:
    notif_{info,warn,error,fatal,good} refer to console_* (no-op if --no-print)
otherwise notif_* source zenity.sh and call z.{level} with --bg
"""
import sys

# global should_notify
# global ignore_scripts
# global should_print

should_notify = True
ignore_scripts = True
should_print = True
should_stdout_result = False

for arg in sys.argv:
    if arg == '--no-notif':
        should_notify = False
        continue
    
    if arg.startswith('--ignore-scripts'):
        _, _, argval = arg.partition('=')
        ignore_scripts = False if argval.lower() == 'false' else True
        continue
    
    if arg == '--no-print':
        should_print = False
        continue
    
    if arg == '--stdout-result':
        should_stdout_result = True
        continue

if should_print:
    from rich.console import Console
    from rich.theme import Theme
    import os
    
    console = Console(file=sys.stderr,
                      color_system="truecolor",
                      tab_size=4,
                      stderr=True,
                      width=int(int(os.environ.get('COLUMNS', 240)) * 2 / 3),
                      theme=Theme({
                          '#':      'dim',
                          'debug':  'dim',
                          'warn':   'yellow',
                          'error':  'red',
                          'fatal':  'bright_red',
                          'good':   'green',
                          'prompt': 'b bright_cyan',
                          }))
    
    
    def console_log(message):
        console.log(message, _stack_offset=2)
    
    
    console_error = lambda message: console.log(f'[error]{message}[/]', _stack_offset=2)
    console_warn = lambda message: console.log(f'[warn]{message}[/]', _stack_offset=2)
    console_debug = lambda message: console.log(f'[debug]{message}[/]', _stack_offset=2)
    console_fatal = lambda message: console.log(f'[fatal]{message}[/]', _stack_offset=2)
    console_good = lambda message: console.log(f'[good]{message}[/]', _stack_offset=2)
else:
    console_log = lambda *args, **kwargs: True
    console_error = lambda *args, **kwargs: True
    console_warn = lambda *args, **kwargs: True
    console_debug = lambda *args, **kwargs: True
    console_fatal = lambda *args, **kwargs: True
    console_good = lambda *args, **kwargs: True

info = console_log
warn = console_warn
error = console_error
debug = console_debug
fatal = console_fatal
good = console_good

if not should_notify:
    notif_info = info
    notif_warn = warn
    notif_error = error
    notif_fatal = fatal
    notif_good = good

else:
    
    def _notif(text, level: "good, info, warn, error, fatal") -> bool:
        """
        Makes a bash command to source ~/dev/bashscripts/zenity.sh and calls one of the z.{level} functions.
        Not affected by `--no-print`, unless the actual sourcing and calling of zenity.sh fails.
        `notify_if_stderr` must be False to prevent recursion in case the actual source of zenity.sh fails.
        Note: zenity.sh functions also log to stderr.
        """
        import os
        zenity = os.path.expanduser("~/dev/bashscripts/zenity.sh")
        # return bash(f'source "{zenity}"; z.{level} "{text}" --bg', notify_if_stderr=False)
        return bash([f'source {zenity}; z.{level} "{text}" --bg'],
                    notify_if_stderr=False)
    
    
    def notif_fatal(text):
        return _notif(text, "fatal")
    
    
    def notif_error(text):
        return _notif(text, "error")
    
    
    def notif_warn(text):
        return _notif(text, "warn")
    
    
    def notif_info(text):
        return _notif(text, "info")
    
    
    def notif_good(text):
        return _notif(text, "good")


def bash(cmd, *, timeout=2, quiet=False, notify_if_stderr=should_notify, background=False) -> bool:
    """
    Runs `cmd` with bash. Returns whether the process returned OK or not.

    If the process was not OK:
     - prints cmd and return code via `console_fatal` (which might be a noop if `--no-print` was passed somewhere)
     - notifies err message with zenity (recursively), unless `notify_if_stderr=False`.


    `quiet=True` means no console_log, no notif_fatal.
    """
    # TODO: bash(cmd, *args, timeout=2, ...)
    if should_print and not quiet: debug(f"common.bash({repr(cmd)}, {timeout = }, {quiet = }, {notify_if_stderr = }, {background = })")
    import subprocess
    try:
        try:
            # marginally faster than isinstance
            cmdarr = cmd.split()
        except AttributeError:
            cmdarr = cmd
        
        if background:
            proc = subprocess.Popen(cmdarr,
                                    shell=True,
                                    executable='/bin/bash',
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL
                                    )
        else:
            proc = subprocess.Popen(cmdarr,
            
                                    # both shell and executable are needed
                                    shell=True,
                                    executable='/bin/bash',
                                    # timeout=timeout,
            
                                    # DONT pipe stderr, Popen prints stderr automatically
                                    )
        if background:
            return True
        returncode = proc.wait(timeout=timeout)
        returned_ok = returncode in (None, 0)
        if quiet:
            return returned_ok
        
        # quiet is False, so if something went wrong, notify and print that
        if not returned_ok:
            err = ''
            if should_print:
                err = f'common.bash({repr(cmd)})\n\treturncode: {returncode}'
                fatal(err)
            if notify_if_stderr:
                if not err: err = f'common.bash({repr(cmd)})\n\treturncode: {returncode}'
                notif_fatal(err)
            return False
        return True
    except subprocess.TimeoutExpired:
        if quiet:
            return False
        err = ''
        if should_print:
            err = f'common.bash({repr(cmd)}) timed out'
            fatal(err)
        if notify_if_stderr:
            if not err: err = f'common.bash({repr(cmd)}) timed out'
            notif_fatal(err)
        return False


# def _log(text, level: "megatitle, title, good, info, warn, fatal, debug, bold, important, prompt (bright white)") -> bool:
#     """Note: these are really slow (20-30ms each)"""
#     import os
#     logsh = os.path.expanduser("~/dev/bashscripts/log.sh")
#     return bash(f'. "{logsh}"; log.{level} "{text}"', notify_if_stderr=True)
#
#
# def log_megatitle(text):
#     return _log(text, "megatitle")
#
#
# def log_title(text):
#     return _log(text, "title")
#
#
# def log_fatal(text):
#     return _log(text, "fatal")
#
#
# def log_error(text):
#     return _log(text, "error")
#
#
# def log_warn(text):
#     return _log(text, "warn")
#
#
# def log_info(text):
#     return _log(text, "info")
#
#
# def log_good(text):
#     return _log(text, "good")
#
#
# def log_debug(text):
#     return _log(text, "debug")
#
#
# def log_notice(text):
#     return _log(text, "notice")

def proc_output(cmd) -> str:
    import subprocess
    return subprocess.Popen(cmd.split(), stdout=subprocess.PIPE).stdout.read().decode()


def launch(executable, *args) -> bool:
    # TODO: bash(cmd, *args, timeout=2, ...)
    executable = quote_if_space(executable)
    import os
    for d in os.environ['PATH'].split(':'):
        if os.path.isfile(joined := os.path.join(d, executable)):
            if args:
                return bash([joined, *args], background=True)
            else:
                return bash(joined, background=True)
    return False
    
    launchsh = os.path.expanduser("~/dev/bashscripts/launch.sh")
    logsh = os.path.expanduser("~/dev/bashscripts/log.sh")
    return bash([f'source {logsh}; source "{launchsh}"; launch {cmd}'], notify_if_stderr=False)


def is_wid(val) -> bool:
    """e.g. '100901473'"""
    return 8 <= len(val) <= 9 and val.isdigit()


def is_hexid(val) -> bool:
    """e.g. '0x0603a261'"""
    return val.startswith('0x') or (len(val) == 6 and val.isdigit())


def quote_if_space(s):
    return s if ' ' not in s else f"'{s}'"


def prettydoc(fn) -> str:
    import inspect
    return f"{fn.__qualname__}{inspect.signature(fn)}\n{fn.__doc__}"


def prettyerr(e: Exception) -> str:
    return f'{e.__class__.__qualname__}: {", ".join(e.args)}'


settings = {
    "last_is_most_recent": {
        "nautilus",
        # "chrome",
        "brave",
        "vlc",
        "pycharm",
        "kitty",
        },
    "kitty": {
        "same_name_means_duplicate": False,
        },
    "evince":              {
        "same_name_means_duplicate": False,
        },
    "pycharm":             {
        "ignore": ["Content window"]
        },
    "code":                {
        "ignore": [
            "gilad@gilad.*"
            ]
        }
    }


def get_monitors() -> list[dict]:
    import re
    import subprocess as sp
    monitor_re = re.compile(r'(?P<primary>primary )?(?P<w>\d{4})x(?P<h>\d{4})\+(?P<x>\d{1,4})\+(?P<y>\d{1,4})')
    monitors = []
    for line in sp.Popen(['xrandr'], stdout=sp.PIPE).stdout.read().decode().splitlines():
        if line.startswith(' '):
            continue
        if 'disconnected' in line:
            continue
        match = monitor_re.search(line)
        if not match:
            continue
        monitor = dict()
        for k, v in match.groupdict().items():
            if v is not None and v.isdigit():
                monitor[k] = int(v)
            else:
                monitor[k] = v
        monitors.append(monitor)
    if len(monitors) > 1:
        # Make sure monitors are sorted top to bottom. this means no support for side-by-side monitors
        if not all(monitors[i + 1]['y'] > mon['y'] for i, mon in enumerate(monitors[:-1])):
            err = f"Monitors are not sorted top to bottom (y should increase). {monitors = }"
            notif_fatal(f'common.get_monitors() | {err}')
            raise RuntimeError(err)
    
    return monitors


def compile_wmc_pattern():
    import re
    import os
    user = os.uname().nodename
    return re.compile(
            r'(?P<hexid>0x[a-f\d]+)\s+'
            r'(?P<desktop>\d)\s+'
            r'('
            r'(?P<x>\d{1,5})\s+'
            r'(?P<y>\d{1,5})\s+'
            r'(?P<w>\d{1,5})\s+'
            r'(?P<h>\d{1,5})\s+'
            r'|'
            r'(?P<pid>\d{4,6})\s+'
            r'(?P<classname>[\w\d_\-. ]+)\s+'
            r')'
            rf'(?P<user>{user})\s+'
            r'(?P<name>.+)'
            )


def split_wmc_line(line, pattern=None) -> dict:
    # currently only handles '-lG' (Geometry) and '-lpx' (pid and class name)
    if not pattern:
        pattern = compile_wmc_pattern()
    match = pattern.fullmatch(line)
    if not match:
        print(f'no match! line: \n{line}', file=sys.stderr)
        breakpoint()
    # if no -G, then x,y, ... are None
    return {k: int(v) if v.isdigit() else v.rstrip() for k, v in match.groupdict().items() if v}
