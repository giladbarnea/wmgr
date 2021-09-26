#!python3.9

def main(app: str, *args, **kwargs) -> bool:
    """
    Arguments
        `app` is what `getwid.main` supports: name (`'pycharm'`), wid (`'100901473'`), pid (`'125888'`), hexid (`'0x0603a261'`).
        `alt=foo,bar` Possibly calls this function recursively for each alternative until succeeds
         supported both in args and kwargs
         
        `--launch-new[=EXEC_PATH]`
    
    """

    # from common import should_print # 0.5ms
    import common  # 2ms?
    if common.should_print: common.debug(f'\nmain({app = }, {args = }, {kwargs = })')

    launch_new = False
    exec_path = None
    import subprocess
    alt_names: list = []
    for arg in args:
        if arg.startswith('--alt='):
            alt_names = arg[6:].split(',')
            continue
        if arg.startswith('--launch-new'):
            *_, exec_path = arg.partition("=")
            launch_new = True
            continue
    ## Uncomment when supports launch_new from args/kwargs
    # def is_text(_arg) -> bool:
    #     if not _arg:
    #         return False
    #     if isinstance(_arg, str):
    #         return _arg.lower().strip() != 'true'
    #
    #     return False
    #
    # def parse_boollike(_arg) -> bool:
    #     if not _arg:
    #         return False
    #     if isinstance(_arg, str):
    #         return _arg.lower().strip() == 'true'
    #
    #     if isinstance(_arg, int):
    #         return _arg == 1
    #     return _arg is True
    # if is_text(launch_new):
    #     exec_path = launch_new.strip()
    #     launch_new = True
    # else:
    #     exec_path = None
    #     launch_new = parse_boollike(launch_new)

    import getwid
    wid = getwid.main(app)  # ~30ms, 80% of run time
    if common.should_print: common.info(f'getwid returned: {repr(wid)}')

    if wid:
        proc = subprocess.Popen(['xdotool', 'windowactivate', wid], stderr=subprocess.PIPE)  # ~5ms, 12% of run time
        stderr = proc.stderr.read()
        if not stderr:
            if common.should_print: common.good(f'Activated {wid} successfully')
            return True

        # We have stderr
        # xdotool is quiet unless err which looks like "XGetWindowProperty[_NET_WM_DESKTOP] failed (code=1)" but code is 0
        if common.should_print:
            common.warn((f"wid: {repr(wid)} failed because xdotool stderred: "
                         f'{stderr}'
                         f"\n\tCalling getwid with ignore={wid}..."))
        wid = getwid.main(app, ignore={wid})
        if common.should_print: common.info(f'getwid returned: {repr(wid)}')

        if not wid:
            if not launch_new:
                # The simple use case of activating an app that's not running
                common.notif_fatal(f'wid is Falsey and launch_new is False. aborting')
                return False
            if exec_path:
                return common.launch(exec_path)
            else:
                return common.launch(app)
        proc = subprocess.Popen(['xdotool', 'windowactivate', wid], stderr=subprocess.PIPE)
        stderr = proc.stderr.read()
        if not stderr:
            if common.should_print: common.good(f'Activated {wid} successfully')
            return True
        common.notif_fatal((f"wid: {repr(wid)} failed because xdotool stderred: "
                            f"{stderr}"
                            "\n\tgiving up"))
        return False

    if not wid and not launch_new:
        alt_names.extend(kwargs.get('alt', []))
        if not alt_names:
            common.notif_fatal("wid is Falsey, alt not in kwargs, and no arg startswith --alt=. aborting")
            return False
        # alt_names is not None
        for alt_name in alt_names:
            if main(alt_name):
                return True
        common.notif_fatal(f'wid is Falsey, {alt_names = } but none succeeded. aborting')
        return False

    if common.should_print: common.info("wid is falsey, launching new")
    if exec_path:
        return common.launch(exec_path)
    else:
        return common.launch(app)


if __name__ == '__main__':
    import sys

    isok = main(*sys.argv[1:])
    sys.exit(not isok)
    #
    # try:
    #     # should_print and console_log(f'[INFO] before calling main({", ".join(sys.argv[1:])})')
    #     isok = main(*sys.argv[1:])
    # except Exception as e:
    #     print(f'[fatal] main() raised {e.__class__}: {", ".join(map(str, e.args))}. sys.argv[1:] are: {", ".join(sys.argv[1:])}', file=sys.stderr)  # else:
    #     # should_print and console_log(f'main() → {isok}')
