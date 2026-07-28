import requests
import pathlib
import hashlib
import re

import os
import platform
from concurrent import futures


VERSION_MANIFEST_URL = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
ASSETS_ROOT_URL = "https://resources.download.minecraft.net"

LIBRARIES_ROOT_DIRECTORY = "libraries"
ASSETS_ROOT_DIRECTORY = "assets"
OS_ARCH = {
    "x86_64": "amd64",
    "x64": "amd64",
    "amd64": "amd64",
    "i386": "x86",
    "i486": "x86",
    "i586": "x86",
    "i686": "x86",
    "x86": "x86",
    "arm64": "aarch64",
    "aarch64": "aarch64",
    "armv7l": "arm",
    "armv6l": "arm",
}


def _perform_json_request(url: str, timeout: int = 5.0) -> dict:
    headers = {"Accept": "application/json", "User-Agent": "minecraft-extractor/1.0.0"}
    response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)

    response.raise_for_status()
    return response.json()


def _verify_file_sha256(file_path: pathlib.Path, expected_hash: str) -> bool:
    with open(file_path, "rb") as file:
        calculated_hash = hashlib.file_digest(file, "sha1").hexdigest()
    return calculated_hash.lower() == expected_hash.lower()


def _perform_download_request(
    url: string,
    path: pathlib.Path,
    expected_hash: str,
    timeout: int = 5.0,
) -> None:
    if path.exists() and _verify_file_sha256(path, expected_hash):
        print(f"Skipping {path} download, it already exists")
        return

    print(f"Downloading {url} to {path}...")
    headers = {"User-Agent": "minecraft-extractor/1.0.0"}
    response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True, stream=True)
    response.raise_for_status()

    # Ensuring that all directories up to the `path` are created.
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb+") as file:
        for chunk in response.iter_content(chunk_size = 8192):
            if chunk:
                file.write(chunk)

    if _verify_file_sha256(path, expected_hash):
        print(f"Successfully downloaded and verified {path}")
    else:
        print(f"Could not verify file {path}")


def get_latest_release() -> dict | None:
    versions_manifest = _perform_json_request(VERSION_MANIFEST_URL)
    latest_release_version = versions_manifest["latest"]["release"]

    latest_release_manifest = None
    for manifest in versions_manifest["versions"]:
        if manifest["type"] != "release":
            continue
        if manifest["id"] != latest_release_version:
            continue
        latest_release_manifest = manifest
        break
    return latest_release_manifest


def download_client_jar(version_manifest: dict) -> None:
    print("Downloading client.jar...")
    _perform_download_request(
        version_manifest["downloads"]["client"]["url"],
        pathlib.Path("client.jar"),
        version_manifest["downloads"]["client"]["sha1"],
    )


def _is_library_allowed(library: dict) -> bool:
    system = platform.system()

    if system == "Windows":
        os_name = "windows"
        os_version = platform.version()
    elif system == "Darwin":
        os_name = "osx"
        os_version = platform.mac_ver()[0] or platform.release()
    elif system == "Linux":
        os_name = "linux"
        os_version = platform.release()
    else:
        os_name = system.lower()
        os_version = platform.release()

    machine = platform.machine().lower()
    os_arch = OS_ARCH.get(machine, machine)
    rules = library.get("rules")

    # A library without rules applies to every platform.
    if not rules:
        return True

    allowed = False
    for rule in rules:
        os_rule = rule.get("os", {})

        required_name = os_rule.get("name")
        if required_name is not None and required_name != os_name:
            continue

        version_pattern = os_rule.get("version")
        if version_pattern is not None and re.fullmatch(version_pattern, os_version) is None:
            continue

        arch_pattern = os_rule.get("arch")
        if arch_pattern is not None and re.fullmatch(arch_pattern, os_arch) is None:
            continue

        allowed = rule.get("action") == "allow"

    return allowed


def download_client_libraries(version_manifest: dict) -> None:
    client_libraries = version_manifest["libraries"]

    print(f"Will use {os.cpu_count()} workers for concurrent download")
    with futures.ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        submitted_futures = []
        for library in client_libraries:
            if not _is_library_allowed(library):
                print(f"Skipping library {library["name"]}, since it's not allowed")
                continue
            artifact = library["downloads"]["artifact"]
            path = pathlib.Path(LIBRARIES_ROOT_DIRECTORY).joinpath(artifact["path"])
            future = executor.submit(_perform_download_request, artifact["url"], path, artifact["sha1"])
            submitted_futures.append(future)

        print(f"Will download {len(submitted_futures)} client libraries")
        futures.wait(submitted_futures)


def download_client_assets(version_manifest: dict) -> None:
    asset_index = version_manifest["assetIndex"]
    version_assets = _perform_json_request(asset_index["url"])

    print(f"Will use {os.cpu_count()} workers for concurrent assets download")
    with futures.ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        submitted_futures = []
        for key in version_assets["objects"]:
            asset = version_assets["objects"][key]
            asset_hash = asset["hash"]

            download_url = f"{ASSETS_ROOT_URL}/{asset_hash[:2]}/{asset_hash}"
            path = pathlib.Path(ASSETS_ROOT_DIRECTORY).joinpath(key)

            future = executor.submit(_perform_download_request, download_url, path, asset_hash)
            submitted_futures.append(future)

        print(f"Will download {len(submitted_futures)} client assets")
        futures.wait(submitted_futures)


def main() -> None:
    latest_release = get_latest_release()
    if latest_release is None:
        print("Could not find latest release version")
        return

    print(f"Latest release version: {latest_release["id"]}")
    version_manifest = _perform_json_request(latest_release["url"])
    download_client_jar(version_manifest)
    download_client_libraries(version_manifest)
    download_client_assets(version_manifest)

    print("All downloads succeeded.")
    print(f"Main client class: {version_manifest["mainClass"]}")


if __name__ == "__main__":
    main()
