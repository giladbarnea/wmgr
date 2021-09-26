#!/usr/bin/env bash
###############
# $winid eg 39845898
# -------------------
# _iswindowstate
# isalwaysontop
# ismaximized_horz
# ismaximized_vert
# isfullscreen
# windowstate
# get_window_xcoord_by_winid
# xprop -id
# xdotool getwindowgeometry
#
# xdotool getactivewindow : winid
# xdotool search : winid
function isfullscreen() {
  local _edge_constraints
  _edge_constraints=$(xprop -id "$1" | grep -o -P '(?<=EDGE_CONSTRAINTS\(CARDINAL\) = )\d{2,3}$')
  export isfs

  if [[ "$_edge_constraints" == 85 ]]; then
    isfs=true
  else
    isfs=false
  fi
}

function ismaximized_horz() {
  export ismax_horz
  ismax_horz=$(_iswindowstate "$1" '_NET_WM_STATE_MAXIMIZED_HORZ')

}
function ismaximized_vert() {
  export ismax_vert
  ismax_vert=$(_iswindowstate "$1" '_NET_WM_STATE_MAXIMIZED_VERT')

}
function get_monitor_amount() {
  export monitor_amount
  monitor_amount=$(xrandr | grep -c -w connected)
}
function get_monitor_num_by_winid() {
  export monitor_num
  get_window_xcoord_by_winid "$1"
  monitor_num=$(("$xcoord" / 1920))
}
function get_primary_monitor_num() {
  local _pmonitor_rel_x
  export pmonitor_num
  _pmonitor_rel_x=$(xrandr --current | grep -o -P '(?<=primary \d{4}x\d{4}\+)\d{0,4}')
  pmonitor_num=$(("$_pmonitor_rel_x" / 1920))
}
#########################
# ** ####### DEPRECATED ########
#########################
function xsearch() {
  # Exports `wid`. $1: process name (string)
  log "\nxsearch(${*}) | doing 'xdotool search --onlyvisible --classname \"\$1\"'"
  wids=($(xdotool search --onlyvisible --classname "$1" | pyp lines))
  if [[ -z "$wids" ]]; then
    log "xsearch() | '--clasname' returned empty, trying with '--name'..."
    wids=($(xdotool search --onlyvisible --name "$1" | pyp lines))
  fi
  if [[ -z "$wids" ]]; then
    log "xsearch() | bad: '--name' returned empty. aborting"
    return 1
  fi
  log "xsearch() | wids (${#wids}): $wids. popuplating names..."
  #  names=($(echo $wids | pyp lines))
  declare -a names=()
  for wid in $wids; do
    name=$(xdotool getwindowname $wid)
    names+=($name)
  done
  log "xsearch() | names (${#names}): $names"
  local fn
  local otherfn
  log "xsearch() | is either nautilus, chrome or vlc?"
  if [[ "$1" == "nautilus" || "$1" == "chrome" || "$1" == "vlc" ]]; then
    log "xsearch() | yes, either nautilus, chrome or vlc"
    fn="head"
    otherfn="tail"
  else
    log "xsearch() | no, neither nautilus nor chrome nor vlc"
    fn="tail"
    otherfn="head"
  fi
  log "xsearch() | fn: $fn, otherfn: $otherfn. using '$fn -1'"
  wid=$(echo "$wids" | $fn -1)
  log "xsearch() | wid: $wid"

  if [[ -n $(xdotool getwindowpid "$wid") ]]; then
    log "xsearch() | good: wid ok, echoing: $wid"
    echo -n "$wid"
    return 0
  else
    log "xsearch() | fail: wid not ok. trying 2nd to last"
    wid=$(echo "$wids" | $fn -2 | $otherfn -1)
    log "xsearch() | wid: $wid"

    if [[ -n $(xdotool getwindowpid "$wid") ]]; then
      log "xsearch() | good: wid ok, echoing: $wid"
      echo -n "$wid"
      return 0
    else
      log "xsearch() | fail: wid not ok. nothing echoed"
      return 1
    fi
  fi
}
#########################
# ** ####### NEW ########
#########################
function toggle_always_on_top() {
  # Doesn't export. works on active window
  log.title "toggle_always_on_top(${*})"
  local wid
  local hexid
  wid=$(xdotool getactivewindow)
  log.debug "wid: $wid"
  local hexid
  if ! hexid="$("$WINMGMT"/gethexid.py "$wid" --no-print | tail -1)"; then
    log.fatal "failed gethexid \"$wid\""
    return 1
  fi
  log.debug "hexid: $hexid"
  if is_always_on_top "$wid"; then
    log.debug "$wid is always on top, toggling off"
    wmctrl -r :ACTIVE: -b 'remove,above'
    xprop -id "$hexid" -f _NET_WM_WINDOW_OPACITY 32c -set _NET_WM_WINDOW_OPACITY "$(printf 0x%x $((0xffffffff * 100 / 100)))"
  else
    log.debug "$wid is not always on top, toggling on"
    wmctrl -r :ACTIVE: -b 'add,above'
    xprop -id "$hexid" -f _NET_WM_WINDOW_OPACITY 32c -set _NET_WM_WINDOW_OPACITY "$(printf 0x%x $((0xffffffff * 85 / 100)))"
  fi
}
# # is_always_on_top STRING_OR_NUMBER
function is_always_on_top() {
  log.title "is_always_on_top(${*})"
  if [[ -z "$1" ]]; then
    log.fatal "expecting 1 arg"
    halp "$0"
    return 1
  fi
  if does_win_state_include "$1" "Above"; then
    log.debug "[is_always_on_top] returning 0"
    return 0
  else
    log.debug "[is_always_on_top] returning 1"
    return 1
  fi
}
# # does_win_state_include STRING_OR_NUMBER Maximized|Above|...
function does_win_state_include() {
  log.title "does_win_state_include(${*})"
  if [[ -z "$1" ]]; then
    log.fatal "expecting at least 1 arg"
    halp "$0"
    return 1
  fi
  local wid
  wid=$(python3.8 "$WINMGMT"/getwid.py "$1" --no-print | tail -1)
  #  wait $!
  log.debug "wid: $wid"
  if xwininfo -wm -id "$wid" | grep -Z "$2"; then
    log.debug "[does_win_state_include] returning 0"
    return 0
  else
    log.debug "[does_win_state_include] returning 1"
    return 1
  fi
}
# is_border_stuck NUMBER_OR_STRING
function is_border_stuck() {
  log.title "is_border_stuck(${*})"
  if [[ -z "$1" ]]; then
    log.fatal "expecting 1 arg"
    halp "$0"
    return 1
  fi
  if does_win_state_include "$1" "Maximized"; then
    # if "Maximized" is found, it means its stuck
    log.debug "[is_border_stuck] returning 0"
    return 0
  else
    log.debug "[is_border_stuck] returning 1"
    return 1
  fi

}
function unmaximize() {
  # Works on active window
  log.title "unmaximize($*)"
  local window
  if [[ -z "$1" ]]; then
    window=$(xdotool getactivewindow)
  else
    # log.fatal "[unmaximize($*)] NOT IMPLEMENTED accepting window arg"
    window=$(python3.8 "$WINMGMT"/getwid.py "$window" --no-print)
    # return 1
  fi
  log.debug "[unmaximize()] window: $window"
  if is_border_stuck "$window"; then
    # if wmctrl -v -r ":ACTIVE:" -b 'remove,maximized_horz,maximized_vert'; then
    if vex wmctrl -v -r "\"$window\"" -b "'remove,maximized_horz,maximized_vert'"; then
      log.debug "[unmaximize()] unmaximized successfully, returning 0"
      return 0
    else
      log.fatal "[unmaximize()] failed unmaximizing, returning 1"
      return 1
    fi
  else
    log.debug "[unmaximize()] window is not maximized in any way, not unstucking anything. returning 0"
    return 0
  fi
  #  i=$((0))
  #  while is_border_stuck "$window"; do
  #    log "[unmaximize()] active window is stuck (i=$i), toggling maximization by sending shift+ctrl+super+alt+Up"
  #    sleep 0.3
  #    xdotool key --window "$window" key --delay 150 ctrl+shift+super+alt+Up
  #    sleep 0.3
  #    i=$((i + 1))
  #    if [[ $i -eq 4 ]]; then
  #      elogzen "[unmaximize()] fail: tried unstucking window $i times. returning 1"
  #      return 1
  #    fi
  #  done
  #  return 0

}
# function move_and_resize() {
#   # Doesn't export. works on active window. args are [x, y, w, h] in percentage (including %)
#   log "\nmove_and_resize(x=$1, y=$2, w=$3, h=$4) | calling 'unmaximize'"
#   unmaximize
#   log "move_and_resize() | active window not stuck | calling 'xdt getactivewindow windowmove ... windowsize ...'"
#   xdotool getactivewindow windowmove "$1" "$2" windowsize "$3" "$4"
# }

# # move_and_resize ⟨POSITION⟩ [APP]
# `POSITION` has to be one of `lr` | `ur` | `ul` | `ll` | `c` | `l`.
# `APP` passed to `getwid.py`. Applies to active window if not specified.
function move_and_resize() {
  log.title "move_and_resize(${*})"
  # unmaximize
  if [[ ! "$2" ]]; then
    log.fatal "$0: not enough args (got ${#$})"
    halp "$0"
    return 1
  fi

  local to="$1"
  local app="$2"
  shift 2
  local x y w h
  local wid
  while [[ $# -gt 0 ]]; do
    case $to in
    lr)
      x="50%"
      y="50%"
      shift
      ;;
    ur)
      x="50%"
      y="0%"
      shift
      ;;
    ul)
      x="0%"
      y="0%"
      shift
      ;;
    ll)
      x="0%"
      y="50%"
      shift
      ;;
    c)
      x="25%"
      y="25%"
      shift
      ;;
    l)
      vex get_window_geo "$wid"
      x=$((X - 70))
      y=$((Y - 115))
      w=$((WIDTH + 125))
      h=$((HEIGHT + 60))
      log.debug "x: $x | y: $y | w: $w | h: $h | wid: $wid"
      if [[ -z "$wid" ]]; then
        wid=getactivewindow
      fi
      vex xdotool "$wid" windowmove "$x" "$y" windowsize "$w" "$h"
      return $?
      ;;

    *)
      if [[ -z "$app" ]]; then
        app="$1"
        log.debug "app: $app"
        wid="$(python3.8 "$WINMGMT/getwid.py" "$app" --no-print)"
        log.debug "wid: $wid"
        shift
      else
        source "$SCRIPTS/zenity.sh"
        z.fatal "fail: too many args: $1. aborting"
        return 1
      fi
      ;;
    esac
  done

  log.info "x: $x, y: $y, wid: $wid"
  if [[ -n "$wid" ]]; then
    vex xdotool windowsize "$wid" 50% 50% windowmove window="$wid" "$x" "$y"
  else
    vex xdotool getactivewindow windowsize 50% 50% windowmove "$x" "$y"
  fi
  return $?
}
# # get_window_geo [APP]
# Uses `xdotool` to export `WINDOW`, `X`, `Y`, `WIDTH`, `HEIGHT`, `SCREEN`.
# `APP` is passed to getwid.py if specified.
function get_window_geo() {
  log.title "get_window_geo(${*})"
  local wid
  if [[ -z "$1" ]]; then
    log.debug "[get_window_geo()] no arg. calling 'xdt getactivewindow getwindowgeometry --shell'"
    eval "$(xdotool getactivewindow getwindowgeometry --shell)"
  else
    log.debug "[get_window_geo()] calling 'getwid $1'"
    wid=$(python3.8 "$WINMGMT/getwid.py" "$1" --no-print | tail -1)
    eval "$(xdotool getwindowgeometry --shell "$wid")"
  fi
  # shellcheck disable=SC2153
  log.debug "[get_window_geo()] WINDOW: $WINDOW, X: $X, Y: $Y, WIDTH: $WIDTH, HEIGHT: $HEIGHT, SCREEN: $SCREEN"

}
function chromeactivate() {
  python3 -c "
import subprocess as sp
p = sp.Popen('xdotool search --onlyvisible --classname chrome'.split(), stdout=sp.PIPE)
for pid in reversed(p.stdout.readlines()):
    name = sp.check_output((b'xdotool getwindowname '+pid).split(), stderr=sp.STDOUT)
    if b'hidden tab' in name:
        print('skipping (hidden tab): ',name, pid)
        continue
    if sp.check_output((b'xdotool windowactivate '+pid).split(), stderr=sp.STDOUT):
        print('failed xdt windowactivate, pid: ',pid)
    else:
        print('success xdt windowactivate, pid: ',pid)
        break
else:
    # no chrome at all; launch chrome
    if sp.check_output((b'/opt/google/chrome/chrome').split(), stderr=sp.STDOUT):
        print('failed \'/opt/google/chrome/chrome\'')
"
}
function pycharmactivate() {
  python3 -c "
import subprocess as sp
p = sp.Popen('xdotool search --onlyvisible --classname pycharm'.split(), stdout=sp.PIPE)
for pid in reversed(p.stdout.readlines()):
  name = sp.check_output((b'xdotool getwindowname '+pid).split(), stderr=sp.STDOUT)
  if name.startswith(b'Run ') or name.startswith(b'Debug ') or name.startswith(b'Content '):
    print('bad (name): ',name, pid)
    continue
  out = sp.check_output((b'xdotool windowactivate '+pid).split(), stderr=sp.STDOUT)
  if out.startswith(b'X Error of failed request'):
    print('bad (failed windowactivate): ',name, pid)
    pass
  else:
    print('good (successful windowactivate): ',name, pid)
    break
"
}
function vlcactivate() {
  python3 -c "
import subprocess as sp
p = sp.Popen('xdotool search --onlyvisible --classname vlc'.split(), stdout=sp.PIPE)
for pid in reversed(p.stdout.readlines()):
  name = sp.check_output((b'xdotool getwindowname '+pid).split(), stderr=sp.STDOUT)
  if not b'' in name:
    # print('bad: ',name, pid)
    continue
  if sp.check_output((b'xdotool windowactivate '+pid).split(), stderr=sp.STDOUT):
    # print('bad pid: ',pid)
    pass
  else:
    # print('good pid: ',pid)
    break
"
}
# function foo() {
#   local only_one_dim
#   [[ -n $1 && "$1" == 'x' || "$1" == 'y' ]]  only_one_dim=true || only_one_dim=false
#   echo "$only_one_dim"
# }
