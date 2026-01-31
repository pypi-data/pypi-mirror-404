"""
Generate LLM package hash for build-time verification.

Usage:
    python -m cllmv.pkg_hash
"""

import ctypes
import json
import os
from importlib.metadata import distribution, PackageNotFoundError
from pathlib import Path


def find_package_path(package_name: str) -> str | None:
    """
    Find the installation path of a package without importing it.
    """
    try:
        dist = distribution(package_name)
    except PackageNotFoundError:
        return None

    # For editable installs, check direct_url.json
    try:
        direct_url_text = dist.read_text("direct_url.json")
        if direct_url_text:
            direct_url = json.loads(direct_url_text)
            if direct_url.get("dir_info", {}).get("editable"):
                url = direct_url.get("url", "")
                if url.startswith("file://"):
                    source_dir = url[7:]
                    for candidate in [
                        os.path.join(source_dir, package_name),
                        os.path.join(source_dir, "python", package_name),
                        os.path.join(source_dir, "src", package_name),
                    ]:
                        if os.path.isdir(candidate) and os.path.exists(
                            os.path.join(candidate, "__init__.py")
                        ):
                            return candidate
    except FileNotFoundError:
        pass

    # For regular installs, find the package in dist.files
    if dist.files:
        for f in dist.files:
            parts = str(f).split("/")
            if (
                len(parts) >= 2
                and parts[0] == package_name
                and parts[1] == "__init__.py"
            ):
                full_path = f.locate()
                return str(full_path.parent)

    # Fallback: try via dist location
    if hasattr(dist, "_path"):
        dist_info_path = Path(dist._path)
        site_packages = dist_info_path.parent
        pkg_dir = site_packages / package_name
        if pkg_dir.is_dir() and (pkg_dir / "__init__.py").exists():
            return str(pkg_dir)

    return None


def compute_hash(package_name: str, package_path: str, lib_path: str) -> str | None:
    """Call the C library to compute the package hash."""
    if not os.path.exists(lib_path):
        return None

    try:
        lib = ctypes.CDLL(lib_path)
        lib.compute_package_hash.argtypes = [
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_size_t,
        ]
        lib.compute_package_hash.restype = ctypes.c_int

        hash_buf = ctypes.create_string_buffer(65)
        ret = lib.compute_package_hash(
            package_name.encode("utf-8"),
            package_path.encode("utf-8"),
            hash_buf,
            65,
        )

        if ret != 0:
            return None

        return hash_buf.value.decode("utf-8")
    except Exception:
        return None


def main():
    """Main entry point for python -m cllmv.pkg_hash"""
    # Find the library path (same logic as base.py)
    lib_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "lib", "libcllmv.so"
    )

    result = {
        "package": None,
        "path": None,
        "hash": None,
        "error": None,
    }

    # Try sglang first, then vllm
    for package_name in ["sglang", "vllm"]:
        package_path = find_package_path(package_name)
        if package_path:
            result["package"] = package_name
            result["path"] = package_path

            if not os.path.exists(lib_path):
                result["error"] = f"Library not found: {lib_path}"
                break

            pkg_hash = compute_hash(package_name, package_path, lib_path)
            if pkg_hash:
                result["hash"] = pkg_hash
            else:
                result["error"] = "Hash computation failed"
            break

    if result["package"] is None:
        result["error"] = "No LLM package (sglang/vllm) found"

    print(json.dumps(result))


if __name__ == "__main__":
    main()
