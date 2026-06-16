#!/usr/bin/env python3
"""
Project Backup / Migration Todo List Generator
Scans directory structures in ~/Projects and ~/deployments, evaluates their Git
states, and outputs a todo.txt compatible file (projects-backup.txt) formatted
for the Tuxedo CLI.

Mental Model: Key-Value Metadata Model
Each scanned directory generates a single todo item containing:
- A +project-name tag (sanitized directory name)
- Custom key-value pairs representing the status of each migration checklist item:
    * github:ok|no         (Checks if a GitHub remote is configured)
    * clean:ok|dirty|untracked (Checks if working tree has changes)
    * pushed:ok|unpushed|no-remote|no-commits (Checks if all branches are pushed)
    * notes:todo           (Prompt to manually verify local notes/documentation)
- A context tag (@projects or @deployments) indicating where the project lives.
"""

import os
import sys
import datetime
import subprocess
import argparse

# Directory patterns to exclude from scans and size calculations
SKIP_DIRS = {
    '.git',
    '.venv',
    'venv',
    'node_modules',
    '__pycache__',
    '.pytest_cache',
    '.next',
    'target',
    'dist',
    'build',
}

# ANSI color codes for pretty CLI output
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_RED = "\033[91m"
COLOR_BLUE = "\033[94m"
COLOR_CYAN = "\033[96m"
COLOR_RESET = "\033[0m"
COLOR_BOLD = "\033[1m"

def supports_color():
    """Checks if the terminal supports color."""
    plat = sys.platform
    supported_platform = plat != 'win32' or 'ANSICON' in os.environ
    is_a_tty = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
    return supported_platform and is_a_tty

# Initialize coloring based on support
USE_COLOR = supports_color()

def colorize(text, color):
    if USE_COLOR:
        return f"{color}{text}{COLOR_RESET}"
    return text

def run_git_command(repo_path, args):
    """Runs a git command in the context of the repository path."""
    try:
        env = os.environ.copy()
        # Clean up any potential git environment variables that might interfere
        for var in ['GIT_DIR', 'GIT_WORK_TREE']:
            env.pop(var, None)
            
        result = subprocess.run(
            ['git'] + args,
            cwd=repo_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            check=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

def check_git_status(repo_path):
    """Checks if the working tree is clean, dirty, or contains only untracked files."""
    status = run_git_command(repo_path, ['status', '--porcelain'])
    if status is None:
        return "error"
    if not status:
        return "ok"
    
    lines = status.splitlines()
    has_tracked_changes = False
    has_untracked = False
    
    for line in lines:
        if line.startswith('??'):
            has_untracked = True
        else:
            has_tracked_changes = True
            
    if has_tracked_changes:
        return "dirty"
    if has_untracked:
        return "untracked"
    return "ok"

def check_branches_pushed(repo_path, has_remotes):
    """Checks if all local branches have been successfully pushed to remote."""
    if not has_remotes:
        return "no-remote"
        
    # Check if there are any commits at all
    log_res = run_git_command(repo_path, ['rev-parse', '--head'])
    if log_res is None:
        return "no-commits"
    
    # Check git branch -vv output
    branches_out = run_git_command(repo_path, ['branch', '-vv'])
    if not branches_out:
        return "ok"
        
    for line in branches_out.splitlines():
        line = line.strip()
        if not line:
            continue
        
        # Check if the branch line has a tracking upstream
        start_idx = line.find('[')
        end_idx = line.find(']')
        if start_idx == -1 or end_idx == -1 or end_idx < start_idx:
            # Local branch with no upstream tracking branch
            return "unpushed"
        
        upstream_info = line[start_idx+1:end_idx]
        if "ahead" in upstream_info or "gone" in upstream_info:
            return "unpushed"
            
    return "ok"

def check_local_notes(repo_path):
    """Optionally flags if local notes/documentation exist to prompt check."""
    # We always default to 'todo' for local notes verification as requested,
    # but we can scan for note-like files to show a tip in console.
    note_filenames = {'notes.txt', 'notes.md', 'todo.txt', 'todo.md', 'note.txt', 'note.md', 'todo.org', 'readme.md', 'readme.txt'}
    try:
        for entry in os.scandir(repo_path):
            if entry.is_file() and entry.name.lower() in note_filenames:
                return True
    except Exception:
        pass
    return False

def check_env_files(repo_path):
    """Detects if any .env or environment configuration files exist in the repository."""
    env_names = {
        ".env",
        ".env.local",
        ".env.production",
        ".env.development",
    }

    try:
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for filename in files:
                if filename in env_names:
                    return "check"
    except Exception:
        pass

    return "none"

def check_databases(repo_path):
    """Detects if any SQLite database files exist in the repository."""
    db_extensions = (
        ".db",
        ".sqlite",
        ".sqlite3",
    )

    try:
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for filename in files:
                if filename.endswith(db_extensions):
                    return "check"
    except Exception:
        pass

    return "none"

def check_docker(repo_path):
    """Detects if the repository contains Docker or Compose configuration files."""
    docker_files = {
        "docker-compose.yml",
        "docker-compose.yaml",
        "compose.yml",
        "compose.yaml",
        "Dockerfile",
    }

    try:
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            if any(f in docker_files for f in files):
                return "yes"
    except Exception:
        pass

    return "no"

def get_directory_size_mb(path):
    """Calculates the physical size of important project data on disk in MB, skipping dependencies/builds."""
    total = 0

    try:
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for f in files:
                fp = os.path.join(root, f)
                try:
                    total += os.path.getsize(fp)
                except OSError:
                    pass
    except Exception:
        return "unknown"

    size_mb = round(total / (1024 * 1024))
    return f"{size_mb}mb"

def sanitize_project_name(name):
    """Sanitizes directory name to conform to todo.txt project tag naming rules."""
    clean_name = "".join(c if c.isalnum() or c == '-' else '-' for c in name.lower())
    clean_name = clean_name.strip('-')
    while '--' in clean_name:
        clean_name = clean_name.replace('--', '-')
    return clean_name

def scan_directory(base_path, context_tag, date_str):
    """Scans the subdirectories, runs git/file checks, and builds todo.txt task lines."""
    tasks = []
    expanded_path = os.path.expanduser(base_path)
    
    print(colorize(f"\nScanning: {expanded_path}", COLOR_BOLD + COLOR_CYAN))
    
    if not os.path.exists(expanded_path):
        print(colorize(f"  [!] Directory does not exist. Skipping.", COLOR_YELLOW))
        return tasks
    if not os.path.isdir(expanded_path):
        print(colorize(f"  [!] Path is not a directory. Skipping.", COLOR_YELLOW))
        return tasks
        
    try:
        entries = sorted(os.scandir(expanded_path), key=lambda e: e.name.lower())
    except Exception as e:
        print(colorize(f"  [!] Failed to read directory: {e}", COLOR_RED))
        return tasks

    for entry in entries:
        if not entry.is_dir() or entry.name.startswith('.'):
            continue
            
        project_dir = entry.path
        project_name = entry.name
        clean_project_name = sanitize_project_name(project_name)
        
        # Run general checks first
        env_status = check_env_files(project_dir)
        database_status = check_databases(project_dir)
        docker_status = check_docker(project_dir)
        size_status = get_directory_size_mb(project_dir)
        
        # Determine check colorizations
        env_col = COLOR_YELLOW if env_status == "check" else COLOR_GREEN
        db_col = COLOR_YELLOW if database_status == "check" else COLOR_GREEN
        docker_col = COLOR_CYAN if docker_status == "yes" else COLOR_GREEN
        
        size_col = COLOR_GREEN
        if size_status.endswith("mb"):
            try:
                size_mb = int(size_status[:-2])
                if size_mb >= 2000:
                    size_col = COLOR_RED
                elif size_mb >= 500:
                    size_col = COLOR_YELLOW
            except ValueError:
                pass
        
        # Check if it is a git repo
        git_dir = os.path.join(project_dir, '.git')
        is_git = os.path.exists(git_dir) and os.path.isdir(git_dir)
        
        if is_git:
            # 1. GitHub remote check
            remotes = run_git_command(project_dir, ['remote', '-v'])
            has_remotes = bool(remotes)
            has_github = "github.com" in remotes.lower() if remotes else False
            github_status = "ok" if has_github else "no"
            
            # 2. Clean status check
            clean_status = check_git_status(project_dir)
            
            # 3. Pushed branches check
            pushed_status = check_branches_pushed(project_dir, has_remotes)
            
            # 4. Notes check
            notes_found = check_local_notes(project_dir)
            notes_status = "todo"
            
            # Colors for Git status metrics
            github_col = COLOR_GREEN if github_status == "ok" else COLOR_RED
            clean_col = COLOR_GREEN if clean_status == "ok" else (COLOR_YELLOW if clean_status == "untracked" else COLOR_RED)
            pushed_col = COLOR_GREEN if pushed_status == "ok" else (COLOR_YELLOW if pushed_status in ("no-remote", "no-commits") else COLOR_RED)
            notes_col = COLOR_CYAN if notes_found else COLOR_YELLOW
            
            notes_tip = " (notes found)" if notes_found else ""
            
            # First line: basic project identity and Git details
            print(f"  + {project_name:<25} "
                  f"git:yes | "
                  f"github:{colorize(github_status.ljust(3), github_col)} | "
                  f"clean:{colorize(clean_status.ljust(9), clean_col)} | "
                  f"pushed:{colorize(pushed_status.ljust(10), pushed_col)} | "
                  f"notes:{colorize(notes_status.ljust(4), notes_col)}{notes_tip}")
            
            # Second line: non-Git details (size, env, db, docker)
            print(f"    {'':<25} "
                  f"size:{colorize(size_status.ljust(8), size_col)} | "
                  f"env:{colorize(env_status.ljust(5), env_col)} | "
                  f"db:{colorize(database_status.ljust(5), db_col)} | "
                  f"docker:{colorize(docker_status.ljust(3), docker_col)}")
                  
            # Create todo.txt line
            task_line = (f"{date_str} Verify project +{clean_project_name} github:{github_status} "
                         f"clean:{clean_status} pushed:{pushed_status} notes:{notes_status} "
                         f"env:{env_status} database:{database_status} docker:{docker_status} "
                         f"size:{size_status} {context_tag}")
        else:
            notes_found = check_local_notes(project_dir)
            notes_status = "todo"
            notes_tip = " (notes found)" if notes_found else ""
            
            na3 = "n/a".ljust(3)
            na9 = "n/a".ljust(9)
            na10 = "n/a".ljust(10)
            
            # First line: basic project identity
            print(f"  + {project_name:<25} "
                  f"git:{colorize('no', COLOR_YELLOW):<3} | "
                  f"github:{colorize(na3, COLOR_YELLOW)} | "
                  f"clean:{colorize(na9, COLOR_YELLOW)} | "
                  f"pushed:{colorize(na10, COLOR_YELLOW)} | "
                  f"notes:{colorize(notes_status.ljust(4), COLOR_YELLOW)}{notes_tip}")
            
            # Second line: non-Git details (size, env, db, docker)
            print(f"    {'':<25} "
                  f"size:{colorize(size_status.ljust(8), size_col)} | "
                  f"env:{colorize(env_status.ljust(5), env_col)} | "
                  f"db:{colorize(database_status.ljust(5), db_col)} | "
                  f"docker:{colorize(docker_status.ljust(3), docker_col)}")
                  
            task_line = (f"{date_str} Verify non-git project +{clean_project_name} git:no notes:{notes_status} "
                         f"env:{env_status} database:{database_status} docker:{docker_status} "
                         f"size:{size_status} {context_tag}")
            
        tasks.append(task_line)
        
    return tasks

def main():
    parser = argparse.ArgumentParser(
        description="Scan workspace folders and generate a todo.txt migration list for Tuxedo CLI."
    )
    parser.add_argument(
        "--projects", 
        default="~/Projects", 
        help="Path to projects directory (default: ~/Projects)"
    )
    parser.add_argument(
        "--deployments", 
        default="~/deployments", 
        help="Path to deployments directory (default: ~/deployments)"
    )
    parser.add_argument(
        "--output", 
        default="projects-backup.txt", 
        help="Output filepath (default: projects-backup.txt)"
    )
    
    args = parser.parse_args()
    
    date_str = datetime.date.today().strftime('%Y-%m-%d')
    
    print(colorize("===============================================", COLOR_BOLD + COLOR_BLUE))
    print(colorize("    Workspace Migration Todo List Generator     ", COLOR_BOLD + COLOR_BLUE))
    print(colorize("===============================================", COLOR_BOLD + COLOR_BLUE))
    
    all_tasks = []
    
    # Scan Projects
    projects_tasks = scan_directory(args.projects, "@projects", date_str)
    all_tasks.extend(projects_tasks)
    
    # Scan Deployments
    deployments_tasks = scan_directory(args.deployments, "@deployments", date_str)
    all_tasks.extend(deployments_tasks)
    
    if not all_tasks:
        print(colorize("\n[!] No subdirectories found to verify.", COLOR_YELLOW))
        return
        
    # Write to output file
    output_path = os.path.abspath(args.output)
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            for task in all_tasks:
                f.write(task + '\n')
        print(colorize("\n===============================================", COLOR_BOLD + COLOR_BLUE))
        print(colorize(f"Success! Generated {len(all_tasks)} tasks.", COLOR_BOLD + COLOR_GREEN))
        print(f"Todo file written to: {colorize(output_path, COLOR_CYAN)}")
        print(colorize("===============================================", COLOR_BOLD + COLOR_BLUE))
        print("\nTo load this file in Tuxedo CLI, you can:")
        print(f"  cat {args.output} >> ~/.config/tuxedo/todo.txt  (or your active todo.txt path)")
    except Exception as e:
        print(colorize(f"\n[!] Failed to write output file: {e}", COLOR_RED))
        sys.exit(1)

if __name__ == '__main__':
    main()
