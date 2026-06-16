# NixOS Migration

Migration project for moving my development workstation from Arch Linux to NixOS.

## Objectives

- Learn NixOS through practical usage.
- Maintain a productive backend development environment.
- Keep system configuration under version control.
- Avoid unnecessary workstation customization during migration.

## Success Criteria

The migration is complete when:

- NixOS is installed.
- Network connectivity works.
- Git is configured.
- Zed is installed.
- Zen Browser is installed.
- UV is installed.
- Docker is installed.
- Existing FastAPI projects run successfully.

Everything else is optional.

## Repository Structure

- `docs/` — migration plan, strategy, and backup documentation.
- `arch-inventory/` — lists of packages, services, and configuration dumped from Arch Linux.
- `scripts/` — automation tools for the migration process.
- `todo.txt` — active task list managed with Tuxedo.
- `projects-backup.txt` — generated project backup audit tasks.
- `LICENSE` — project license.
- `README.md` — this file.

### Key Files

- `docs/plan.md` — main migration roadmap.
- `scripts/project-todo-list.py` — generates project backup audit tasks.
- `docs/project_backup_list.md` — documentation for the backup audit workflow.

## Guiding Principle

NixOS should support project development.

Project development should not be postponed for NixOS.
