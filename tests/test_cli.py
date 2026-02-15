"""Epic 6: CLI tests."""

import subprocess
import sys
import zipfile


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "bin_to_wheel", *args],
        capture_output=True,
        text=True,
    )


def test_help_flag():
    r = run_cli("--help")
    assert r.returncode == 0
    assert "bin-to-wheel" in r.stdout.lower() or "--name" in r.stdout


def test_missing_required_args():
    r = run_cli()
    assert r.returncode != 0


def test_platform_and_auto_platform_exclusive():
    r = run_cli(
        "--name", "foo",
        "--version", "1.0",
        "--binary", "/dev/null",
        "--platform", "linux-x86_64",
        "--auto-platform",
    )
    assert r.returncode != 0
    assert "not allowed" in r.stderr.lower() or "exclusive" in r.stderr.lower()


def test_builds_wheel(fake_binary, output_dir):
    r = run_cli(
        "--name", "test-pkg",
        "--version", "0.1.0",
        "--binary", str(fake_binary),
        "--platform", "linux-x86_64",
        "--output-dir", str(output_dir),
    )
    assert r.returncode == 0, f"stderr: {r.stderr}"
    wheels = list(output_dir.glob("*.whl"))
    assert len(wheels) == 1


def test_auto_platform_builds_wheel(fake_binary, output_dir):
    r = run_cli(
        "--name", "test-pkg",
        "--version", "0.1.0",
        "--binary", str(fake_binary),
        "--auto-platform",
        "--output-dir", str(output_dir),
    )
    assert r.returncode == 0, f"stderr: {r.stderr}"
    wheels = list(output_dir.glob("*.whl"))
    assert len(wheels) == 1


def test_entry_point_flag(fake_binary, output_dir):
    r = run_cli(
        "--name", "my-tool",
        "--version", "1.0.0",
        "--binary", str(fake_binary),
        "--platform", "linux-x86_64",
        "--output-dir", str(output_dir),
        "--entry-point", "my-tool",
    )
    assert r.returncode == 0, f"stderr: {r.stderr}"
    whl = list(output_dir.glob("*.whl"))[0]
    with zipfile.ZipFile(whl) as zf:
        ep = zf.read("my_tool-1.0.0.dist-info/entry_points.txt").decode()
        assert "my-tool = my_tool:main" in ep


def test_output_path_printed(fake_binary, output_dir):
    r = run_cli(
        "--name", "test-pkg",
        "--version", "0.1.0",
        "--binary", str(fake_binary),
        "--platform", "linux-x86_64",
        "--output-dir", str(output_dir),
    )
    assert r.returncode == 0
    assert ".whl" in r.stdout


def test_binary_not_found(output_dir):
    r = run_cli(
        "--name", "test-pkg",
        "--version", "0.1.0",
        "--binary", "/nonexistent/binary",
        "--platform", "linux-x86_64",
        "--output-dir", str(output_dir),
    )
    assert r.returncode != 0


def test_multi_binary_builds_wheel(tmp_path, output_dir):
    """Two --binary flags produce a wheel with both binaries."""
    bin1 = tmp_path / "flapi"
    bin1.write_bytes(b"#!/bin/sh\necho flapi\n")
    bin2 = tmp_path / "flapii"
    bin2.write_bytes(b"#!/bin/sh\necho flapii\n")

    r = run_cli(
        "--name", "flapi-io",
        "--version", "1.0.0",
        "--binary", str(bin1), "--entry-point", "flapi",
        "--binary", str(bin2), "--entry-point", "flapii",
        "--platform", "linux-x86_64",
        "--output-dir", str(output_dir),
    )
    assert r.returncode == 0, f"stderr: {r.stderr}"

    whl = list(output_dir.glob("*.whl"))[0]
    with zipfile.ZipFile(whl) as zf:
        names = zf.namelist()
        assert "flapi_io/bin/flapi" in names
        assert "flapi_io/bin/flapii" in names
        ep = zf.read("flapi_io-1.0.0.dist-info/entry_points.txt").decode()
        assert "flapi = flapi_io:main_flapi" in ep
        assert "flapii = flapi_io:main_flapii" in ep


def test_multi_binary_mismatched_entry_points(tmp_path, output_dir):
    """Mismatched --binary and --entry-point counts should fail."""
    bin1 = tmp_path / "a"
    bin1.write_bytes(b"x")
    bin2 = tmp_path / "b"
    bin2.write_bytes(b"y")

    r = run_cli(
        "--name", "test-pkg",
        "--version", "1.0.0",
        "--binary", str(bin1),
        "--binary", str(bin2),
        "--entry-point", "only-one",
        "--platform", "linux-x86_64",
        "--output-dir", str(output_dir),
    )
    assert r.returncode != 0
    assert "count" in r.stderr.lower() or "match" in r.stderr.lower()
