"""Shared fixtures for unit tests."""

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def sample_compose_yaml():
    """Valid Docker Compose YAML with multiple services."""
    return """
services:
  default:
    image: jackpayne123/nyuctf-agent:v2
    working_dir: /home/ctfplayer
  db:
    image: postgres:15
  local_build:
    build: ./app
"""


@pytest.fixture
def sample_compose_yaml_no_default():
    """Compose YAML where first service is not named 'default'."""
    return """
services:
  app:
    image: nginx:latest
    working_dir: /var/www
  db:
    image: postgres:15
"""


@pytest.fixture
def sample_compose_yaml_no_working_dir():
    """Compose YAML without working_dir specified."""
    return """
services:
  default:
    image: nginx:latest
"""


@pytest.fixture
def mock_eval_log():
    """Mock EvalLog with sample data for extract_result_from_eval_log."""
    log = MagicMock()

    # Create mock sample with store
    sample = MagicMock()
    sample.store = {
        "HumanAgentState:answer": "flag{test_flag}",
        "HumanAgentState:accumulated_time": 120.5,
    }

    # Create mock score
    score_obj = MagicMock()
    score_obj.value = 1.0
    sample.scores = {"accuracy": score_obj}

    # Create mock output
    sample.output = MagicMock()
    sample.output.completion = "flag{test_flag}"

    log.samples = [sample]
    log.status = "success"

    return log


@pytest.fixture
def mock_eval_log_empty():
    """Mock EvalLog with no samples."""
    log = MagicMock()
    log.samples = []
    log.status = "success"
    return log


@pytest.fixture
def mock_eval_log_string_score():
    """Mock EvalLog with string score values."""
    log = MagicMock()

    sample = MagicMock()
    sample.store = {
        "HumanAgentState:answer": "correct answer",
        "HumanAgentState:accumulated_time": 60.0,
    }

    score_obj = MagicMock()
    score_obj.value = "C"  # String score
    sample.scores = {"accuracy": score_obj}
    sample.output = MagicMock()
    sample.output.completion = "correct answer"

    log.samples = [sample]
    return log


@pytest.fixture
def mock_task_state():
    """Mock TaskState for scorer tests."""
    state = MagicMock()

    # Mock message with content
    message = MagicMock()
    message.content = "Some output content"
    message.tool_calls = None

    state.messages = [message]
    state.output = MagicMock()
    state.output.completion = ""

    return state


@pytest.fixture
def mock_task_state_with_flag():
    """Mock TaskState containing the cybergym flag."""
    state = MagicMock()

    message = MagicMock()
    message.content = "Output: flag{3xpl017_cyb3r6ym}"
    message.tool_calls = None

    state.messages = [message]
    state.output = MagicMock()
    state.output.completion = ""

    return state


@pytest.fixture
def mock_task_state_with_submit():
    """Mock TaskState where submit.sh was called."""
    state = MagicMock()

    message = MagicMock()
    message.content = "Running submission..."

    # Mock tool call for submit.sh
    tool_call = MagicMock()
    tool_call.function = "bash"
    tool_call.arguments = {"cmd": "./submit.sh poc.py"}
    message.tool_calls = [tool_call]

    state.messages = [message]
    state.output = MagicMock()
    state.output.completion = ""

    return state


@pytest.fixture
def mock_task_state_cvebench_success():
    """Mock TaskState with CVEBench success indicator."""
    state = MagicMock()

    message = MagicMock()
    message.content = '{"status": true, "message": "Exploit successful"}'

    state.messages = [message]
    state.output = MagicMock()
    state.output.completion = ""

    return state
