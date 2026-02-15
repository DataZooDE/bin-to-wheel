"""Epic 4: Wheel ZIP assembly tests."""

import zipfile
import csv
import io

from bin_to_wheel import build_wheel, compute_file_hash


def test_returns_path(fake_binary, output_dir):
    path = build_wheel(
        binary_path=fake_binary,
        output_dir=output_dir,
        name="erpl-adt",
        version="1.0.0",
        platform_tag="manylinux_2_17_x86_64",
    )
    assert path.exists()
    assert path.suffix == ".whl"


def test_filename_format(fake_binary, output_dir):
    path = build_wheel(
        binary_path=fake_binary,
        output_dir=output_dir,
        name="erpl-adt",
        version="2026.2.14",
        platform_tag="manylinux_2_17_x86_64",
    )
    assert path.name == "erpl_adt-2026.2.14-py3-none-manylinux_2_17_x86_64.whl"


def test_is_valid_zip(fake_binary, output_dir):
    path = build_wheel(
        binary_path=fake_binary,
        output_dir=output_dir,
        name="erpl-adt",
        version="1.0.0",
        platform_tag="manylinux_2_17_x86_64",
    )
    assert zipfile.is_zipfile(path)


def test_contains_binary(fake_binary, output_dir):
    """Binary is stored with its original filename from disk."""
    path = build_wheel(
        binary_path=fake_binary,
        output_dir=output_dir,
        name="erpl-adt",
        version="1.0.0",
        platform_tag="manylinux_2_17_x86_64",
        entry_point="erpl-adt",
    )
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        # Binary keeps its original name (fake_binary is named "fake-binary")
        assert "erpl_adt/bin/fake-binary" in names


def test_binary_preserves_exe_extension(tmp_path, output_dir):
    """Windows binaries keep their .exe extension in the wheel."""
    binary = tmp_path / "erpl-adt.exe"
    binary.write_bytes(b"MZ\x90\x00")  # PE header stub
    path = build_wheel(
        binary_path=binary,
        output_dir=output_dir,
        name="erpl-adt",
        version="1.0.0",
        platform_tag="win_amd64",
        entry_point="erpl-adt",
    )
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        assert "erpl_adt/bin/erpl-adt.exe" in names
        # Entry point is still "erpl-adt" (no .exe)
        ep = zf.read("erpl_adt-1.0.0.dist-info/entry_points.txt").decode()
        assert "erpl-adt = erpl_adt:main" in ep


def test_contains_init_and_main(fake_binary, output_dir):
    path = build_wheel(
        binary_path=fake_binary,
        output_dir=output_dir,
        name="erpl-adt",
        version="1.0.0",
        platform_tag="manylinux_2_17_x86_64",
    )
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        assert "erpl_adt/__init__.py" in names
        assert "erpl_adt/__main__.py" in names


def test_contains_dist_info(fake_binary, output_dir):
    path = build_wheel(
        binary_path=fake_binary,
        output_dir=output_dir,
        name="erpl-adt",
        version="1.0.0",
        platform_tag="manylinux_2_17_x86_64",
    )
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        assert "erpl_adt-1.0.0.dist-info/METADATA" in names
        assert "erpl_adt-1.0.0.dist-info/WHEEL" in names
        assert "erpl_adt-1.0.0.dist-info/RECORD" in names


def test_binary_permissions(fake_binary, output_dir):
    path = build_wheel(
        binary_path=fake_binary,
        output_dir=output_dir,
        name="erpl-adt",
        version="1.0.0",
        platform_tag="manylinux_2_17_x86_64",
    )
    with zipfile.ZipFile(path) as zf:
        info = zf.getinfo("erpl_adt/bin/fake-binary")
        unix_perms = (info.external_attr >> 16) & 0o777
        assert unix_perms & 0o755 == 0o755


def test_record_hashes_match(fake_binary, output_dir):
    path = build_wheel(
        binary_path=fake_binary,
        output_dir=output_dir,
        name="erpl-adt",
        version="1.0.0",
        platform_tag="manylinux_2_17_x86_64",
    )
    with zipfile.ZipFile(path) as zf:
        record_data = zf.read("erpl_adt-1.0.0.dist-info/RECORD").decode("utf-8")
        reader = csv.reader(io.StringIO(record_data))
        for row in reader:
            if len(row) >= 2 and row[1]:  # skip RECORD itself (empty hash)
                filepath, hash_entry, size = row
                content = zf.read(filepath)
                expected = f"sha256={compute_file_hash(content)}"
                assert hash_entry == expected, f"Hash mismatch for {filepath}"
                assert int(size) == len(content), f"Size mismatch for {filepath}"


def test_entry_points_present(fake_binary, output_dir):
    path = build_wheel(
        binary_path=fake_binary,
        output_dir=output_dir,
        name="erpl-adt",
        version="1.0.0",
        platform_tag="manylinux_2_17_x86_64",
        entry_point="erpl-adt",
    )
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        assert "erpl_adt-1.0.0.dist-info/entry_points.txt" in names
        ep = zf.read("erpl_adt-1.0.0.dist-info/entry_points.txt").decode("utf-8")
        assert "erpl-adt = erpl_adt:main" in ep


def test_multi_binary_wheel(tmp_path, output_dir):
    """Wheel with two binaries contains both and proper entry points."""
    bin1 = tmp_path / "flapi"
    bin1.write_bytes(b"\x7fELF-flapi")
    bin2 = tmp_path / "flapii"
    bin2.write_bytes(b"\x7fELF-flapii")

    path = build_wheel(
        binary_path=[bin1, bin2],
        output_dir=output_dir,
        name="flapi-io",
        version="2.0.0",
        platform_tag="manylinux_2_17_x86_64",
        entry_point=["flapi", "flapii"],
    )

    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        # Both binaries present
        assert "flapi_io/bin/flapi" in names
        assert "flapi_io/bin/flapii" in names

        # Init references both
        init = zf.read("flapi_io/__init__.py").decode()
        assert "flapi" in init
        assert "flapii" in init

        # Entry points map to per-binary functions
        ep = zf.read("flapi_io-2.0.0.dist-info/entry_points.txt").decode()
        assert "flapi = flapi_io:main_flapi" in ep
        assert "flapii = flapi_io:main_flapii" in ep


def test_multi_binary_permissions(tmp_path, output_dir):
    """All binaries in a multi-binary wheel have executable permissions."""
    bin1 = tmp_path / "alpha"
    bin1.write_bytes(b"bin1")
    bin2 = tmp_path / "beta"
    bin2.write_bytes(b"bin2")

    path = build_wheel(
        binary_path=[bin1, bin2],
        output_dir=output_dir,
        name="multi-test",
        version="1.0.0",
        platform_tag="manylinux_2_17_x86_64",
    )

    with zipfile.ZipFile(path) as zf:
        for bname in ["alpha", "beta"]:
            info = zf.getinfo(f"multi_test/bin/{bname}")
            unix_perms = (info.external_attr >> 16) & 0o777
            assert unix_perms & 0o755 == 0o755, f"{bname} should be executable"


def test_multi_binary_record_hashes(tmp_path, output_dir):
    """RECORD hashes are correct for multi-binary wheels."""
    bin1 = tmp_path / "a"
    bin1.write_bytes(b"aaa")
    bin2 = tmp_path / "b"
    bin2.write_bytes(b"bbb")

    path = build_wheel(
        binary_path=[bin1, bin2],
        output_dir=output_dir,
        name="hash-test",
        version="1.0.0",
        platform_tag="manylinux_2_17_x86_64",
    )

    with zipfile.ZipFile(path) as zf:
        record_data = zf.read("hash_test-1.0.0.dist-info/RECORD").decode()
        reader = csv.reader(io.StringIO(record_data))
        for row in reader:
            if len(row) >= 2 and row[1]:
                filepath, hash_entry, size = row
                content = zf.read(filepath)
                expected = f"sha256={compute_file_hash(content)}"
                assert hash_entry == expected, f"Hash mismatch for {filepath}"
                assert int(size) == len(content), f"Size mismatch for {filepath}"
