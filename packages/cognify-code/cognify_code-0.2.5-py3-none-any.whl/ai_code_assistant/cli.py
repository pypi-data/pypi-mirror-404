"""Command-line interface for AI Code Assistant."""

import sys
from pathlib import Path
from typing import List, Optional, Tuple

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from ai_code_assistant import __version__
from ai_code_assistant.config import Config, load_config, get_language_by_extension
from ai_code_assistant.llm import LLMManager
from ai_code_assistant.reviewer import CodeAnalyzer
from ai_code_assistant.generator import CodeGenerator
from ai_code_assistant.chat import ChatSession
from ai_code_assistant.editor import FileEditor
from ai_code_assistant.utils import FileHandler, get_formatter
from ai_code_assistant.context import ContextSelector, ContextConfig

console = Console()


WELCOME_BANNER = """
[bold cyan]
   ██████╗ ██████╗  ██████╗ ███╗   ██╗██╗███████╗██╗   ██╗
  ██╔════╝██╔═══██╗██╔════╝ ████╗  ██║██║██╔════╝╚██╗ ██╔╝
  ██║     ██║   ██║██║  ███╗██╔██╗ ██║██║█████╗   ╚████╔╝ 
  ██║     ██║   ██║██║   ██║██║╚██╗██║██║██╔══╝    ╚██╔╝  
  ╚██████╗╚██████╔╝╚██████╔╝██║ ╚████║██║██║        ██║   
   ╚═════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝╚═╝╚═╝        ╚═╝   
[/bold cyan]
"""


def show_welcome():
    """Display welcome screen with logo and quick start info."""
    console.print(WELCOME_BANNER)
    console.print(f"[bold white]  Your Local AI-Powered Code Assistant[/bold white]  [dim]v{__version__}[/dim]\n")
    
    info_text = """[bold cyan]🚀 Quick Start:[/bold cyan]
  [green]cognify status[/green]        Check Ollama connection
  [green]cognify review[/green] <file>  Review code for issues
  [green]cognify generate[/green] "..." Generate code from description
  [green]cognify agent[/green]          Start interactive AI agent
  [green]cognify chat[/green]           Chat about your code

[bold cyan]📚 More Commands:[/bold cyan]
  [green]cognify edit[/green] <file>    Edit file with AI
  [green]cognify refactor[/green]       Multi-file refactoring
  [green]cognify search[/green] "..."   Semantic code search
  [green]cognify git commit[/green]     AI-powered commit messages

[dim]Run [white]cognify --help[/white] for all commands[/dim]
[dim]Docs: https://github.com/akkssy/cognify-ai[/dim]"""
    
    console.print(Panel(info_text, border_style="cyan", padding=(1, 2)))



def get_components(config_path: Optional[Path] = None):
    """Initialize and return all components."""
    config = load_config(config_path)
    llm = LLMManager(config)
    return config, llm


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="cognify")
@click.option("--config", "-c", type=click.Path(exists=True, path_type=Path), help="Config file path")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.pass_context
def main(ctx, config: Optional[Path], verbose: bool):
    """Cognify - Your Local AI-Powered Code Assistant."""
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config
    ctx.obj["verbose"] = verbose
    
    # Show welcome screen if no command is provided
    if ctx.invoked_subcommand is None:
        show_welcome()


@main.command()
@click.argument("files", nargs=-1, type=click.Path(exists=True, path_type=Path))
@click.option("--type", "-t", "review_type", default="full", 
              type=click.Choice(["full", "quick", "security"]), help="Review type")
@click.option("--format", "-f", "output_format", default="console",
              type=click.Choice(["console", "markdown", "json"]), help="Output format")
@click.option("--output", "-o", type=click.Path(path_type=Path), help="Output file path")
@click.option("--recursive", "-r", is_flag=True, help="Recursively review directories")
@click.option("--context", multiple=True, type=click.Path(exists=True, path_type=Path),
              help="Additional context files to include")
@click.option("--auto-context", is_flag=True, help="Automatically include related files as context")
@click.option("--max-context-tokens", type=int, default=8000, help="Max tokens for context")
@click.pass_context
def review(ctx, files: Tuple[Path, ...], review_type: str, output_format: str,
           output: Optional[Path], recursive: bool, context: Tuple[Path, ...],
           auto_context: bool, max_context_tokens: int):
    """Review code files for issues and improvements."""
    if not files:
        console.print("[red]Error:[/red] No files specified")
        sys.exit(1)

    config, llm = get_components(ctx.obj.get("config_path"))
    analyzer = CodeAnalyzer(config, llm)
    file_handler = FileHandler(config)
    formatter = get_formatter(output_format, config.output.use_colors)

    # Collect all files to review
    all_files = []
    for file_path in files:
        if file_path.is_dir():
            all_files.extend(file_handler.find_code_files(file_path, recursive=recursive))
        else:
            all_files.append(file_path)

    if not all_files:
        console.print("[yellow]No code files found to review[/yellow]")
        return

    console.print(f"\n[bold]Reviewing {len(all_files)} file(s)...[/bold]\n")
    
    all_output = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Analyzing...", total=len(all_files))
        
        for file_path in all_files:
            progress.update(task, description=f"Reviewing {file_path.name}...")
            
            result = analyzer.review_file(file_path, review_type=review_type)
            formatted = formatter.format_review(result)
            all_output.append(formatted)
            
            progress.advance(task)

    # Save or display output
    if output:
        combined = "\n\n---\n\n".join(all_output) if output_format != "json" else all_output
        if output_format == "json":
            import json
            combined = json.dumps([json.loads(o) for o in all_output], indent=2)
        output.write_text(combined)
        console.print(f"\n[green]Report saved to:[/green] {output}")


@main.command()
@click.argument("description")
@click.option("--mode", "-m", default="generic",
              type=click.Choice(["function", "class", "script", "test", "generic"]))
@click.option("--language", "-l", default="python", help="Target language")
@click.option("--name", "-n", help="Name for function/class")
@click.option("--params", "-p", help="Parameters (for function mode)")
@click.option("--output", "-o", type=click.Path(path_type=Path), help="Output file")
@click.option("--format", "-f", "output_format", default="console",
              type=click.Choice(["console", "markdown", "json"]))
@click.option("--source", "-s", type=click.Path(exists=True, path_type=Path),
              help="Source file (for test mode)")
@click.option("--stream/--no-stream", default=True, help="Stream output in real-time")
@click.option("--context", multiple=True, type=click.Path(exists=True, path_type=Path),
              help="Context files to include for better generation")
@click.option("--auto-context", is_flag=True, help="Automatically find relevant context files")
@click.option("--max-context-tokens", type=int, default=8000, help="Max tokens for context")
@click.pass_context
def generate(ctx, description: str, mode: str, language: str, name: Optional[str],
             params: Optional[str], output: Optional[Path], output_format: str,
             source: Optional[Path], stream: bool, context: Tuple[Path, ...],
             auto_context: bool, max_context_tokens: int):
    """Generate code from natural language description."""
    from rich.live import Live
    from rich.markdown import Markdown
    from rich.panel import Panel
    
    config, llm = get_components(ctx.obj.get("config_path"))
    generator = CodeGenerator(config, llm)
    formatter = get_formatter(output_format, config.output.use_colors)

    console.print(f"\n[bold]Generating {mode} in {language}...[/bold]\n")

    # Handle test mode source requirement
    source_code = ""
    if mode == "test":
        if not source:
            console.print("[red]Error:[/red] --source required for test mode")
            sys.exit(1)
        source_code = source.read_text()

    if stream:
        # Streaming mode - show output as it generates
        full_response = ""
        final_code = ""
        
        console.print("[dim]Streaming response...[/dim]\n")
        
        for chunk, is_complete in generator.generate_stream(
            description=description,
            mode=mode,
            language=language,
            name=name or "",
            parameters=params or "",
            source_code=source_code,
        ):
            if is_complete:
                final_code = chunk
            else:
                console.print(chunk, end="", highlight=False)
                full_response += chunk
        
        console.print("\n")
        
        # Create result for formatting
        from ai_code_assistant.generator import GenerationResult
        result = GenerationResult(
            code=final_code,
            language=language,
            mode=mode,
            description=description,
            raw_response=full_response,
        )
        
        # Show extracted code in a panel
        console.print(Panel(
            final_code,
            title=f"[bold green]Generated {mode.title()}[/bold green]",
            border_style="green",
        ))
    else:
        # Non-streaming mode (original behavior)
        with console.status("[bold green]Generating code..."):
            if mode == "function":
                result = generator.generate_function(
                    description=description, name=name or "generated_function",
                    language=language, parameters=params or "",
                )
            elif mode == "class":
                result = generator.generate_class(
                    description=description, name=name or "GeneratedClass", language=language,
                )
            elif mode == "script":
                result = generator.generate_script(
                    description=description, requirements=[description], language=language,
                )
            elif mode == "test":
                result = generator.generate_tests(source_code=source_code, language=language)
            else:
                result = generator.generate(description=description, language=language)

        formatted = formatter.format_generation(result)

    if output and result.success:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(result.code)
        console.print(f"\n[green]Code saved to:[/green] {output}")


@main.command()
@click.option("--context", "-c", multiple=True, type=click.Path(exists=True, path_type=Path),
              help="Files to load as context")
@click.option("--stream/--no-stream", default=True, help="Stream responses")
@click.pass_context
def chat(ctx, context: Tuple[Path, ...], stream: bool):
    """Start an interactive chat session about code."""
    config, llm = get_components(ctx.obj.get("config_path"))
    session = ChatSession(config, llm)

    # Load context files
    for file_path in context:
        if session.load_file_context(file_path):
            console.print(f"[dim]Loaded context: {file_path}[/dim]")
        else:
            console.print(f"[yellow]Warning: Could not load {file_path}[/yellow]")

    console.print(Panel(
        "[bold]AI Code Assistant Chat[/bold]\n\n"
        "Commands:\n"
        "  /load <file>  - Load a file as context\n"
        "  /clear        - Clear conversation history\n"
        "  /context      - Show loaded context files\n"
        "  /export       - Export conversation to markdown\n"
        "  /quit or exit - Exit chat\n",
        title="Interactive Mode",
    ))

    while True:
        try:
            user_input = console.input("\n[bold cyan]You>[/bold cyan] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye![/dim]")
            break

        if not user_input:
            continue

        # Handle exit commands without slash
        if user_input.lower() in ("exit", "quit", "bye", "q"):
            console.print("[dim]Goodbye![/dim]")
            break

        # Handle commands
        if user_input.startswith("/"):
            cmd_parts = user_input[1:].split(maxsplit=1)
            cmd = cmd_parts[0].lower()
            arg = cmd_parts[1] if len(cmd_parts) > 1 else ""

            if cmd == "quit" or cmd == "exit":
                console.print("[dim]Goodbye![/dim]")
                break
            elif cmd == "clear":
                session.clear_history()
                console.print("[dim]History cleared[/dim]")
            elif cmd == "context":
                if session._code_context:
                    for name in session._code_context:
                        console.print(f"  • {name}")
                else:
                    console.print("[dim]No context files loaded[/dim]")
            elif cmd == "load" and arg:
                path = Path(arg)
                if session.load_file_context(path):
                    console.print(f"[green]Loaded: {path}[/green]")
                else:
                    console.print(f"[red]Could not load: {path}[/red]")
            elif cmd == "export":
                export_path = Path("chat_export.md")
                export_path.write_text(session.export_history())
                console.print(f"[green]Exported to: {export_path}[/green]")
            else:
                console.print(f"[yellow]Unknown command: {cmd}[/yellow]")
            continue

        # Send message
        console.print("\n[bold green]Assistant>[/bold green] ", end="")

        if stream:
            for chunk in session.send_message(user_input, stream=True):
                console.print(chunk, end="")
            console.print()
        else:
            response = session.send_message(user_input, stream=False)
            console.print(response)


@main.command()
@click.pass_context
def status(ctx):
    """Check Ollama connection and model status."""
    config, llm = get_components(ctx.obj.get("config_path"))

    console.print("\n[bold]AI Code Assistant Status[/bold]\n")

    # Model info
    info = llm.get_model_info()
    console.print(f"Model: [cyan]{info['model']}[/cyan]")
    console.print(f"Server: [cyan]{info['base_url']}[/cyan]")
    console.print(f"Temperature: {info['temperature']}")
    console.print(f"Max tokens: {info['max_tokens']}")

    # Connection check
    console.print("\n[bold]Connection Test:[/bold]")
    with console.status("[bold yellow]Testing connection to Ollama..."):
        if llm.check_connection():
            console.print("[green]✓ Ollama is accessible and model is loaded[/green]")
        else:
            console.print("[red]✗ Could not connect to Ollama[/red]")
            console.print("\nMake sure Ollama is running:")
            console.print("  1. Install Ollama: https://ollama.ai")
            console.print(f"  2. Pull the model: ollama pull {info['model']}")
            console.print("  3. Start Ollama: ollama serve")

    # Index status
    console.print("\n[bold]Codebase Index:[/bold]")
    try:
        from ai_code_assistant.retrieval import CodebaseSearch
        search = CodebaseSearch(root_path=str(Path.cwd()))
        count = search._collection.count()
        console.print(f"[green]✓ Index found with {count} chunks[/green]")
    except FileNotFoundError:
        console.print("[yellow]○ No index found. Run 'ai-assist index' to create one.[/yellow]")
    except Exception as e:
        console.print(f"[red]✗ Index error: {e}[/red]")


@main.command()
@click.argument("directory", default=".", type=click.Path(exists=True, path_type=Path))
@click.option("--clear", is_flag=True, help="Clear existing index before indexing")
@click.pass_context
def index(ctx, directory: Path, clear: bool):
    """Index codebase for semantic search.

    This creates a searchable index of your code that enables
    natural language queries to find relevant code.

    Example:
        ai-assist index .
        ai-assist index ./src --clear
    """
    from ai_code_assistant.retrieval import CodebaseIndexer
    from ai_code_assistant.retrieval.indexer import IndexConfig

    config = load_config(ctx.obj.get("config_path"))

    # Create indexer config from app config
    index_config = IndexConfig(
        embedding_model=config.retrieval.embedding_model,
        persist_directory=config.retrieval.persist_directory,
        collection_name=config.retrieval.collection_name,
    )

    console.print(f"\n[bold]Indexing codebase: {directory.absolute()}[/bold]\n")
    console.print(f"Embedding model: [cyan]{index_config.embedding_model}[/cyan]")
    console.print(f"Index location: [cyan]{index_config.persist_directory}[/cyan]\n")

    indexer = CodebaseIndexer(config=index_config, root_path=str(directory.absolute()))

    if clear:
        console.print("[yellow]Clearing existing index...[/yellow]")
        indexer.clear_index()

    console.print("[bold green]Starting indexing...[/bold green]\n")

    # First-time model download might take a while
    console.print("[dim]Note: First run downloads the embedding model (~90MB)[/dim]\n")

    stats = indexer.index_directory(verbose=True)

    console.print(f"\n[bold green]✓ Indexing complete![/bold green]")
    console.print(f"  Files indexed: {len(stats.indexed_files)}")
    console.print(f"  Total chunks: {stats.total_chunks}")
    if stats.skipped_files:
        console.print(f"  Files skipped: {len(stats.skipped_files)}")
    if stats.errors:
        console.print(f"  [yellow]Errors: {len(stats.errors)}[/yellow]")


@main.command()
@click.argument("query")
@click.option("--top-k", "-k", default=5, help="Number of results to return")
@click.option("--file", "-f", "file_filter", help="Filter by file path")
@click.option("--language", "-l", "lang_filter", help="Filter by language")
@click.option("--format", "output_format", default="console",
              type=click.Choice(["console", "json", "context"]))
@click.pass_context
def search(ctx, query: str, top_k: int, file_filter: Optional[str],
           lang_filter: Optional[str], output_format: str):
    """Search codebase using natural language.

    Find relevant code by describing what you're looking for.

    Examples:
        ai-assist search "user authentication"
        ai-assist search "database connection" -k 10
        ai-assist search "error handling" --language python
        ai-assist search "config loading" --format context
    """
    from ai_code_assistant.retrieval import CodebaseSearch
    from ai_code_assistant.retrieval.indexer import IndexConfig

    config = load_config(ctx.obj.get("config_path"))

    index_config = IndexConfig(
        embedding_model=config.retrieval.embedding_model,
        persist_directory=config.retrieval.persist_directory,
        collection_name=config.retrieval.collection_name,
    )

    try:
        searcher = CodebaseSearch(config=index_config, root_path=str(Path.cwd()))
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        console.print("\nRun [cyan]ai-assist index .[/cyan] first to create the index.")
        sys.exit(1)

    with console.status("[bold green]Searching..."):
        response = searcher.search(
            query=query,
            top_k=top_k,
            file_filter=file_filter,
            language_filter=lang_filter,
        )

    if output_format == "json":
        import json
        output = {
            "query": response.query,
            "total_results": response.total_results,
            "results": [r.to_dict() for r in response.results],
        }
        console.print(json.dumps(output, indent=2))

    elif output_format == "context":
        # Format for use as LLM context
        console.print(response.format_for_llm(max_results=top_k))

    else:  # console
        console.print(f"\n[bold]Search:[/bold] {query}")
        console.print(f"[bold]Results:[/bold] {response.total_results}\n")

        if not response.has_results:
            console.print("[yellow]No results found.[/yellow]")
            console.print("\nTips:")
            console.print("  • Try broader search terms")
            console.print("  • Check if the codebase is indexed: ai-assist status")
            return

        for i, result in enumerate(response.results, 1):
            console.print(f"[bold cyan]─── Result {i} ───[/bold cyan]")
            console.print(f"[bold]{result.file_path}[/bold]:{result.start_line}-{result.end_line}")
            console.print(f"[dim]Type: {result.chunk_type} | Name: {result.name} | Score: {result.score:.3f}[/dim]")
            console.print()

            # Show code with syntax highlighting
            from rich.syntax import Syntax
            syntax = Syntax(
                result.content,
                result.language or "text",
                line_numbers=True,
                start_line=result.start_line,
                theme="monokai",
            )
            console.print(syntax)
            console.print()


@main.command()
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@click.argument("instruction")
@click.option("--mode", "-m", default="edit",
              type=click.Choice(["edit", "refactor", "fix", "add"]),
              help="Edit mode")
@click.option("--preview", "-p", is_flag=True, help="Preview changes without applying")
@click.option("--no-backup", is_flag=True, help="Don't create backup file")
@click.option("--format", "-f", "output_format", default="console",
              type=click.Choice(["console", "json"]), help="Output format")
@click.option("--start-line", "-s", type=int, help="Start line for targeted edit")
@click.option("--end-line", "-e", type=int, help="End line for targeted edit")
@click.option("--context", multiple=True, type=click.Path(exists=True, path_type=Path),
              help="Additional context files to include")
@click.option("--auto-context", is_flag=True, help="Automatically include related files as context")
@click.option("--max-context-tokens", type=int, default=8000, help="Max tokens for context")
@click.pass_context
def edit(ctx, file: Path, instruction: str, mode: str, preview: bool,
         no_backup: bool, output_format: str, start_line: Optional[int],
         end_line: Optional[int], context: Tuple[Path, ...], auto_context: bool,
         max_context_tokens: int):
    """Edit a file using AI based on natural language instructions.

    Examples:
        ai-assist edit main.py "Add error handling to the parse function"
        ai-assist edit utils.py "Add type hints" --mode refactor
        ai-assist edit app.py "Fix the null pointer bug" --mode fix
        ai-assist edit api.py "Add logging" --preview
        ai-assist edit config.py "Update the timeout value" -s 10 -e 20
    """
    config, llm = get_components(ctx.obj.get("config_path"))
    editor = FileEditor(config, llm)

    # Determine edit mode
    edit_mode = mode
    if start_line and end_line:
        edit_mode = "targeted"

    console.print(f"\n[bold]Editing {file}...[/bold]")
    console.print(f"Mode: [cyan]{edit_mode}[/cyan]")
    console.print(f"Instruction: [dim]{instruction}[/dim]\n")

    with console.status("[bold green]Generating edit..."):
        result = editor.edit_file(
            file_path=file,
            instruction=instruction,
            mode=edit_mode,
            preview=preview,
            create_backup=not no_backup,
            start_line=start_line,
            end_line=end_line,
        )

    if output_format == "json":
        import json
        console.print(json.dumps(result.to_dict(), indent=2))
        return

    # Console output
    if not result.success:
        console.print(f"[red]Error:[/red] {result.error}")
        sys.exit(1)

    if not result.has_changes:
        console.print("[yellow]No changes detected.[/yellow]")
        return

    # Show diff
    if result.diff:
        console.print("[bold]Changes:[/bold]")
        console.print(f"  [green]+{result.diff.additions}[/green] additions, "
                      f"[red]-{result.diff.deletions}[/red] deletions\n")

        from rich.syntax import Syntax
        diff_text = result.diff.unified_diff
        syntax = Syntax(diff_text, "diff", theme="monokai")
        console.print(syntax)

    if preview:
        console.print("\n[yellow]Preview mode - changes not applied[/yellow]")
        console.print("Run without --preview to apply changes.")
    else:
        if result.applied:
            console.print(f"\n[green]✓ Changes applied to {file}[/green]")
            if result.backup_path:
                console.print(f"[dim]Backup saved: {result.backup_path}[/dim]")
        else:
            console.print(f"\n[red]✗ Failed to apply changes[/red]")


@main.command()
@click.argument("instruction")
@click.option("--files", "-f", multiple=True, type=click.Path(exists=True, path_type=Path),
              help="Specific files to include")
@click.option("--pattern", "-p", help="Glob pattern to match files (e.g., '**/*.py')")
@click.option("--directory", "-d", type=click.Path(exists=True, path_type=Path),
              default=".", help="Directory to search for files")
@click.option("--dry-run", is_flag=True, help="Show plan without applying changes")
@click.option("--no-confirm", is_flag=True, help="Skip confirmation prompt")
@click.option("--no-backup", is_flag=True, help="Don't create backup")
@click.option("--format", "output_format", default="console",
              type=click.Choice(["console", "json"]), help="Output format")
@click.pass_context
def refactor(ctx, instruction: str, files: Tuple[Path, ...], pattern: Optional[str],
             directory: Path, dry_run: bool, no_confirm: bool, no_backup: bool,
             output_format: str):
    """Perform multi-file refactoring using AI.

    Analyzes the codebase and applies coordinated changes across multiple files.

    Examples:
        ai-assist refactor "Add type hints to all functions"
        ai-assist refactor "Rename User class to Account" -p "**/*.py"
        ai-assist refactor "Extract database logic to repository pattern" --dry-run
        ai-assist refactor "Add logging to all API endpoints" -d ./src/api
    """
    from ai_code_assistant.refactor import MultiFileEditor
    from ai_code_assistant.utils import FileHandler

    config, llm = get_components(ctx.obj.get("config_path"))
    editor = MultiFileEditor(config, llm)
    file_handler = FileHandler(config)

    # Collect files to refactor
    all_files: List[Path] = list(files)

    if pattern:
        # Use glob pattern
        all_files.extend(directory.glob(pattern))
    elif not files:
        # Default: find all code files in directory
        all_files.extend(file_handler.find_code_files(directory, recursive=True))

    # Remove duplicates and limit
    all_files = list(set(all_files))[:config.refactor.max_files]

    if not all_files:
        console.print("[red]Error:[/red] No files found to refactor")
        sys.exit(1)

    console.print(f"\n[bold]Multi-File Refactoring[/bold]")
    console.print(f"Instruction: [cyan]{instruction}[/cyan]")
    console.print(f"Files in scope: [cyan]{len(all_files)}[/cyan]\n")

    # Show files
    if ctx.obj.get("verbose"):
        for f in all_files[:10]:
            console.print(f"  • {f}")
        if len(all_files) > 10:
            console.print(f"  ... and {len(all_files) - 10} more")
        console.print()

    # Analyze and create plan
    with console.status("[bold green]Analyzing codebase..."):
        result = editor.refactor(
            instruction=instruction,
            files=all_files,
            dry_run=True,  # Always start with dry run to show plan
            create_backup=not no_backup,
        )

    if result.error and not result.plan.changes:
        console.print(f"[red]Error:[/red] {result.error}")
        sys.exit(1)

    # Output as JSON if requested
    if output_format == "json":
        import json
        console.print(json.dumps(result.to_dict(), indent=2))
        return

    # Show plan
    plan = result.plan
    console.print(f"[bold]Refactoring Plan[/bold]")
    console.print(f"Summary: {plan.summary}")
    console.print(f"Complexity: [cyan]{plan.complexity}[/cyan]")
    console.print(f"Files affected: [cyan]{plan.total_files}[/cyan]\n")

    if plan.risks:
        console.print("[yellow]Risks:[/yellow]")
        for risk in plan.risks:
            console.print(f"  ⚠ {risk}")
        console.print()

    # Show changes
    console.print("[bold]Planned Changes:[/bold]")
    for change in plan.changes:
        icon = {"modify": "📝", "create": "✨", "delete": "🗑️", "rename": "📛"}.get(
            change.change_type.value, "•"
        )
        console.print(f"  {icon} [{change.change_type.value}] {change.file_path}")
        console.print(f"     {change.description}")

    if dry_run:
        console.print("\n[yellow]Dry run - no changes applied[/yellow]")
        return

    # Confirm before applying
    if not no_confirm and config.refactor.require_confirmation:
        console.print()
        if not click.confirm("Apply these changes?"):
            console.print("[dim]Cancelled[/dim]")
            return

    # Apply changes
    console.print("\n[bold green]Applying changes...[/bold green]")

    with console.status("[bold green]Generating and applying changes..."):
        result = editor.refactor(
            instruction=instruction,
            files=all_files,
            dry_run=False,
            create_backup=not no_backup,
        )

    if result.error:
        console.print(f"[red]Error:[/red] {result.error}")
        sys.exit(1)

    # Show results
    console.print(f"\n[bold green]✓ Refactoring complete![/bold green]")
    console.print(f"  Files changed: {result.files_changed}")
    console.print(f"  Additions: [green]+{result.total_additions}[/green]")
    console.print(f"  Deletions: [red]-{result.total_deletions}[/red]")

    if result.backup_dir:
        console.print(f"\n[dim]Backup saved: {result.backup_dir}[/dim]")

    if result.files_failed > 0:
        console.print(f"\n[yellow]Warning: {result.files_failed} file(s) failed[/yellow]")
        for change in result.plan.changes:
            if change.error:
                console.print(f"  • {change.file_path}: {change.error}")


@main.command()
@click.argument("old_name")
@click.argument("new_name")
@click.option("--type", "-t", "symbol_type", default="symbol",
              type=click.Choice(["function", "class", "variable", "method", "symbol"]),
              help="Type of symbol to rename")
@click.option("--files", "-f", multiple=True, type=click.Path(exists=True, path_type=Path),
              help="Specific files to include")
@click.option("--pattern", "-p", help="Glob pattern to match files")
@click.option("--directory", "-d", type=click.Path(exists=True, path_type=Path),
              default=".", help="Directory to search")
@click.option("--dry-run", is_flag=True, help="Show changes without applying")
@click.pass_context
def rename(ctx, old_name: str, new_name: str, symbol_type: str, files: Tuple[Path, ...],
           pattern: Optional[str], directory: Path, dry_run: bool):
    """Rename a symbol across multiple files.

    Examples:
        ai-assist rename UserService AccountService --type class
        ai-assist rename get_user fetch_user --type function -p "**/*.py"
        ai-assist rename API_KEY API_SECRET --type variable --dry-run
    """
    from ai_code_assistant.refactor import MultiFileEditor
    from ai_code_assistant.utils import FileHandler

    config, llm = get_components(ctx.obj.get("config_path"))
    editor = MultiFileEditor(config, llm)
    file_handler = FileHandler(config)

    # Collect files
    all_files: List[Path] = list(files)
    if pattern:
        all_files.extend(directory.glob(pattern))
    elif not files:
        all_files.extend(file_handler.find_code_files(directory, recursive=True))

    all_files = list(set(all_files))[:config.refactor.max_files]

    if not all_files:
        console.print("[red]Error:[/red] No files found")
        sys.exit(1)

    console.print(f"\n[bold]Rename Symbol[/bold]")
    console.print(f"Renaming {symbol_type}: [cyan]{old_name}[/cyan] → [green]{new_name}[/green]")
    console.print(f"Files to search: [cyan]{len(all_files)}[/cyan]\n")

    with console.status("[bold green]Searching and renaming..."):
        result = editor.rename_symbol(
            old_name=old_name,
            new_name=new_name,
            symbol_type=symbol_type,
            files=all_files,
            dry_run=dry_run,
        )

    if result.error:
        console.print(f"[red]Error:[/red] {result.error}")
        sys.exit(1)

    # Show results
    console.print(f"[bold]Files affected: {result.plan.total_files}[/bold]\n")

    for change in result.plan.changes:
        status = "[green]✓[/green]" if change.applied else "[yellow]○[/yellow]"
        console.print(f"  {status} {change.file_path}")

    if dry_run:
        console.print("\n[yellow]Dry run - no changes applied[/yellow]")
    else:
        console.print(f"\n[green]✓ Renamed {old_name} to {new_name} in {result.files_changed} file(s)[/green]")



@main.command()
@click.option("--format", "-f", "output_format", default="console",
              type=click.Choice(["console", "json"]), help="Output format")
@click.pass_context
def providers(ctx, output_format: str):
    """List all available LLM providers and their models.

    Shows provider information including:
    - Whether an API key is required
    - Free tier availability
    - Available models with descriptions

    Examples:
        ai-assist providers
        ai-assist providers --format json
    """
    from ai_code_assistant.providers.factory import get_available_providers

    providers_info = get_available_providers()

    if output_format == "json":
        import json
        console.print(json.dumps(providers_info, indent=2))
        return

    # Console output
    console.print("\n[bold]Available LLM Providers[/bold]\n")

    for provider_name, info in providers_info.items():
        # Provider header
        api_badge = "[red]API Key Required[/red]" if info["requires_api_key"] else "[green]No API Key[/green]"
        free_badge = "[green]Free Tier[/green]" if info["free_tier"] else "[yellow]Paid Only[/yellow]"

        console.print(f"[bold cyan]━━━ {info['display_name']} ({provider_name}) ━━━[/bold cyan]")
        console.print(f"  {api_badge} | {free_badge}")
        console.print(f"  Default model: [dim]{info['default_model']}[/dim]")
        console.print()

        # Models table
        console.print("  [bold]Models:[/bold]")
        for model in info["models"]:
            free_icon = "🆓" if model["is_free"] else "💰"
            console.print(f"    {free_icon} [cyan]{model['name']}[/cyan]")
            console.print(f"       {model['description']}")
            console.print(f"       Context: {model['context_window']:,} tokens")
        console.print()

    # Show current configuration
    config = load_config(ctx.obj.get("config_path"))
    console.print("[bold]Current Configuration:[/bold]")
    console.print(f"  Provider: [cyan]{config.llm.provider}[/cyan]")
    console.print(f"  Model: [cyan]{config.llm.model}[/cyan]")

    # Check for API keys
    import os
    console.print("\n[bold]API Key Status:[/bold]")
    env_vars = [
        ("GOOGLE_API_KEY", "Google"),
        ("GROQ_API_KEY", "Groq"),
        ("CEREBRAS_API_KEY", "Cerebras"),
        ("OPENROUTER_API_KEY", "OpenRouter"),
        ("OPENAI_API_KEY", "OpenAI"),
    ]
    for env_var, name in env_vars:
        status = "[green]✓ Set[/green]" if os.getenv(env_var) else "[dim]Not set[/dim]"
        console.print(f"  {name}: {status}")


@main.command("use-provider")
@click.argument("provider", type=click.Choice(["ollama", "google", "groq", "cerebras", "openrouter", "openai"]))
@click.option("--model", "-m", help="Model to use (uses provider default if not specified)")
@click.option("--api-key", "-k", help="API key (can also use environment variable)")
@click.option("--test", "-t", is_flag=True, help="Test the connection after switching")
@click.pass_context
def use_provider(ctx, provider: str, model: Optional[str], api_key: Optional[str], test: bool):
    """Switch to a different LLM provider.

    This updates the current session's provider. To make permanent changes,
    update your config.yaml file.

    Examples:
        ai-assist use-provider groq
        ai-assist use-provider google --model gemini-1.5-pro
        ai-assist use-provider openrouter --model deepseek/deepseek-r1:free --test
    """
    from ai_code_assistant.providers.factory import PROVIDER_REGISTRY, get_provider
    from ai_code_assistant.providers.base import ProviderConfig, ProviderType

    config = load_config(ctx.obj.get("config_path"))

    # Get provider class for default model
    provider_type = ProviderType(provider)
    provider_class = PROVIDER_REGISTRY.get(provider_type)

    if not provider_class:
        console.print(f"[red]Error:[/red] Unknown provider: {provider}")
        sys.exit(1)

    # Use default model if not specified
    if not model:
        model = provider_class.default_model

    console.print(f"\n[bold]Switching to {provider_class.display_name}[/bold]")
    console.print(f"  Model: [cyan]{model}[/cyan]")

    # Check API key
    import os
    env_var_map = {
        "google": "GOOGLE_API_KEY",
        "groq": "GROQ_API_KEY",
        "cerebras": "CEREBRAS_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
        "openai": "OPENAI_API_KEY",
    }

    if provider_class.requires_api_key:
        env_var = env_var_map.get(provider)
        env_key = os.getenv(env_var) if env_var else None

        if not api_key and not env_key:
            console.print(f"\n[yellow]Warning:[/yellow] No API key provided")
            console.print(f"Set {env_var} environment variable or use --api-key")
            console.print(f"\n{provider_class.get_setup_instructions()}")
            sys.exit(1)

        api_key = api_key or env_key

    # Create provider config
    provider_config = ProviderConfig(
        provider=provider_type,
        model=model,
        api_key=api_key,
        temperature=config.llm.temperature,
        max_tokens=config.llm.max_tokens,
        timeout=config.llm.timeout,
    )

    # Validate config
    try:
        provider_instance = get_provider(provider_config)
        is_valid, error = provider_instance.validate_config()
        if not is_valid:
            console.print(f"[red]Configuration error:[/red] {error}")
            sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error creating provider:[/red] {e}")
        sys.exit(1)

    console.print("[green]✓ Provider configured successfully[/green]")

    # Test connection if requested
    if test:
        console.print("\n[bold]Testing connection...[/bold]")
        with console.status("[bold green]Sending test request..."):
            try:
                response = provider_instance.invoke("Say 'Hello from {provider}!' and nothing else.")
                console.print(f"[green]✓ Connection successful![/green]")
                console.print(f"  Response: [dim]{response.strip()}[/dim]")
            except Exception as e:
                console.print(f"[red]✗ Connection failed:[/red] {e}")
                sys.exit(1)

    # Show how to make permanent
    console.print("\n[dim]To make this permanent, update your config.yaml:[/dim]")
    console.print(f"[dim]  llm:[/dim]")
    console.print(f"[dim]    provider: {provider}[/dim]")
    console.print(f"[dim]    model: {model}[/dim]")


@main.command("test-provider")
@click.option("--provider", "-p", help="Provider to test (uses current config if not specified)")
@click.option("--model", "-m", help="Model to test")
@click.option("--prompt", default="Write a Python function that adds two numbers.", help="Test prompt")
@click.pass_context
def test_provider(ctx, provider: Optional[str], model: Optional[str], prompt: str):
    """Test the current or specified LLM provider.

    Sends a test prompt and displays the response with timing information.

    Examples:
        ai-assist test-provider
        ai-assist test-provider --provider groq
        ai-assist test-provider --prompt "Explain recursion in one sentence"
    """
    import time
    from ai_code_assistant.providers.factory import get_provider, PROVIDER_REGISTRY
    from ai_code_assistant.providers.base import ProviderConfig, ProviderType

    config = load_config(ctx.obj.get("config_path"))

    # Use current config or specified provider
    if provider:
        provider_type = ProviderType(provider)
        provider_class = PROVIDER_REGISTRY.get(provider_type)
        if not model:
            model = provider_class.default_model
    else:
        provider_type = ProviderType(config.llm.provider)
        model = model or config.llm.model

    console.print(f"\n[bold]Testing LLM Provider[/bold]")
    console.print(f"  Provider: [cyan]{provider_type.value}[/cyan]")
    console.print(f"  Model: [cyan]{model}[/cyan]")
    console.print(f"  Prompt: [dim]{prompt[:50]}{'...' if len(prompt) > 50 else ''}[/dim]\n")

    # Create provider
    import os
    env_var_map = {
        "google": "GOOGLE_API_KEY",
        "groq": "GROQ_API_KEY",
        "cerebras": "CEREBRAS_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
        "openai": "OPENAI_API_KEY",
    }

    api_key = config.llm.api_key
    if not api_key:
        env_var = env_var_map.get(provider_type.value)
        api_key = os.getenv(env_var) if env_var else None

    provider_config = ProviderConfig(
        provider=provider_type,
        model=model,
        api_key=api_key,
        base_url=config.llm.base_url if provider_type == ProviderType.OLLAMA else None,
        temperature=config.llm.temperature,
        max_tokens=config.llm.max_tokens,
        timeout=config.llm.timeout,
    )

    try:
        provider_instance = get_provider(provider_config)
    except Exception as e:
        console.print(f"[red]Error creating provider:[/red] {e}")
        sys.exit(1)

    # Send test request
    console.print("[bold]Sending request...[/bold]\n")
    start_time = time.time()

    try:
        response = provider_instance.invoke(prompt)
        elapsed = time.time() - start_time

        console.print("[bold green]Response:[/bold green]")
        console.print(Panel(response.strip(), border_style="green"))

        console.print(f"\n[dim]Time: {elapsed:.2f}s[/dim]")
        console.print(f"[dim]Tokens (approx): {len(response.split())} words[/dim]")

    except Exception as e:
        elapsed = time.time() - start_time
        console.print(f"[red]Error:[/red] {e}")
        console.print(f"[dim]Failed after {elapsed:.2f}s[/dim]")
        sys.exit(1)



# ============================================================================
# Git Integration Commands
# ============================================================================

@main.group()
def git():
    """Git integration commands with AI-powered commit messages."""
    pass


@git.command("status")
@click.pass_context
def git_status(ctx):
    """Show git status with summary.

    Examples:
        ai-assist git status
    """
    from ai_code_assistant.git import GitManager

    try:
        git_mgr = GitManager()
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    status = git_mgr.get_status()

    console.print(f"\n[bold]Git Status[/bold]")
    console.print(f"  Branch: [cyan]{status.branch}[/cyan]")

    if status.ahead:
        console.print(f"  [green]↑ {status.ahead} commit(s) ahead[/green]")
    if status.behind:
        console.print(f"  [yellow]↓ {status.behind} commit(s) behind[/yellow]")

    if not status.has_changes:
        console.print("\n[green]✓ Working tree clean[/green]")
        return

    console.print(f"\n[bold]Changes ({status.total_changes} files):[/bold]")

    if status.staged:
        console.print(f"\n  [green]Staged ({len(status.staged)}):[/green]")
        for f in status.staged[:10]:
            console.print(f"    [green]✓[/green] {f}")
        if len(status.staged) > 10:
            console.print(f"    ... and {len(status.staged) - 10} more")

    if status.modified:
        console.print(f"\n  [yellow]Modified ({len(status.modified)}):[/yellow]")
        for f in status.modified[:10]:
            console.print(f"    [yellow]●[/yellow] {f}")
        if len(status.modified) > 10:
            console.print(f"    ... and {len(status.modified) - 10} more")

    if status.untracked:
        console.print(f"\n  [dim]Untracked ({len(status.untracked)}):[/dim]")
        for f in status.untracked[:10]:
            console.print(f"    [dim]?[/dim] {f}")
        if len(status.untracked) > 10:
            console.print(f"    ... and {len(status.untracked) - 10} more")

    if status.deleted:
        console.print(f"\n  [red]Deleted ({len(status.deleted)}):[/red]")
        for f in status.deleted[:10]:
            console.print(f"    [red]✗[/red] {f}")


@git.command("commit")
@click.option("--message", "-m", help="Commit message (AI generates if not provided)")
@click.option("--all", "-a", "stage_all", is_flag=True, help="Stage all changes before commit")
@click.option("--push", "-p", "push_after", is_flag=True, help="Push after commit")
@click.option("--no-confirm", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def git_commit(ctx, message: Optional[str], stage_all: bool, push_after: bool, no_confirm: bool):
    """Commit changes with AI-generated message.

    If no message is provided, AI analyzes the diff and generates one.

    Examples:
        ai-assist git commit                    # AI generates message
        ai-assist git commit -m "Fix bug"       # Use provided message
        ai-assist git commit -a --push          # Stage all, commit, push
        ai-assist git commit --no-confirm       # Skip confirmation
    """
    from ai_code_assistant.git import GitManager, CommitMessageGenerator

    config, llm = get_components(ctx.obj.get("config_path"))

    try:
        git_mgr = GitManager()
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    status = git_mgr.get_status()

    # Stage all if requested
    if stage_all:
        console.print("[dim]Staging all changes...[/dim]")
        git_mgr.stage_all()
        status = git_mgr.get_status()

    # Check if there are staged changes
    if not status.has_staged:
        if status.has_changes:
            console.print("[yellow]No staged changes.[/yellow]")
            console.print("Use [cyan]--all[/cyan] to stage all changes, or stage manually with [cyan]git add[/cyan]")
        else:
            console.print("[yellow]Nothing to commit, working tree clean.[/yellow]")
        sys.exit(1)

    # Generate or use provided message
    if not message:
        console.print("\n[bold]Generating commit message...[/bold]")
        with console.status("[bold green]Analyzing changes..."):
            generator = CommitMessageGenerator(llm)
            message = generator.generate(git_mgr)

        if not message:
            console.print("[red]Error:[/red] Could not generate commit message")
            sys.exit(1)

    # Show commit preview
    diff = git_mgr.get_diff(staged=True)
    console.print(f"\n[bold]Commit Preview[/bold]")
    console.print(f"  Files: [cyan]{diff.files_changed}[/cyan]")
    console.print(f"  Changes: [green]+{diff.insertions}[/green] / [red]-{diff.deletions}[/red]")
    console.print(f"\n[bold]Message:[/bold]")
    console.print(Panel(message, border_style="cyan"))

    # Confirm
    if not no_confirm:
        if not click.confirm("\nProceed with commit?"):
            console.print("[dim]Cancelled[/dim]")
            return

    # Commit
    try:
        commit_hash = git_mgr.commit(message)
        console.print(f"\n[green]✓ Committed:[/green] {commit_hash}")
    except Exception as e:
        console.print(f"[red]Error committing:[/red] {e}")
        sys.exit(1)

    # Push if requested
    if push_after:
        console.print("\n[bold]Pushing to remote...[/bold]")
        success, output = git_mgr.push()
        if success:
            console.print(f"[green]✓ Pushed to {status.remote}/{status.branch}[/green]")
        else:
            console.print(f"[red]Error pushing:[/red] {output}")
            sys.exit(1)


@git.command("push")
@click.option("--remote", "-r", default="origin", help="Remote name")
@click.option("--branch", "-b", help="Branch name (default: current branch)")
@click.option("--set-upstream", "-u", is_flag=True, help="Set upstream for the branch")
@click.pass_context
def git_push(ctx, remote: str, branch: Optional[str], set_upstream: bool):
    """Push commits to remote repository.

    Examples:
        ai-assist git push
        ai-assist git push --remote origin --branch main
        ai-assist git push -u  # Set upstream
    """
    from ai_code_assistant.git import GitManager

    try:
        git_mgr = GitManager()
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    status = git_mgr.get_status()
    branch = branch or status.branch

    console.print(f"\n[bold]Pushing to {remote}/{branch}...[/bold]")

    with console.status("[bold green]Pushing..."):
        success, output = git_mgr.push(remote=remote, branch=branch, set_upstream=set_upstream)

    if success:
        console.print(f"[green]✓ Successfully pushed to {remote}/{branch}[/green]")

        # Show remote URL
        remote_url = git_mgr.get_remote_url()
        if "github.com" in remote_url:
            # Convert SSH to HTTPS URL for display
            if remote_url.startswith("git@"):
                remote_url = remote_url.replace("git@github.com:", "https://github.com/").replace(".git", "")
            console.print(f"\n[dim]View at: {remote_url}[/dim]")
    else:
        console.print(f"[red]Error:[/red] Push failed")
        console.print(f"[dim]{output}[/dim]")
        sys.exit(1)


@git.command("sync")
@click.option("--message", "-m", help="Commit message (AI generates if not provided)")
@click.option("--no-confirm", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def git_sync(ctx, message: Optional[str], no_confirm: bool):
    """Stage all changes, commit with AI message, and push.

    This is a convenience command that combines:
    1. git add -A
    2. git commit (with AI-generated message)
    3. git push

    Examples:
        ai-assist git sync                  # Full sync with AI message
        ai-assist git sync -m "Update"      # Sync with custom message
        ai-assist git sync --no-confirm     # Skip confirmation
    """
    from ai_code_assistant.git import GitManager, CommitMessageGenerator

    config, llm = get_components(ctx.obj.get("config_path"))

    try:
        git_mgr = GitManager()
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    status = git_mgr.get_status()

    if not status.has_changes:
        console.print("[yellow]Nothing to sync, working tree clean.[/yellow]")
        return

    console.print(f"\n[bold]Git Sync[/bold]")
    console.print(f"  Branch: [cyan]{status.branch}[/cyan]")
    console.print(f"  Changes: [cyan]{status.total_changes} files[/cyan]")

    # Stage all
    console.print("\n[dim]Staging all changes...[/dim]")
    git_mgr.stage_all()
    status = git_mgr.get_status()

    # Generate message if not provided
    if not message:
        console.print("[dim]Generating commit message...[/dim]")
        with console.status("[bold green]Analyzing changes..."):
            generator = CommitMessageGenerator(llm)
            message = generator.generate(git_mgr)

        if not message:
            console.print("[red]Error:[/red] Could not generate commit message")
            sys.exit(1)

    # Show preview
    diff = git_mgr.get_diff(staged=True)
    console.print(f"\n[bold]Sync Preview[/bold]")
    console.print(f"  Files: [cyan]{diff.files_changed}[/cyan]")
    console.print(f"  Changes: [green]+{diff.insertions}[/green] / [red]-{diff.deletions}[/red]")
    console.print(f"  Push to: [cyan]{status.remote}/{status.branch}[/cyan]")
    console.print(f"\n[bold]Message:[/bold]")
    console.print(Panel(message, border_style="cyan"))

    # Confirm
    if not no_confirm:
        if not click.confirm("\nProceed with sync?"):
            console.print("[dim]Cancelled[/dim]")
            return

    # Commit
    console.print("\n[dim]Committing...[/dim]")
    try:
        commit_hash = git_mgr.commit(message)
        console.print(f"[green]✓ Committed:[/green] {commit_hash}")
    except Exception as e:
        console.print(f"[red]Error committing:[/red] {e}")
        sys.exit(1)

    # Push
    console.print("[dim]Pushing...[/dim]")
    success, output = git_mgr.push()
    if success:
        console.print(f"[green]✓ Pushed to {status.remote}/{status.branch}[/green]")

        # Show GitHub URL
        remote_url = git_mgr.get_remote_url()
        if "github.com" in remote_url:
            if remote_url.startswith("git@"):
                remote_url = remote_url.replace("git@github.com:", "https://github.com/").replace(".git", "")
            elif remote_url.endswith(".git"):
                remote_url = remote_url[:-4]
            console.print(f"\n[bold green]✓ Sync complete![/bold green]")
            console.print(f"[dim]View at: {remote_url}[/dim]")
    else:
        console.print(f"[red]Error pushing:[/red] {output}")
        sys.exit(1)


@git.command("log")
@click.option("--count", "-n", default=10, help="Number of commits to show")
@click.pass_context
def git_log(ctx, count: int):
    """Show recent commit history.

    Examples:
        ai-assist git log
        ai-assist git log -n 20
    """
    from ai_code_assistant.git import GitManager

    try:
        git_mgr = GitManager()
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    commits = git_mgr.get_recent_commits(count=count)

    console.print(f"\n[bold]Recent Commits[/bold]\n")

    for commit in commits:
        console.print(f"[yellow]{commit['short_hash']}[/yellow] {commit['message']}")
        console.print(f"  [dim]{commit['author']} • {commit['time']}[/dim]")

# =============================================================================
# Agent Commands
# =============================================================================

@main.command()
@click.option("--path", "-p", type=click.Path(exists=True, path_type=Path), 
              default=".", help="Project root path")
@click.pass_context
def agent(ctx, path: Path):
    """Start interactive AI code agent.
    
    The agent can:
    - Generate code based on descriptions
    - Review files for issues
    - Edit existing code
    - Explain how code works
    - Refactor code
    - Generate tests
    
    Examples:
        ai-assist agent
        ai-assist agent --path ./my-project
        
    In agent mode, try commands like:
        "create a function to validate email addresses"
        "review src/main.py"
        "explain how the config module works"
        "refactor utils.py to use async"
        "generate tests for src/api.py"
    """
    from ai_code_assistant.chat import AgentChatSession
    from rich.markdown import Markdown
    from rich.prompt import Prompt
    
    config, llm = get_components(ctx.obj.get("config_path"))
    
    # Initialize agent session
    session = AgentChatSession(config, llm, path.resolve())
    
    # Show welcome message
    console.print(Panel.fit(
        "[bold cyan]🤖 AI Code Agent[/bold cyan]\n\n"
        "I can help you with:\n"
        "  • [green]Generate[/green] - Create new code\n"
        "  • [yellow]Review[/yellow] - Analyze code for issues\n"
        "  • [blue]Edit[/blue] - Modify existing files\n"
        "  • [magenta]Explain[/magenta] - Understand code\n"
        "  • [cyan]Refactor[/cyan] - Improve code quality\n"
        "  • [white]Test[/white] - Generate unit tests\n\n"
        "Type [bold]'help'[/bold] for examples, [bold]'quit'[/bold] to exit.",
        title="Welcome",
        border_style="cyan",
    ))
    
    # Show project info
    project_info = session.get_project_info()
    console.print(f"\n{project_info}\n")
    
    # Main loop
    while True:
        try:
            user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]")
            
            if not user_input.strip():
                continue
            
            # Handle special commands
            lower_input = user_input.lower().strip()
            
            if lower_input in ("quit", "exit", "q"):
                console.print("[dim]Goodbye![/dim]")
                break
            
            if lower_input == "help":
                _show_agent_help()
                continue
            
            if lower_input == "clear":
                session.clear_history()
                console.print("[dim]History cleared.[/dim]")
                continue
            
            if lower_input == "status":
                if session.has_pending_changes:
                    console.print("[yellow]You have pending changes awaiting confirmation.[/yellow]")
                else:
                    console.print("[green]No pending changes.[/green]")
                continue
            
            # Process through agent with streaming
            console.print(f"\n[bold green]Agent[/bold green]")
            
            final_msg = None
            for chunk, msg in session.send_message_stream(user_input):
                if chunk:
                    console.print(chunk, end="")
                if msg is not None:
                    final_msg = msg
            
            console.print()  # Newline after streaming
            
            # Show confirmation prompt if needed
            if final_msg and final_msg.pending_action:
                console.print("\n[yellow]Apply these changes? (yes/no)[/yellow]")
        
        except KeyboardInterrupt:
            console.print("\n[dim]Use 'quit' to exit[/dim]")
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")


def _show_agent_help():
    """Show agent help message."""
    help_text = """
[bold]Code Generation[/bold]
  • "create a function to parse JSON files"
  • "write a class for managing database connections"
  • "generate a REST API endpoint for users"

[bold]Code Review[/bold]
  • "review src/main.py"
  • "check utils.py for security issues"
  • "analyze the config module"

[bold]Code Editing[/bold]
  • "edit src/api.py to add error handling"
  • "fix the bug in utils.py line 42"
  • "add logging to the main function"

[bold]Code Explanation[/bold]
  • "explain src/config.py"
  • "how does the authentication work?"
  • "what does this function do?"

[bold]Refactoring[/bold]
  • "refactor utils.py to use async/await"
  • "improve the code quality of main.py"
  • "simplify the database module"

[bold]Test Generation[/bold]
  • "generate tests for src/api.py"
  • "write unit tests for the User class"
  • "create pytest tests for utils.py"

[bold]Project Info[/bold]
  • "show project structure"
  • "what languages are used?"
  • "list all Python files"

[bold]Special Commands[/bold]
  • help   - Show this help
  • status - Check for pending changes
  • clear  - Clear conversation history
  • quit   - Exit agent mode
"""
    console.print(Panel(help_text, title="Agent Help", border_style="cyan"))


@main.command("agent-review")
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@click.option("--path", "-p", type=click.Path(exists=True, path_type=Path),
              default=".", help="Project root path")
@click.option("--stream/--no-stream", default=True, help="Stream output in real-time")
@click.pass_context
def agent_review(ctx, file: Path, path: Path, stream: bool):
    """Quick code review using the agent.
    
    Examples:
        ai-assist agent-review src/main.py
        ai-assist agent-review utils.py --path ./my-project
        ai-assist agent-review main.py --no-stream
    """
    from ai_code_assistant.agent import CodeAgent
    
    config, llm = get_components(ctx.obj.get("config_path"))
    agent = CodeAgent(llm, path.resolve())
    
    console.print(f"\n[bold]Reviewing {file}...[/bold]\n")
    
    if stream:
        for chunk, response in agent.process_stream(f"review {file}"):
            if chunk:
                console.print(chunk, end="")
        console.print()
    else:
        with console.status("[bold green]Analyzing..."):
            response = agent.process(f"review {file}")
        console.print(response.message)


@main.command("agent-generate")
@click.argument("description")
@click.option("--file", "-f", type=click.Path(path_type=Path), help="Output file path")
@click.option("--language", "-l", help="Programming language")
@click.option("--path", "-p", type=click.Path(exists=True, path_type=Path),
              default=".", help="Project root path")
@click.option("--apply", "-a", is_flag=True, help="Apply changes without confirmation")
@click.option("--stream/--no-stream", default=True, help="Stream output in real-time")
@click.pass_context
def agent_generate(ctx, description: str, file: Optional[Path], language: Optional[str],
                   path: Path, apply: bool, stream: bool):
    """Generate code using the agent.
    
    Examples:
        ai-assist agent-generate "a function to validate email"
        ai-assist agent-generate "REST API for users" -f src/api.py
        ai-assist agent-generate "sorting algorithm" -l python
        ai-assist agent-generate "hello world" --no-stream
    """
    from ai_code_assistant.agent import CodeAgent
    
    config, llm = get_components(ctx.obj.get("config_path"))
    agent = CodeAgent(llm, path.resolve())
    
    # Build the request
    request = description
    if file:
        request = f"create {file}: {description}"
    if language:
        request = f"{request} in {language}"
    
    console.print(f"\n[bold]Generating code...[/bold]\n")
    
    final_response = None
    if stream:
        for chunk, response in agent.process_stream(request):
            if chunk:
                console.print(chunk, end="")
            if response is not None:
                final_response = response
        console.print()
    else:
        with console.status("[bold green]Generating..."):
            final_response = agent.process(request)
        console.print(final_response.message)
    
    if final_response and final_response.requires_confirmation:
        if apply:
            success, msg = agent.confirm_changes()
            console.print(f"\n{msg}")
        else:
            if click.confirm("\nApply these changes?"):
                success, msg = agent.confirm_changes()
                console.print(f"\n{msg}")
            else:
                console.print("[dim]Changes discarded.[/dim]")


@main.command("agent-explain")
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@click.option("--path", "-p", type=click.Path(exists=True, path_type=Path),
              default=".", help="Project root path")
@click.option("--stream/--no-stream", default=True, help="Stream output in real-time")
@click.pass_context
def agent_explain(ctx, file: Path, path: Path, stream: bool):
    """Explain code using the agent.
    
    Examples:
        ai-assist agent-explain src/main.py
        ai-assist agent-explain config.py --path ./my-project
        ai-assist agent-explain main.py --no-stream
    """
    from ai_code_assistant.agent import CodeAgent
    
    config, llm = get_components(ctx.obj.get("config_path"))
    agent = CodeAgent(llm, path.resolve())
    
    console.print(f"\n[bold]Explaining {file}...[/bold]\n")
    
    if stream:
        for chunk, response in agent.process_stream(f"explain {file}"):
            if chunk:
                console.print(chunk, end="")
        console.print()
    else:
        from rich.markdown import Markdown
        with console.status("[bold green]Analyzing..."):
            response = agent.process(f"explain {file}")
        try:
            console.print(Markdown(response.message))
        except Exception:
            console.print(response.message)


if __name__ == "__main__":
    main()
