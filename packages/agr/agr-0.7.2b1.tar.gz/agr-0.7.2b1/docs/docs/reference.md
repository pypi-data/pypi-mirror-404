---
title: Reference
---

# Reference

## CLI Commands

### agr add

Install skills from GitHub or local paths.

```bash
agr add <handle>...
```

**Arguments:**

- `handle` — Skill handle (`user/skill` or `user/repo/skill`) or local path (`./path`)

**Options:**

- `--overwrite`, `-o` — Replace existing skills

**Examples:**

```bash
agr add anthropics/skills/frontend-design
agr add kasperjunge/commit kasperjunge/pr
agr add ./my-skill
agr add anthropics/skills/pdf --overwrite
```

### agr remove

Uninstall skills.

```bash
agr remove <handle>...
```

**Examples:**

```bash
agr remove anthropics/skills/frontend-design
agr remove kasperjunge/commit
agr remove ./my-skill
```

### agr sync

Install all dependencies from `agr.toml`.

```bash
agr sync
```

Installs any skills listed in `agr.toml` that aren't already installed.

### agr list

Show all skills and their installation status.

```bash
agr list
```

Displays skills from `agr.toml` and whether they're installed.

### agr init

Create `agr.toml` or a skill scaffold.

```bash
agr init              # Create agr.toml
agr init <name>       # Create skill scaffold
```

**Examples:**

```bash
agr init                    # Creates agr.toml in current directory
agr init my-skill           # Creates my-skill/SKILL.md
```

### agrx

Run a skill temporarily without adding to `agr.toml`.

```bash
agrx <handle> [options]
```

Downloads the skill, runs it with the selected tool, and cleans up afterwards.

**Options:**

- `--interactive`, `-i` — Run skill, then continue in interactive mode
- `--prompt`, `-p` — Prompt to pass to the skill
- `--global`, `-g` — Install to the global tool skills directory (e.g. `~/.claude/skills/`, `~/.codex/skills/`) instead of the repo-local one

**Examples:**

```bash
agrx anthropics/skills/pdf
agrx anthropics/skills/pdf -p "Extract tables from report.pdf"
agrx kasperjunge/commit -i
agrx kasperjunge/commit --source github
```

## agr.toml Format

```toml
default_source = "github"

dependencies = [
    {handle = "anthropics/skills/frontend-design"},
    {handle = "kasperjunge/commit"},
    {handle = "./local-skill"},
]

[[source]]
name = "github"
type = "git"
url = "https://github.com/{owner}/{repo}.git"
```

Each dependency has:

- `handle` — Remote handle or local path
- `source` — Optional source name for remote handles

Note: `dependencies` must appear before any `[[source]]` blocks in `agr.toml`.

## Troubleshooting

### Skill not found

Check that the skill exists in the repository. agr searches:

- `resources/skills/{name}/SKILL.md`
- `skills/{name}/SKILL.md`
- `{name}/SKILL.md`

### Skill already exists

Use `--overwrite`:

```bash
agr add user/skill --overwrite
```

### Repository not found

Check:

- Username and repo name are correct
- Repository is public
- Default branch is `main`

### Not in a git repository

`agrx` requires a git repository (or use `--global`):

```bash
agrx user/skill --global
```

### Network errors

Ensure the repository is public and you have internet access.
