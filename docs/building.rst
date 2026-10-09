===================================
Building the Overviewer from Source
===================================

These instructions are for building the C extension for Overviewer. Once you
have finished with these instructions, head to :doc:`running`.

.. note::

    Pre-built Windows and Debian executables are available on the
    :doc:`installing` page.  These kits already contain the compiled code and
    require no further setup, so you can skip to the next section of the docs:
    :doc:`running`.

Get The Source
==============

First step: download the platform-independent source! Either clone with Git
(recommended if you know Git) or download the most recent snapshot:

* Git URL to clone: ``git://github.com/GregoryAM-SP/The-Minecraft-Overviewer.git``
* `Download most recent tar archive <https://github.com/GregoryAM-SP/tarball/master>`_

* `Download most recent zip archive <https://github.com/GregoryAM-SP/The-Minecraft-Overviewer/releases>`_

Once you have the source, see below for instructions on building for your
system.

Build Instructions For Various Operating Systems
================================================

.. contents::
    :local:

Linux
-----

You will need Python 3.10 or newer, the gcc compiler, and a working build
environment. On Ubuntu and Debian, this can be done by installing the
``build-essential`` package. The supported Ubuntu baselines are 22.04, 24.04,
and 26.04, using their default Python 3 versions.

On Debian-derived distributions (e.g. Ubuntu), install only Python, virtualenv,
pip, Python headers, compiler tooling, and git from the package manager::

    sudo apt-get update
    sudo apt-get install python3 python3-dev python3-venv python3-pip build-essential git

On Linux, create and activate a project virtual environment in Bash, then
install Overviewer's Python dependencies from ``requirements.txt``::

    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt

Overviewer requires Pillow's source headers to build its C extension. Download
or clone the Pillow source release that exactly matches the version of Pillow
installed in the virtual environment, and point ``PIL_INCLUDE_DIR`` at its
``src/libImaging`` directory. A version mismatch between the installed Pillow
library and the headers can lead to compile failures or segfaults while running
Overviewer due to an ABI mismatch::

    PILLOW_VERSION=$(python -c "import PIL; print(PIL.__version__)")
    git clone --branch="$PILLOW_VERSION" --depth=1 https://github.com/python-pillow/Pillow.git /tmp/pillow
    export PIL_INCLUDE_DIR=/tmp/pillow/src/libImaging

Then build::

    python setup.py build

At this point, you can run ``overviewer.py`` from the current directory while
the virtual environment is activated::

    python overviewer.py --config=/path/to/your/config


macOS
-----

Install the Xcode Command Line Tools with ``xcode-select --install`` and
Python 3.10 or newer from `python.org <https://www.python.org/downloads/macos/>`_
if needed. From the Overviewer source directory, create a virtual environment
and install its dependencies::

    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt

Download the `Pillow sources <https://github.com/python-pillow/Pillow>`_ matching
the installed Pillow version, point ``PIL_INCLUDE_DIR`` at their ``src/libImaging``
directory, and build::

    PILLOW_VERSION=$(python -c "import PIL; print(PIL.__version__)")
    git clone --branch="$PILLOW_VERSION" --depth=1 https://github.com/python-pillow/Pillow.git /tmp/pillow
    export PIL_INCLUDE_DIR=/tmp/pillow/src/libImaging
    python setup.py build

Run Overviewer using the activated environment's ``python``.


Windows Build Instructions
--------------------------

First, you'll need a compiler.  You can either use Visual Studio, or
cygwin/mingw. The free `Visual Studio Community
<https://www.visualstudio.com/vs/community/>`_ is okay. You will need to select the "Desktop Development with C++" WORKLOAD. Microsoft has been changing up the names on this with the "Community" edition of Visual Studio. If nothing else works, just install every Individual Visual C++ component you can find :)


Prerequisites
~~~~~~~~~~~~~

You will need the following:

- `Python 3.10 or newer <https://www.python.org/downloads/windows/>`_
- `Pillow sources <https://github.com/python-pillow/Pillow>`_ matching the
  installed Pillow version exactly.
- The Pillow Extension for Python.
- The Numpy Extension for Python.

On Windows, create and activate a project virtual environment in PowerShell,
then install the dependencies::

    py -3.10 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt

The Windows examples use Python 3.10, matching the Ubuntu 22.04 baseline.
Do not overwrite an existing environment containing work you need to keep.


Building with Visual Studio
~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Get the latest Overviewer source code as per above.
2. Install Visual Studio's **Desktop development with C++** workload.
3. In PowerShell, change to the folder containing the Overviewer source code.
4. With the virtual environment above activated, download the headers for the
   installed Pillow version and build::

    $pillowVersion = python -c "import PIL; print(PIL.__version__)"
    python -m pip download --no-deps --no-binary=:all: --dest tmp "pillow==$pillowVersion"
    python -m tarfile -e ".\tmp\pillow-$pillowVersion.tar.gz" .\tmp
    $env:PIL_INCLUDE_DIR = (Resolve-Path ".\tmp\pillow-$pillowVersion\src\libImaging").Path
    python setup.py build

   Setuptools normally discovers Visual Studio automatically. If discovery
   fails, run from its x64 Native Tools command prompt, or call ``vcvars64.bat``
   and the build command in the same ``cmd.exe`` process. Do not use headers
   from a different Pillow checkout: an ABI mismatch can crash the renderer.

If you encounter the following errors::

    error: Unable to find vcvarsall.bat

then open a Visual Studio x64 Native Tools command prompt (``cmd.exe``, not
PowerShell), change to the source directory, and try::

    set DISTUTILS_USE_SDK=1
    set MSSdk=1
    set PIL_INCLUDE_DIR=C:\path\to\matching\Pillow\src\libImaging
    .venv\Scripts\python.exe setup.py build

If the build was successful, there will be a ``c_overviewer*.pyd`` file in
``overviewer_core``. Run Overviewer with the same venv's Python executable.

Building with mingw-w64 and msys2
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is the recommended way to build on Windows without MSVC.

1. Install msys2 by following **all** the instructions on
   `the msys2 installation page <https://msys2.github.io/>`_.

2. Install the dependencies::

    pacman -S git mingw-w64-x86_64-python3-numpy mingw-w64-x86_64-python3-Pillow mingw-w64-x86_64-python3 mingw-w64-x86_64-toolchain

3. Clone the Minecraft-Overviewer git repository::

    git clone https://github.com/overviewer/Minecraft-Overviewer.git

   The source code will be downloaded to your msys2 home directory, e.g.
   ``C:\msys2\home\Potato\Minecraft-Overviewer``

4. Close the msys2 shell. Instead, open the MinGW64 shell.

5. Build the Overviewer by changing your current working directory to the source
   directory and executing the build script::

    cd Minecraft-Overviewer
    python3 setup.py build

After it finishes, you should now be able to execute ``overviewer.py`` from the MINGW64
shell.

Building with mingw
~~~~~~~~~~~~~~~~~~~

1. Open a MinGW shell.
2. cd to the Overviewer directory.
3. Download or clone the Pillow source release that exactly matches the Pillow package installed in your Python environment.
4. Point ``PIL_INCLUDE_DIR`` at that Pillow source tree's ``src/libImaging`` directory.
5. Build::

    export PIL_INCLUDE_DIR=/path/to/Pillow/src/libImaging
    python3 setup.py build --compiler=mingw32

If the build fails with complaints about ``-mno-cygwin``, open the file ``Lib/distutils/cygwincompiler.py``
in an editor of your choice, and remove all mentions of ``-mno-cygwin``. This is a bug in distutils,
filed as `Issue 12641 <http://bugs.python.org/issue12641>`_.