# minecraft-extractor

A simple script for downloading the Minecraft client and its assets, as well as
running data generation.

## Getting started

This project is split into two parts: client and assets download and actual
data generation.

You'll need stable Python version installed to run the project. Start with
executing `download.py`, which will download client JAR, its libraries and
assets.

Then, you can run `minecraft.py` which will build the classpath and execute the
selected action against the client JAR through installed Java. You can run
`python minecraft.py --help` for more information.

## Third-Party Rights

**THIS IS NOT AN OFFICIAL MINECRAFT PRODUCT. IT IS NOT APPROVED BY, ENDORSED
BY, ASSOCIATED WITH, OR SUPPORTED BY MOJANG OR MICROSOFT.**

Minecraft, Mojang, Microsoft, and all associated names, trademarks, software,
game files, libraries, assets, textures, sounds, and other materials are the
property of their respective owners.

Any files downloaded, generated, accessed, or processed by this project that
originate from, reproduce, contain, or are derived from Minecraft, Mojang, or
Microsoft materials remain subject to the applicable Minecraft End User Licence
Agreement, Minecraft Usage Guidelines, Microsoft Services Agreement, and any
other applicable third-party terms.

This project claims no ownership of and grants no licence to any Mojang,
Microsoft, or other third-party materials. Users are solely responsible for
obtaining those materials from authorised sources and for ensuring that their
use complies with all applicable terms and laws.
