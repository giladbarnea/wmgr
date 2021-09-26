#!python3.9


# @profile
def main(app: str, *args, **kwargs) -> str or bool:
    """
    `app` can be: name (`'pycharm'`), wid (`'100901473'`), pid (`'125888'`), hexid (`'0x0603a261'`).
    
    `kwargs` support:
     - `ignore={wid, name, ...}` (a set that can contain wids and names, not hexid or pid)

    Note: two pycharm instances have the same pid (not the same hexid)
    
    Returns wid, e.g. '100901473', or False if fails.
    """

    def print_help():
        import common
        print(common.prettydoc(main))
        return False

    if 'help' in app or app == '-h':
        print_help()
        return False

    import common

    def should_ignore(_ignore: set, _name: str) -> bool:  # ignore: set of strings or re.Pattern's
        for _ig in _ignore:
            try:
                if _ig.search(_name):
                    return True
            except AttributeError:  # str
                if _name == _ig:
                    return True
        return False

    if common.should_print:
        common.debug(f'\n⟨getwid.py⟩ app = "{app}", {args = }, {kwargs = }')

    app = str(app)  # normalize
    if common.is_wid(app):
        # ** `app` is wid, e.g. '100901473'
        if common.should_print: common.good(f'⟨getwid.py⟩ `app` is wid (8<=len<=9 and digit):')
        if common.should_stdout_result: print(app, end='')
        return app
    if common.is_hexid(app):
        # ** `app` is hexid, e.g. '0x0603a261', or pid, e.g. '125888'. load the window name into `app` var to pass to xdt
        if common.should_print: common.info(f'⟨getwid.py⟩ `app` is hexid (0x...) or pid (6 digits)')
        import subprocess as sp
        pattern = common.compile_wmc_pattern()
        for line in common.proc_output('wmctrl -lpx').splitlines():
            linedict = common.split_wmc_line(line, pattern)
            hexid = linedict['hexid']
            pid = linedict['pid']
            name = linedict['name']
            if hexid == app or pid == app:
                app = name
                break
        else:
            # split_wmc_line or 'wmctrl -lpx' didn't return any hexid or pid that equalled 'app'
            breakpoint()

    # ** `app` is name
    import subprocess as sp

    # ~20ms?
    wids = []
    for line in common.proc_output(f'xdotool search --onlyvisible --classname {common.quote_if_space(app)}').splitlines():
        stripped = line.rstrip()
        if stripped:
            wids.append(stripped)

    if not wids:
        if common.should_print: common.warn(f'⟨getwid.py⟩ xdotool search --classname did not return anything, trying with --name')
        for line in common.proc_output(f'xdotool search --onlyvisible --name {common.quote_if_space(app)}').splitlines():
            stripped = line.rstrip()
            if stripped:
                wids.append(stripped)

        if not wids:
            if common.should_print: common.error(f"⟨getwid.py⟩ xdotool search --onlyvisible '--classname' and '--name' returned empty for app: '{app}'. Returning False")
            return False

    if common.should_print: common.info(f'⟨getwid.py⟩ wids: {wids}')
    from collections import OrderedDict
    name_2_wid = OrderedDict()

    import re

    # ** popuplate `ignore` set
    # * from settings.json e.g. code: { ignore: ["gilad@gilad.*"] }
    try:
        # ignore: set of strings or re.Pattern's
        ignore = set()
        for ig in common.settings[app]['ignore']:
            if "*" in ig:
                ignore.add(re.compile(ig))
            else:
                ignore.add(ig)

    except KeyError:
        ignore = set()

    # * from kwargs
    kwargs_ignore = kwargs.get('ignore')
    if kwargs_ignore:
        ignore.update(kwargs_ignore)

    # * from --ignore-scripts arg, true by default
    if common.ignore_scripts:
        from pathlib import Path
        # getwid.py, winactivate.py...
        winmgmt_py_files = map(lambda p: p.name, Path(__file__).parent.glob('*.py'))

    # ** check which wids should not be added to name_2_wid. not adding to name_2_wid means ignoring
    if common.should_print: common.debug(f'⟨getwid.py⟩ ignore set: {ignore}')
    same_name_means_duplicate = common.settings.get(app, {}).get('same_name_means_duplicate', True)
    for wid in wids:
        if wid in ignore:
            # ignore can contain wids and names
            if common.should_print: common.warn(f'\t⟨getwid.py⟩ ignoring: {repr(wid)}')
            continue

        # ~10ms?
        name = sp.Popen(['xdotool', 'getwindowname', wid], stdout=sp.PIPE).stdout.read().decode().strip()

        if common.should_print: common.debug(f'\t⟨getwid.py⟩ figuring out if should ignore: name: {repr(name)}, wid: {repr(wid)}')
        if same_name_means_duplicate and name in name_2_wid:
            # duplicate, because was popuplated in the end of loop. duplicates mean both are bad. ignore
            if common.should_print: common.warn(f'\t⟨getwid.py⟩ ignoring because duplicate. name: {repr(name)}, wid: {repr(wid)}')
            ignore.add(name)
            del name_2_wid[name]
            continue
        # reaching here means it's a new name
        if common.ignore_scripts:

            if any(winmgmt_py_file in name and not (  # any of the following conditions means we should not ignore
                    # "^...getwid.py ...$" is bad, but "^... getwid.py$" isn't because that's probably pycharm editing the file:
                    (app == 'pycharm' and name.endswith(winmgmt_py_file))
                    or
                    # "^...getwid.py ...Visual Studio Code" is also ok
                    (app == 'code' and name.endswith('Visual Studio Code'))
            )
                   for winmgmt_py_file in winmgmt_py_files):
                if common.should_print: common.warn(f'\t⟨getwid.py⟩ ignoring because some winmgmt_py_file name is substring of name: {repr(name)}, wid: {repr(wid)}, app: {app}')
                continue
        if should_ignore(ignore, name):
            if common.should_print: common.warn(f'\t⟨getwid.py⟩ ignoring because should_ignore({ignore}, {name}). wid: {repr(wid)}')
            continue

        name_2_wid[name] = wid

        if common.should_print: common.good(f'\t⟨getwid.py⟩ (not ignoring): name: {repr(name)}, wid: {repr(wid)}')
    if common.should_print: common.debug(f'⟨getwid.py⟩ name_2_wid: {name_2_wid}')
    if not name_2_wid:
        if common.should_print: common.fatal("⟨getwid.py⟩: no good wid found (all ignored or none found in the first place). returning False")
        return False

    if len(name_2_wid) == 1:
        wid = name_2_wid[next(iter(name_2_wid))]
        if common.should_print: common.good(f'⟨getwid.py⟩ returning wid:')
        if common.should_stdout_result: print(wid, end='')
        return wid

    last = app in common.settings['last_is_most_recent']
    item = name_2_wid.popitem(last=last)
    if common.should_print: common.good(f'⟨getwid.py⟩ returning item[1]. item: {item}')
    if common.should_stdout_result: print(item[1], end='')
    return item[1]


if __name__ == '__main__':
    import sys

    try:
        main(*sys.argv[1:])
    except Exception as e:
        import common

        prettyerr = common.prettyerr(e)
        common.notif_fatal(prettyerr)
