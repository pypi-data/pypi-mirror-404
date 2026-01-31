"""Skills management CLI commands."""

import click
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..design import print_error

console = Console()


def _get_skills_dir() -> Path:
    """Get the skills directory."""
    return Path.cwd() / ".emdash" / "skills"


@click.group()
def skills():
    """Manage agent skills."""
    pass


@skills.command("list")
def skills_list():
    """List all available skills."""
    from emdash_core.agent.skills import SkillRegistry

    skills_dir = _get_skills_dir()
    registry = SkillRegistry.get_instance()
    registry.load_skills(skills_dir)

    all_skills = registry.get_all_skills()

    if not all_skills:
        console.print("[yellow]No skills found.[/yellow]")
        console.print(f"[dim]Create skills in {skills_dir}/<skill-name>/SKILL.md[/dim]")
        return

    table = Table(title="Available Skills")
    table.add_column("Name", style="cyan")
    table.add_column("Description")
    table.add_column("User Invocable", style="green")
    table.add_column("Tools")
    table.add_column("Scripts", style="yellow")

    for skill in all_skills.values():
        invocable = "Yes (/{})".format(skill.name) if skill.user_invocable else "No"
        tools = ", ".join(skill.tools) if skill.tools else "-"
        scripts = str(len(skill.scripts)) if skill.scripts else "-"
        table.add_row(skill.name, skill.description, invocable, tools, scripts)

    console.print(table)


@skills.command("show")
@click.argument("name")
def skills_show(name: str):
    """Show details of a specific skill."""
    from emdash_core.agent.skills import SkillRegistry

    skills_dir = _get_skills_dir()
    registry = SkillRegistry.get_instance()
    registry.load_skills(skills_dir)

    skill = registry.get_skill(name)

    if skill is None:
        console.print(f"[red]Skill '{name}' not found.[/red]")
        available = registry.list_skills()
        if available:
            console.print(f"[dim]Available skills: {', '.join(available)}[/dim]")
        return

    # Build scripts info
    scripts_info = "None"
    if skill.scripts:
        scripts_info = "\n".join([f"  - {s.name} ({s})" for s in skill.scripts])

    # Show skill details
    details = (
        f"[bold]Description:[/bold] {skill.description}\n\n"
        f"[bold]User Invocable:[/bold] {'Yes (/' + skill.name + ')' if skill.user_invocable else 'No'}\n\n"
        f"[bold]Tools:[/bold] {', '.join(skill.tools) if skill.tools else 'None'}\n\n"
        f"[bold]Scripts:[/bold] {len(skill.scripts) if skill.scripts else 'None'}"
    )

    if skill.scripts:
        details += "\n"
        for script in skill.scripts:
            details += f"\n  [yellow]{script.name}[/yellow]: {script}"

    details += f"\n\n[bold]File:[/bold] {skill.file_path}"

    console.print(Panel(
        details,
        title=f"[cyan]{skill.name}[/cyan]",
        border_style="cyan",
    ))

    console.print()
    console.print("[bold]Instructions:[/bold]")
    console.print(Panel(
        skill.instructions,
        border_style="dim",
    ))


@skills.command("create")
@click.argument("name")
@click.option("--description", "-d", default="", help="Skill description")
@click.option("--user-invocable/--no-user-invocable", default=True, help="Can be invoked with /name")
@click.option("--tools", "-t", multiple=True, help="Tools this skill needs (can specify multiple)")
@click.option("--with-script", "-s", is_flag=True, help="Include a sample executable script")
def skills_create(name: str, description: str, user_invocable: bool, tools: tuple, with_script: bool):
    """Create a new skill.

    Creates a skill directory with SKILL.md template and optional scripts.

    Example:
        emdash skills create commit -d "Generate commit messages" -t execute_command -t read_file
        emdash skills create deploy -d "Deploy application" --with-script
    """
    import os
    import stat

    # Validate name
    name = name.lower().strip()
    if len(name) > 64:
        console.print("[red]Skill name must be 64 characters or less.[/red]")
        return

    if not name.replace("-", "").replace("_", "").isalnum():
        console.print("[red]Skill name must contain only lowercase letters, numbers, hyphens, and underscores.[/red]")
        return

    skills_dir = _get_skills_dir()
    skill_dir = skills_dir / name
    skill_file = skill_dir / "SKILL.md"

    if skill_dir.exists():
        console.print(f"[red]Skill '{name}' already exists at {skill_dir}[/red]")
        return

    # Build content
    tools_str = ", ".join(tools) if tools else ""
    description = description or f"Description for {name} skill"

    # Add script documentation if creating with script
    script_docs = ""
    if with_script:
        script_docs = """

## Scripts

This skill includes executable scripts that can be run by the agent:

- `run.sh` - Main script for this skill. Execute it using: `bash <skill_dir>/run.sh`

Scripts are self-contained bash executables. The agent will run them using the Bash tool when needed.
"""

    content = f"""---
name: {name}
description: {description}
user_invocable: {str(user_invocable).lower()}
tools: [{tools_str}]
---

# {name.replace('-', ' ').title()}

{description}

## Instructions

Add your skill instructions here. These will be provided to the agent when the skill is invoked.
{script_docs}
## Usage

Describe how this skill should be used.

## Examples

Provide example scenarios here.
"""

    try:
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file.write_text(content)
        console.print(f"[green]Created skill '{name}' at {skill_file}[/green]")

        # Create sample script if requested
        if with_script:
            script_file = skill_dir / "run.sh"
            script_content = f"""#!/bin/bash
# {name} skill script
# This script is executed by the agent when needed.
# All scripts must be self-contained and executable.

set -e

echo "Running {name} skill script..."

# Add your script logic here
# Example:
# - Check prerequisites
# - Execute commands
# - Output results

echo "Script completed successfully."
"""
            script_file.write_text(script_content)
            # Make executable
            current_mode = script_file.stat().st_mode
            os.chmod(script_file, current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            console.print(f"[green]Created script: {script_file}[/green]")

        console.print(f"[dim]Edit the SKILL.md file to customize the skill instructions.[/dim]")
        if with_script:
            console.print(f"[dim]Edit run.sh to add your script logic.[/dim]")
    except Exception as e:
        print_error(e, "Error creating skill")


@skills.command("delete")
@click.argument("name")
@click.option("--force", "-f", is_flag=True, help="Delete without confirmation")
def skills_delete(name: str, force: bool):
    """Delete a skill."""
    skills_dir = _get_skills_dir()
    skill_dir = skills_dir / name

    if not skill_dir.exists():
        console.print(f"[red]Skill '{name}' not found.[/red]")
        return

    if not force:
        if not click.confirm(f"Are you sure you want to delete skill '{name}'?"):
            console.print("[yellow]Cancelled.[/yellow]")
            return

    import shutil
    shutil.rmtree(skill_dir)
    console.print(f"[green]Deleted skill '{name}'.[/green]")


@skills.command("init")
def skills_init():
    """Initialize skills directory with example skills."""
    skills_dir = _get_skills_dir()

    if skills_dir.exists() and list(skills_dir.iterdir()):
        console.print(f"[yellow]Skills directory already exists at {skills_dir}[/yellow]")
        if not click.confirm("Do you want to add example skills anyway?"):
            return

    skills_dir.mkdir(parents=True, exist_ok=True)

    # Create example commit skill
    commit_dir = skills_dir / "commit"
    if not commit_dir.exists():
        commit_dir.mkdir(parents=True, exist_ok=True)
        (commit_dir / "SKILL.md").write_text("""---
name: commit
description: Generate commit messages following conventional commits format
user_invocable: true
tools: [execute_command, read_file]
---

# Commit Message Generation

Generate clear, conventional commit messages based on staged changes.

## Instructions

1. Run `git diff --cached` to see staged changes
2. Analyze the changes to understand what was modified
3. Generate a commit message following conventional commits format:
   - feat: A new feature
   - fix: A bug fix
   - docs: Documentation only changes
   - style: Changes that don't affect meaning (formatting, etc)
   - refactor: Code change that neither fixes a bug nor adds a feature
   - test: Adding or modifying tests
   - chore: Changes to build process or auxiliary tools

4. Format: `<type>(<scope>): <description>`

## Examples

- `feat(auth): add OAuth2 support`
- `fix(api): handle null response in user endpoint`
- `docs(readme): update installation instructions`
""")
        console.print("[green]Created example skill: commit[/green]")

    # Create example review-pr skill
    review_dir = skills_dir / "review-pr"
    if not review_dir.exists():
        review_dir.mkdir(parents=True, exist_ok=True)
        (review_dir / "SKILL.md").write_text("""---
name: review-pr
description: Review pull requests with code quality and security focus
user_invocable: true
tools: [read_file, semantic_search, grep]
---

# Pull Request Review

Conduct thorough code reviews focusing on quality, security, and best practices.

## Instructions

1. Review the PR changes systematically
2. Check for:
   - Code quality and readability
   - Security vulnerabilities (injection, XSS, etc.)
   - Performance implications
   - Test coverage
   - Documentation updates
3. Provide constructive feedback with specific suggestions
4. Highlight both issues and good practices

## Review Checklist

- [ ] Code follows project conventions
- [ ] No obvious security vulnerabilities
- [ ] Error handling is appropriate
- [ ] Tests cover new functionality
- [ ] No unnecessary complexity
- [ ] Documentation is updated if needed

## Output Format

Provide feedback in sections:
1. **Summary**: Overall assessment
2. **Positives**: What's done well
3. **Concerns**: Issues that should be addressed
4. **Suggestions**: Optional improvements
""")
        console.print("[green]Created example skill: review-pr[/green]")

    # Create example security-review skill
    security_dir = skills_dir / "security-review"
    if not security_dir.exists():
        security_dir.mkdir(parents=True, exist_ok=True)
        (security_dir / "SKILL.md").write_text("""---
name: security-review
description: Security-focused code review for vulnerabilities
user_invocable: true
tools: [read_file, grep, semantic_search]
---

# Security Review

Conduct security-focused code review to identify vulnerabilities.

## Instructions

1. Search for common vulnerability patterns:
   - SQL injection
   - XSS (Cross-Site Scripting)
   - Command injection
   - Path traversal
   - Insecure deserialization
   - Hardcoded secrets
   - Improper input validation

2. Review authentication and authorization:
   - Session management
   - Password handling
   - Access control

3. Check data handling:
   - Sensitive data exposure
   - Encryption usage
   - Data validation

## OWASP Top 10 Checklist

- [ ] A01: Broken Access Control
- [ ] A02: Cryptographic Failures
- [ ] A03: Injection
- [ ] A04: Insecure Design
- [ ] A05: Security Misconfiguration
- [ ] A06: Vulnerable Components
- [ ] A07: Authentication Failures
- [ ] A08: Software Integrity Failures
- [ ] A09: Logging Failures
- [ ] A10: SSRF

## Output

Report findings with:
- Severity (Critical/High/Medium/Low)
- Location (file:line)
- Description
- Remediation suggestion
""")
        console.print("[green]Created example skill: security-review[/green]")

    console.print()
    console.print(f"[cyan]Skills directory initialized at {skills_dir}[/cyan]")
    console.print("[dim]Use 'emdash skills list' to see available skills.[/dim]")
