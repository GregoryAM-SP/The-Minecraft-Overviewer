=====================
Minecraft Overviewer
=====================

The Minecraft Overviewer is a command-line tool for rendering high-resolution
maps of Minecraft worlds. It generates a set of static html and image files and
uses Leaflet to display a nice interactive map.

The Overviewer was in active development for nearly a decade before being
abandoned by its original developers. The community has since taken over development.

It has many features, including day and night lighting, cave rendering, mineral overlays,
and many plugins for even more features! It is written mostly in Python with
critical sections in C as an extension module.

Documentation
---------------
For information on downloading, compiling, installing, and running The Overviewer,
visit the docs site. This repo has a wiki in development, but for now, the docs
are the most complete option.

http://docs.overviewer.org

Disclaimers
-----------
Before you dive into using this, just be aware that, for large maps, there is a
*lot* of data to parse through and process. If your world is very large, expect
the initial render to take at least an hour, possibly even days. (Since Minecraft
maps are practically infinite, the maximum time this could take is also
infinite!)

Running Overviewer
------------------
While Overviewer can be run directly from the command line, it's generally easiest to set up a configuration file and running script once that you can then use whenever you want to update your map, so that's what we'll go over here. It's worth noting that this guide is designed for use on Windows computers.

**Step 1:** Download the latest zipped release from `Github <https://github.com/GregoryAM-SP/The-Minecraft-Overviewer/releases/>`__.

**Step 2:** Download the sample `configuration and batch files <https://josh47.com/i/SampleOverviewerFiles.zip>`__.

**Step 3:** Unzip the downloaded files. You can put them wherever you like on your system.

**Step 4:** Edit *RunOverviewer.bat* using your favorite text editor (Notepad works great). 

 - Change D:\\Path\\To\\overviewer-version to the path where you extracted the release zip.
 - Change D:\\Path\\To\\Config\\ConfigOverviewer.txt to the path where you put the configuration file, and change the name if necessary.
 - Change D:\\Path\\To\\OutputLog\\log.txt to wherever you'd like the log file to be saved. You can rename log.txt to something else if you'd like, or remove the path and the ">>" entirely if you prefer the output to go to your terminal instead.
 - Save the file.

**Step 5:** Edit *ConfigOverviewer.txt*

 - Replace C:/Users/YourPathHere with the path to your world file.
 - Replace D:/YourPathHere with the path to where you want the map's files to be.
 - Add, remove, or edit any renders you'd like to change. The sample comes with four smooth-lighting renders from the overworld, one for each isometric perspective. For more info on the config file, visit http://docs.overviewer.org/en/latest/config/. Overviewer supports the Nether, the End, and a cave view, though these are not included in the sample config.
 - Save the file.

**Step 6:** You're ready to run! Double-click the RunOverviewer.bat file to begin. It will open a terminal window, and then you can press the key directed to continue and start the render. As mentioned above, if this is the first time you're running the render, it could take hours or possibly even days. Don't worry, updating the map after the initial run is much faster.

**Step 7:** Once it completes, you can go to the folder you instructed it to place the output in and open "Index.html" to view the map. To share with others, you can give them the whole folder, or host it online!

**In the future:** To update your map, just double-click the RunOverviewer.bat file again. Overviewer will automatically check your world to find out where things have changed, and only update those parts of the map.

Getting Help
---------------
Aside from the old docs, another option is to reach out on the `Overviewer Discord <https://discord.gg/32Bz2yW>`__! There you can find a friendly, helpful community. Please read the rules in the \#Rules channel before messaging.

Viewing the Results
-------------------
Within the output directory you will find two things: an index.html file, and a
directory hierarchy full of images. To view your world, simply open index.html
in a web browser.

You can throw these files up to a web server to let others view your map.

Bedrock and other formats
=========================

Minecraft Overviewer only supports the world format from the Java edition of Minecraft.
Minecraft Bedrock (the Windows 10 version) is not supported by Overviewer, but users
have reported success using `Amulet <https://www.amuletmc.com/>`__ to convert
Bedrock worlds to the Java format, and then used Overviewer to render the converted
worlds.
