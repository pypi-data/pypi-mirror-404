"""Inspect AI runner for CLI task execution.

Wraps Inspect's human_cli agent to run tasks downloaded from the API.
"""

import logging
import os
import tempfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any
from zipfile import ZipFile

import yaml

from inspect_ai import Task, eval as inspect_eval
from inspect_ai.agent import human_cli
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_ai.log import EvalLog

from .scorers import ScorerType, get_scorer

logger = logging.getLogger(__name__)


def _get_file_dest_from_compose(compose_path: Path) -> str:
    """Extract working_dir from compose file to determine file mount destination.

    The compose file is the source of truth for where the container's working
    directory is set. We mount task files there so they're available to the user.
    Falls back to /root if no working_dir is specified.
    """
    if not compose_path.exists():
        return "/root"

    try:
        compose = yaml.safe_load(compose_path.read_text())
        services = compose.get("services", {})

        # Try 'default' service first (Inspect convention), then first service
        for service_name in ["default", next(iter(services), None)]:
            if service_name and service_name in services:
                working_dir = services[service_name].get("working_dir")
                if working_dir:
                    logger.debug(f"Found working_dir in compose: {working_dir}")
                    return working_dir

    except Exception as e:
        logger.warning(f"Failed to parse compose file for working_dir: {e}")

    return "/root"


@dataclass
class TaskResult:
    """Result from running a task via Inspect."""

    answer: str | None
    time_seconds: float
    score: float | None
    score_binarized: int | None
    eval_log_path: Path | None


def extract_result_from_eval_log(eval_log: EvalLog) -> TaskResult:
    """
    Extract timing, answer, and score from an Inspect EvalLog.

    Uses the HumanAgentState stored by human_cli.
    """
    answer = None
    time_seconds = 0.0
    score = None
    score_binarized = None

    if not eval_log.samples:
        logger.warning("No samples in eval log")
        return TaskResult(
            answer=None,
            time_seconds=0.0,
            score=None,
            score_binarized=None,
            eval_log_path=None,
        )

    # Get the first (and typically only) sample
    sample = eval_log.samples[0]

    # Extract HumanAgentState from sample store
    if hasattr(sample, "store") and sample.store:
        store = sample.store
        prefix = "HumanAgentState:"

        if hasattr(store, "get"):
            answer = store.get(f"{prefix}answer")
            accumulated_time = store.get(f"{prefix}accumulated_time", 0.0) or 0.0
            time_seconds = accumulated_time

    # Fallback: get answer from output completion
    if answer is None and hasattr(sample, "output"):
        if hasattr(sample.output, "completion"):
            answer = sample.output.completion

    # Get score from sample
    if hasattr(sample, "scores") and sample.scores:
        for scorer_name, score_obj in sample.scores.items():
            if hasattr(score_obj, "value"):
                value = score_obj.value
                if isinstance(value, (int, float)):
                    score = float(value)
                    score_binarized = 1 if score >= 0.5 else 0
                elif isinstance(value, str):
                    value_lower = value.lower()
                    if value_lower in ("c", "correct", "yes", "pass", "1"):
                        score = 1.0
                        score_binarized = 1
                    elif value_lower in ("i", "incorrect", "no", "fail", "0"):
                        score = 0.0
                        score_binarized = 0
                break

    return TaskResult(
        answer=answer,
        time_seconds=time_seconds,
        score=score,
        score_binarized=score_binarized,
        eval_log_path=None,
    )


class TaskRunner:
    """Runs tasks using Inspect's human_cli agent."""

    def __init__(
        self,
        work_dir: Path | None = None,
    ):
        """
        Initialize the task runner.

        Args:
            work_dir: Working directory for task files. If None, uses temp dir.
        """
        self.work_dir = work_dir or Path(tempfile.mkdtemp(prefix="hte-cli-"))
        self.work_dir.mkdir(parents=True, exist_ok=True)

    def setup_task_files(
        self,
        task_id: str,
        files_zip: bytes | None = None,
        compose_yaml: str | None = None,
    ) -> Path:
        """
        Set up task files in the working directory.

        Args:
            task_id: Task identifier
            files_zip: Optional zip archive of task files
            compose_yaml: Optional Docker Compose content

        Returns:
            Path to the task directory
        """
        # Create task-specific directory
        safe_task_id = task_id.replace("/", "_").replace(":", "_")
        task_dir = self.work_dir / safe_task_id
        task_dir.mkdir(parents=True, exist_ok=True)

        # Extract files if provided
        if files_zip:
            with ZipFile(BytesIO(files_zip)) as zf:
                zf.extractall(task_dir)
            logger.info(f"Extracted task files to {task_dir}")

        # Write compose file if provided
        if compose_yaml:
            compose_path = task_dir / "compose.yaml"
            compose_path.write_text(compose_yaml)
            logger.info(f"Wrote compose.yaml to {compose_path}")

        return task_dir

    def create_inspect_task(
        self,
        task_id: str,
        instructions: str,
        target: str = "",
        sandbox_config: tuple[str, str] | None = None,
        files: dict[str, str] | None = None,
        scorer_type: str = "flag_includes",
        intermediate_scoring: bool = True,
    ) -> Task:
        """
        Create an Inspect Task for human_cli execution.

        Args:
            task_id: Task identifier
            instructions: Task instructions for the human
            target: Expected answer (for scoring)
            sandbox_config: Optional (type, config_path) for Docker sandbox
            files: Optional dict mapping dest paths to source paths for mounting
            scorer_type: Scorer type from backend (determines scoring behavior)
            intermediate_scoring: Whether task score is available client-side

        Returns:
            Inspect Task configured for human_cli
        """
        # Create sample with files to mount into sandbox
        sample = Sample(
            id=task_id,
            input=instructions,
            target=target,
            sandbox=sandbox_config,
            files=files or {},
        )

        # Get scorer based on type (matches Bench class implementations)
        scorer = get_scorer(ScorerType(scorer_type), target)

        # Create task with human_cli agent
        return Task(
            dataset=MemoryDataset([sample]),
            solver=human_cli(
                answer=True,
                intermediate_scoring=intermediate_scoring,
                record_session=True,
            ),
            scorer=scorer,
        )

    def run(
        self,
        task_id: str,
        instructions: str,
        target: str = "",
        compose_yaml: str | None = None,
        files_zip: bytes | None = None,
        log_dir: Path | None = None,
        scorer_type: str = "flag_includes",
        intermediate_scoring: bool = True,
    ) -> TaskResult:
        """
        Run a task using Inspect's human_cli.

        Args:
            task_id: Task identifier
            instructions: Task instructions
            target: Expected answer for scoring
            compose_yaml: Docker Compose content
            files_zip: Task files as zip
            log_dir: Directory for eval logs
            scorer_type: Scorer type from backend (determines scoring behavior)
            intermediate_scoring: Whether task score is available client-side

        Returns:
            TaskResult with answer, timing, and score
        """
        # Set up task files
        task_dir = self.setup_task_files(task_id, files_zip, compose_yaml)

        # Determine sandbox config
        sandbox_config = None
        compose_path = task_dir / "compose.yaml"
        if compose_path.exists():
            sandbox_config = ("docker", str(compose_path))
            logger.info(f"Using Docker sandbox: {compose_path}")

        # Collect files to mount into sandbox (exclude compose.yaml and README.md)
        # Destination is the container's working_dir from compose.yaml
        file_dest_base = _get_file_dest_from_compose(compose_path)

        files_to_mount: dict[str, str] = {}
        excluded_files = {"compose.yaml", "README.md", "instructions.txt", "logs"}

        # Walk directory tree recursively to handle nested file structures
        # (e.g., cybench tasks with blog/, nginx/, rcache/ subdirectories)
        for file_path in task_dir.rglob("*"):
            if not file_path.is_file():
                continue
            # Get relative path from task_dir
            rel_path = file_path.relative_to(task_dir)
            # Skip excluded files (check both filename and first directory component)
            if rel_path.name in excluded_files or rel_path.parts[0] in excluded_files:
                continue
            # Build destination path preserving directory structure
            dest_path = f"{file_dest_base}/{rel_path}"
            files_to_mount[dest_path] = str(file_path)
            logger.info(f"Will mount file: {rel_path} -> {dest_path}")

        # Create the Inspect task
        inspect_task = self.create_inspect_task(
            task_id=task_id,
            instructions=instructions,
            target=target,
            sandbox_config=sandbox_config,
            files=files_to_mount if files_to_mount else None,
            scorer_type=scorer_type,
            intermediate_scoring=intermediate_scoring,
        )

        # Set up log directory
        if log_dir is None:
            log_dir = task_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        # Change to task directory for relative paths in compose
        original_cwd = os.getcwd()
        try:
            os.chdir(task_dir)

            # Run the evaluation
            logger.info(f"Starting Inspect evaluation for {task_id}")
            results = inspect_eval(
                inspect_task,
                log_dir=str(log_dir),
                display="plain",
            )

            if not results:
                logger.error("No results returned from Inspect")
                return TaskResult(
                    answer=None,
                    time_seconds=0.0,
                    score=None,
                    score_binarized=None,
                    eval_log_path=None,
                )

            # Get the eval log
            eval_log = results[0] if isinstance(results, list) else results

            # Check for failed evaluation - Inspect returns status="error" or
            # "cancelled" instead of raising exceptions for Docker/sandbox failures
            if hasattr(eval_log, "status") and eval_log.status != "success":
                error_msg = f"Task evaluation failed with status: {eval_log.status}"
                if hasattr(eval_log, "error") and eval_log.error:
                    error_msg += f". Error: {eval_log.error.message}"
                raise RuntimeError(error_msg)

            # Extract result
            result = extract_result_from_eval_log(eval_log)

            # Find the log file
            log_files = list(log_dir.glob("*.eval"))
            if log_files:
                result.eval_log_path = log_files[-1]  # Most recent
                logger.info(f"Eval log saved to {result.eval_log_path}")

            return result

        finally:
            os.chdir(original_cwd)

    def run_from_assignment(
        self,
        assignment: dict[str, Any],
        compose_yaml: str | None = None,
        files_zip: bytes | None = None,
        log_dir: Path | None = None,
    ) -> TaskResult:
        """
        Run a task from an assignment dict (as returned by API).

        Args:
            assignment: Assignment data from API
            compose_yaml: Docker Compose content
            files_zip: Task files as zip
            log_dir: Directory for eval logs

        Returns:
            TaskResult with answer, timing, and score
        """
        task_id = assignment["task_id"]
        task_data = assignment.get("task", {})
        instructions = task_data.get("instructions", "")
        # Target comes from backend (preferred) or can be extracted from metadata
        target = task_data.get("target", "")
        if not target or target == "?":
            # Fallback to metadata fields for various benchmarks
            meta = task_data.get("metadata", {})
            target = (
                meta.get("target", "")
                or meta.get("solution_flag", "")  # intercode-ctf
                or meta.get("flag", "")  # cybench, nyuctf
                or meta.get("answer", "")  # generic
            )

        # Extract scoring configuration from backend (required fields)
        scorer_type = task_data.get("scorer_type")
        if not scorer_type:
            raise ValueError(
                f"Backend did not return scorer_type for task {task_id}. "
                "This is a backend configuration error."
            )
        intermediate_scoring = task_data.get("intermediate_scoring")
        if intermediate_scoring is None:
            raise ValueError(
                f"Backend did not return intermediate_scoring for task {task_id}. "
                "This is a backend configuration error."
            )

        return self.run(
            task_id=task_id,
            instructions=instructions,
            target=target,
            compose_yaml=compose_yaml,
            files_zip=files_zip,
            log_dir=log_dir,
            scorer_type=scorer_type,
            intermediate_scoring=intermediate_scoring,
        )

    def cleanup(self) -> None:
        """Clean up temporary files."""
        import shutil

        if self.work_dir.exists() and str(self.work_dir).startswith(tempfile.gettempdir()):
            shutil.rmtree(self.work_dir)
            logger.info(f"Cleaned up work directory: {self.work_dir}")
