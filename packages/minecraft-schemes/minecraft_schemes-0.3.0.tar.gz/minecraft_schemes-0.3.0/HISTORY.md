# History

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Not planned yet.

## [0.3.0] - 2026-01-31

### Added

- **Scheme:** Added support for parsing version information files (the `version.json` embedded within `client.jar`).
- **Scheme:** Added parse support for index file of Mojang Java Runtimes, and file manifest of each java runtime.
- **Parsing:** Added a dedicated converter class in `mcschemes.tools.parser.Converter.DedicatedConverter`.
    - This is intended to replace the `mcschemes.tools.parser.createConverter()`.

### Backwards-incompatible Changes

- **Scheme:** `mcschemes.assetindex.AssetIndex` now use the `Path` object from the standard library's `pathlib` module to represent file relative
  paths in asset index files.

    1. Previously, it will use `str` to represent file relative paths, so you can access information (e.g. hash, size) by the following way:

        ```python
        from mcschemes.assetindex import AssetIndex
  
        asset_index: AssetIndex = ...  # Some operations to obtain the json and structure it to the AssetIndex instance
        file_info = asset_index.objects['icons/icon_128x128.png']
  
        [...]  # Do your operations for file_info
        ```

    2. Now, you need to use a `pathlib.Path` object as the key to access the corresponding information:

        ```python
        from pathlib import Path
        from mcschemes.assetindex import AssetIndex
      
        asset_index: AssetIndex = ...  # Some operations to obtain the json and structure it to the AssetIndex instance
        file_info = asset_index.objects[Path('icons/icon_128x128.png')]
      
        [...]  # Do your operations for file_info
        ```

### Deprecations

- **Parsing:** `mcschemes.tools.parser.createConverter()` is now marked as deprecated and will be removed in future versions.
    - Now pass a converter class based on `cattrs.Converter` to the kw-only argument ``converter_class`` is no longer determines the type of the
      returned dedicated converter instance.

### Changes

- **Project metadata:** This version history file has been revised to conform to the format described
  in [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
- **Project metadata:** Fully updated the [README file](README.md):
    - Added a summary of the main features and benefits.
    - Added a summary of file structures supported by this library.
    - Usage example are now more useful and better represent typical use cases.
- **Organizational:** Reorganized the project structure:
    - `mcschemes.tools.parser` now is a package.
        - Sub-package `mcschemes.tools.parser.converters` is added to contains dedicated converters.
- **Typing:** `typing-extensions` was used instead of stdlib `typing` for better backward-compatibility for type annotation.
- **Scheme:** Several changes for SHA-1 hexdigest container:
    - The comparison between two `mcsehemes.specials.Sha1Sum` instances now is based on the case-insensitive form of the `hexdigest` attribute of
      both.
    - The exception class `mcschemes.specials.ChecksumMismatch` is now exposed.
- **Parsing:** `mcschemes.tools.parser.parse()` now will check the second argument `scheme` in more robust way.

### Fixed

- **Tooling:** Fixed a mistake when comparing the OS name in the function `mcschemes.tools.rules.isAllow()`.

## [0.2.0] - 2025-12-11

### Added

- **Project metadata:** Added `MANIFEST.in` for setuptools.
- **Scheme:** Added a SHA-1 hexdigest container type for `sha1`/`hash` fields (un-)structuring. Its definition can be found at:
  `mcschemes.specials.Sha1Sum`.
- **Tooling:** Added some tool functions to calculate a set of rules (iterable of `mcschemes.clientmanifest.nodes.RuleEntry` instances) means allow or
  disallow some operation, such as append an argument or download a library file.

### Changes

- **Project metadata:** Declared build backend `setuptools` into `pyproject.toml`.
- **Project metadata:** According to [PEP 561](https://peps.python.org/pep-0561), an empty `py.typed` is added into the root directory of package.
- **Project metadata:** Corrected the date format for all tier-2 titles in this version history file.
- **Organizational:** Moved `typings.py` to the root directory of package.

## [0.1.0.post1] - 2025-12-05

### Changes

- **Project metadata:** Added project urls into `pyproject.toml`.
- **Project metadata:** Added disclaimer in `README.md`.

## [0.1.0] - 2025-12-04

### Added

The initial release.
