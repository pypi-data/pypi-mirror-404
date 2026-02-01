<div align="center">

# 🧩 agent-resources (agr)

**A package manager for AI agents.**

Install agent skills from GitHub with one command.

[![PyPI](https://img.shields.io/pypi/v/agr?color=blue)](https://pypi.org/project/agr/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

---

> **Note:** Support for rules, subagents, and slash commands has been removed. Most AI coding agents are converging on skills as the standard format, so agr now focuses exclusively on skills. To convert your existing rules, commands, or subagents to skills, run:
> ```bash
> agrx kasperjunge/migrate-to-skills
> agrx kasperjunge/migrate-to-skills -p "convert files in ./my-commands"
> ```

---

## Getting Started

Install agr CLI:

```bash
pip install agr
```

Install your first skill:

```bash
agr add anthropics/skills/frontend-design
```

That's it. The skill is now available in your configured tool (Claude Code, Codex, Cursor, or Copilot).

---

## What is agr?

**agr** installs agent skills from GitHub directly into your tool's skills folder
(`.claude/skills/`, `.codex/skills/`, `.cursor/skills/`, or `.github/skills/`).

**agrx** runs skills instantly from your terminal — download, run, then clean up.

---

## Install Skills

```bash
agr add anthropics/skills/frontend-design     # Install a skill
agr add anthropics/skills/pdf anthropics/skills/mcp-builder   # Install multiple
agr add anthropics/skills/pdf --source github # Install from an explicit source
```

Remote installs require `git` to be available on your system.

**Beta note:** Multi-source support is only in the beta release right now. Install `agr==0.7.2b1` to use `default_source`, `[[source]]`, or `--source`.

### Handle format

```
username/skill-name         → From user's agent-resources repo
username/repo/skill-name    → From a specific repo
./path/to/skill             → From local directory
```

---

## Run Skills From Your Terminal

```bash
agrx anthropics/skills/pdf                              # Run a skill instantly
agrx anthropics/skills/pdf -p "Extract tables from report.pdf"   # With a prompt
agrx anthropics/skills/skill-creator -i                 # Run, then continue chatting
agrx anthropics/skills/pdf --source github              # Explicit source
```

---

## Team Sync

Your dependencies are tracked in `agr.toml`:

```toml
default_source = "github"

dependencies = [
    {handle = "anthropics/skills/frontend-design", type = "skill"},
    {handle = "anthropics/skills/brand-guidelines", type = "skill"},
]

[[source]]
name = "github"
type = "git"
url = "https://github.com/{owner}/{repo}.git"
```

Note: `dependencies` must appear before any `[[source]]` blocks in `agr.toml`.

Teammates run:

```bash
agr sync
```

---

## Create Your Own Skill

```bash
agr init my-skill
```

Creates `my-skill/SKILL.md`:

```markdown
---
name: my-skill
description: What this skill does.
---

# My Skill

Instructions for the agent.
```

If you're adding it to this repo, place it under `./skills/`.

Test it locally:

```bash
agr add ./skills/my-skill
```

Share it:

```bash
# Push to GitHub, then others can:
agr add your-username/my-skill
```

---

## Initialize a Repo

`agr init` can discover skills in your repo and add them to `agr.toml`.

```bash
agr init       # Auto-discover skills and create agr.toml
agr init -i    # Guided setup
```

Skills inside tool folders (e.g. `.claude/skills/`, `.codex/skills/`,
`.cursor/skills/`, `.github/skills/`) are ignored by default. To bring them into
`./skills/`, run:

```bash
agr init --migrate
```

---

## All Commands

| Command | Description |
|---------|-------------|
| `agr add <handle>` | Install a skill |
| `agr remove <handle>` | Uninstall a skill |
| `agr sync` | Install all from agr.toml |
| `agr list` | Show installed skills |
| `agr init` | Create agr.toml |
| `agr init <name>` | Create a new skill |
| `agrx <handle>` | Run skill temporarily |

---

## Community Skills

```bash
# Go development — @dsjacobsen
agr add dsjacobsen/golang-pro

# Drupal development — @madsnorgaard
agr add madsnorgaard/drupal-expert
```

**Built something?** [Share it here](https://github.com/kasperjunge/agent-resources/issues).

---

<div align="center">

[Documentation](https://kasperjunge.github.io/agent-resources/) · [MIT License](LICENSE)

</div>
