"""Unit tests for hte_cli/image_utils.py."""

import subprocess
from unittest.mock import MagicMock, patch


from hte_cli.image_utils import (
    check_image_exists_locally,
    extract_images_from_compose,
    prepull_compose_images,
    pull_image_with_progress,
    get_host_architecture,
    get_host_docker_platform,
    get_image_architecture,
    check_image_architecture_matches_host,
    is_running_in_linux_vm_on_arm,
    remove_image,
    fix_image_architecture,
)


class TestExtractImagesFromCompose:
    """Tests for extract_images_from_compose."""

    def test_extracts_image_names(self):
        """Extracts all image names from services."""
        compose_yaml = """
services:
  default:
    image: jackpayne123/nyuctf-agent:v2
  db:
    image: postgres:15
  cache:
    image: redis:7-alpine
"""
        images = extract_images_from_compose(compose_yaml)
        assert len(images) == 3
        assert "jackpayne123/nyuctf-agent:v2" in images
        assert "postgres:15" in images
        assert "redis:7-alpine" in images

    def test_handles_missing_services(self):
        """Returns empty list for compose without services key."""
        compose_yaml = """
version: "3"
networks:
  default:
"""
        images = extract_images_from_compose(compose_yaml)
        assert images == []

    def test_handles_malformed_yaml(self):
        """Returns empty list for invalid YAML."""
        compose_yaml = "this is not: valid: yaml: {{{{"
        images = extract_images_from_compose(compose_yaml)
        assert images == []

    def test_handles_empty_yaml(self):
        """Returns empty list for empty/null YAML."""
        assert extract_images_from_compose("") == []
        assert extract_images_from_compose("null") == []

    def test_handles_services_without_image(self):
        """Skips services that use 'build:' instead of 'image:'."""
        compose_yaml = """
services:
  app:
    build: ./app
  db:
    image: postgres:15
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
"""
        images = extract_images_from_compose(compose_yaml)
        assert images == ["postgres:15"]

    def test_handles_empty_services(self):
        """Returns empty list when services dict is empty."""
        compose_yaml = "services: {}"
        images = extract_images_from_compose(compose_yaml)
        assert images == []

    def test_handles_services_with_null_config(self):
        """Handles services where config is null/None."""
        compose_yaml = """
services:
  app:
  db:
    image: postgres:15
"""
        images = extract_images_from_compose(compose_yaml)
        assert images == ["postgres:15"]


class TestCheckImageExistsLocally:
    """Tests for check_image_exists_locally."""

    @patch("subprocess.run")
    def test_returns_true_when_exists(self, mock_run):
        """True when docker inspect succeeds (returncode=0)."""
        mock_run.return_value = MagicMock(returncode=0)

        result = check_image_exists_locally("nginx:latest")

        assert result is True
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert "docker" in call_args[0][0]
        assert "inspect" in call_args[0][0]
        assert "nginx:latest" in call_args[0][0]

    @patch("subprocess.run")
    def test_returns_false_when_not_exists(self, mock_run):
        """False when docker inspect fails."""
        mock_run.return_value = MagicMock(returncode=1)

        result = check_image_exists_locally("nonexistent:image")

        assert result is False

    @patch("subprocess.run")
    def test_returns_false_on_timeout(self, mock_run):
        """False when subprocess times out."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="docker", timeout=10)

        result = check_image_exists_locally("nginx:latest")

        assert result is False

    @patch("subprocess.run")
    def test_returns_false_when_docker_missing(self, mock_run):
        """False when docker command not found."""
        mock_run.side_effect = FileNotFoundError("docker not found")

        result = check_image_exists_locally("nginx:latest")

        assert result is False


class TestPullImageWithProgress:
    """Tests for pull_image_with_progress (with PTY mocking)."""

    @patch("hte_cli.image_utils.os.close")
    @patch("hte_cli.image_utils.os.read")
    @patch("hte_cli.image_utils.select.select")
    @patch("hte_cli.image_utils.subprocess.Popen")
    @patch("hte_cli.image_utils.pty.openpty")
    def test_calls_docker_pull(self, mock_openpty, mock_popen, mock_select, mock_read, mock_close):
        """Invokes correct docker pull command."""
        mock_openpty.return_value = (3, 4)  # master_fd, slave_fd

        mock_process = MagicMock()
        mock_process.poll.side_effect = [None, 0]  # Running, then done
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        mock_select.return_value = ([], [], [])  # No data ready
        mock_read.return_value = b""

        result = pull_image_with_progress("nginx:latest")

        assert result is True
        mock_popen.assert_called_once()
        call_args = mock_popen.call_args
        assert call_args[0][0] == ["docker", "pull", "nginx:latest"]

    @patch("hte_cli.image_utils.os.close")
    @patch("hte_cli.image_utils.os.read")
    @patch("hte_cli.image_utils.select.select")
    @patch("hte_cli.image_utils.subprocess.Popen")
    @patch("hte_cli.image_utils.pty.openpty")
    def test_progress_callback_receives_output(
        self, mock_openpty, mock_popen, mock_select, mock_read, mock_close
    ):
        """Progress callback called with output lines."""
        mock_openpty.return_value = (3, 4)

        mock_process = MagicMock()
        mock_process.poll.side_effect = [None, None, 0]
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        # Simulate output
        mock_select.side_effect = [([3], [], []), ([3], [], []), ([], [], [])]
        mock_read.side_effect = [
            b"abc123: Pulling from library/nginx\r\n",
            b"abc123: Downloading  10MB/50MB\r\n",
            b"",
        ]

        progress_lines = []

        def on_progress(image, line):
            progress_lines.append((image, line))

        result = pull_image_with_progress("nginx:latest", on_progress=on_progress)

        assert result is True
        assert len(progress_lines) > 0
        assert progress_lines[0][0] == "nginx:latest"

    @patch("hte_cli.image_utils.os.close")
    @patch("hte_cli.image_utils.os.read")
    @patch("hte_cli.image_utils.select.select")
    @patch("hte_cli.image_utils.subprocess.Popen")
    @patch("hte_cli.image_utils.pty.openpty")
    def test_returns_true_on_success(
        self, mock_openpty, mock_popen, mock_select, mock_read, mock_close
    ):
        """True when pull succeeds."""
        mock_openpty.return_value = (3, 4)

        mock_process = MagicMock()
        mock_process.poll.return_value = 0  # Immediate success
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        mock_select.return_value = ([], [], [])

        result = pull_image_with_progress("nginx:latest")

        assert result is True

    @patch("hte_cli.image_utils.os.close")
    @patch("hte_cli.image_utils.os.read")
    @patch("hte_cli.image_utils.select.select")
    @patch("hte_cli.image_utils.subprocess.Popen")
    @patch("hte_cli.image_utils.pty.openpty")
    def test_returns_false_on_failure(
        self, mock_openpty, mock_popen, mock_select, mock_read, mock_close
    ):
        """False when pull fails."""
        mock_openpty.return_value = (3, 4)

        mock_process = MagicMock()
        mock_process.poll.return_value = 1  # Failure
        mock_process.returncode = 1
        mock_popen.return_value = mock_process

        mock_select.return_value = ([], [], [])

        result = pull_image_with_progress("nonexistent:image")

        assert result is False

    @patch("hte_cli.image_utils.os.close")
    @patch("hte_cli.image_utils.os.read")
    @patch("hte_cli.image_utils.select.select")
    @patch("hte_cli.image_utils.subprocess.Popen")
    @patch("hte_cli.image_utils.pty.openpty")
    def test_complete_callback_called(
        self, mock_openpty, mock_popen, mock_select, mock_read, mock_close
    ):
        """on_complete callback called with result."""
        mock_openpty.return_value = (3, 4)

        mock_process = MagicMock()
        mock_process.poll.return_value = 0
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        mock_select.return_value = ([], [], [])

        complete_calls = []

        def on_complete(image, success):
            complete_calls.append((image, success))

        pull_image_with_progress("nginx:latest", on_complete=on_complete)

        assert len(complete_calls) == 1
        assert complete_calls[0] == ("nginx:latest", True)

    @patch("hte_cli.image_utils.pty.openpty")
    def test_returns_false_on_exception(self, mock_openpty):
        """False when exception raised."""
        mock_openpty.side_effect = OSError("PTY creation failed")

        complete_calls = []

        def on_complete(image, success):
            complete_calls.append((image, success))

        result = pull_image_with_progress("nginx:latest", on_complete=on_complete)

        assert result is False
        assert len(complete_calls) == 1
        assert complete_calls[0] == ("nginx:latest", False)


class TestPrepullComposeImages:
    """Tests for prepull_compose_images."""

    @patch("hte_cli.image_utils.pull_image_with_progress")
    @patch("hte_cli.image_utils.check_image_exists_locally")
    def test_skips_cached_images(self, mock_check, mock_pull):
        """Skips images that are already cached."""
        mock_check.return_value = True  # All cached

        compose_yaml = """
services:
  app:
    image: nginx:latest
  db:
    image: postgres:15
"""
        complete_calls = []

        def on_complete(image, success, reason):
            complete_calls.append((image, success, reason))

        pulled, failed = prepull_compose_images(compose_yaml, on_image_complete=on_complete)

        assert pulled == 2
        assert failed == 0
        mock_pull.assert_not_called()  # No pulls needed
        assert all(c[2] == "cached" for c in complete_calls)

    @patch("hte_cli.image_utils.pull_image_with_progress")
    @patch("hte_cli.image_utils.check_image_exists_locally")
    def test_pulls_missing_images(self, mock_check, mock_pull):
        """Pulls images that are not cached."""
        mock_check.return_value = False  # Not cached
        mock_pull.return_value = True  # Pull succeeds

        compose_yaml = """
services:
  app:
    image: nginx:latest
"""
        start_calls = []
        complete_calls = []

        def on_start(image, idx, total):
            start_calls.append((image, idx, total))

        def on_complete(image, success, reason):
            complete_calls.append((image, success, reason))

        pulled, failed = prepull_compose_images(
            compose_yaml,
            on_image_start=on_start,
            on_image_complete=on_complete,
        )

        assert pulled == 1
        assert failed == 0
        mock_pull.assert_called_once()
        assert start_calls[0] == ("nginx:latest", 1, 1)
        assert complete_calls[0] == ("nginx:latest", True, "pulled")

    @patch("hte_cli.image_utils.pull_image_with_progress")
    @patch("hte_cli.image_utils.check_image_exists_locally")
    def test_counts_failed_pulls(self, mock_check, mock_pull):
        """Counts failed pull attempts."""
        mock_check.return_value = False
        mock_pull.return_value = False  # Pull fails

        compose_yaml = """
services:
  app:
    image: nonexistent:image
"""
        complete_calls = []

        def on_complete(image, success, reason):
            complete_calls.append((image, success, reason))

        pulled, failed = prepull_compose_images(compose_yaml, on_image_complete=on_complete)

        assert pulled == 0
        assert failed == 1
        assert complete_calls[0] == ("nonexistent:image", False, "failed")

    def test_handles_empty_compose(self):
        """Returns (0, 0) for compose with no images."""
        compose_yaml = "services: {}"

        pulled, failed = prepull_compose_images(compose_yaml)

        assert pulled == 0
        assert failed == 0

    @patch("hte_cli.image_utils.pull_image_with_progress")
    @patch("hte_cli.image_utils.check_image_exists_locally")
    def test_mixed_cached_and_pulled(self, mock_check, mock_pull):
        """Handles mix of cached and pulled images."""
        # First image cached, second not
        mock_check.side_effect = [True, False]
        mock_pull.return_value = True

        compose_yaml = """
services:
  cached:
    image: nginx:latest
  new:
    image: postgres:15
"""
        pulled, failed = prepull_compose_images(compose_yaml)

        assert pulled == 2
        assert failed == 0
        mock_pull.assert_called_once()  # Only one pull


class TestGetHostArchitecture:
    """Tests for get_host_architecture."""

    @patch("hte_cli.image_utils.platform.machine")
    def test_returns_platform_machine(self, mock_machine):
        """Returns the result of platform.machine()."""
        mock_machine.return_value = "x86_64"
        assert get_host_architecture() == "x86_64"

        mock_machine.return_value = "aarch64"
        assert get_host_architecture() == "aarch64"


class TestGetHostDockerPlatform:
    """Tests for get_host_docker_platform."""

    @patch("hte_cli.image_utils.platform.machine")
    def test_returns_linux_amd64_for_x86(self, mock_machine):
        """Maps x86_64 to linux/amd64."""
        mock_machine.return_value = "x86_64"
        assert get_host_docker_platform() == "linux/amd64"

    @patch("hte_cli.image_utils.platform.machine")
    def test_returns_linux_arm64_for_aarch64(self, mock_machine):
        """Maps aarch64 to linux/arm64."""
        mock_machine.return_value = "aarch64"
        assert get_host_docker_platform() == "linux/arm64"

    @patch("hte_cli.image_utils.platform.machine")
    def test_returns_linux_arm64_for_arm64(self, mock_machine):
        """Maps arm64 to linux/arm64."""
        mock_machine.return_value = "arm64"
        assert get_host_docker_platform() == "linux/arm64"

    @patch("hte_cli.image_utils.platform.machine")
    def test_returns_none_for_unknown(self, mock_machine):
        """Returns None for unknown architectures."""
        mock_machine.return_value = "i386"
        assert get_host_docker_platform() is None


class TestGetImageArchitecture:
    """Tests for get_image_architecture."""

    @patch("subprocess.run")
    def test_returns_architecture_from_docker(self, mock_run):
        """Returns architecture string from docker inspect."""
        mock_run.return_value = MagicMock(returncode=0, stdout="amd64\n")
        assert get_image_architecture("python:3.12-slim") == "amd64"

    @patch("subprocess.run")
    def test_returns_none_when_image_not_found(self, mock_run):
        """Returns None when image doesn't exist."""
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        assert get_image_architecture("nonexistent:image") is None

    @patch("subprocess.run")
    def test_returns_none_on_timeout(self, mock_run):
        """Returns None on subprocess timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="docker", timeout=10)
        assert get_image_architecture("python:3.12-slim") is None


class TestCheckImageArchitectureMatchesHost:
    """Tests for check_image_architecture_matches_host."""

    @patch("hte_cli.image_utils.get_image_architecture")
    @patch("hte_cli.image_utils.platform.machine")
    def test_matches_when_both_amd64(self, mock_machine, mock_get_arch):
        """Returns True when both image and host are amd64."""
        mock_machine.return_value = "x86_64"
        mock_get_arch.return_value = "amd64"

        matches, image_arch, host_arch = check_image_architecture_matches_host("python:3.12-slim")

        assert matches is True
        assert image_arch == "amd64"
        assert host_arch == "x86_64"

    @patch("hte_cli.image_utils.get_image_architecture")
    @patch("hte_cli.image_utils.platform.machine")
    def test_matches_when_both_arm64(self, mock_machine, mock_get_arch):
        """Returns True when both image and host are arm64."""
        mock_machine.return_value = "aarch64"
        mock_get_arch.return_value = "arm64"

        matches, image_arch, host_arch = check_image_architecture_matches_host("python:3.12-slim")

        assert matches is True
        assert image_arch == "arm64"
        assert host_arch == "aarch64"

    @patch("hte_cli.image_utils.get_image_architecture")
    @patch("hte_cli.image_utils.platform.machine")
    def test_mismatch_amd64_on_arm_host(self, mock_machine, mock_get_arch):
        """Returns False when amd64 image on arm64 host."""
        mock_machine.return_value = "aarch64"
        mock_get_arch.return_value = "amd64"

        matches, image_arch, host_arch = check_image_architecture_matches_host("python:3.12-slim")

        assert matches is False
        assert image_arch == "amd64"
        assert host_arch == "aarch64"

    @patch("hte_cli.image_utils.get_image_architecture")
    @patch("hte_cli.image_utils.platform.machine")
    def test_returns_true_when_image_not_cached(self, mock_machine, mock_get_arch):
        """Returns True (no issue) when image isn't cached."""
        mock_machine.return_value = "aarch64"
        mock_get_arch.return_value = None  # Not cached

        matches, image_arch, host_arch = check_image_architecture_matches_host("python:3.12-slim")

        assert matches is True
        assert image_arch is None


class TestIsRunningInLinuxVmOnArm:
    """Tests for is_running_in_linux_vm_on_arm."""

    @patch("hte_cli.image_utils.platform.machine")
    @patch("sys.platform", "linux")
    def test_true_for_linux_aarch64(self, mock_machine):
        """Returns True for Linux on aarch64."""
        mock_machine.return_value = "aarch64"
        assert is_running_in_linux_vm_on_arm() is True

    @patch("hte_cli.image_utils.platform.machine")
    @patch("sys.platform", "linux")
    def test_true_for_linux_arm64(self, mock_machine):
        """Returns True for Linux on arm64."""
        mock_machine.return_value = "arm64"
        assert is_running_in_linux_vm_on_arm() is True

    @patch("hte_cli.image_utils.platform.machine")
    @patch("sys.platform", "darwin")
    def test_false_for_macos_arm64(self, mock_machine):
        """Returns False for macOS even on ARM."""
        mock_machine.return_value = "arm64"
        assert is_running_in_linux_vm_on_arm() is False

    @patch("hte_cli.image_utils.platform.machine")
    @patch("sys.platform", "linux")
    def test_false_for_linux_x86(self, mock_machine):
        """Returns False for Linux on x86."""
        mock_machine.return_value = "x86_64"
        assert is_running_in_linux_vm_on_arm() is False


class TestRemoveImage:
    """Tests for remove_image."""

    @patch("subprocess.run")
    def test_returns_true_on_success(self, mock_run):
        """Returns True when docker rmi succeeds."""
        mock_run.return_value = MagicMock(returncode=0)
        assert remove_image("python:3.12-slim") is True

    @patch("subprocess.run")
    def test_returns_false_on_failure(self, mock_run):
        """Returns False when docker rmi fails."""
        mock_run.return_value = MagicMock(returncode=1)
        assert remove_image("python:3.12-slim") is False


class TestFixImageArchitecture:
    """Tests for fix_image_architecture."""

    @patch("hte_cli.image_utils.pull_image_with_progress")
    @patch("hte_cli.image_utils.remove_image")
    @patch("hte_cli.image_utils.check_image_architecture_matches_host")
    def test_no_fix_needed_when_matches(self, mock_check, mock_remove, mock_pull):
        """Returns (False, message) when architecture already matches."""
        mock_check.return_value = (True, "arm64", "aarch64")

        needed_fix, message = fix_image_architecture("python:3.12-slim")

        assert needed_fix is False
        assert "architecture OK" in message
        mock_remove.assert_not_called()
        mock_pull.assert_not_called()

    @patch("hte_cli.image_utils.pull_image_with_progress")
    @patch("hte_cli.image_utils.remove_image")
    @patch("hte_cli.image_utils.check_image_architecture_matches_host")
    @patch("hte_cli.image_utils.platform.machine")
    def test_fixes_mismatch_by_repulling(self, mock_machine, mock_check, mock_remove, mock_pull):
        """Removes and re-pulls when architecture mismatches."""
        mock_machine.return_value = "aarch64"
        mock_check.return_value = (False, "amd64", "aarch64")  # Mismatch!
        mock_remove.return_value = True
        mock_pull.return_value = True

        needed_fix, message = fix_image_architecture("python:3.12-slim")

        assert needed_fix is True
        assert "re-pulled" in message
        mock_remove.assert_called_once_with("python:3.12-slim")
        mock_pull.assert_called_once_with("python:3.12-slim", platform="linux/arm64")

    @patch("hte_cli.image_utils.pull_image_with_progress")
    @patch("hte_cli.image_utils.remove_image")
    @patch("hte_cli.image_utils.check_image_architecture_matches_host")
    @patch("hte_cli.image_utils.platform.machine")
    def test_returns_false_when_repull_fails(self, mock_machine, mock_check, mock_remove, mock_pull):
        """Returns (False, message) when re-pull fails."""
        mock_machine.return_value = "aarch64"
        mock_check.return_value = (False, "amd64", "aarch64")
        mock_remove.return_value = True
        mock_pull.return_value = False  # Pull fails

        needed_fix, message = fix_image_architecture("python:3.12-slim")

        assert needed_fix is False
        assert "failed to re-pull" in message
