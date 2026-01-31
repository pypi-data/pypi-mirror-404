"""Docker image utilities for pre-pulling compose images."""

import logging
import os
import platform
import pty
import re
import select
import subprocess
from collections.abc import Callable

import yaml

logger = logging.getLogger(__name__)


# Architecture mapping: Python's platform.machine() -> Docker platform
ARCH_TO_DOCKER_PLATFORM = {
    "x86_64": "linux/amd64",
    "amd64": "linux/amd64",
    "aarch64": "linux/arm64",
    "arm64": "linux/arm64",
}

# Docker image architecture names (from docker inspect)
DOCKER_ARCH_TO_PLATFORM = {
    "amd64": "linux/amd64",
    "arm64": "linux/arm64",
}


def get_host_architecture() -> str:
    """
    Get the host machine's architecture.

    Returns:
        Architecture string (e.g., "x86_64", "arm64", "aarch64")
    """
    return platform.machine()


def get_host_docker_platform() -> str | None:
    """
    Get the Docker platform string for the host architecture.

    Returns:
        Docker platform (e.g., "linux/amd64", "linux/arm64") or None if unknown
    """
    arch = get_host_architecture()
    return ARCH_TO_DOCKER_PLATFORM.get(arch)


def get_image_architecture(image: str) -> str | None:
    """
    Get the architecture of a locally cached Docker image.

    Args:
        image: Image name (e.g., "python:3.12-slim")

    Returns:
        Architecture string (e.g., "amd64", "arm64") or None if not found/error
    """
    try:
        result = subprocess.run(
            ["docker", "image", "inspect", image, "--format", "{{.Architecture}}"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def check_image_architecture_matches_host(image: str) -> tuple[bool, str | None, str | None]:
    """
    Check if a cached image's architecture matches the host.

    Args:
        image: Image name to check

    Returns:
        Tuple of (matches, image_arch, host_arch):
        - matches: True if architectures match or image not cached
        - image_arch: The cached image's architecture (None if not cached)
        - host_arch: The host's architecture
    """
    host_arch = get_host_architecture()
    host_platform = get_host_docker_platform()

    if not host_platform:
        # Unknown host architecture - can't check
        logger.warning(f"Unknown host architecture: {host_arch}")
        return (True, None, host_arch)

    image_arch = get_image_architecture(image)
    if not image_arch:
        # Image not cached - nothing to check
        return (True, None, host_arch)

    image_platform = DOCKER_ARCH_TO_PLATFORM.get(image_arch)
    matches = image_platform == host_platform

    if not matches:
        logger.info(
            f"Architecture mismatch for {image}: "
            f"cached={image_arch} ({image_platform}), host={host_arch} ({host_platform})"
        )

    return (matches, image_arch, host_arch)


def is_running_in_linux_vm_on_arm() -> bool:
    """
    Detect if running Linux ARM64 (likely a VM on Apple Silicon).

    This is a common setup that causes architecture issues because:
    - macOS Docker Desktop handles multi-arch via Rosetta
    - Linux ARM64 in a VM doesn't have that, needs explicit platform handling

    Returns:
        True if running Linux on ARM64
    """
    import sys
    return sys.platform == "linux" and get_host_architecture() in ("aarch64", "arm64")


def extract_images_from_compose(compose_yaml: str) -> list[str]:
    """
    Extract Docker image names from a compose.yaml string.

    Args:
        compose_yaml: Docker Compose YAML content

    Returns:
        List of image names (e.g., ["jackpayne123/nyuctf-agent:v2", "ctf-game:latest"])
    """
    try:
        compose_data = yaml.safe_load(compose_yaml)
        if not compose_data or "services" not in compose_data:
            return []

        images = []
        for service_name, service_config in compose_data.get("services", {}).items():
            if isinstance(service_config, dict) and "image" in service_config:
                images.append(service_config["image"])
        return images
    except yaml.YAMLError as e:
        logger.warning(f"Failed to parse compose.yaml: {e}")
        return []


def extract_image_platforms_from_compose(compose_yaml: str) -> dict[str, str | None]:
    """
    Extract Docker image names and their platforms from a compose.yaml string.

    Args:
        compose_yaml: Docker Compose YAML content

    Returns:
        Dict mapping image names to their platform (or None if no platform specified)
    """
    try:
        compose_data = yaml.safe_load(compose_yaml)
        if not compose_data or "services" not in compose_data:
            return {}

        image_platforms = {}
        for service_name, service_config in compose_data.get("services", {}).items():
            if isinstance(service_config, dict) and "image" in service_config:
                image = service_config["image"]
                platform = service_config.get("platform")
                image_platforms[image] = platform
        return image_platforms
    except yaml.YAMLError as e:
        logger.warning(f"Failed to parse compose.yaml: {e}")
        return {}


def check_image_exists_locally(image: str) -> bool:
    """
    Check if a Docker image exists locally.

    Args:
        image: Image name (e.g., "jackpayne123/nyuctf-agent:v2")

    Returns:
        True if image exists locally, False otherwise
    """
    try:
        result = subprocess.run(
            ["docker", "image", "inspect", image],
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def remove_image(image: str) -> bool:
    """
    Remove a Docker image from local cache.

    Args:
        image: Image name to remove

    Returns:
        True if removed successfully, False otherwise
    """
    try:
        result = subprocess.run(
            ["docker", "rmi", image],
            capture_output=True,
            timeout=30,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def fix_image_architecture(
    image: str,
    on_status: Callable[[str], None] | None = None,
) -> tuple[bool, str]:
    """
    Check if a cached image has wrong architecture and fix it if needed.

    For Linux ARM64 hosts (e.g., VM on Apple Silicon), this:
    1. Checks if the cached image is amd64 when host is arm64
    2. Removes the wrongly-cached image
    3. Re-pulls with explicit --platform linux/arm64

    Args:
        image: Image name to check/fix
        on_status: Callback for status updates

    Returns:
        Tuple of (needed_fix, message):
        - needed_fix: True if image was re-pulled
        - message: Description of what happened
    """
    matches, image_arch, host_arch = check_image_architecture_matches_host(image)

    if matches:
        if image_arch:
            return (False, f"architecture OK ({image_arch})")
        else:
            return (False, "not cached")

    # Architecture mismatch detected
    host_platform = get_host_docker_platform()
    if not host_platform:
        return (False, f"unknown host architecture: {host_arch}")

    if on_status:
        on_status(f"Cached image is {image_arch}, host is {host_arch} - re-pulling...")

    # Remove the wrongly-cached image
    logger.info(f"Removing wrongly-cached {image_arch} image: {image}")
    if not remove_image(image):
        return (False, f"failed to remove cached {image_arch} image")

    # Re-pull with correct platform
    logger.info(f"Re-pulling {image} with platform {host_platform}")
    success = pull_image_with_progress(image, platform=host_platform)

    if success:
        return (True, f"re-pulled as {host_platform.split('/')[-1]}")
    else:
        return (False, f"failed to re-pull with platform {host_platform}")


def pull_image_with_progress(
    image: str,
    platform: str | None = None,
    on_progress: Callable[[str, str], None] | None = None,
    on_complete: Callable[[str, bool], None] | None = None,
    on_error: Callable[[str, str], None] | None = None,
) -> bool:
    """
    Pull a Docker image with progress callbacks using PTY for real progress output.

    Args:
        image: Image name to pull
        platform: Optional platform to pull (e.g., "linux/amd64")
        on_progress: Callback(image, status_line) called for each progress update
        on_complete: Callback(image, success) called when pull completes
        on_error: Callback(image, error_message) called when pull fails

    Returns:
        True if pull succeeded, False otherwise
    """
    try:
        # Use PTY to get real progress output from docker
        master_fd, slave_fd = pty.openpty()

        cmd = ["docker", "pull", image]
        if platform:
            cmd.extend(["--platform", platform])

        process = subprocess.Popen(
            cmd,
            stdout=slave_fd,
            stderr=slave_fd,
            stdin=slave_fd,
            close_fds=True,
        )

        os.close(slave_fd)  # Close slave in parent

        # Read output from master with timeout
        output_buffer = ""
        # Regex to parse docker progress: "abc123: Downloading [===>  ] 10.5MB/50MB"
        progress_pattern = re.compile(
            r"([a-f0-9]+):\s*(Downloading|Extracting|Verifying Checksum|Download complete|Pull complete|Already exists|Waiting)(?:\s+\[.*?\]\s+)?(\d+\.?\d*\s*[kMG]?B)?(?:/(\d+\.?\d*\s*[kMG]?B))?"
        )

        while True:
            # Check if process is done
            ret = process.poll()
            if ret is not None:
                # Read any remaining output
                try:
                    while True:
                        ready, _, _ = select.select([master_fd], [], [], 0.1)
                        if not ready:
                            break
                        chunk = os.read(master_fd, 4096)
                        if not chunk:
                            break
                except OSError:
                    pass
                break

            # Read available output
            try:
                ready, _, _ = select.select([master_fd], [], [], 0.1)
                if ready:
                    chunk = os.read(master_fd, 4096)
                    if chunk:
                        output_buffer += chunk.decode("utf-8", errors="replace")

                        # Parse and report progress
                        # Docker uses carriage returns to update lines in place
                        lines = output_buffer.replace("\r", "\n").split("\n")
                        output_buffer = lines[-1]  # Keep incomplete line

                        for line in lines[:-1]:
                            line = line.strip()
                            # Strip ANSI escape codes
                            line = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", line)
                            if line and on_progress:
                                on_progress(image, line)
            except OSError:
                break

        os.close(master_fd)
        success = process.returncode == 0

        if on_complete:
            on_complete(image, success)

        return success

    except (FileNotFoundError, OSError) as e:
        logger.error(f"Failed to pull {image}: {e}")
        if on_complete:
            on_complete(image, False)
        return False


def prepull_compose_images(
    compose_yaml: str,
    on_image_start: Callable[[str, int, int], None] | None = None,
    on_image_progress: Callable[[str, str], None] | None = None,
    on_image_complete: Callable[[str, bool, str], None] | None = None,
) -> tuple[int, int]:
    """
    Pre-pull all images from a compose.yaml file.

    Args:
        compose_yaml: Docker Compose YAML content
        on_image_start: Callback(image, current_idx, total) when starting an image
        on_image_progress: Callback(image, status_line) for pull progress
        on_image_complete: Callback(image, success, reason) when image completes

    Returns:
        Tuple of (images_pulled, images_failed)
    """
    images = extract_images_from_compose(compose_yaml)
    if not images:
        return (0, 0)

    pulled = 0
    failed = 0

    for idx, image in enumerate(images):
        # Check if already cached
        if check_image_exists_locally(image):
            if on_image_complete:
                on_image_complete(image, True, "cached")
            pulled += 1
            continue

        # Need to pull
        if on_image_start:
            on_image_start(image, idx + 1, len(images))

        success = pull_image_with_progress(
            image,
            on_progress=on_image_progress,
        )

        if success:
            if on_image_complete:
                on_image_complete(image, True, "pulled")
            pulled += 1
        else:
            if on_image_complete:
                on_image_complete(image, False, "failed")
            failed += 1

    return (pulled, failed)
