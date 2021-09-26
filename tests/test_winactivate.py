from subprocess import Popen, PIPE
import shlex
import logging
from rich.logging import RichHandler
# from rich import inspect, print
from rich.console import Console
from pytest import mark
import sys

rhandler = RichHandler(rich_tracebacks=True, tracebacks_extra_lines=10, tracebacks_show_locals=True)
logger = logging.getLogger()
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s %(name) %(levelname) %(message)s'))
logger.addHandler(handler)
logger.addHandler(rhandler)
logger.setLevel(logging.DEBUG)
console = Console()


def test__kwargs__alt__terminator__ipython():
    """Run from PyCharm, with IPython in terminator"""
    sys.argv.append('--no-print')  # hack
    from winactivate import main as winactivate_main
    rv = winactivate_main("vagrant@sm-env")
    assert not rv
    rv = winactivate_main("vagrant@sm-env", alt=['IPython: '])
    assert rv


def test__kwargs__alt__terminator__docker_attach():
    """Run from PyCharm, with docker attached in terminator"""
    sys.argv.append('--no-print')  # hack
    from winactivate import main as winactivate_main
    rv = winactivate_main("vagrant@sm-env")
    assert not rv
    rv = winactivate_main("vagrant@sm-env", alt=['docker attach ', 'IPython: '])
    assert rv


@mark.skip()
def test__terminator__xfce4__shell():
    cmd = '/home/vagrant/dev/bashscripts/winactivate.py "vagrant@sm-env"'
    process = Popen(shlex.split(cmd), executable='python3.8', stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    # inspect(stdout)
    console.log('stdout:', stdout)
    console.log('stderr:', stderr)
