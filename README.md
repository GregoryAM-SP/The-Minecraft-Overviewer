# The Minecraft Overviewer

### What is The Minecraft Overviewer?
The Minecraft Overviewer is a command-line tool for rendering high-resolution maps of Minecraft Worlds.\
It generates a set of static HTML Image files and uses LeafletJS to display an interactive map.

While The Minecraft Overviewer was in active development for several years by the original developers, they have stopped development; leading to the community to take over the project and work to continue development.

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
For large maps, there is a lot of data to parse through the process. If your world is very large, expect the initial render to take at least an hour to render, or possibly longer.

Since Minecraft Maps can be infinite, the maximum time this could take is also infinite.\
**Keep this in mind for large worlds.**

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
