#!python3.9
import os
import re
import sys
from typing import Literal


def main(where: Literal['next'], *args):
    """
    `where` currently can only be "next".
    `args` support `--win=...` (not supporting pid. only wid (8-9 digits), hex (0x...) or name).
    `--no-print` is global and makes `console_log` a noop.
    """
    import common

    common.debug(f'\n{where = }, {args = }')
    monitors = common.get_monitors()
    common.debug(f'{monitors = }')
    if where == 'next' and len(monitors) == 1:
        common.warn('there is only one monitor, returning')
        return False
    for arg in args:
        if arg.startswith('--win'):
            _, _, val = arg.partition('=')
            if common.is_wid(val):
                # wid
                win_name = common.proc_output(f'xdotool getwindowname {common.quote_if_space(val)}')
            elif val.isdigit() and len(val) == 6:
                # pid
                errmsg = 'not supporting pid. only wid (8-9 digits), hex (0x...) or name'
                common.fatal(errmsg)
                raise NotImplementedError(errmsg)
            else:
                # any other value can already be grepped from wmctrl -l (not really because
                win_name = val
            break
    else:
        win_name = common.proc_output('xdotool getactivewindow getwindowname')
    common.debug(f'{win_name = }')

    line = common.proc_output(f'wmctrl -lG | grep "{re.escape(win_name)}"')
    if not line:
        common.warn('wmctrl -lG | grep "{re.escape(win_name)}" returned nothing, trying without escaping')
        line = common.proc_output(f'wmctrl -lG | grep {common.quote_if_space(win_name)}')
        if not line:
            common.error('wmctrl -lG | grep "{win_name}" returned nothing as well')
            breakpoint()

    wmc_pattern = common.compile_wmc_pattern()
    windict = common.split_wmc_line(line, wmc_pattern)
    common.debug(f'{windict = }')
    target_coords = dict()
    # ** Setting target_coords['y'] by inferring whether win is in top mon or bottom
    if windict['y'] < monitors[0]['h'] + monitors[0]['y']:
        # * win in top mon
        current_mon = monitors[0]
        target_mon = monitors[1]
        target_coords['y'] = windict['y'] + target_mon['y']
        msg = (f"\ntarget_coords['y'] (window in top mon)\n\t"
               f"because window's y ({windict['y']}) < the sum of "
               f"0th monitor's height ({monitors[0]['h']}) + y ({monitors[0]['y']}) = {monitors[0]['h'] + monitors[0]['y']},\n\t"
               f"window is in top monitor, meaning 0th mon is current and 1th is target,\n\t"
               f"and target y is set to windict['y'] + target_mon['y'] = {windict['y']} + {target_mon['y']} = {target_coords['y']}")

    else:
        # * win in bottom mon
        # assuming window is on second (bottom) monitor, no checks
        current_mon = monitors[1]
        target_mon = monitors[0]
        target_coords['y'] = windict['y'] - current_mon['y']
        msg = (f"\ntarget_coords['y'] (window in bottom mon)\n\t"
               f"because window's y ({windict['y']}) >= the sum of "
               f"0th monitor's height ({monitors[0]['h']}) + y ({monitors[0]['y']}) = {monitors[0]['h'] + monitors[0]['y']},\n\t"
               f"window is in bottom monitor, meaning 0th mon is target and 1th is current,\n\t"
               f"and target y is set to windict['y'] - current_mon['y'] = {windict['y']} - {current_mon['y']} = {target_coords['y']}")
    common.info(msg)

    # ** Setting target_coords['h'] by whether it would fit in target mon
    win_relative_y_within_target_mon = target_coords['y'] - target_mon['y']
    if win_relative_y_within_target_mon + windict['h'] > target_mon['h']:
        if windict['h'] > target_mon['h']:
            # * window is just too tall for target montior, even if we place it at the top of target monitor
            target_coords['h'] = target_mon['h']
            target_coords['y'] = target_mon['y']
            msg = (f"\ntarget_coords['h'] (window's height won't fit, regardless of relative y within target monitor)\n\t"
                   f"because windict['h'] ({windict['h']}) > target_mon['h'] ({target_mon['h']}),\n\t"
                   f"target_coords['h'] is set to target_mon['h'] = {target_coords['h']}, and\n\t"
                   f"target_coords['y'] is set to target_mon['y'] = {target_coords['y']},\n\t"
                   )
        else:
            # * window itself isn't too tall for target montior, if we just place it high enough within target monitor
            target_coords['h'] = windict['h']
            diff_between_target_mon_height_and_win_height = target_mon['h'] - windict['h']
            half_that_diff = int(diff_between_target_mon_height_and_win_height / 2)
            target_coords['y'] = target_mon['y'] + half_that_diff
            msg = (f"\ntarget_coords['h'] (window isn't too tall but won't fit because of relative y)\n\t"
                   f"because win_relative_y_within_target_mon ({win_relative_y_within_target_mon}) + windict['h'] ({windict['h']}) = {win_relative_y_within_target_mon + windict['h']} > target_mon['h'] ({target_mon['h']}),\n\t"
                   f"it means window's height will fit inside target mon if we place it at the most {diff_between_target_mon_height_and_win_height}px from top of target mon,\n\t"
                   f"so target_coords['h'] is set to windict['h'] ({windict['h']}),\n\t"
                   f"and target_coords['y'] is set to {target_coords['y']}, which is target_mon['y'] ({target_mon['y']}) + half the height diff ({half_that_diff})")
    else:
        # * window's height will fit inside target monitor, even with its relative y
        ratio_between_current_mon_height_and_win_height = round(windict['h'] / current_mon['h'], 3)
        target_coords['h'] = int(min(ratio_between_current_mon_height_and_win_height * target_mon['h'], target_mon['h']))
        msg = (f"\ntarget_coords['h'] (window's height will fit including relative y)\n\t"
               f"because win_relative_y_within_target_mon ({win_relative_y_within_target_mon}) + windict['h'] ({windict['h']}) = {win_relative_y_within_target_mon + windict['h']} <= target_mon['h'] ({target_mon['h']}),\n\t"
               f"it means win is {ratio_between_current_mon_height_and_win_height}x current monitor's height ({current_mon['h']}),\n\t"
               f"so target_coords['h'] is set respectively = {target_coords['h']}")
    common.info(msg)

    # ** Setting target_coords['x'] accounting for each monitor's x offset
    # bottom monitor has x offset of 326
    # top monitor has x offset of 0
    # from bottom to top: windict['x'] (326) - current_mon['x'] (326) is 0 → 0 + target_mon['x'] (0) is 0 → target_mon['x'] = 0
    # from top to bottom: windict['x'] (0) - current_mon['x'] (0) is 0 → 0 + target_mon['x'] (326) is 326 → target_mon['x'] = 326
    win_relative_x_within_current_mon = windict['x'] - current_mon['x']
    target_coords['x'] = win_relative_x_within_current_mon + target_mon['x']
    msg = (f"\ntarget_coords['x'] (accounting for offset)\n\t"
           f"because windict['x'] is ({windict['x']}) and current_mon['x'] is ({current_mon['x']}) → win_relative_x_within_current_mon is {win_relative_x_within_current_mon},\n\t"
           f"so target_coords['x'] ({target_coords['x']}) is set to win_relative_x_within_current_mon ({win_relative_x_within_current_mon}) + target_mon['x'] ({target_mon['x']})")
    common.info(msg)

    # ** Setting target_coords['w']
    # don't strech beyond target monitor width
    if target_coords['x'] + windict['w'] > target_mon['w']:
        if windict['w'] > target_mon['w']:
            # * window is just too wide for target montior, even if we place it at the left border of target monitor
            target_coords['w'] = target_mon['w']
            target_coords['x'] = target_mon['x']
            msg = (f"\ntarget_coords['w'] (window's width won't fit, regardless of relative x within target monitor)\n\t"
                   f"because windict['w'] ({windict['w']}) > target_mon['w'] ({target_mon['w']}),\n\t"
                   f"target_coords['w'] is set to target_mon['w'] = {target_coords['w']}, and\n\t"
                   f"target_coords['x'] is set to target_mon['x'] = {target_coords['x']},\n\t"
                   )
        else:
            # * window itself isn't too wide for target montior, if we just place it left enough within target monitor
            target_coords['w'] = windict['w']
            diff_between_target_mon_width_and_win_width = target_mon['w'] - windict['w']
            half_that_diff = int(diff_between_target_mon_width_and_win_width / 2)
            target_coords['x'] = target_mon['x'] + half_that_diff
            msg = (f"\ntarget_coords['w'] (window isn't too wide but won't fit because of relative x)\n\t"
                   f"because target_coords['x'] ({target_coords['x']}) + windict['w'] ({windict['w']}) = {target_coords['x'] + windict['w']} > target_mon['w'] ({target_mon['w']}),\n\t"
                   f"it means window's width will fit inside target mon if we place it at the most {diff_between_target_mon_width_and_win_width}px from the left border of target mon,\n\t"
                   f"so target_coords['w'] is set to windict['w'] ({windict['w']}),\n\t"
                   f"and target_coords['x'] is set to {target_coords['x']}, which is target_mon['x'] ({target_mon['x']}) + half the height diff ({half_that_diff})")

    else:
        # * window's width will fit inside target monitor, even with its relative x
        ratio_between_current_mon_width_and_win_width = round(windict['w'] / current_mon['w'], 3)
        target_coords['w'] = int(min(ratio_between_current_mon_width_and_win_width * target_mon['w'], target_mon['w']))
        msg = (f"\ntarget_coords['w'] (window's width will fit including relative x)\n\t"
               f"because target_coords['x'] ({target_coords['x']}) + windict['w'] ({windict['w']}) = {target_coords['x'] + windict['w']} <= target_mon['w'] ({target_mon['w']}),\n\t"
               f"it means win is {ratio_between_current_mon_width_and_win_width}x current monitor's width ({current_mon['w']}),\n\t"
               f"so target_coords['w'] is set to windict['w'] = {target_coords['w']}")
    common.info(msg)
    common.debug(f'\n{current_mon = }\n             {target_mon = }\n             {target_coords = }')

    target_coords_str = ','.join(map(str, [target_coords['x'], target_coords['y'], target_coords['w'], target_coords['h']]))
    common.info(f'\ntarget_coords_str: "{target_coords_str}"')
    code = os.system(f"wmctrl -ivr '{windict['hexid']}' -e '0,{target_coords_str}'")
    return code == 0


if __name__ == '__main__':
    try:
        main(*sys.argv[1:])
    except Exception as e:
        import common

        prettyerr = common.prettyerr(e)
        common.notif_fatal(prettyerr)
