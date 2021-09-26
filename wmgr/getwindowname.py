#!python3.9


def main(app: str, *args):
    from common import console_log
    console_log(f'\ngetwindowname.main({app = }, {args = })')
    if not app.startswith('0x'):
        if not app.isdigit():
            # name
            print(app, end='')
            return app
        if 8 <= len(app) <= 9:
            # wid
            import subprocess as sp
            name = sp.getoutput(f'xdotool getwindowname "{app}"')
            print(name, end='')
            return name
        # pid
        import subprocess as sp
        lines = sp.getoutput(f'wmctrl -lpx | grep "{app}"').splitlines()
        import common
        if len(lines) == 1:
            line = lines[0]
            
            linedict = common.split_wmc_line(line)
            name = linedict['name']
            print(name, end='')
            return name
        linedicts = []
        from pathlib import Path
        for line in lines:
            linedict = common.split_wmc_line(line)
            name = linedict['name']
            if name == f'{Path(__file__).name} {app}':
                continue
            linedicts.append(linedict)
        console_log(f'{linedicts = }')
        last_is_most_recent = common.get_last_is_most_recent()
        for x in last_is_most_recent:
            if all(x in linedict['classname'] for linedict in linedicts):
                name = linedicts[-1]['name']
                print(name, end='')
                return name
        name = linedicts[0]['name']
        print(name, end='')
        return name
    # hex
    import subprocess as sp
    line = sp.getoutput(f'wmctrl -lpx | grep "{app}"')
    import common
    linedict = common.split_wmc_line(line)
    name = linedict['name']
    print(name, end='')
    return name


if __name__ == '__main__':
    import sys
    
    main(*sys.argv[1:])
