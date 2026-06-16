# NixOS Migration Plan

## Goals

### Primary Goals

* Migrate from Arch Linux to NixOS.
* Learn NixOS fundamentals through practical usage.
* Maintain a productive backend development environment.
* Avoid spending weeks perfecting workstation configuration.
* Keep all configuration under version control.

### Secondary Goals

* Rebuild shell configuration intentionally.
* Remove obsolete scripts, aliases, and historical baggage.
* Create a reproducible setup for both desktop and laptop.
* Gradually learn flakes, Home Manager, and modules.

### Non-Goals

* Achieving the perfect NixOS setup immediately.
* Becoming a Nix expert before building projects.
* Recreating every aspect of the current Arch configuration.
* Replacing every tool with a Nix-native alternative.

---

# Phase 0 — Backup and Inventory

## Back Up

* ~/Projects
* ~/.ssh
* ~/.gitconfig
* ~/.config/nvim
* ~/.config/hypr
* ~/.config/niri
* ~/.config/starship.toml
* Any important documents

## Package Inventory

```bash
pacman -Qqe > pkglist.txt
```

Use this only as a reference, not as a checklist.

---

# Phase 1 — Initial NixOS Installation

## Requirements

* NixOS Graphical ISO
* Bootable USB installer

## First Boot Objectives

The machine is considered usable when:

* Internet works
* Git works
* Terminal works
* Browser works
* Zed works
* UV works

Nothing else is required initially.

---

# Phase 2 — Minimal Development Environment

Install only:

* Git
* Zed
* Zen Browser
* UV
* Docker
* Neovim
* tmux
* Starship

Optional:

* Antigravity CLI

No Java tooling.
No Rust tooling.
No advanced shell customization.

Only what is needed for FastAPI projects.

---

# Phase 3 — Version Control

Create:

```text
~/nixos-config
```

Initialize:

```bash
git init
```

Track all system configuration from the beginning.

---

# Phase 4 — Home Manager

Move configuration gradually:

* Git
* Bash or Zsh
* Starship
* Neovim
* SSH
* Terminal preferences

Do not migrate old scripts blindly.

Audit each script individually.

---

# Phase 5 — FastAPI Development

Create reproducible development environments.

Required tools:

* Python
* UV
* Docker
* PostgreSQL

Learn:

* flakes
* nix develop
* development shells

Only as needed by active projects.

---

# Phase 6 — Desktop Environment

Desktop:

* Hyprland

Laptop:

* Niri

Shared:

* Starship
* Terminal
* Fonts
* Shell configuration
* Git configuration
* Development tooling

Investigate:

* DankMaterialShell

Goal:

Maintain a consistent workflow across both machines.

---

# Phase 7 — Language Expansion

Add tooling only when required.

## Java

Potential tools:

* JDK
* Gradle
* JetBrains IDEs

## Rust

Potential tools:

* rustup
* cargo
* rust-analyzer

## JavaScript

Potential tools:

* Node.js
* npm
* pnpm

---

# Phase 8 — Continuous Learning

Learn in this order:

1. configuration.nix
2. Home Manager
3. Nix language basics
4. Flakes
5. Modules
6. Development shells
7. Packaging
8. Overlays

Avoid learning advanced concepts before a real need appears.

---

# Guiding Principle

NixOS should support project development.

Project development should not be postponed for NixOS.

If a Nix task does not unblock a current project, it goes into the backlog.

