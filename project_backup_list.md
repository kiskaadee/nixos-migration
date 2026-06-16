# Workspace Migration Todo List Model

To facilitate your migration from Arch Linux to NixOS without creating a bloated, hard-to-read `todo.txt` file, we have designed the **Key-Value Metadata Model**. This model tracks all checks on a single line per project, using `key:value` tags that the Tuxedo CLI (and other `todo.txt` clients) natively support.

---

## The Mental Model: Key-Value Tags

In the standard `todo.txt` format, metadata tags use the `key:value` syntax. We use these tags to track the four key status metrics for each project. 

Instead of writing 4 separate tasks for a single project, each project gets **exactly one line**. For example:

```text
2026-06-16 Verify project +my-awesome-app github:ok clean:dirty pushed:unpushed notes:todo @projects
```

### Tag Glossary

| Key | Value | Description |
| :--- | :--- | :--- |
| **`github:`** | `ok` | A git remote containing `github.com` is configured. |
| | `no` | No GitHub remote is found. |
| **`clean:`** | `ok` | The working tree is clean. |
| | `dirty` | The working tree has modified/staged files. |
| | `untracked` | Only untracked files are present (working tree is otherwise clean). |
| **`pushed:`** | `ok` | All local branches match their upstream branch commits. |
| | `unpushed` | Local branches exist that are ahead of their upstream, or have no upstream branch. |
| | `no-remote` | No remotes are configured for the repository. |
| | `no-commits` | The repository has no commits yet. |
| **`notes:`** | `todo` | Always pre-populated as a prompt to manually verify if local note files are preserved. |
| **`git:`** | `no` | *(For non-git directories only)* Indicates the subdirectory is not a git repository. |

### Context Tags

The tasks are annotated with contexts so you can filter them easily in Tuxedo:
- `@projects` for subdirectories scanned in `~/Projects`
- `@deployments` for subdirectories scanned in `~/deployments`

---

## Script Architecture

The script [project-todo-list.py](file:///home/kiskaadee/Projects/nixox-migration/project-todo-list.py) is self-contained and uses only Python's standard library. It does the following when executed:
1. Resolves paths (expanding `~/` to absolute paths).
2. Traverses every subdirectory in the specified parent folders.
3. Automatically queries local Git status for each folder:
   - Evaluates remotes for GitHub urls.
   - Parses `git status --porcelain` to classify clean vs dirty vs untracked states.
   - Parses `git branch -vv` to verify tracking status and find unpushed commits.
   - Scans directories for note files (e.g. `notes.md`, `todo.txt`) to print a visual hint.
4. Outputs the `projects-backup.txt` file ready to be appended to your active `todo.txt` file.
5. Prints a colored summary of the scan results in your console.

---

## How to Run the Script

Since the projects are on your Arch Linux machine, follow these steps to execute the script:

### 1. Copy the Script
Copy [project-todo-list.py](file:///home/kiskaadee/Projects/nixox-migration/project-todo-list.py) to your Arch Linux machine.

### 2. Make it Executable
Ensure the script is executable:
```bash
chmod +x project-todo-list.py
```

### 3. Run the Scan
Execute the script using its default values (which will scan `~/Projects` and `~/deployments` and write to `projects-backup.txt` in your current directory):
```bash
./project-todo-list.py
```

#### Customizing Paths
If your projects or deployments are located elsewhere, use command-line arguments:
```bash
./project-todo-list.py --projects ~/MyCode --deployments ~/servers --output migrate-todo.txt
```

---

## Loading into Tuxedo CLI

To import the generated list into your Tuxedo todo list, append it to your active `todo.txt` file:

```bash
cat projects-backup.txt >> ~/.config/tuxedo/todo.txt
```
*(Make sure to replace `~/.config/tuxedo/todo.txt` with your actual `$TODO_FILE` path if customized).*

Once imported, you can run Tuxedo's TUI or CLI to manage them:
- Filter for projects needing attention: `tuxedo ls @projects`
- Filter for deployment projects: `tuxedo ls @deployments`
- As you verify each project, edit the line (e.g. change `pushed:unpushed` to `pushed:ok`) and check off the task once all key-values are `ok`.
