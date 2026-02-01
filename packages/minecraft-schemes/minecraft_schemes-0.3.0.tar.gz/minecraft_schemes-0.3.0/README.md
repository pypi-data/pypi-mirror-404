# minecraft-schemes

A Python library for help you to parse Minecraft-relative JSON to structured objects.

**Disclaimer:** Although the project name contains "minecraft", this project is not supported by Mojang Studios or Microsoft.

## Features

### Already implemented

- Easy installing
- Open source
- All public APIs are static typed
- Supports parsing various file structures used by Mojang and Minecraft ([see below](#supported-file-structures))
- Easy-to-use file structure definitions, powered by [`attrs`](https://www.attrs.org)
- Rapidly file parsing, powered by [`cattrs`](https://catt.rs)
- Conditional testing for game/command line options and dependency libraries (in `client.json`)

### Not implemented yet (not a complete list)

- [ ] Export the data structures to the file
- [ ] Parse/build supports for `launcher_profiles.json` (used by official Minecraft Launcher)
- [ ] Search/exactly find a specified version in `version_manifest.json`
- [ ] Game/JVM command line options concatenating and completing

## Supported file structures

Click link to see the corresponding documentations.

- `version_manifest.json` and `version_manifest_v2.json` [[Minecraft Wiki](https://minecraft.wiki/w/Version_manifest.json)]
    - A JSON file that list Minecraft versions available in the official launcher.
- `client.json` [[Minecraft Wiki](https://minecraft.wiki/w/Client.json)]
    - A JSON file that accompanies client.jar in `.minecraft/versions/<version>` and lists the version's attributes.
    - Usually named `<game version>.json`.
    - Don't confuse this file with `version.json`; they are fundamentally different.
- Asset index
  file [[Minecraft Wiki (only Chinese version)](https://zh.minecraft.wiki/w/%E6%95%A3%E5%88%97%E8%B5%84%E6%BA%90%E6%96%87%E4%BB%B6#%E8%B5%84%E6%BA%90%E7%B4%A2%E5%BC%95)]
    - A series of JSON files used to query the hash value of the corresponding hashed resource file based on the resource path, in order to invoke
      the file.
    - Can be downloaded from the URL pointed in the `client.json`: `[Root Tag] > "assetIndex" > "url"`
- `version.json` [[Minecraft Wiki](https://minecraft.wiki/w/Version.json)]
    - A JSON file that offers some basic information about the version's attributes.
    - Embedded within client.jar in `.minecraft/versions/<version>` and `server.jar`.
    - Don't confuse this file with `client.json`; they are fundamentally different.
- Mojang Java Runtime index file and manifest files
    - A JSON file that list manifest files of Java Runtime provided by Mojang via their "codename".
    - Not documented by Minecraft Wiki or Mojang, but it is believed to be for the purposes described above.

## Install

Install `minecraft-schemes` using pip:

```commandline
pip install minecraft-schemes
```

The release page also provides various versions of wheel files for manual download and installation.

## Usage Example

#### Parse `version_manifest.json` ([download at here](https://piston-meta.mojang.com/mc/game/version_manifest_v2.json))

```python
import mcschemes

with open('version_manifest.json', mode='r') as f:
    version_manifest = mcschemes.load(f, mcschemes.Scheme.VERSION_MANIFEST)

print('Latest release:', version_manifest.latest.release)
print('Latest snapshot:', version_manifest.latest.snapshot)
print('Number of available versions:', len(version_manifest.versions))
for entity in version_manifest.versions:
    if entity.type == 'release':
        print('The ID of the first release version found:', entity.id)
        print('The release time of the first release version found:', entity.releaseTime)
        print('The last update time of the first release version found:', entity.time)
        break
```

### Parse `client.json`

This example code uses `client.json` from Minecraft Java Edition
1.21.11, [download at here](https://piston-meta.mojang.com/v1/packages/3f42d3ea921915b36c581a435ed03683a7023fb1/1.21.11.json).

```python
import mcschemes

with open('1.21.11.json', mode='r') as f:
    client_manifest_1_21_11 = mcschemes.load(f, mcschemes.Scheme.CLIENT_MANIFEST)

print('Version ID:', client_manifest_1_21_11.id)
# The following field is structured as a member of enum mcschemes.enums.VersionType
print('Version Type:', str(client_manifest_1_21_11.type))
print('Asset version ID:', client_manifest_1_21_11.assetIndex.id)
print('Main class:', client_manifest_1_21_11.mainClass)
print('Release time:', client_manifest_1_21_11.releaseTime)
print('Last update time:', client_manifest_1_21_11.time)
print('Number of dependency libraries:', len(client_manifest_1_21_11.libraries))
client_jar_file_info = client_manifest_1_21_11.downloads.get('client')
if client_jar_file_info:
    print('URL to download the client JAR file:', client_jar_file_info.url)
```

### Parse asset index file

This example code uses the asset index file version 29. You can download
it [at here](https://piston-meta.mojang.com/v1/packages/aaf4be9d6e197c384a09b1d9c631c6900d1f077c/29.json).

```python
from pathlib import Path

import mcschemes

with open('29.json', mode='r') as f:
    asset_index = mcschemes.load(f, mcschemes.Scheme.ASSET_INDEX)

print('Number of asset files:', len(asset_index.objects))
asset_file_relative_path = Path('icons/icon_256x256.png')
if asset_file_relative_path in asset_index.objects:
    target_asset_file_info = asset_index.objects[asset_file_relative_path]
    print('Information about asset file {0}: hash={1.hash}, size={1.size}'.format(asset_file_relative_path, target_asset_file_info))
```

### Parse `version.json` from a client JAR file

This example code uses the client JAR file from Minecraft Java Edition 1.21.11. You can download it in official Minecraft Launcher
or [at here](https://piston-data.mojang.com/v1/objects/ba2df812c2d12e0219c489c4cd9a5e1f0760f5bd/client.jar).

```python
from pathlib import Path

import mcschemes

version_attrs = mcschemes.loadVersionAttrsFromClientJar(Path.home().joinpath('.minecraft/versions/1.21.11/1.21.11.jar'))

print('Unique identifier of this client JAR:', version_attrs.id)
print('User-friendly name of this client JAR:', version_attrs.name)
print('Data version of this client JAR:', version_attrs.world_version)
print('Protocol version of this client JAR:', version_attrs.protocol_version)
print('Build time of this client JAR:', version_attrs.build_time)
if version_attrs.series_id:
    print('Series ID (branch name) of this client JAR:', version_attrs.series_id)
```

### Load `client.json`, then filter and concatenate command line

This example code uses `client.json` from Minecraft Java Edition
1.21.11, [download at here](https://piston-meta.mojang.com/v1/packages/3f42d3ea921915b36c581a435ed03683a7023fb1/1.21.11.json).

**Note:** this example only demonstrates basic conditional filtering and concatenation operations, and does not consider the replacement of
placeholder parameters (which may be supported in future versions).

```python
import mcschemes
from mcschemes.tools import rules

with open('1.21.11.json', mode='r') as f:
    client_manifest_1_21_11 = mcschemes.load(f, mcschemes.Scheme.CLIENT_MANIFEST)

features: dict[str, bool] = {
    'is_demo_user'         : True,
    'has_custom_resolution': True
}
cmdline: list[str] = ['java']
for jvm_arg_entry in client_manifest_1_21_11.arguments.jvm:
    if rules.isArgumentCanBeAppended(jvm_arg_entry, features=features):
        cmdline.extend(jvm_arg_entry.value)
cmdline.append(client_manifest_1_21_11.mainClass)
for game_arg_entry in client_manifest_1_21_11.arguments.game:
    if rules.isArgumentCanBeAppended(game_arg_entry, features=features):
        cmdline.extend(game_arg_entry.value)
print('Concatenated command line (without placeholder replacements):', cmdline)
```
