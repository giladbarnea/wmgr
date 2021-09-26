#!python3.9

import sys


def main(app: str, *args):
    """Returns pid, e.g. 125888.
    Handles name (pycharm), wid (100901473), pid (125888), hexid (0x0603a261)

    Note: two pycharm instances have the same pid (not true for hexid)
    """
    from common import console_log
    console_log(f'\ngetpid.main({app = }, {args = })')
    if 8 <= len(app) <= 9 and app.isdigit():
        # app is wid, e.g. '100901473'
        import subprocess as sp
        pid = sp.getoutput(f'xdotool getwindowpid "{app}"')
        print(pid, end='')
        return pid
    if len(app) == 6 and app.isdigit():
        # app is pid, e.g. '125888'
        print(app, end='')
        return app
    if app.startswith('0x'):
        # app is hexid, e.g. '0x0603a261'
        import common
        import subprocess as sp
        for line in sp.getoutput('wmctrl -lpx').splitlines():
            linedict = common.split_wmc_line(line)
            hexid = linedict['hexid']
            pid = linedict['pid']
            if hexid == app:
                print(pid, end='')
                return pid
        console_log(f"[fatal] no line in 'wmctrl -lpx' matched hexid: {app}. aborting[/]")
        return False
    # app is name
    console_log(f'[#] app is a name ({app}), importing getwid...[/]')
    import getwid
    wid = getwid.main(app)
    console_log(f'{wid = }')
    import subprocess as sp
    pid = sp.getoutput(f'xdotool getwindowpid "{wid}"')
    print(pid, end='')
    return pid


if __name__ == '__main__':
    main(*sys.argv[1:])
