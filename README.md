![Overviewer](https://gregoryam.com/assets/img/github/overviewer-img.webp?h=0347c3bd38ae284637ade776034fd281)
[![Unit tests](https://github.com/GregoryAM-SP/The-Minecraft-Overviewer/actions/workflows/ci.yml/badge.svg)](https://github.com/GregoryAM-SP/The-Minecraft-Overviewer/actions/workflows/ci.yml)
<br><strong>Works with Minecraft Java Edition v1.2.1 - v1.20.x</strong>
<hr>

### [Python 3.8.10](https://www.python.org/downloads/release/python-3810/) Required

<hr>

### (Example Map)<br> [Overviewer Debug World Render](https://overviewer.gregoryam.com/ov_render/)

<hr>

### What is The Minecraft Overviewer?
The Minecraft Overviewer is a command-line tool for rendering high-resolution maps of Minecraft Worlds.\
It generates a set of static HTML Image files and uses LeafletJS to display an interactive map.

While The Minecraft Overviewer was in active development for nearly a decade by the original developers, they have stopped development; leading to the community to take over the project and work to continue development.

## The Minecraft Overviewer includes:
- Day / Night Lighting
- Cave Rendering
- Mineral Overlays
- Many Plugins for more features!

## The Minecraft Overviewer Codebase:
Mostly written in Python with critial sections written in C as an extension module.

## Documentation
You can visit [docs.overviewer.org](https://docs.overviewer.org) to view the entire documentation of The Minecraft Overviewer.

This Repo will soon have a Wiki that will better reflect the documentation.

## Disclaimer!
For large maps, there is a lot of data to parse through the process. If your world is very large, expect the initial render to take at least an hour to render, or possibly even days.

Since Minecraft Maps can be infinite, the maximum time this could take is also infinite.\
**Keep this in mind for large worlds.**

## Running Overviewer

While Overviewer can be run directly from the command line, it's generally easiest to set up a configuration file and running script once that you can then use whenever you want to update your map, so that's what we'll go over here. It's worth noting that this guide is designed for use on Windows computers.

**Step 1:** Download the latest zipped release from [Github](https://github.com/GregoryAM-SP/The-Minecraft-Overviewer/releases).

**Step 2:** Download the sample [configuration and batch files](https://josh47.com/i/SampleOverviewerFiles.zip).

**Step 3:** Unzip the downloaded files. You can put them wherever you like on your system.

**Step 4:** Edit *RunOverviewer.bat* using your favorite text editor (Notepad works great). 

 - Change D:\Path\To\overviewer-version to the path where you extracted the release zip.
 - Change D:\Path\To\Config\ConfigOverviewer.txt to the path where you put the configuration file, and change the name if necessary.
 - Change D:\Path\To\OutputLog\log.txt to wherever you'd like the log file to be saved. You can rename log.txt to something else if you'd like, or remove the path and the ">>" entirely if you prefer the output to go to your terminal instead.
 - Save the file.

**Step 5:** Edit *ConfigOverviewer.txt*

 - Replace C:/Users/YourPathHere with the path to your world file.
 - Replace D:/YourPathHere with the path to where you want the map's files to be.
 - Add, remove, or edit any renders you'd like to change. The sample comes with four smooth-lighting renders from the overworld, one for each isometric perspective. For more info on the config file, visit [the docs](http://docs.overviewer.org/en/latest/config/). Overviewer supports the Nether, the End, and a cave view, though these are not included in the sample config.
 - Save the file.

**Step 6:** You're ready to run! Double-click the RunOverviewer.bat file to begin. It will open a terminal window, and then you can press the key directed to continue and start the render. As mentioned above, if this is the first time you're running the render, it could take hours or possibly even days. Don't worry, updating the map after the initial run is much faster.

**Step 7:** Once it completes, you can go to the folder you instructed it to place the output in and open "Index.html" to view the map. To share with others, you can give them the whole folder, or host it online!

**In the future:** To update your map, just double-click the RunOverviewer.bat file again. Overviewer will automatically check your world to find out where things have changed, and only update those parts of the map.

## Getting Help
A great place to start is the old [docs](http://docs.overviewer.org/en/latest/). They aren't being updated anymore, but since this repo's Wiki is still a work in progress, they're a great tool and nearly all the information in them is still accurate.

Another option is to reach out on the [Overviewer Discord](https://discord.gg/32Bz2yW)! There you can find a friendly, helpful community. Please read the rules in the \#Rules channel before messaging.

## Viewing the results
Within the output directory you've specified, you will find:
- Index.html (The render of your world)
- JavaScript (JS), Cascading Style Sheets (CSS) and PNG files.
- Directory: world-lighting (containing the generated chunk images)
- Directory: markers ( These markers can be used with GenPOI )

You can upload these files on a web server and let others view your map.

## Bedrock and other formats
The Minecraft Overviewer **only** supports the world format from the Java Edition of Minecraft.\
Minecraft Bedrock worlds are not supported.

Using a tool such as [Amulet](https://www.amuletmc.com/) to convert your Bedrock Worlds into Java Edition Worlds has been reported to work.\
But, the results may vary.
