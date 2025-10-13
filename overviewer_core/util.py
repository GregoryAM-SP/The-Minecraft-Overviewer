#    This file is part of the Minecraft Overviewer.
#
#    Minecraft Overviewer is free software: you can redistribute it and/or
#    modify it under the terms of the GNU General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or (at
#    your option) any later version.
#
#    Minecraft Overviewer is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
#    Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with the Overviewer.  If not, see <http://www.gnu.org/licenses/>.

"""
Misc utility routines used by multiple files that don't belong anywhere else
"""

import errno
import os.path
import platform
import sys
from itertools import cycle, islice, product
from string import hexdigits
from subprocess import PIPE, Popen

DIMENSION_INFO = {
    "minecraft:overworld": ("DIM0", 0, "minecraft:overworld"),
    "minecraft:the_end": ("DIM1", 1, "minecraft:the_end"),
    "minecraft:the_nether": ("DIM-1", -1, "minecraft:the_nether"),
}


def get_dimension_data(dimension):
    if isinstance(dimension, int):
        for dim_name, (folder, dim_id, _) in DIMENSION_INFO.items():
            if dim_id == dimension:
                return DIMENSION_INFO[dim_name]
    elif isinstance(dimension, str):
        if dimension in DIMENSION_INFO:
            return DIMENSION_INFO[dimension]
        elif dimension in ("overworld"):
            return DIMENSION_INFO["minecraft:overworld"]
        elif dimension in ("the_end", "end"):
            return DIMENSION_INFO["minecraft:the_end"]
        elif dimension in ("the_nether", "nether"):
            return DIMENSION_INFO["minecraft:the_nether"]

    return None


def get_program_path():
    # Check if running as a frozen executable (e.g., created with PyInstaller)
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    
    # If not frozen, attempt to use __file__ or sys.argv[0] to determine the script path
    try:
        return os.path.dirname(os.path.dirname(__file__))  # For normal script run
    except NameError:
        # Fall back to sys.argv[0] if __file__ is not available (e.g., when running interactively)
        return os.path.dirname(sys.argv[0])


def findGitHash():
    try:
        p = Popen('git rev-parse HEAD', stdout=PIPE, stderr=PIPE, shell=True)
        p.stderr.close()
        line = p.stdout.readlines()[0].decode('utf-8').strip()
        if line and len(line) == 40 and all(c in hexdigits for c in line):
            return line
    except Exception:
        try:
            from . import overviewer_version
            return overviewer_version.HASH
        except Exception:
            pass
    return "unknown"


def findGitTag():
    try:
        p = Popen('git describe --tags --abbrev=0', stdout=PIPE, stderr=PIPE, shell=True)
        p.stderr.close()
        line = p.stdout.readlines()[0].decode('utf-8').strip()
        return line
    except Exception:
        try:
            from . import overviewer_version
            return overviewer_version.VERSION
        except Exception:
            pass
    return "unknown"


def is_bare_console():
    """Returns true if Overviewer is running in a bare console in
    Windows, that is, if overviewer wasn't started in a cmd.exe
    session.
    """
    if platform.system() == 'Windows':
        try:
            import ctypes
            GetConsoleProcessList = ctypes.windll.kernel32.GetConsoleProcessList
            num = GetConsoleProcessList(ctypes.byref(ctypes.c_int(0)), ctypes.c_int(1))
            if (num == 1):
                return True

        except Exception:
            pass
    return False


def nice_exit(ret=0):
    """Drop-in replacement for sys.exit that will automatically detect
    bare consoles and wait for user input before closing.
    """
    if ret and is_bare_console():
        print("")
        print("Press [Enter] to close this window.")
        input()
    sys.exit(ret)


# http://docs.python.org/library/itertools.html
def roundrobin(iterables):
    "roundrobin('ABC', 'D', 'EF') --> A D E B F C"
    # Recipe credited to George Sakkis
    pending = len(iterables)
    nexts = cycle(iter(it).__next__ for it in iterables)
    while pending:
        try:
            for next in nexts:
                yield next()
        except StopIteration:
            pending -= 1
            nexts = cycle(islice(nexts, pending))


def dict_subset(d, keys):
    "Return a new dictionary that is built from copying select keys from d"
    n = dict()
    for key in keys:
        if key in d:
            n[key] = d[key]
    return n


def pid_exists(pid):    # http://stackoverflow.com/a/6940314/1318435
    """Check whether pid exists in the current process table."""
    if pid < 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError as e:
        return e.errno != errno.ESRCH
    else:
        return True
