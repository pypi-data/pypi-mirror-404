"""Unit tests for hte_cli/runner.py."""

from unittest.mock import MagicMock, patch

import pytest

from hte_cli.runner import (
    TaskResult,
    TaskRunner,
    _get_file_dest_from_compose,
    extract_result_from_eval_log,
)


class TestGetFileDestFromCompose:
    """Tests for _get_file_dest_from_compose."""

    def test_extracts_working_dir_from_default_service(self, tmp_path):
        """Gets working_dir from 'default' service."""
        compose_path = tmp_path / "compose.yaml"
        compose_path.write_text("""
services:
  default:
    image: test:latest
    working_dir: /home/ctfplayer
  other:
    image: other:latest
    working_dir: /other
""")
        result = _get_file_dest_from_compose(compose_path)
        assert result == "/home/ctfplayer"

    def test_extracts_working_dir_from_first_service(self, tmp_path):
        """Falls back to first service when no 'default' service."""
        compose_path = tmp_path / "compose.yaml"
        compose_path.write_text("""
services:
  app:
    image: nginx:latest
    working_dir: /var/www
  db:
    image: postgres:15
""")
        result = _get_file_dest_from_compose(compose_path)
        assert result == "/var/www"

    def test_returns_root_when_no_working_dir(self, tmp_path):
        """Returns '/root' when no working_dir specified."""
        compose_path = tmp_path / "compose.yaml"
        compose_path.write_text("""
services:
  default:
    image: nginx:latest
""")
        result = _get_file_dest_from_compose(compose_path)
        assert result == "/root"

    def test_returns_root_for_missing_file(self, tmp_path):
        """Returns '/root' when compose file doesn't exist."""
        compose_path = tmp_path / "nonexistent.yaml"
        result = _get_file_dest_from_compose(compose_path)
        assert result == "/root"

    def test_handles_malformed_yaml(self, tmp_path):
        """Returns '/root' for invalid YAML."""
        compose_path = tmp_path / "compose.yaml"
        compose_path.write_text("this is not: valid: yaml: {{{{")
        result = _get_file_dest_from_compose(compose_path)
        assert result == "/root"

    def test_handles_empty_services(self, tmp_path):
        """Returns '/root' when services dict is empty."""
        compose_path = tmp_path / "compose.yaml"
        compose_path.write_text("services: {}")
        result = _get_file_dest_from_compose(compose_path)
        assert result == "/root"


class TestExtractResultFromEvalLog:
    """Tests for extract_result_from_eval_log."""

    def test_extracts_answer_from_store(self, mock_eval_log):
        """Gets answer from HumanAgentState:answer in store."""
        result = extract_result_from_eval_log(mock_eval_log)
        assert result.answer == "flag{test_flag}"

    def test_extracts_time_from_store(self, mock_eval_log):
        """Gets accumulated_time from store."""
        result = extract_result_from_eval_log(mock_eval_log)
        assert result.time_seconds == 120.5

    def test_extracts_score_from_samples(self, mock_eval_log):
        """Gets numeric score from sample.scores."""
        result = extract_result_from_eval_log(mock_eval_log)
        assert result.score == 1.0
        assert result.score_binarized == 1

    def test_handles_string_scores(self, mock_eval_log_string_score):
        """Handles 'C'/'I'/'correct'/'incorrect' string scores."""
        result = extract_result_from_eval_log(mock_eval_log_string_score)
        assert result.score == 1.0
        assert result.score_binarized == 1

    def test_handles_empty_samples(self, mock_eval_log_empty):
        """Returns empty TaskResult for no samples."""
        result = extract_result_from_eval_log(mock_eval_log_empty)
        assert result.answer is None
        assert result.time_seconds == 0.0
        assert result.score is None
        assert result.score_binarized is None

    def test_fallback_to_output_completion(self):
        """Falls back to output.completion when store has no answer."""
        log = MagicMock()
        sample = MagicMock()
        sample.store = {}  # No HumanAgentState:answer
        sample.output = MagicMock()
        sample.output.completion = "fallback answer"
        sample.scores = {}
        log.samples = [sample]

        result = extract_result_from_eval_log(log)
        assert result.answer == "fallback answer"

    def test_handles_score_value_zero(self):
        """Correctly handles score value of 0.0."""
        log = MagicMock()
        sample = MagicMock()
        sample.store = {"HumanAgentState:accumulated_time": 30.0}
        sample.output = MagicMock()
        sample.output.completion = "wrong"

        score_obj = MagicMock()
        score_obj.value = 0.0
        sample.scores = {"accuracy": score_obj}
        log.samples = [sample]

        result = extract_result_from_eval_log(log)
        assert result.score == 0.0
        assert result.score_binarized == 0

    def test_handles_incorrect_string_score(self):
        """Handles 'I' or 'incorrect' string scores."""
        log = MagicMock()
        sample = MagicMock()
        sample.store = {}
        sample.output = MagicMock()
        sample.output.completion = ""

        score_obj = MagicMock()
        score_obj.value = "incorrect"
        sample.scores = {"accuracy": score_obj}
        log.samples = [sample]

        result = extract_result_from_eval_log(log)
        assert result.score == 0.0
        assert result.score_binarized == 0


class TestScoringConfigValidation:
    """Tests for run_from_assignment validation of scoring config."""

    def test_missing_scorer_type_raises_error(self):
        """Raises ValueError when scorer_type is None."""
        runner = TaskRunner()
        assignment = {
            "task_id": "test-task",
            "task": {
                "instructions": "Do something",
                "target": "flag{test}",
                "scorer_type": None,  # Missing
                "intermediate_scoring": True,
            },
        }

        with pytest.raises(ValueError) as exc_info:
            runner.run_from_assignment(assignment)

        assert "scorer_type" in str(exc_info.value)
        assert "backend configuration error" in str(exc_info.value).lower()
        runner.cleanup()

    def test_missing_intermediate_scoring_raises_error(self):
        """Raises ValueError when intermediate_scoring is None."""
        runner = TaskRunner()
        assignment = {
            "task_id": "test-task",
            "task": {
                "instructions": "Do something",
                "target": "flag{test}",
                "scorer_type": "flag_includes",
                "intermediate_scoring": None,  # Missing
            },
        }

        with pytest.raises(ValueError) as exc_info:
            runner.run_from_assignment(assignment)

        assert "intermediate_scoring" in str(exc_info.value)
        assert "backend configuration error" in str(exc_info.value).lower()
        runner.cleanup()

    def test_scorer_type_missing_key_raises_error(self):
        """Raises ValueError when scorer_type key is missing entirely."""
        runner = TaskRunner()
        assignment = {
            "task_id": "test-task",
            "task": {
                "instructions": "Do something",
                "target": "flag{test}",
                # scorer_type key missing
                "intermediate_scoring": True,
            },
        }

        with pytest.raises(ValueError) as exc_info:
            runner.run_from_assignment(assignment)

        assert "scorer_type" in str(exc_info.value)
        runner.cleanup()


class TestTargetExtraction:
    """Tests for target extraction fallback chain in run_from_assignment."""

    @patch.object(TaskRunner, "run")
    def test_target_from_task_data_preferred(self, mock_run):
        """Target from task_data.target takes precedence over metadata."""
        mock_run.return_value = TaskResult(
            answer="flag", time_seconds=10.0, score=1.0, score_binarized=1, eval_log_path=None
        )

        runner = TaskRunner()
        assignment = {
            "task_id": "test-task",
            "task": {
                "instructions": "Do something",
                "target": "primary_target",  # Should be used
                "metadata": {
                    "solution_flag": "fallback_flag",  # Should be ignored
                },
                "scorer_type": "flag_includes",
                "intermediate_scoring": True,
            },
        }

        runner.run_from_assignment(assignment)

        # Check that run was called with the primary target
        call_kwargs = mock_run.call_args.kwargs
        assert call_kwargs["target"] == "primary_target"
        runner.cleanup()

    @patch.object(TaskRunner, "run")
    def test_target_fallback_to_solution_flag(self, mock_run):
        """Falls back to metadata.solution_flag for intercode-ctf."""
        mock_run.return_value = TaskResult(
            answer="flag", time_seconds=10.0, score=1.0, score_binarized=1, eval_log_path=None
        )

        runner = TaskRunner()
        assignment = {
            "task_id": "intercode-ctf_test",
            "task": {
                "instructions": "Do something",
                "target": "",  # Empty - trigger fallback
                "metadata": {
                    "solution_flag": "flag{solution}",
                },
                "scorer_type": "flag_includes",
                "intermediate_scoring": True,
            },
        }

        runner.run_from_assignment(assignment)

        call_kwargs = mock_run.call_args.kwargs
        assert call_kwargs["target"] == "flag{solution}"
        runner.cleanup()

    @patch.object(TaskRunner, "run")
    def test_target_fallback_to_flag(self, mock_run):
        """Falls back to metadata.flag for cybench/nyuctf."""
        mock_run.return_value = TaskResult(
            answer="flag", time_seconds=10.0, score=1.0, score_binarized=1, eval_log_path=None
        )

        runner = TaskRunner()
        assignment = {
            "task_id": "cybench-test",
            "task": {
                "instructions": "Do something",
                "target": "",  # Empty
                "metadata": {
                    "flag": "flag{cybench}",
                },
                "scorer_type": "flag_includes",
                "intermediate_scoring": True,
            },
        }

        runner.run_from_assignment(assignment)

        call_kwargs = mock_run.call_args.kwargs
        assert call_kwargs["target"] == "flag{cybench}"
        runner.cleanup()

    @patch.object(TaskRunner, "run")
    def test_target_fallback_to_answer(self, mock_run):
        """Falls back to metadata.answer as last resort."""
        mock_run.return_value = TaskResult(
            answer="ans", time_seconds=10.0, score=1.0, score_binarized=1, eval_log_path=None
        )

        runner = TaskRunner()
        assignment = {
            "task_id": "generic-test",
            "task": {
                "instructions": "Do something",
                "target": "",  # Empty
                "metadata": {
                    "answer": "the_answer",
                },
                "scorer_type": "flag_includes",
                "intermediate_scoring": True,
            },
        }

        runner.run_from_assignment(assignment)

        call_kwargs = mock_run.call_args.kwargs
        assert call_kwargs["target"] == "the_answer"
        runner.cleanup()

    @patch.object(TaskRunner, "run")
    def test_target_question_mark_triggers_fallback(self, mock_run):
        """Target of '?' triggers fallback to metadata."""
        mock_run.return_value = TaskResult(
            answer="flag", time_seconds=10.0, score=1.0, score_binarized=1, eval_log_path=None
        )

        runner = TaskRunner()
        assignment = {
            "task_id": "test-task",
            "task": {
                "instructions": "Do something",
                "target": "?",  # Question mark - special case
                "metadata": {
                    "flag": "flag{from_metadata}",
                },
                "scorer_type": "flag_includes",
                "intermediate_scoring": True,
            },
        }

        runner.run_from_assignment(assignment)

        call_kwargs = mock_run.call_args.kwargs
        assert call_kwargs["target"] == "flag{from_metadata}"
        runner.cleanup()


class TestTaskRunnerSetup:
    """Tests for TaskRunner setup_task_files."""

    def test_creates_task_directory(self, tmp_path):
        """Creates task-specific directory."""
        runner = TaskRunner(work_dir=tmp_path)
        task_dir = runner.setup_task_files("test-task-123")

        assert task_dir.exists()
        assert task_dir.name == "test-task-123"
        runner.cleanup()

    def test_sanitizes_task_id(self, tmp_path):
        """Sanitizes task_id with slashes and colons."""
        runner = TaskRunner(work_dir=tmp_path)
        task_dir = runner.setup_task_files("intercode-ctf/general_skills/task_4")

        assert task_dir.exists()
        assert "/" not in task_dir.name
        assert task_dir.name == "intercode-ctf_general_skills_task_4"
        runner.cleanup()

    def test_writes_compose_yaml(self, tmp_path, sample_compose_yaml):
        """Writes compose.yaml when provided."""
        runner = TaskRunner(work_dir=tmp_path)
        task_dir = runner.setup_task_files(
            "test-task",
            compose_yaml=sample_compose_yaml,
        )

        compose_path = task_dir / "compose.yaml"
        assert compose_path.exists()
        assert "jackpayne123/nyuctf-agent:v2" in compose_path.read_text()
        runner.cleanup()

    def test_extracts_zip_files(self, tmp_path):
        """Extracts files from zip archive."""
        import io
        import zipfile

        # Create a test zip
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr("test_file.txt", "test content")
            zf.writestr("subdir/nested.txt", "nested content")
        zip_bytes = zip_buffer.getvalue()

        runner = TaskRunner(work_dir=tmp_path)
        task_dir = runner.setup_task_files("test-task", files_zip=zip_bytes)

        assert (task_dir / "test_file.txt").exists()
        assert (task_dir / "test_file.txt").read_text() == "test content"
        assert (task_dir / "subdir" / "nested.txt").exists()
        runner.cleanup()
