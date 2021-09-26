#!python3.9

def main(app: str, *args):
    """gethexid.py
    Returns hex, e.g. 0x0603a261.
    `app` can be: name (pycharm), wid (100901473), pid (125888), hexid (0x0603a261)

    Note: two pycharm instances have the same pid (not true for hexid)
    
    Does not call
    """
    import common
    if 'help' in app or app == '-h' or any('help' in arg or arg == '-h' for arg in args):
        print(common.prettydoc(main))
        return False
    if common.should_print: common.debug(f'gethexid.main({app = }, {args = })')
    if common.is_hexid(app):
        if common.should_stdout_result: print(app, end='')
        return app
    import subprocess as sp
    wmc_pattern = None
    if common.is_wid(app):
        wmc_pattern = common.compile_wmc_pattern()
        # app is wid, e.g. '100901473'
        name = sp.Popen(f'xdotool getwindowname "{app}"'.split(), stdout=sp.PIPE).stdout.read().decode()
        line = sp.Popen(f'wmctrl -lpx | grep "{name}"'.split(), stdout=sp.PIPE).stdout.read().decode()  # only one wid or hexid
        linedict = common.split_wmc_line(line, wmc_pattern)
        hexid = linedict['hexid']
        if common.should_stdout_result: print(hexid, end='')
        return hexid

    # app is pid or name
    lines = sp.Popen(f'wmctrl -lpx | grep "{app}"'.split(), stdout=sp.PIPE).stdout.read().decode().splitlines()
    if common.should_print: common.debug(f'⟨gethexid.py⟩ wmc lines: {lines}')
    if not wmc_pattern:
        wmc_pattern = common.compile_wmc_pattern()
    if len(lines) == 1:
        line = lines[0]
        linedict = common.split_wmc_line(line, wmc_pattern)
        hexid = linedict['hexid']
        if common.should_stdout_result: print(hexid, end='')
        return hexid
    linedicts = []
    script_file_name = __file__
    import re
    # TODO: use --ignore-scripts
    compiled_re = re.compile(rf'{script_file_name} ([\'"])?{app}\1?')
    for line in lines:
        linedict = common.split_wmc_line(line, wmc_pattern)
        name = linedict['name']

        if compiled_re.search(name):
            # gethexid.py Lotion, gethexid.py 'Lotion', gethexid.py "Lotion"
            continue
        linedicts.append(linedict)

    if common.should_print: common.debug(f'⟨gethexid.py⟩ linedicts: {linedicts}')
    if len(linedicts) == 1:
        linedict = linedicts[0]

        hexid = linedict['hexid']
        if common.should_stdout_result: print(hexid, end='')
        return hexid

    classnames_lowercase = []
    all_linedicts_have_same_classname = False
    linedicts_with_relevant_classnames = []
    linedicts_with_relevant_classnames_length = 0
    for linedict in linedicts:
        classname_lowercase = linedict['classname'].lower()
        linedict['classname'] = classname_lowercase
        if app not in classname_lowercase:
            all_linedicts_have_same_classname = False
            break
        classnames_lowercase.append(classname_lowercase)
        linedicts_with_relevant_classnames.append(linedict)
        linedicts_with_relevant_classnames_length += 1
    all_linedicts_have_same_classname = True
    if all_linedicts_have_same_classname:
        # several linedicts, all of them have the same classname
        for x in common.settings['last_is_most_recent']:
            # if this app is among the apps in last_is_most_recent,
            # then return the hexid of the last of them
            if all(x in classname for classname in classnames_lowercase):
                hexid = linedicts[-1]['hexid']
                if common.should_stdout_result: print(hexid, end='')
                return hexid
        hexid = linedicts[0]['hexid']
        if common.should_stdout_result: print(hexid, end='')
        return hexid
    else:
        # several linedicts, different classnames
        # apps_with_relevant_classnames = [linedict for linedict in linedicts if app in linedict['classname'].lower()]
        if linedicts_with_relevant_classnames_length == 1:
            linedict = linedicts_with_relevant_classnames[0]

            hexid = linedict['hexid']
            if common.should_stdout_result: print(hexid, end='')
            return hexid
        else:
            for x in common.settings['last_is_most_recent']:
                # if this app is among the apps in last_is_most_recent,
                # then return the hexid of the last of them
                if all(x in linedict for linedict in linedicts_with_relevant_classnames):
                    hexid = linedicts[-1]['hexid']
                    if common.should_stdout_result: print(hexid, end='')
                    return hexid
            hexid = linedicts_with_relevant_classnames[0]['hexid']
            if common.should_stdout_result: print(hexid, end='')
            return hexid


if __name__ == '__main__':
    import sys

    main(*sys.argv[1:])
