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

Windows Build Instructions
--------------------------

First, you'll need a compiler.  You can either use Visual Studio, or
cygwin/mingw. The free `Visual Studio Community
<https://www.visualstudio.com/vs/community/>`_ is okay. You will need to select the "Desktop Development with C++" WORKLOAD. Microsoft has been changing up the names on this with the "Community" edition of Visual Studio. If nothing else works, just install every Individual Visual C++ component you can find :)


Prerequisites
~~~~~~~~~~~~~

You will need the following:

- `Python 3.10 or newer <https://www.python.org/downloads/windows/>`_
- A copy of the `Pillow sources <https://github.com/python-pillow/Pillow>`_.
- The Pillow Extension for Python.
- The Numpy Extension for Python.
- The extensions can be installed via::

    py -3.10 -m pip -U numpy pillow


Building with Visual Studio
~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Get the latest Overviewer source code as per above.
2. From the Start menu, navigate to 'Visual Studio 2017' and open the **'Developer Command Prompt for VS 2017'** (*or whatever year*) shortcut. A regular command or powershell prompt will *NOT* work for this.
3. cd to the folder containing the Overviewer source code.
4. Download or clone the Pillow source release that exactly matches the Pillow package installed in your Python environment.
5. Point ``PIL_INCLUDE_DIR`` at that Pillow source tree's ``src/libImaging`` directory.
6. First try a build::

    set PIL_INCLUDE_DIR=C:\path\to\Pillow\src\libImaging
    py -3.10 setup.py build

If you encounter the following errors::

    error: Unable to find vcvarsall.bat

then try the following::

    set DISTUTILS_USE_SDK=1
    set MSSdk=1
    py -3.10 setup.py build

If the build was successful, there should be a c_overviewer.pyd file in your current working directory.

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

5. Build the Overviewer by changing your current working directory into the source
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

Then create a virtual environment and install Overviewer's Python dependencies
from ``requirements.txt``::

    python3 -m venv .venv
    .venv/bin/python -m pip install --upgrade pip
    .venv/bin/python -m pip install -r requirements.txt

Overviewer requires Pillow's source headers to build its C extension. Download
or clone the Pillow source release that exactly matches the version of Pillow
installed in the virtual environment, and point ``PIL_INCLUDE_DIR`` at its
``src/libImaging`` directory. A version mismatch between the installed Pillow
library and the headers can lead to compile failures or segfaults while running
Overviewer due to an ABI mismatch::

    PILLOW_VERSION=$(.venv/bin/python -c "import PIL; print(PIL.__version__)")
    git clone --branch="$PILLOW_VERSION" --depth=1 https://github.com/python-pillow/Pillow.git /tmp/pillow
    export PIL_INCLUDE_DIR=/tmp/pillow/src/libImaging

Then build::

    .venv/bin/python setup.py build

At this point, you can run ``overviewer.py`` from the current directory with the
virtual environment's Python::

    .venv/bin/python overviewer.py --config=/path/to/your/config


macOS
-----

#. Install the Xcode Command Line Tools by running the following command in a terminal (located in your /Applications/Utilities folder)::

    xcode-select --install

#. Install Python 3.10 or newer if you don't already have it, for example from `the official Python website <https://www.python.org/downloads/mac-osx/>`_.
#. Install PIP, e.g. with::

    sudo easy_install pip

#. Install Pillow (overviewer needs PIL, Pillow is a fork of PIL that provides the same functionality)::

    pip install Pillow

#. Install numpy::

    pip install numpy

#. Download the Pillow source files for the same Pillow version installed in your Python environment and unpack the tar.gz file to a directory you can remember
#. Download the Minecraft Overviewer source-code from https://overviewer.org/builds/overviewer-latest.tar.gz
#. Extract overviewer-[Version].tar.gz and move it to a directory you can remember
#. Point ``PIL_INCLUDE_DIR`` at the Pillow-[Version]/src/libImaging directory
#. Make sure your installation of Python 3 is in ``$PATH``
#. In a terminal, change your current working directory to your overviewer-[Version] folder (e.g. by using ``cd Desktop/overviewer-[Version]``)
#. Build::

    export PIL_INCLUDE_DIR=/path/to/Pillow-[Version]/src/libImaging
    python3 setup.py build

You should now be able to run Overviewer with ``./overviewer.py`` inside of the
Overviewer directory.