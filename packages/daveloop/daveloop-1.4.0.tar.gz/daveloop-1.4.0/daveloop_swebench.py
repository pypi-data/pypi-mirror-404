#!/usr/bin/env python3
"""
DaveLoop SWE-bench Runner
Evaluates DaveLoop agent against SWE-bench benchmark tasks.
"""

import subprocess
import sys
import os
import json
import argparse
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import tempfile

# Import DaveLoop components
from daveloop import (
    Colors as C, print_header_box, print_section, print_status,
    print_success_box, print_error_box, print_warning_box,
    run_claude_code, check_exit_condition, SIGNAL_RESOLVED
)

# Configuration
SCRIPT_DIR = Path(__file__).parent
RESULTS_DIR = SCRIPT_DIR / "swebench_results"
WORK_DIR = SCRIPT_DIR / "swebench_work"
PROMPT_FILE = SCRIPT_DIR / "daveloop_prompt.md"

MAX_ITERATIONS_PER_TASK = 10

BANNER = f"""
{C.BRIGHT_BLUE}{C.BOLD}
   ███████╗██╗    ██╗███████╗      ██████╗ ███████╗███╗   ██╗ ██████╗██╗  ██╗
   ██╔════╝██║    ██║██╔════╝      ██╔══██╗██╔════╝████╗  ██║██╔════╝██║  ██║
   ███████╗██║ █╗ ██║█████╗  █████╗██████╔╝█████╗  ██╔██╗ ██║██║     ███████║
   ╚════██║██║███╗██║██╔══╝  ╚════╝██╔══██╗██╔══╝  ██║╚██╗██║██║     ██╔══██║
   ███████║╚███╔███╔╝███████╗      ██████╔╝███████╗██║ ╚████║╚██████╗██║  ██║
   ╚══════╝ ╚══╝╚══╝ ╚══════╝      ╚═════╝ ╚══════╝╚═╝  ╚═══╝ ╚═════╝╚═╝  ╚═╝
{C.RESET}
{C.WHITE}              DaveLoop × SWE-bench: Real-World Bug Benchmark{C.RESET}
"""

# ============================================================================
# SWE-bench Dataset Interface
# ============================================================================

class SWEBenchTask:
    """Represents a single SWE-bench task."""

    def __init__(self, data: Dict):
        self.instance_id = data.get('instance_id', '')
        self.repo = data.get('repo', '')
        self.base_commit = data.get('base_commit', '')
        self.problem_statement = data.get('problem_statement', '')
        self.hints_text = data.get('hints_text', '')
        self.patch = data.get('patch', '')
        self.test_patch = data.get('test_patch', '')
        self.version = data.get('version', '')
        self.environment_setup_commit = data.get('environment_setup_commit', '')

    def __str__(self):
        return f"{self.instance_id} ({self.repo})"


def load_swebench_dataset(dataset_name: str = "princeton-nlp/SWE-bench_Lite", split: str = "test", limit: Optional[int] = None) -> List[SWEBenchTask]:
    """Load SWE-bench dataset from Hugging Face."""
    try:
        from datasets import load_dataset

        print_section(f"Loading {dataset_name}", C.BRIGHT_CYAN)
        print(f"  {C.CYAN}Downloading dataset from Hugging Face...{C.RESET}")

        dataset = load_dataset(dataset_name, split=split)

        if limit:
            dataset = dataset.select(range(min(limit, len(dataset))))

        tasks = [SWEBenchTask(item) for item in dataset]

        print(f"  {C.GREEN}✓ Loaded {len(tasks)} tasks{C.RESET}\n")
        return tasks

    except ImportError:
        print_error_box("datasets library not installed. Run: pip install datasets")
        sys.exit(1)
    except Exception as e:
        print_error_box(f"Failed to load dataset: {e}")
        sys.exit(1)


def load_swebench_local(json_file: Path) -> List[SWEBenchTask]:
    """Load SWE-bench tasks from local JSON file."""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if isinstance(data, list):
            tasks = [SWEBenchTask(item) for item in data]
        else:
            tasks = [SWEBenchTask(data)]

        print(f"  {C.GREEN}✓ Loaded {len(tasks)} tasks from {json_file}{C.RESET}\n")
        return tasks

    except Exception as e:
        print_error_box(f"Failed to load local file: {e}")
        sys.exit(1)


# ============================================================================
# Repository Setup
# ============================================================================

def remove_readonly(func, path, excinfo):
    """Helper to handle readonly files on Windows."""
    import stat
    os.chmod(path, stat.S_IWRITE)
    func(path)


def safe_rmtree(path):
    """Safely remove directory tree, handling Windows permission issues."""
    try:
        shutil.rmtree(path, onerror=remove_readonly)
    except Exception as e:
        print(f"  {C.YELLOW}Warning: Could not fully clean directory: {e}{C.RESET}")


def setup_task_repo(task: SWEBenchTask, work_dir: Path) -> Optional[Path]:
    """Clone and setup repository for a task."""
    repo_name = task.repo.replace('/', '_')
    repo_path = work_dir / repo_name / task.instance_id

    print_section(f"Setting up: {task.instance_id}", C.BRIGHT_CYAN)

    # Clean existing directory
    if repo_path.exists():
        print(f"  {C.YELLOW}Cleaning existing directory...{C.RESET}")
        safe_rmtree(repo_path)

    repo_path.mkdir(parents=True, exist_ok=True)

    # Clone repository
    repo_url = f"https://github.com/{task.repo}.git"
    print(f"  {C.CYAN}Cloning {repo_url}...{C.RESET}")

    try:
        subprocess.run(
            ["git", "clone", "--quiet", repo_url, str(repo_path)],
            check=True,
            capture_output=True,
            timeout=300
        )
    except subprocess.CalledProcessError as e:
        print_error_box(f"Failed to clone repository: {e.stderr.decode()}")
        return None
    except subprocess.TimeoutExpired:
        print_error_box("Git clone timed out after 5 minutes")
        return None

    # Checkout base commit
    print(f"  {C.CYAN}Checking out commit {task.base_commit[:8]}...{C.RESET}")
    try:
        subprocess.run(
            ["git", "checkout", task.base_commit],
            cwd=repo_path,
            check=True,
            capture_output=True
        )
    except subprocess.CalledProcessError as e:
        print_error_box(f"Failed to checkout commit: {e.stderr.decode()}")
        return None

    print(f"  {C.GREEN}✓ Repository ready at {repo_path}{C.RESET}\n")
    return repo_path


# ============================================================================
# Task Execution
# ============================================================================

def create_task_prompt(task: SWEBenchTask) -> str:
    """Create DaveLoop prompt for a SWE-bench task."""
    prompt = f"""# SWE-bench Task: {task.instance_id}

## Repository
{task.repo}

## Problem Statement
{task.problem_statement}
"""

    if task.hints_text:
        prompt += f"""
## Hints
{task.hints_text}
"""

    prompt += """

## Your Task
Analyze and fix the issue described above. Use the reasoning protocol before each action.
When you believe the issue is resolved, run the tests and output [DAVELOOP:RESOLVED].
"""

    return prompt


def run_task(task: SWEBenchTask, repo_path: Path, system_prompt: str, max_iterations: int = 10) -> Dict:
    """Run DaveLoop on a single SWE-bench task."""
    result = {
        'instance_id': task.instance_id,
        'repo': task.repo,
        'resolved': False,
        'iterations': 0,
        'error': None,
        'start_time': datetime.now().isoformat(),
        'end_time': None
    }

    print_header_box(f"RUNNING: {task.instance_id}", C.BRIGHT_MAGENTA)

    task_prompt = create_task_prompt(task)
    context = task_prompt

    for iteration in range(1, max_iterations + 1):
        result['iterations'] = iteration

        print(f"\n{C.BRIGHT_BLUE}{'─'*70}")
        print(f"  ITERATION {iteration}/{max_iterations}")
        print(f"{'─'*70}{C.RESET}\n")

        # Build prompt
        if iteration == 1:
            full_prompt = f"{system_prompt}\n\n---\n\n{context}"
            continue_session = False
        else:
            full_prompt = context
            continue_session = True

        # Run Claude
        print(f"  {C.BRIGHT_BLUE}▶ Claude is working...{C.RESET}\n")
        output = run_claude_code(full_prompt, str(repo_path), continue_session=continue_session, stream=True)

        print(f"\n  {C.BLUE}✓ Iteration complete{C.RESET}\n")

        # Check exit condition
        signal, should_exit = check_exit_condition(output)

        if should_exit:
            if signal == "RESOLVED":
                result['resolved'] = True
                result['end_time'] = datetime.now().isoformat()
                print_success_box(f"Task resolved in {iteration} iteration(s)!")
                return result
            elif signal in ["BLOCKED", "ERROR"]:
                result['error'] = signal
                result['end_time'] = datetime.now().isoformat()
                print_error_box(f"Task failed: {signal}")
                return result

        # Continue to next iteration
        context = f"""
## Iteration {iteration + 1}

The issue is NOT yet resolved. You have full context from previous iterations.
Continue debugging and fixing the issue. Use the reasoning protocol before each action.
"""

    # Max iterations reached
    result['error'] = 'MAX_ITERATIONS'
    result['end_time'] = datetime.now().isoformat()
    print_warning_box(f"Max iterations ({max_iterations}) reached without resolution")
    return result


# ============================================================================
# Evaluation & Reporting
# ============================================================================

def save_results(results: List[Dict], output_file: Path):
    """Save results to JSON file."""
    RESULTS_DIR.mkdir(exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    print(f"\n  {C.GREEN}✓ Results saved to {output_file}{C.RESET}")


def print_summary(results: List[Dict]):
    """Print summary statistics."""
    total = len(results)
    resolved = sum(1 for r in results if r['resolved'])
    failed = sum(1 for r in results if r.get('error'))

    print_header_box("EVALUATION SUMMARY", C.BRIGHT_GREEN)
    print_status("Total Tasks", str(total), C.WHITE)
    print_status("Resolved", f"{resolved} ({resolved/total*100:.1f}%)", C.GREEN)
    print_status("Failed", f"{failed} ({failed/total*100:.1f}%)", C.RED)
    print()

    # Breakdown by error type
    if failed > 0:
        print(f"  {C.BLUE}│{C.RESET} {C.WHITE}Failure Breakdown:{C.RESET}")
        error_types = {}
        for r in results:
            if r.get('error'):
                error_types[r['error']] = error_types.get(r['error'], 0) + 1

        for error_type, count in error_types.items():
            print(f"  {C.BLUE}│{C.RESET}   - {error_type}: {count}")
        print()


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="DaveLoop SWE-bench Evaluation",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("-d", "--dataset",
                       default="princeton-nlp/SWE-bench_Lite",
                       help="Hugging Face dataset name (default: SWE-bench_Lite)")
    parser.add_argument("-f", "--file",
                       help="Load tasks from local JSON file instead of Hugging Face")
    parser.add_argument("-l", "--limit", type=int,
                       help="Limit number of tasks to run")
    parser.add_argument("-m", "--max-iterations", type=int,
                       default=MAX_ITERATIONS_PER_TASK,
                       help="Max iterations per task")
    parser.add_argument("-s", "--start-from", type=int, default=0,
                       help="Start from task index (0-based)")
    parser.add_argument("--keep-repos", action="store_true",
                       help="Keep cloned repositories after evaluation")

    args = parser.parse_args()

    # Clear screen and show banner
    os.system('cls' if os.name == 'nt' else 'clear')
    print(BANNER)

    # Load system prompt
    if PROMPT_FILE.exists():
        system_prompt = PROMPT_FILE.read_text(encoding="utf-8")
    else:
        print_warning_box(f"Prompt file not found: {PROMPT_FILE}")
        system_prompt = "You are a debugging agent. Fix bugs and output [DAVELOOP:RESOLVED] when done."

    # Load tasks
    if args.file:
        tasks = load_swebench_local(Path(args.file))
    else:
        tasks = load_swebench_dataset(args.dataset, limit=args.limit)

    if args.start_from > 0:
        tasks = tasks[args.start_from:]
        print(f"  {C.YELLOW}Starting from task index {args.start_from}{C.RESET}\n")

    # Setup work directory
    WORK_DIR.mkdir(exist_ok=True)

    # Run evaluation
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    results = []

    print_header_box(f"SESSION: {session_id}", C.BRIGHT_BLUE)
    print_status("Dataset", args.dataset if not args.file else args.file, C.WHITE)
    print_status("Tasks", str(len(tasks)), C.WHITE)
    print_status("Max Iterations/Task", str(args.max_iterations), C.WHITE)
    print_status("Work Directory", str(WORK_DIR), C.WHITE)
    print()

    for i, task in enumerate(tasks, 1):
        print(f"\n{C.BRIGHT_MAGENTA}{'='*70}")
        print(f"  TASK {i}/{len(tasks)}: {task.instance_id}")
        print(f"{'='*70}{C.RESET}\n")

        # Setup repository
        repo_path = setup_task_repo(task, WORK_DIR)
        if not repo_path:
            results.append({
                'instance_id': task.instance_id,
                'repo': task.repo,
                'resolved': False,
                'error': 'SETUP_FAILED',
                'iterations': 0
            })
            continue

        # Run task
        try:
            result = run_task(task, repo_path, system_prompt, args.max_iterations)
            results.append(result)
        except KeyboardInterrupt:
            print_warning_box("Evaluation interrupted by user")
            break
        except Exception as e:
            print_error_box(f"Unexpected error: {e}")
            results.append({
                'instance_id': task.instance_id,
                'repo': task.repo,
                'resolved': False,
                'error': f'EXCEPTION: {str(e)}',
                'iterations': 0
            })
        finally:
            # Cleanup repository unless --keep-repos
            if not args.keep_repos and repo_path.exists():
                print(f"  {C.DIM}Cleaning up repository...{C.RESET}")
                safe_rmtree(repo_path)

    # Save and display results
    output_file = RESULTS_DIR / f"results_{session_id}.json"
    save_results(results, output_file)
    print_summary(results)

    print(f"\n{C.BRIGHT_BLUE}{'='*70}{C.RESET}")
    print(f"  {C.BOLD}Evaluation complete!{C.RESET}")
    print(f"  {C.DIM}Results: {output_file}{C.RESET}")
    print(f"{C.BRIGHT_BLUE}{'='*70}{C.RESET}\n")

    return 0 if all(r['resolved'] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
