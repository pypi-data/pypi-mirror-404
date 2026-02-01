"""
Ragtime CLI - semantic search and memory storage.
"""

from pathlib import Path
import subprocess
import click

from .db import RagtimeDB
from .config import RagtimeConfig, init_config
from .indexers.docs import index_directory as index_docs
from .memory import Memory, MemoryStore


def get_db(project_path: Path) -> RagtimeDB:
    """Get or create database for a project."""
    db_path = project_path / ".ragtime" / "index"
    return RagtimeDB(db_path)


def get_memory_store(project_path: Path) -> MemoryStore:
    """Get memory store for a project."""
    db = get_db(project_path)
    return MemoryStore(project_path, db)


def get_author() -> str:
    """Get the current developer's username."""
    try:
        # Try gh CLI first
        result = subprocess.run(
            ["gh", "api", "user", "--jq", ".login"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    try:
        # Fall back to git config
        result = subprocess.run(
            ["git", "config", "user.name"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().lower().replace(" ", "-")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return "unknown"


def check_ghp_installed() -> bool:
    """Check if ghp-cli is installed."""
    try:
        result = subprocess.run(
            ["ghp", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def get_issue_from_ghp(issue_num: int, path: Path) -> dict | None:
    """Get issue details using ghp issue open."""
    try:
        result = subprocess.run(
            ["ghp", "issue", "open", str(issue_num), "--json"],
            cwd=path,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            import json
            return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        pass
    return None


def get_issue_from_gh(issue_num: int, path: Path) -> dict | None:
    """Get issue details using gh CLI."""
    try:
        result = subprocess.run(
            ["gh", "issue", "view", str(issue_num), "--json", "title,body,labels,number"],
            cwd=path,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            import json
            return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        pass
    return None


def get_current_branch(path: Path) -> str | None:
    """Get the current git branch name."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=path,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


@click.group()
@click.version_option(version="0.1.2")
def main():
    """Ragtime - semantic search over code and documentation."""
    pass


@main.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path), default=".")
def init(path: Path):
    """Initialize ragtime config for a project."""
    path = path.resolve()
    config = init_config(path)
    click.echo(f"Created .ragtime/config.yaml with defaults:")
    click.echo(f"  Docs paths: {config.docs.paths}")
    click.echo(f"  Code paths: {config.code.paths}")
    click.echo(f"  Languages: {config.code.languages}")

    # Create memory directory structure
    memory_dir = path / ".claude" / "memory"
    (memory_dir / "app").mkdir(parents=True, exist_ok=True)
    (memory_dir / "team").mkdir(parents=True, exist_ok=True)
    (memory_dir / "branches").mkdir(parents=True, exist_ok=True)
    click.echo(f"\nCreated .claude/memory/ structure")

    # Check for ghp-cli
    if check_ghp_installed():
        click.echo(f"\n✓ ghp-cli detected - will use for issue lookups")
    else:
        click.echo(f"\n• ghp-cli not found - will use gh CLI for issue lookups")
        click.echo(f"  Install ghp for enhanced workflow: pip install ghp-cli")


@main.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path), default=".")
@click.option("--type", "index_type", type=click.Choice(["all", "docs", "code"]), default="all")
@click.option("--clear", is_flag=True, help="Clear existing index before indexing")
def index(path: Path, index_type: str, clear: bool):
    """Index a project directory."""
    path = path.resolve()
    db = get_db(path)
    config = RagtimeConfig.load(path)

    if clear:
        click.echo("Clearing existing index...")
        if index_type == "all":
            db.clear()
        else:
            db.clear(type_filter=index_type)

    # Index docs
    if index_type in ("all", "docs"):
        total_entries = []
        for docs_path in config.docs.paths:
            docs_root = path / docs_path
            if not docs_root.exists():
                click.echo(f"  Docs path {docs_root} not found, skipping...")
                continue
            click.echo(f"Indexing docs in {docs_root}...")
            entries = index_docs(
                docs_root,
                patterns=config.docs.patterns,
                exclude=config.docs.exclude,
            )
            total_entries.extend(entries)

        if total_entries:
            ids = [e.file_path for e in total_entries]
            documents = [e.content for e in total_entries]
            metadatas = [e.to_metadata() for e in total_entries]

            db.upsert(ids=ids, documents=documents, metadatas=metadatas)
            click.echo(f"  Indexed {len(total_entries)} documents")
        else:
            click.echo("  No documents found")

    # Index code
    if index_type in ("all", "code"):
        # Build exclude list that includes docs paths
        code_exclude = list(config.code.exclude)
        for docs_path in config.docs.paths:
            code_exclude.append(f"**/{docs_path}/**")

        click.echo("Code indexing not yet implemented")
        click.echo(f"  Will exclude docs paths: {config.docs.paths}")
        # TODO: Implement code indexer with code_exclude

    # Show stats
    stats = db.stats()
    click.echo(f"\nIndex stats: {stats['total']} total ({stats['docs']} docs, {stats['code']} code)")


@main.command()
@click.argument("query")
@click.option("--path", type=click.Path(exists=True, path_type=Path), default=".")
@click.option("--type", "type_filter", type=click.Choice(["all", "docs", "code"]), default="all")
@click.option("--namespace", "-n", help="Filter by namespace")
@click.option("--limit", "-l", default=5, help="Max results")
@click.option("--verbose", "-v", is_flag=True, help="Show full content")
def search(query: str, path: Path, type_filter: str, namespace: str, limit: int, verbose: bool):
    """Search indexed content."""
    path = Path(path).resolve()
    db = get_db(path)

    type_arg = None if type_filter == "all" else type_filter

    results = db.search(
        query=query,
        limit=limit,
        type_filter=type_arg,
        namespace=namespace,
    )

    if not results:
        click.echo("No results found.")
        return

    for i, result in enumerate(results, 1):
        meta = result["metadata"]
        distance = result["distance"]
        score = 1 - distance if distance else None

        click.echo(f"\n{'─' * 60}")
        click.echo(f"[{i}] {meta.get('file', 'unknown')}")
        click.echo(f"    Type: {meta.get('type')} | Namespace: {meta.get('namespace', '-')}")
        if score:
            click.echo(f"    Score: {score:.3f}")

        if verbose:
            click.echo(f"\n{result['content'][:500]}...")
        else:
            # Show first 150 chars
            preview = result["content"][:150].replace("\n", " ")
            click.echo(f"    {preview}...")


@main.command()
@click.option("--path", type=click.Path(exists=True, path_type=Path), default=".")
def stats(path: Path):
    """Show index statistics."""
    path = Path(path).resolve()
    db = get_db(path)

    s = db.stats()
    click.echo(f"Total indexed: {s['total']}")
    click.echo(f"  Docs: {s['docs']}")
    click.echo(f"  Code: {s['code']}")


@main.command()
@click.option("--path", type=click.Path(exists=True, path_type=Path), default=".")
@click.option("--type", "type_filter", type=click.Choice(["all", "docs", "code"]), default="all")
@click.confirmation_option(prompt="Are you sure you want to clear the index?")
def clear(path: Path, type_filter: str):
    """Clear the index."""
    path = Path(path).resolve()
    db = get_db(path)

    if type_filter == "all":
        db.clear()
        click.echo("Index cleared.")
    else:
        db.clear(type_filter=type_filter)
        click.echo(f"Cleared {type_filter} from index.")


@main.command()
@click.option("--path", type=click.Path(exists=True, path_type=Path), default=".")
def config(path: Path):
    """Show current configuration."""
    path = Path(path).resolve()
    cfg = RagtimeConfig.load(path)

    click.echo("Docs:")
    click.echo(f"  Paths: {cfg.docs.paths}")
    click.echo(f"  Patterns: {cfg.docs.patterns}")
    click.echo(f"  Exclude: {cfg.docs.exclude}")
    click.echo("\nCode:")
    click.echo(f"  Paths: {cfg.code.paths}")
    click.echo(f"  Languages: {cfg.code.languages}")
    click.echo(f"  Exclude: {cfg.code.exclude}")


# ============================================================================
# Memory Storage Commands
# ============================================================================


@main.command()
@click.argument("content")
@click.option("--path", type=click.Path(exists=True, path_type=Path), default=".")
@click.option("--namespace", "-n", required=True, help="Namespace: app, team, user-{name}, branch-{name}")
@click.option("--type", "-t", "memory_type", required=True,
              type=click.Choice(["architecture", "feature", "integration", "convention",
                                 "preference", "decision", "pattern", "task-state", "handoff"]),
              help="Memory type")
@click.option("--component", "-c", help="Component area (e.g., auth, claims, shifts)")
@click.option("--confidence", default="medium",
              type=click.Choice(["high", "medium", "low"]),
              help="Confidence level")
@click.option("--confidence-reason", help="Why this confidence level")
@click.option("--source", "-s", default="remember", help="Source of this memory")
@click.option("--issue", help="Related GitHub issue (e.g., #301)")
@click.option("--epic", help="Parent epic (e.g., #286)")
@click.option("--branch", help="Related branch name")
def remember(content: str, path: Path, namespace: str, memory_type: str,
             component: str, confidence: str, confidence_reason: str,
             source: str, issue: str, epic: str, branch: str):
    """Store a memory with structured metadata.

    Example:
        ragtime remember "Auth uses JWT with 15-min expiry" \\
            --namespace app --type architecture --component auth
    """
    path = Path(path).resolve()
    store = get_memory_store(path)

    memory = Memory(
        content=content,
        namespace=namespace,
        type=memory_type,
        component=component,
        confidence=confidence,
        confidence_reason=confidence_reason,
        source=source,
        author=get_author(),
        issue=issue,
        epic=epic,
        branch=branch,
    )

    file_path = store.save(memory)
    click.echo(f"✓ Memory saved: {memory.id}")
    click.echo(f"  File: {file_path.relative_to(path)}")
    click.echo(f"  Namespace: {namespace}")
    click.echo(f"  Type: {memory_type}")


@main.command("store-doc")
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@click.option("--path", type=click.Path(exists=True, path_type=Path), default=".")
@click.option("--namespace", "-n", required=True, help="Namespace for the document")
@click.option("--type", "-t", "doc_type", default="handoff",
              type=click.Choice(["handoff", "document", "plan", "notes"]),
              help="Document type")
def store_doc(file: Path, path: Path, namespace: str, doc_type: str):
    """Store a document verbatim (like handoff.md).

    Example:
        ragtime store-doc .claude/handoff.md --namespace branch-feature/auth
    """
    path = Path(path).resolve()
    file = Path(file).resolve()
    store = get_memory_store(path)

    memory = store.store_document(file, namespace, doc_type)
    click.echo(f"✓ Document stored: {memory.id}")
    click.echo(f"  Source: {file.name}")
    click.echo(f"  Namespace: {namespace}")
    click.echo(f"  Type: {doc_type}")


@main.command()
@click.argument("memory_id")
@click.option("--path", type=click.Path(exists=True, path_type=Path), default=".")
@click.confirmation_option(prompt="Are you sure you want to delete this memory?")
def forget(memory_id: str, path: Path):
    """Delete a memory by ID.

    Example:
        ragtime forget abc123
    """
    path = Path(path).resolve()
    store = get_memory_store(path)

    if store.delete(memory_id):
        click.echo(f"✓ Memory {memory_id} deleted")
    else:
        click.echo(f"✗ Memory {memory_id} not found", err=True)


@main.command()
@click.argument("memory_id")
@click.option("--path", type=click.Path(exists=True, path_type=Path), default=".")
@click.option("--confidence", default="high",
              type=click.Choice(["high", "medium", "low"]),
              help="Confidence level for graduated memory")
def graduate(memory_id: str, path: Path, confidence: str):
    """Graduate a branch memory to app namespace.

    Copies the memory to app namespace with high confidence
    and marks the original as graduated.

    Example:
        ragtime graduate abc123
    """
    path = Path(path).resolve()
    store = get_memory_store(path)

    try:
        graduated = store.graduate(memory_id, confidence)
        if graduated:
            click.echo(f"✓ Memory graduated to app namespace")
            click.echo(f"  New ID: {graduated.id}")
            click.echo(f"  Original marked as: graduated")
        else:
            click.echo(f"✗ Memory {memory_id} not found", err=True)
    except ValueError as e:
        click.echo(f"✗ {e}", err=True)


@main.command("memories")
@click.option("--path", type=click.Path(exists=True, path_type=Path), default=".")
@click.option("--namespace", "-n", help="Filter by namespace (use * suffix for prefix match)")
@click.option("--type", "-t", "type_filter", help="Filter by type")
@click.option("--status", "-s", help="Filter by status (active, graduated, abandoned)")
@click.option("--component", "-c", help="Filter by component")
@click.option("--limit", "-l", default=20, help="Max results")
@click.option("--verbose", "-v", is_flag=True, help="Show full content")
def list_memories(path: Path, namespace: str, type_filter: str, status: str,
                  component: str, limit: int, verbose: bool):
    """List memories with optional filters.

    Examples:
        ragtime memories --namespace app
        ragtime memories --namespace branch-* --status active
        ragtime memories --type decision --component auth
    """
    path = Path(path).resolve()
    store = get_memory_store(path)

    memories = store.list_memories(
        namespace=namespace,
        type_filter=type_filter,
        status=status,
        component=component,
        limit=limit,
    )

    if not memories:
        click.echo("No memories found.")
        return

    click.echo(f"Found {len(memories)} memories:\n")

    for mem in memories:
        click.echo(f"{'─' * 60}")
        click.echo(f"[{mem.id}] {mem.namespace} / {mem.type}")
        if mem.component:
            click.echo(f"    Component: {mem.component}")
        click.echo(f"    Status: {mem.status} | Confidence: {mem.confidence}")
        click.echo(f"    Added: {mem.added} | Source: {mem.source}")

        if verbose:
            click.echo(f"\n{mem.content[:500]}...")
        else:
            preview = mem.content[:100].replace("\n", " ")
            click.echo(f"    {preview}...")


@main.command()
@click.option("--path", type=click.Path(exists=True, path_type=Path), default=".")
def reindex(path: Path):
    """Reindex all memory files.

    Scans .claude/memory/ and adds any files not in the index.
    """
    path = Path(path).resolve()
    store = get_memory_store(path)

    count = store.reindex()
    click.echo(f"✓ Reindexed {count} memory files")


@main.command("new-branch")
@click.argument("issue", type=int)
@click.option("--path", type=click.Path(exists=True, path_type=Path), default=".")
@click.option("--content", help="Context document content (overrides auto-generated scaffold)")
@click.option("--issue-json", "issue_json", help="Issue data as JSON (from ghp hook, skips fetch)")
@click.option("--branch", "-b", help="Branch name (auto-detected from git if not provided)")
def new_branch(issue: int, path: Path, content: str, issue_json: str, branch: str):
    """Initialize a branch context from a GitHub issue.

    Creates .claude/memory/branches/{branch-slug}/context.md with either:
    - Provided content (from --content flag, e.g., LLM-generated plan)
    - Auto-generated scaffold from issue metadata (fallback)

    Examples:
        ragtime new-branch 42                         # Scaffold from issue #42
        ragtime new-branch 42 --content "..."         # Use provided content
        ragtime new-branch 42 --issue-json '{...}'    # Use JSON from ghp hook
        ragtime new-branch 42 --branch my-feat        # Specify branch name
    """
    import json
    from datetime import date

    path = Path(path).resolve()

    # Determine branch name
    if not branch:
        branch = get_current_branch(path)
        if not branch or branch in ("main", "master"):
            click.echo("✗ Not on a feature branch. Use --branch to specify.", err=True)
            return

    # Create branch slug for folder name
    branch_slug = branch.replace("/", "-")
    branch_dir = path / ".claude" / "memory" / "branches" / branch_slug
    branch_dir.mkdir(parents=True, exist_ok=True)

    context_file = branch_dir / "context.md"

    if content:
        # Use provided content directly
        context_file.write_text(content)
        click.echo(f"✓ Created context.md with provided content")
        click.echo(f"  Path: {context_file.relative_to(path)}")
        return

    # Get issue data from JSON, ghp, or gh
    issue_data = None
    source = None

    # Use provided JSON if available (from ghp hook)
    if issue_json:
        try:
            issue_data = json.loads(issue_json)
            source = "ghp-hook"
        except json.JSONDecodeError as e:
            click.echo(f"✗ Invalid JSON: {e}", err=True)
            return
    else:
        # Fall back to fetching from API
        click.echo(f"Fetching issue #{issue}...")

        # Try ghp first if available
        if check_ghp_installed():
            issue_data = get_issue_from_ghp(issue, path)
            source = "ghp"

        # Fall back to gh
        if not issue_data:
            issue_data = get_issue_from_gh(issue, path)
            source = "gh"

    if not issue_data:
        click.echo(f"✗ Could not fetch issue #{issue}", err=True)
        click.echo("  Make sure you're in a git repo with GitHub remote")
        return

    # Extract issue fields
    title = issue_data.get("title", f"Issue #{issue}")
    body = issue_data.get("body", "")
    labels = issue_data.get("labels", [])

    # Format labels
    if labels:
        if isinstance(labels[0], dict):
            label_names = [l.get("name", "") for l in labels]
        else:
            label_names = labels
        labels_str = ", ".join(label_names)
    else:
        labels_str = ""

    # Generate scaffold context.md
    scaffold = f"""---
type: context
branch: {branch}
issue: {issue}
status: active
created: '{date.today().isoformat()}'
author: {get_author()}
---

## Issue

**#{issue}**: {title}

{f"**Labels**: {labels_str}" if labels_str else ""}

## Description

{body if body else "_No description provided_"}

## Plan

<!-- Implementation steps - fill in or let Claude generate -->

- [ ] TODO: Define implementation steps

## Acceptance Criteria

<!-- What needs to be true for this to be complete? -->

## Notes

<!-- Additional context, decisions, blockers -->

"""

    context_file.write_text(scaffold)

    click.echo(f"✓ Created context.md from issue #{issue}")
    click.echo(f"  Path: {context_file.relative_to(path)}")
    click.echo(f"  Source: {source}")
    click.echo(f"\nNext: Fill in the Plan section or use /start to generate it")


# ============================================================================
# Command Installation
# ============================================================================


def get_commands_dir() -> Path:
    """Get the directory containing bundled command templates."""
    return Path(__file__).parent / "commands"


def get_available_commands() -> list[str]:
    """List available command templates."""
    commands_dir = get_commands_dir()
    if not commands_dir.exists():
        return []
    return [f.stem for f in commands_dir.glob("*.md")]


@main.command("install")
@click.option("--global", "global_install", is_flag=True, help="Install to ~/.claude/commands/")
@click.option("--workspace", "workspace_install", is_flag=True, help="Install to .claude/commands/")
@click.option("--list", "list_commands", is_flag=True, help="List available commands")
@click.option("--force", is_flag=True, help="Overwrite existing commands without asking")
@click.argument("commands", nargs=-1)
def install_commands(global_install: bool, workspace_install: bool, list_commands: bool,
                     force: bool, commands: tuple):
    """Install Claude command templates.

    Examples:
        ragtime install --list                    # List available commands
        ragtime install --workspace               # Install all to .claude/commands/
        ragtime install --global remember recall  # Install specific commands globally
    """
    available = get_available_commands()

    if list_commands:
        click.echo("Available commands:")
        for cmd in available:
            click.echo(f"  - {cmd}")
        return

    # Determine target directory
    if global_install and workspace_install:
        click.echo("Error: Cannot specify both --global and --workspace", err=True)
        return

    if global_install:
        target_dir = Path.home() / ".claude" / "commands"
    elif workspace_install:
        target_dir = Path.cwd() / ".claude" / "commands"
    else:
        # Default to workspace
        target_dir = Path.cwd() / ".claude" / "commands"
        click.echo("Installing to workspace (.claude/commands/)")
        click.echo("Use --global for ~/.claude/commands/")

    # Determine which commands to install
    if commands:
        to_install = [c for c in commands if c in available]
        not_found = [c for c in commands if c not in available]
        if not_found:
            click.echo(f"Warning: Commands not found: {', '.join(not_found)}", err=True)
    else:
        to_install = available

    if not to_install:
        click.echo("No commands to install.")
        return

    # Create target directory
    target_dir.mkdir(parents=True, exist_ok=True)

    # Install each command
    commands_dir = get_commands_dir()
    installed = 0
    skipped = 0

    for cmd in to_install:
        source = commands_dir / f"{cmd}.md"
        target = target_dir / f"{cmd}.md"

        if target.exists() and not force:
            if click.confirm(f"  {cmd}.md exists. Overwrite?", default=False):
                target.write_text(source.read_text())
                click.echo(f"  ✓ {cmd}.md (overwritten)")
                installed += 1
            else:
                click.echo(f"  - {cmd}.md (skipped)")
                skipped += 1
        else:
            target.write_text(source.read_text())
            click.echo(f"  ✓ {cmd}.md")
            installed += 1

    click.echo(f"\nInstalled {installed} commands to {target_dir}")
    if skipped:
        click.echo(f"Skipped {skipped} existing commands (use --force to overwrite)")

    # Remind about MCP server setup
    click.echo("\nTo use these commands, add ragtime MCP server to your Claude config:")
    click.echo('  "ragtime": {"command": "ragtime-mcp", "args": ["--path", "."]}')


@main.command("setup-ghp")
@click.option("--remove", is_flag=True, help="Remove ragtime hooks from ghp")
def setup_ghp(remove: bool):
    """Register ragtime hooks with ghp-cli.

    Adds event hooks so ghp automatically creates context.md when starting issues.

    Examples:
        ragtime setup-ghp          # Register hooks
        ragtime setup-ghp --remove # Remove hooks
    """
    if not check_ghp_installed():
        click.echo("✗ ghp-cli not installed", err=True)
        click.echo("  Install with: npm install -g @bretwardjames/ghp-cli")
        return

    hook_name = "ragtime-context"

    if remove:
        # Remove the hook
        result = subprocess.run(
            ["ghp", "hooks", "remove", hook_name],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            click.echo(f"✓ Removed hook: {hook_name}")
        else:
            if "not found" in result.stderr.lower():
                click.echo(f"• Hook {hook_name} not registered")
            else:
                click.echo(f"✗ Failed to remove hook: {result.stderr}", err=True)
        return

    # Check if hook already exists
    result = subprocess.run(
        ["ghp", "hooks", "show", hook_name],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        click.echo(f"• Hook {hook_name} already registered")
        click.echo("  Use --remove to unregister first")
        return

    # Register the hook
    # The command uses ${issue.number}, ${issue.json}, and ${branch} from ghp
    hook_command = "ragtime new-branch ${issue.number} --issue-json '${issue.json}' --branch '${branch}'"

    result = subprocess.run(
        [
            "ghp", "hooks", "add", hook_name,
            "--event", "issue-started",
            "--command", hook_command,
            "--display-name", "Ragtime Context",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        click.echo(f"✓ Registered hook: {hook_name}")
        click.echo(f"  Event: issue-started")
        click.echo(f"  Action: Creates context.md from issue metadata")
        click.echo(f"\nNow when you run 'ghp start <issue>', ragtime will auto-create context.md")
    else:
        click.echo(f"✗ Failed to register hook: {result.stderr}", err=True)


# ============================================================================
# Cross-Branch Sync Commands
# ============================================================================


def get_branch_slug(ref: str) -> str:
    """Convert a git ref to a branch slug for folder naming."""
    # Remove origin/ prefix if present
    if ref.startswith("origin/"):
        ref = ref[7:]
    # Replace / with - for folder names
    return ref.replace("/", "-")


@main.command()
@click.argument("ref")
@click.option("--path", type=click.Path(exists=True, path_type=Path), default=".")
def sync(ref: str, path: Path):
    """Sync memories from a remote branch.

    Fetches .claude/memory/branches/* from the specified git ref
    and copies to a local (unmerged) folder for searching.

    Examples:
        ragtime sync origin/jm/feature-auth
        ragtime sync origin/sm/fix-bug
    """
    import shutil
    import tempfile

    path = Path(path).resolve()
    store = get_memory_store(path)

    # Get the branch slug for folder naming
    branch_slug = get_branch_slug(ref)
    unmerged_dir = path / ".claude" / "memory" / "branches" / f"{branch_slug}(unmerged)"

    click.echo(f"Syncing memories from {ref}...")

    # Fetch the ref first
    result = subprocess.run(
        ["git", "fetch", "origin"],
        cwd=path,
        capture_output=True,
        text=True,
    )

    # Check if the ref exists
    result = subprocess.run(
        ["git", "rev-parse", "--verify", ref],
        cwd=path,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        click.echo(f"✗ Ref not found: {ref}", err=True)
        return

    commit_hash = result.stdout.strip()[:8]

    # Check if there are memory files in that ref
    result = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", ref, ".claude/memory/branches/"],
        cwd=path,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0 or not result.stdout.strip():
        click.echo(f"✗ No memories found in {ref}", err=True)
        return

    files = result.stdout.strip().split("\n")
    click.echo(f"  Found {len(files)} memory files")

    # Clear existing unmerged folder if it exists
    if unmerged_dir.exists():
        shutil.rmtree(unmerged_dir)

    unmerged_dir.mkdir(parents=True, exist_ok=True)

    # Extract each file
    synced = 0
    for file_path in files:
        if not file_path.endswith(".md"):
            continue

        # Get file content from git
        result = subprocess.run(
            ["git", "show", f"{ref}:{file_path}"],
            cwd=path,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            continue

        content = result.stdout

        # Determine target path (flatten to unmerged folder)
        # Original: .claude/memory/branches/sm-feature/abc.md
        # Target: .claude/memory/branches/sm-feature(unmerged)/abc.md
        filename = Path(file_path).name
        target_path = unmerged_dir / filename

        target_path.write_text(content)
        synced += 1

        # Index with pre-merge status
        try:
            memory = Memory.from_file(target_path)
            memory.status = "pre-merge"
            # Update the namespace to include (unmerged) marker
            memory.namespace = f"branch-{branch_slug}(unmerged)"

            store.db.upsert(
                ids=[f"{memory.id}-unmerged"],
                documents=[memory.content],
                metadatas=[{
                    **memory.to_metadata(),
                    "status": "pre-merge",
                    "source_ref": ref,
                    "source_commit": commit_hash,
                }],
            )
        except Exception as e:
            click.echo(f"  Warning: Could not index {filename}: {e}", err=True)

    # Write source tracking file
    source_file = unmerged_dir / ".source"
    source_file.write_text(f"{ref} @ {commit_hash}\n")

    click.echo(f"✓ Synced {synced} memories to {unmerged_dir.relative_to(path)}")
    click.echo(f"  Source: {ref} @ {commit_hash}")
    click.echo(f"\nSearch with: ragtime search 'query' --namespace 'branch-{branch_slug}(unmerged)'")


@main.command()
@click.option("--path", type=click.Path(exists=True, path_type=Path), default=".")
@click.option("--dry-run", is_flag=True, help="Show what would be pruned without deleting")
def prune(path: Path, dry_run: bool):
    """Remove stale (unmerged) memory folders.

    Checks each (unmerged) folder and removes it if:
    - The source branch was deleted
    - The source branch was merged (PR closed)

    Examples:
        ragtime prune --dry-run  # See what would be pruned
        ragtime prune            # Actually prune
    """
    import shutil

    path = Path(path).resolve()
    branches_dir = path / ".claude" / "memory" / "branches"

    if not branches_dir.exists():
        click.echo("No branches directory found.")
        return

    # Find all (unmerged) folders
    unmerged_folders = [d for d in branches_dir.iterdir()
                        if d.is_dir() and d.name.endswith("(unmerged)")]

    if not unmerged_folders:
        click.echo("No (unmerged) folders to prune.")
        return

    click.echo(f"Checking {len(unmerged_folders)} (unmerged) folders...\n")

    to_prune = []
    to_keep = []

    for folder in unmerged_folders:
        source_file = folder / ".source"
        if not source_file.exists():
            # No source tracking - mark for pruning
            to_prune.append((folder, "no source tracking"))
            continue

        source_info = source_file.read_text().strip()
        ref = source_info.split(" @ ")[0] if " @ " in source_info else source_info

        # Check if ref still exists
        result = subprocess.run(
            ["git", "rev-parse", "--verify", ref],
            cwd=path,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            # Ref doesn't exist - check if it was merged
            # Extract branch name from ref (e.g., origin/jm/feature -> jm/feature)
            branch_name = ref.replace("origin/", "") if ref.startswith("origin/") else ref

            # Check if a PR was merged for this branch
            pr_result = subprocess.run(
                ["gh", "pr", "list", "--head", branch_name, "--state", "merged", "--json", "number"],
                cwd=path,
                capture_output=True,
                text=True,
            )

            if pr_result.returncode == 0 and pr_result.stdout.strip() != "[]":
                to_prune.append((folder, f"PR merged for {branch_name}"))
            else:
                to_prune.append((folder, f"branch deleted: {ref}"))
        else:
            to_keep.append((folder, ref))

    # Report findings
    if to_prune:
        click.echo("Will prune:")
        for folder, reason in to_prune:
            click.echo(f"  ✗ {folder.name} ({reason})")

    if to_keep:
        click.echo("\nKeeping (branch still active):")
        for folder, ref in to_keep:
            click.echo(f"  ✓ {folder.name}")

    if not to_prune:
        click.echo("\nNothing to prune.")
        return

    # Actually prune if not dry-run
    if dry_run:
        click.echo(f"\n--dry-run: Would prune {len(to_prune)} folders")
    else:
        click.echo("")
        db = get_db(path)

        for folder, reason in to_prune:
            # Remove from index
            branch_slug = folder.name.replace("(unmerged)", "")
            # Find and delete indexed memories for this folder
            results = db.collection.get(
                where={"namespace": f"branch-{folder.name}"}
            )
            if results["ids"]:
                db.delete(results["ids"])

            # Remove folder
            shutil.rmtree(folder)
            click.echo(f"  Pruned: {folder.name}")

        click.echo(f"\n✓ Pruned {len(to_prune)} folders")


if __name__ == "__main__":
    main()
