# bin-to-wheel

Package pre-built binaries into Python wheels. Single binary in, single `.whl` out.

Designed for CI pipelines that compile platform-specific binaries and need to distribute them via PyPI.

## Install

```bash
pip install bin-to-wheel
```

## Usage

```bash
bin-to-wheel \
  --name my-tool \
  --version 1.0.0 \
  --binary ./build/my-tool \
  --platform linux-x86_64 \
  --output-dir ./dist \
  --entry-point my-tool
```

### Platform tags

Friendly names are mapped to PEP 427 platform tags:

| Friendly name | Wheel tag |
|---|---|
| `linux-x86_64` | `manylinux_2_17_x86_64` |
| `macos-arm64` | `macosx_11_0_arm64` |
| `macos-x86_64` | `macosx_10_15_x86_64` |
| `windows-x64` | `win_amd64` |

You can also pass raw PEP 427 tags directly, or use `--auto-platform` to detect the current platform.

### All options

```
--name           Package name (required)
--version        Package version (required)
--binary         Path to the binary to package (required)
--platform       Platform tag (friendly name or raw PEP 427)
--auto-platform  Auto-detect platform (mutually exclusive with --platform)
--output-dir     Output directory (default: dist)
--entry-point    Console script entry point name
--description    Package description
--author         Package author
--license        License identifier
--url            Project URL
--readme         Path to README file for long description
```

## How it works

The generated wheel contains:
- `{package}/bin/{binary}` - the binary with executable permissions
- `{package}/__init__.py` - Python wrapper that finds and runs the binary
- `{package}/__main__.py` - enables `python -m {package}` support
- Standard wheel metadata (METADATA, WHEEL, RECORD, entry_points.txt)

When installed via pip, the entry point script calls the Python wrapper, which `execvp`s (Unix) or `subprocess.call`s (Windows) the bundled binary.

## CI example

```yaml
# GitHub Actions: build wheels for all platforms
steps:
  - uses: actions/download-artifact@v4
    with:
      pattern: binary-*
      path: binaries

  - run: pip install bin-to-wheel

  - run: |
      for platform in linux-x86_64 macos-arm64 macos-x86_64 windows-x64; do
        bin-to-wheel \
          --name my-tool \
          --version ${{ github.ref_name }} \
          --binary binaries/binary-${platform}/my-tool \
          --platform ${platform} \
          --output-dir dist \
          --entry-point my-tool
      done
```

## License

Apache-2.0
