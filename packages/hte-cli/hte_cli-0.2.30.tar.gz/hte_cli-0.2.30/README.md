# hte-cli

Human Time-to-Completion Evaluation CLI - A tool for running assigned cybersecurity tasks with timing and result tracking.

## Installation

```bash
# Recommended (pipx)
pipx install hte-cli

# Or with pip
pip install hte-cli
```

## Quick Start

1. **Login** (get credentials from your coordinator):
   ```bash
   hte-cli auth login
   ```

2. **View your assigned tasks**:
   ```bash
   hte-cli tasks list
   ```

3. **Run a task**:
   ```bash
   hte-cli tasks run
   ```

## Commands

- `hte-cli auth login` - Authenticate with the API
- `hte-cli auth status` - Check authentication status
- `hte-cli tasks list` - List your pending tasks
- `hte-cli tasks run [TASK_ID]` - Run a task (defaults to highest priority)
- `hte-cli tasks pull-images` - Pre-pull Docker images for upcoming tasks
- `hte-cli version` - Show version info

## System Requirements

### All Platforms

- Python 3.11+
- Docker Engine >= 24.0.6
- Docker Compose >= 2.21.0 (included in Docker Desktop 4.25+)

### Windows

- Docker Desktop with WSL2 backend enabled
- WSL2 installed and configured ([Microsoft docs](https://learn.microsoft.com/en-us/windows/wsl/install))

### macOS

- Docker Desktop (Intel or Apple Silicon)
- Note: Apple Silicon (M1/M2/M3) runs x86 containers via emulation - expect slightly slower performance

### Linux

- Docker Engine >= 24.0.6 with Compose plugin
- User added to docker group: `sudo usermod -aG docker $USER` (log out and back in after)

### Verify Docker Setup

```bash
# Check Docker Engine version (need >= 24.0.6)
docker version --format '{{.Client.Version}}'

# Check Docker Compose version (need >= 2.21.0)
docker compose version --short

# Test container can start
docker run --rm hello-world
```

If your Docker Compose version is too old, update Docker Desktop or install the latest compose plugin:
```bash
# Linux: Update compose plugin
sudo apt-get update && sudo apt-get install docker-compose-plugin
```

## Configuration

Set `HTE_API_URL` environment variable to use a custom API endpoint:

```bash
export HTE_API_URL="http://your-server.com/api/v1/cli"
```

## Support

For issues, contact your study coordinator or open an issue at:
https://github.com/sean-peters-au/lyptus-mono

---

## Developer Notes

This CLI is a thin wrapper with no consequential research decisions. It:
- Wraps Inspect AI's `human_cli` agent for task execution
- Syncs results to the backend API
- Handles authentication via OAuth-style code exchange

The research-relevant code lives elsewhere:
- **Task sampling**: `scripts/sample_tasks_for_trials.py`
- **Scoring criteria**: `src/human_ttc_eval/datasets/*/`
- **Methodology**: `docs/methodology/human-expert-methodology-guide.md`
