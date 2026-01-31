"""Command-line interface for Claude Dev CLI."""

import os
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from claude_dev_cli import __version__
from claude_dev_cli.config import Config
from claude_dev_cli.core import ClaudeClient
from claude_dev_cli.commands import (
    generate_tests,
    code_review,
    debug_code,
    generate_docs,
    refactor_code,
    git_commit_message,
)
from claude_dev_cli.usage import UsageTracker
from claude_dev_cli import toon_utils
from claude_dev_cli.plugins import load_plugins
from claude_dev_cli.history import ConversationHistory, Conversation
from claude_dev_cli.template_manager import TemplateManager, Template

console = Console()


@click.group()
@click.version_option(version=__version__)
@click.pass_context
def main(ctx: click.Context) -> None:
    """Claude Dev CLI - AI-powered development assistant with multi-API routing."""
    ctx.ensure_object(dict)
    ctx.obj['console'] = console


# Load plugins after main group is defined
# Silently load plugins - they'll register their commands
try:
    plugins = load_plugins()
    for plugin in plugins:
        plugin.register_commands(main)
except Exception:
    # Don't fail if plugins can't load - continue without them
    pass


@main.command()
@click.argument('prompt', required=False)
@click.option('-f', '--file', type=click.Path(exists=True), help='Include file content in prompt')
@click.option('-s', '--system', help='System prompt')
@click.option('-a', '--api', help='API config to use')
@click.option('-m', '--model', help='Claude model to use')
@click.option('--stream/--no-stream', default=True, help='Stream response')
@click.option('--auto-context', is_flag=True, help='Automatically include git, dependencies, and related files')
@click.pass_context
def ask(
    ctx: click.Context,
    prompt: Optional[str],
    file: Optional[str],
    system: Optional[str],
    api: Optional[str],
    model: Optional[str],
    stream: bool,
    auto_context: bool
) -> None:
    """Ask Claude a question (single-shot mode)."""
    console = ctx.obj['console']
    
    # Build prompt
    prompt_parts = []
    
    # Gather context if requested
    if auto_context and file:
        from claude_dev_cli.context import ContextGatherer
        
        with console.status("[bold blue]Gathering context..."):
            gatherer = ContextGatherer()
            context = gatherer.gather_for_file(Path(file))
            context_info = context.format_for_prompt()
        
        console.print("[dim]✓ Context gathered[/dim]")
        prompt_parts.append(context_info)
    elif file:
        with open(file, 'r') as f:
            file_content = f.read()
            prompt_parts.append(f"File: {file}\n\n{file_content}\n\n")
    
    # Read from stdin if available
    if not sys.stdin.isatty():
        stdin_content = sys.stdin.read().strip()
        if stdin_content:
            prompt_parts.append(f"{stdin_content}\n\n")
    
    if prompt:
        prompt_parts.append(prompt)
    elif not prompt_parts:
        console.print("[red]Error: No prompt provided[/red]")
        sys.exit(1)
    
    full_prompt = ''.join(prompt_parts)
    
    try:
        client = ClaudeClient(api_config_name=api)
        
        if stream:
            for chunk in client.call_streaming(
                full_prompt,
                system_prompt=system,
                model=model
            ):
                console.print(chunk, end='')
            console.print()  # New line at end
        else:
            response = client.call(full_prompt, system_prompt=system, model=model)
            md = Markdown(response)
            console.print(md)
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@main.command()
@click.option('-a', '--api', help='API config to use')
@click.option('--continue', 'continue_conversation', is_flag=True, 
              help='Continue the last conversation')
@click.option('--save/--no-save', default=True, help='Save conversation history')
@click.pass_context
def interactive(
    ctx: click.Context, 
    api: Optional[str],
    continue_conversation: bool,
    save: bool
) -> None:
    """Start interactive chat mode."""
    console = ctx.obj['console']
    
    # Setup conversation history
    config = Config()
    history_dir = config.config_dir / "history"
    conv_history = ConversationHistory(history_dir)
    summ_config = config.get_summarization_config()
    
    # Load or create conversation
    if continue_conversation:
        conversation = conv_history.get_latest_conversation()
        if conversation:
            console.print(f"[green]↶ Continuing conversation from {conversation.updated_at.strftime('%Y-%m-%d %H:%M')}[/green]")
            console.print(f"[dim]Messages: {len(conversation.messages)}[/dim]\n")
        else:
            console.print("[yellow]No previous conversation found, starting new one[/yellow]\n")
            conversation = Conversation()
    else:
        conversation = Conversation()
    
    console.print(Panel.fit(
        "Claude Dev CLI - Interactive Mode\n"
        "Type 'exit' or 'quit' to end\n"
        "Type 'clear' to reset conversation",
        title="Welcome",
        border_style="blue"
    ))
    
    try:
        client = ClaudeClient(api_config_name=api)
        response_buffer = []
        
        while True:
            try:
                user_input = console.input("\n[bold cyan]You:[/bold cyan] ").strip()
                
                if user_input.lower() in ['exit', 'quit']:
                    if save and conversation.messages:
                        conv_history.save_conversation(conversation)
                        console.print(f"\n[dim]💾 Saved conversation: {conversation.conversation_id}[/dim]")
                    break
                
                if user_input.lower() == 'clear':
                    conversation = Conversation()
                    console.print("[yellow]Conversation cleared[/yellow]")
                    continue
                
                if not user_input:
                    continue
                
                # Add user message to history
                conversation.add_message("user", user_input)
                
                # Get response
                console.print("\n[bold green]Claude:[/bold green] ", end='')
                response_buffer = []
                for chunk in client.call_streaming(user_input):
                    console.print(chunk, end='')
                    response_buffer.append(chunk)
                console.print()
                
                # Add assistant response to history
                full_response = ''.join(response_buffer)
                conversation.add_message("assistant", full_response)
                
                # Check if auto-summarization is needed
                if summ_config.auto_summarize and conversation.should_summarize(threshold_tokens=summ_config.threshold_tokens):
                    console.print("\n[yellow]⚠ Conversation getting long, summarizing older messages...[/yellow]")
                    old_messages, recent_messages = conversation.compress_messages(keep_recent=summ_config.keep_recent_messages)
                    
                    if old_messages:
                        # Build summary prompt
                        conversation_text = []
                        if conversation.summary:
                            conversation_text.append(f"Previous summary:\n{conversation.summary}\n\n")
                        
                        conversation_text.append("Conversation to summarize:\n")
                        for msg in old_messages:
                            role_name = "User" if msg.role == "user" else "Assistant"
                            conversation_text.append(f"{role_name}: {msg.content}\n")
                        
                        summary_prompt = (
                            "Please provide a concise summary of this conversation that captures:"
                            "\n1. Main topics discussed"
                            "\n2. Key questions asked and answers provided"
                            "\n3. Important decisions or conclusions"
                            "\n4. Any action items or follow-ups mentioned"
                            "\n\nKeep the summary under 300 words but retain all important context."
                            "\n\n" + "".join(conversation_text)
                        )
                        
                        # Get summary (use same client)
                        new_summary = client.call(summary_prompt)
                        
                        # Update conversation
                        conversation.summary = new_summary
                        conversation.messages = recent_messages
                        
                        tokens_saved = len("".join(conversation_text)) // 4
                        console.print(f"[dim]✓ Summarized older messages (~{tokens_saved:,} tokens saved)[/dim]")
                
                # Auto-save periodically
                if save and len(conversation.messages) % 10 == 0:
                    conv_history.save_conversation(conversation)
                
            except KeyboardInterrupt:
                console.print("\n\n[yellow]Interrupted. Type 'exit' to quit.[/yellow]")
                continue
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if save and conversation.messages:
            conv_history.save_conversation(conversation)
        sys.exit(1)


@main.group()
def completion() -> None:
    """Shell completion installation."""
    pass


@completion.command('install')
@click.option('--shell', type=click.Choice(['bash', 'zsh', 'fish', 'auto']), default='auto',
              help='Shell type (auto-detects if not specified)')
@click.pass_context
def completion_install(ctx: click.Context, shell: str) -> None:
    """Install shell completion for cdc command."""
    console = ctx.obj['console']
    
    # Auto-detect shell if needed
    if shell == 'auto':
        shell_path = os.environ.get('SHELL', '')
        if 'zsh' in shell_path:
            shell = 'zsh'
        elif 'bash' in shell_path:
            shell = 'bash'
        elif 'fish' in shell_path:
            shell = 'fish'
        else:
            console.print("[red]Could not auto-detect shell[/red]")
            console.print("Please specify: --shell bash|zsh|fish")
            sys.exit(1)
    
    console.print(f"[cyan]Installing completion for {shell}...[/cyan]\n")
    
    if shell == 'zsh':
        console.print("Add this to your ~/.zshrc:\n")
        console.print("[yellow]eval \"$(_CDC_COMPLETE=zsh_source cdc)\"[/yellow]\n")
        console.print("Then run: [cyan]source ~/.zshrc[/cyan]")
    elif shell == 'bash':
        console.print("Add this to your ~/.bashrc:\n")
        console.print("[yellow]eval \"$(_CDC_COMPLETE=bash_source cdc)\"[/yellow]\n")
        console.print("Then run: [cyan]source ~/.bashrc[/cyan]")
    elif shell == 'fish':
        console.print("Add this to ~/.config/fish/completions/cdc.fish:\n")
        console.print("[yellow]_CDC_COMPLETE=fish_source cdc | source[/yellow]\n")
        console.print("Then reload: [cyan]exec fish[/cyan]")
    
    console.print("\n[green]✓[/green] Instructions displayed above")
    console.print("[dim]Completion will provide command and option suggestions[/dim]")


@completion.command('generate')
@click.option('--shell', type=click.Choice(['bash', 'zsh', 'fish']), required=True,
              help='Shell type')
@click.pass_context
def completion_generate(ctx: click.Context, shell: str) -> None:
    """Generate completion script for shell."""
    import subprocess
    import sys
    
    env_var = f"_CDC_COMPLETE={shell}_source"
    result = subprocess.run(
        [sys.executable, '-m', 'claude_dev_cli.cli'],
        env={**os.environ, '_CDC_COMPLETE': f'{shell}_source'},
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        click.echo(result.stdout)
    else:
        ctx.obj['console'].print(f"[red]Error generating completion: {result.stderr}[/red]")
        sys.exit(1)


@main.group()
def history() -> None:
    """Manage conversation history."""
    pass


@history.command('list')
@click.option('-n', '--limit', type=int, default=10, help='Number of conversations to show')
@click.option('-s', '--search', help='Search conversations')
@click.pass_context
def history_list(ctx: click.Context, limit: int, search: Optional[str]) -> None:
    """List conversation history."""
    console = ctx.obj['console']
    config = Config()
    conv_history = ConversationHistory(config.config_dir / "history")
    
    conversations = conv_history.list_conversations(limit=limit, search_query=search)
    
    if not conversations:
        console.print("[yellow]No conversations found[/yellow]")
        return
    
    for conv in conversations:
        summary = conv.get_summary(80)
        console.print(f"\n[cyan]{conv.conversation_id}[/cyan]")
        console.print(f"[dim]{conv.updated_at.strftime('%Y-%m-%d %H:%M')} | {len(conv.messages)} messages[/dim]")
        console.print(f"  {summary}")


@history.command('export')
@click.argument('conversation_id')
@click.option('--format', type=click.Choice(['markdown', 'json']), default='markdown')
@click.option('-o', '--output', type=click.Path(), help='Output file')
@click.pass_context
def history_export(ctx: click.Context, conversation_id: str, format: str, output: Optional[str]) -> None:
    """Export a conversation."""
    console = ctx.obj['console']
    config = Config()
    conv_history = ConversationHistory(config.config_dir / "history")
    
    content = conv_history.export_conversation(conversation_id, format)
    if not content:
        console.print(f"[red]Conversation {conversation_id} not found[/red]")
        sys.exit(1)
    
    if output:
        Path(output).write_text(content)
        console.print(f"[green]✓[/green] Exported to {output}")
    else:
        click.echo(content)


@history.command('summarize')
@click.argument('conversation_id', required=False)
@click.option('--keep-recent', type=int, default=4, help='Number of recent message pairs to keep')
@click.option('--latest', is_flag=True, help='Summarize the latest conversation')
@click.pass_context
def history_summarize(
    ctx: click.Context, 
    conversation_id: Optional[str], 
    keep_recent: int,
    latest: bool
) -> None:
    """Summarize a conversation to reduce token usage.
    
    Older messages are compressed into an AI-generated summary while keeping
    recent messages intact. This reduces context window usage and costs.
    
    Examples:
        cdc history summarize 20240109_143022
        cdc history summarize --latest
        cdc history summarize --latest --keep-recent 6
    """
    console = ctx.obj['console']
    config = Config()
    conv_history = ConversationHistory(config.config_dir / "history")
    
    # Determine which conversation to summarize
    if latest:
        conv = conv_history.get_latest_conversation()
        if not conv:
            console.print("[red]No conversations found[/red]")
            sys.exit(1)
        conversation_id = conv.conversation_id
    elif not conversation_id:
        console.print("[red]Error: Provide conversation_id or use --latest[/red]")
        console.print("\nUsage: cdc history summarize CONVERSATION_ID")
        console.print("   or: cdc history summarize --latest")
        sys.exit(1)
    
    # Load conversation to show stats
    conv = conv_history.load_conversation(conversation_id)
    if not conv:
        console.print(f"[red]Conversation {conversation_id} not found[/red]")
        sys.exit(1)
    
    # Show before stats
    tokens_before = conv.estimate_tokens()
    messages_before = len(conv.messages)
    console.print(f"\n[cyan]Conversation:[/cyan] {conversation_id}")
    console.print(f"[dim]Messages: {messages_before} | Estimated tokens: {tokens_before:,}[/dim]\n")
    
    if messages_before <= keep_recent:
        console.print(f"[yellow]Too few messages to summarize ({messages_before} <= {keep_recent})[/yellow]")
        return
    
    # Summarize
    with console.status("[bold blue]Generating summary..."):
        summary = conv_history.summarize_conversation(conversation_id, keep_recent)
    
    if not summary:
        console.print("[red]Failed to generate summary[/red]")
        sys.exit(1)
    
    # Reload and show after stats
    conv = conv_history.load_conversation(conversation_id)
    if conv:
        tokens_after = conv.estimate_tokens()
        messages_after = len(conv.messages)
        
        token_savings = tokens_before - tokens_after
        savings_percent = (token_savings / tokens_before * 100) if tokens_before > 0 else 0
        
        console.print("[green]✓ Conversation summarized[/green]\n")
        console.print(f"[dim]Messages:[/dim] {messages_before} → {messages_after}")
        console.print(f"[dim]Tokens:[/dim] {tokens_before:,} → {tokens_after:,} ({token_savings:,} saved, {savings_percent:.1f}%)\n")
        console.print("[bold]Summary:[/bold]")
        console.print(Panel(summary, border_style="blue"))


@history.command('delete')
@click.argument('conversation_id')
@click.pass_context
def history_delete(ctx: click.Context, conversation_id: str) -> None:
    """Delete a conversation."""
    console = ctx.obj['console']
    config = Config()
    conv_history = ConversationHistory(config.config_dir / "history")
    
    if conv_history.delete_conversation(conversation_id):
        console.print(f"[green]✓[/green] Deleted conversation: {conversation_id}")
    else:
        console.print(f"[red]Conversation {conversation_id} not found[/red]")
        sys.exit(1)


@main.group()
def config() -> None:
    """Manage configuration."""
    pass


@config.command('add')
@click.argument('provider', type=click.Choice(['anthropic', 'openai', 'ollama'], case_sensitive=False), default='anthropic')
@click.argument('name')
@click.option('--api-key', help='API key (or set {NAME}_<PROVIDER>_API_KEY env var; not needed for ollama)')
@click.option('--description', help='Description of this API config')
@click.option('--default', is_flag=True, help='Set as default API config')
@click.option('--base-url', help='Custom API base URL (for Azure, proxies, or local Ollama server)')
@click.pass_context
def config_add(
    ctx: click.Context,
    provider: str,
    name: str,
    api_key: Optional[str],
    description: Optional[str],
    default: bool,
    base_url: Optional[str]
) -> None:
    """Add a new provider configuration.
    
    PROVIDER: Provider type (anthropic, openai, or ollama)
    NAME: Configuration name
    
    Examples:
      cdc config add anthropic personal --default
      cdc config add openai work-openai --api-key sk-...
      cdc config add ollama local --default
      cdc config add ollama remote --base-url http://server:11434
    """
    console = ctx.obj['console']
    
    try:
        from claude_dev_cli.providers.factory import ProviderFactory
        
        # Check if provider is available
        if not ProviderFactory.is_provider_available(provider):
            console.print(f"[red]Error: {provider} provider not available[/red]")
            if provider == 'openai':
                console.print("Install with: pip install 'claude-dev-cli[openai]'")
            elif provider == 'ollama':
                console.print("Install with: pip install 'claude-dev-cli[ollama]'")
            sys.exit(1)
        
        config = Config()
        
        # Get API key from environment if not provided (skip for ollama)
        if api_key is None and provider not in ['ollama']:
            env_var = f"{name.upper()}_{provider.upper()}_API_KEY"
            api_key = os.environ.get(env_var)
            if not api_key:
                # Try generic env var for provider
                generic_env = f"{provider.upper()}_API_KEY"
                api_key = os.environ.get(generic_env)
            if not api_key:
                raise ValueError(
                    f"API key not provided and {env_var} environment variable not set"
                )
        
        # Check if name already exists
        api_configs = config._data.get("api_configs", [])
        for cfg in api_configs:
            if cfg["name"] == name:
                raise ValueError(f"Config with name '{name}' already exists")
        
        # Store API key in secure storage (if provided)
        if api_key:
            config.secure_storage.store_key(name, api_key)
        
        # If this is the first config or make_default is True, set as default
        if default or not api_configs:
            for cfg in api_configs:
                cfg["default"] = False
        
        # Create provider config
        from claude_dev_cli.config import ProviderConfig
        provider_config = ProviderConfig(
            name=name,
            provider=provider,
            api_key="",  # Empty string indicates key is in secure storage (or not needed)
            base_url=base_url,
            description=description,
            default=default or not api_configs
        )
        
        api_configs.append(provider_config.model_dump())
        config._data["api_configs"] = api_configs
        config._save_config()
        
        console.print(f"[green]✓[/green] Added {provider} config: {name}")
        
        # Show storage method (if API key was stored)
        if api_key:
            storage_method = config.secure_storage.get_storage_method()
            if storage_method == "keyring":
                console.print("[dim]🔐 Stored securely in system keyring[/dim]")
            else:
                console.print("[dim]🔒 Stored in encrypted file (keyring unavailable)[/dim]")
        else:
            console.print("[dim]ℹ️  No API key needed for local provider[/dim]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@config.command('migrate-keys')
@click.pass_context
def config_migrate_keys(ctx: click.Context) -> None:
    """Manually migrate API keys to secure storage."""
    console = ctx.obj['console']
    
    try:
        config = Config()
        
        # Check if any keys need migration
        api_configs = config._data.get("api_configs", [])
        plaintext_keys = {c["name"]: c.get("api_key", "") 
                         for c in api_configs 
                         if c.get("api_key")}
        
        if not plaintext_keys:
            console.print("[green]✓[/green] All keys are already in secure storage.")
            storage_method = config.secure_storage.get_storage_method()
            console.print(f"[dim]Using: {storage_method}[/dim]")
            return
        
        console.print(f"[yellow]Found {len(plaintext_keys)} plaintext key(s)[/yellow]")
        console.print("Migrating to secure storage...\n")
        
        # Trigger migration
        config._auto_migrate_keys()
        
        console.print(f"[green]✓[/green] Migrated {len(plaintext_keys)} key(s) to secure storage.")
        storage_method = config.secure_storage.get_storage_method()
        console.print(f"[dim]Using: {storage_method}[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@config.command('list')
@click.pass_context
def config_list(ctx: click.Context) -> None:
    """List all API configurations."""
    console = ctx.obj['console']
    
    config = Config()
    api_configs = config.list_api_configs()
    
    if not api_configs:
        console.print("[yellow]No API configurations found.[/yellow]")
        console.print("Run 'cdc config add' to add one.")
        return
    
    # Show storage method
    storage_method = config.secure_storage.get_storage_method()
    storage_display = {
        "keyring": "🔐 System Keyring (Secure)",
        "encrypted_file": "🔒 Encrypted File (Fallback)"
    }.get(storage_method, storage_method)
    console.print(f"\n[dim]Storage: {storage_display}[/dim]\n")
    
    for cfg in api_configs:
        default_marker = " [bold green](default)[/bold green]" if cfg.default else ""
        provider = getattr(cfg, 'provider', 'anthropic')  # Default to anthropic for backward compatibility
        console.print(f"• {cfg.name}{default_marker} [dim]({provider})[/dim]")
        if cfg.description:
            console.print(f"  {cfg.description}")
        console.print(f"  API Key: {cfg.api_key[:15]}...")
    
    # Show default model
    console.print(f"\n[dim]Default model: {config.get_model()}[/dim]")


@config.command('set-model')
@click.argument('model')
@click.pass_context
def config_set_model(ctx: click.Context, model: str) -> None:
    """Set the default Claude model.
    
    Examples:
      cdc config set-model claude-sonnet-4-20250514
      cdc config set-model claude-3-5-sonnet-20241022
      cdc config set-model claude-opus-4-20250514
    """
    console = ctx.obj['console']
    
    try:
        config = Config()
        config.set_model(model)
        console.print(f"[green]✓[/green] Default model set to: {model}")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@main.group()
def model() -> None:
    """Manage model profiles and pricing."""
    pass


@model.command('add')
@click.argument('name')
@click.argument('model_id')
@click.option('--input-price', type=float, required=True, help='Input price per Mtok (USD)')
@click.option('--output-price', type=float, required=True, help='Output price per Mtok (USD)')
@click.option('--description', help='Model profile description')
@click.option('--api-config', help='Tie to specific API config')
@click.option('--default', is_flag=True, help='Set as default')
@click.pass_context
def model_add(
    ctx: click.Context,
    name: str,
    model_id: str,
    input_price: float,
    output_price: float,
    description: Optional[str],
    api_config: Optional[str],
    default: bool
) -> None:
    """Add a model profile.
    
    Examples:
      cdc model add fast claude-3-5-haiku-20241022 --input-price 0.80 --output-price 4.00
      cdc model add enterprise-smart claude-sonnet-4-5-20250929 --input-price 2.50 --output-price 12.50 --api-config enterprise
    """
    console = ctx.obj['console']
    
    try:
        config = Config()
        config.add_model_profile(
            name=name,
            model_id=model_id,
            input_price=input_price,
            output_price=output_price,
            description=description,
            api_config_name=api_config,
            make_default=default
        )
        
        scope = f" for API '{api_config}'" if api_config else " (global)"
        console.print(f"[green]✓[/green] Model profile '{name}' added{scope}")
        console.print(f"[dim]Model: {model_id}[/dim]")
        console.print(f"[dim]Pricing: ${input_price}/Mtok input, ${output_price}/Mtok output[/dim]")
        
        if default:
            console.print(f"[green]Set as default{scope}[/green]")
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@model.command('list')
@click.option('--api-config', help='Filter by API config')
@click.pass_context
def model_list(ctx: click.Context, api_config: Optional[str]) -> None:
    """List model profiles."""
    console = ctx.obj['console']
    
    try:
        from rich.table import Table
        
        config = Config()
        profiles = config.list_model_profiles(api_config_name=api_config)
        
        if not profiles:
            console.print("[yellow]No model profiles found.[/yellow]")
            console.print("Run 'cdc model add' to create one.")
            return
        
        # Get default profile
        default_profile = config.get_default_model_profile(api_config_name=api_config)
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Name", style="cyan")
        table.add_column("Model ID", style="green")
        table.add_column("Input $/Mtok", justify="right", style="yellow")
        table.add_column("Output $/Mtok", justify="right", style="yellow")
        table.add_column("Scope", style="blue")
        table.add_column("Description")
        
        for profile in profiles:
            default_marker = " ⭐" if profile.name == default_profile else ""
            scope = profile.api_config_name or "global"
            
            table.add_row(
                profile.name + default_marker,
                profile.model_id,
                f"${profile.input_price_per_mtok:.2f}",
                f"${profile.output_price_per_mtok:.2f}",
                scope,
                profile.description or ""
            )
        
        console.print(table)
        console.print(f"\n[dim]Default profile: {default_profile} ⭐[/dim]")
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@model.command('show')
@click.argument('name')
@click.pass_context
def model_show(ctx: click.Context, name: str) -> None:
    """Show model profile details."""
    console = ctx.obj['console']
    
    try:
        config = Config()
        profile = config.get_model_profile(name)
        
        if not profile:
            console.print(f"[red]Model profile '{name}' not found[/red]")
            sys.exit(1)
        
        scope = profile.api_config_name or "global"
        cost_1k_in = profile.input_price_per_mtok / 1000
        cost_1k_out = profile.output_price_per_mtok / 1000
        
        console.print(Panel(
            f"[bold]{profile.name}[/bold]\n\n"
            f"[dim]{profile.description or 'No description'}[/dim]\n\n"
            f"Model ID: [green]{profile.model_id}[/green]\n"
            f"Scope: [blue]{scope}[/blue]\n\n"
            f"Pricing:\n"
            f"  Input:  ${profile.input_price_per_mtok:.2f}/Mtok (${cost_1k_in:.4f}/1K tokens)\n"
            f"  Output: ${profile.output_price_per_mtok:.2f}/Mtok (${cost_1k_out:.4f}/1K tokens)\n\n"
            f"Use cases: {', '.join(profile.use_cases) if profile.use_cases else 'None specified'}",
            title="Model Profile",
            border_style="blue"
        ))
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@model.command('remove')
@click.argument('name')
@click.pass_context
def model_remove(ctx: click.Context, name: str) -> None:
    """Remove a model profile."""
    console = ctx.obj['console']
    
    try:
        config = Config()
        if config.remove_model_profile(name):
            console.print(f"[green]✓[/green] Model profile '{name}' removed")
        else:
            console.print(f"[red]Model profile '{name}' not found[/red]")
            sys.exit(1)
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@model.command('set-default')
@click.argument('name')
@click.option('--api-config', help='Set default for specific API config')
@click.pass_context
def model_set_default(ctx: click.Context, name: str, api_config: Optional[str]) -> None:
    """Set default model profile.
    
    Examples:
      cdc model set-default smart
      cdc model set-default enterprise-smart --api-config enterprise
    """
    console = ctx.obj['console']
    
    try:
        config = Config()
        
        if api_config:
            config.set_api_default_model_profile(api_config, name)
            console.print(f"[green]✓[/green] Default model for API '{api_config}' set to: {name}")
        else:
            config.set_default_model_profile(name)
            console.print(f"[green]✓[/green] Global default model set to: {name}")
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@main.group()
def generate() -> None:
    """Generate code, tests, and documentation."""
    pass


@generate.command('tests')
@click.argument('paths', nargs=-1, type=click.Path(exists=True))
@click.option('-o', '--output', type=click.Path(), help='Output file path (single file only)')
@click.option('-a', '--api', help='API config to use')
@click.option('-i', '--interactive', is_flag=True, help='Interactive refinement mode')
@click.option('--auto-context', is_flag=True, help='Include dependencies and related files')
@click.option('--max-files', type=int, default=10, help='Maximum files to process (default: 10)')
@click.pass_context
def gen_tests(
    ctx: click.Context,
    paths: tuple,
    output: Optional[str],
    api: Optional[str],
    interactive: bool,
    auto_context: bool,
    max_files: int
) -> None:
    """Generate pytest tests for Python files.
    
    Can generate tests for multiple files or directories:
    
      cdc generate tests file1.py file2.py
      cdc generate tests src/
    """
    console = ctx.obj['console']
    from claude_dev_cli.path_utils import expand_paths
    
    try:
        if not paths:
            console.print("[yellow]No files specified. Provide file paths.[/yellow]")
            return
        
        files = expand_paths(list(paths), max_files=max_files)
        if not files:
            console.print("[yellow]No files found.[/yellow]")
            return
        
        # Output only works with single file
        if output and len(files) > 1:
            console.print("[yellow]Warning: --output only works with single file. Ignoring output option.[/yellow]")
            output = None
        
        if len(files) > 1:
            console.print(f"\n[bold]Generating tests for {len(files)} file(s):[/bold]")
            for f in files[:5]:
                console.print(f"  • {f}")
            if len(files) > 5:
                console.print(f"  ... and {len(files) - 5} more")
            console.print()
        
        # Build combined prompt
        files_content = ""
        for file_path in files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                files_content += f"\n\n## File: {file_path}\n\n```\n{content}\n```\n"
            except Exception as e:
                console.print(f"[yellow]Warning: Could not read {file_path}: {e}[/yellow]")
        
        if auto_context:
            from claude_dev_cli.context import ContextGatherer
            
            with console.status("[bold blue]Gathering context..."):
                gatherer = ContextGatherer()
                context = gatherer.gather_for_file(files[0], include_git=False)
                context_info = context.format_for_prompt()
            
            console.print("[dim]✓ Context gathered (dependencies, related files)[/dim]")
            
            client = ClaudeClient(api_config_name=api)
            prompt = f"{context_info}\n\nFiles:{files_content}\n\nPlease generate comprehensive pytest tests for these files, including fixtures, edge cases, and proper mocking where needed."
        else:
            with console.status(f"[bold blue]Generating tests for {len(files)} file(s)..."):
                client = ClaudeClient(api_config_name=api)
                prompt = f"Files to test:{files_content}\n\nPlease generate comprehensive pytest tests for these files, including fixtures, edge cases, and proper mocking where needed."
        
        result = client.call(prompt)
        
        if interactive:
            # Show initial result
            console.print("\n[bold]Initial Tests:[/bold]\n")
            console.print(result)
            
            # Interactive refinement loop
            client = ClaudeClient(api_config_name=api)
            conversation_context = [result]
            
            while True:
                console.print("\n[dim]Commands: 'save' to save and exit, 'exit' to discard, or ask for changes[/dim]")
                user_input = console.input("[cyan]You:[/cyan] ").strip()
                
                if user_input.lower() == 'exit':
                    console.print("[yellow]Discarded changes[/yellow]")
                    return
                
                if user_input.lower() == 'save':
                    result = conversation_context[-1]
                    break
                
                if not user_input:
                    continue
                
                # Get refinement
                refinement_prompt = f"Previous tests:\n\n{conversation_context[-1]}\n\nUser request: {user_input}\n\nProvide the updated tests."
                
                console.print("\n[bold green]Claude:[/bold green] ", end='')
                response_parts = []
                for chunk in client.call_streaming(refinement_prompt):
                    console.print(chunk, end='')
                    response_parts.append(chunk)
                console.print()
                
                result = ''.join(response_parts)
                conversation_context.append(result)
        
        if output:
            with open(output, 'w') as f:
                f.write(result)
            console.print(f"\n[green]✓[/green] Tests saved to: {output}")
        elif not interactive:
            console.print(result)
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@generate.command('docs')
@click.argument('paths', nargs=-1, type=click.Path(exists=True))
@click.option('-o', '--output', type=click.Path(), help='Output file path (single file only)')
@click.option('-a', '--api', help='API config to use')
@click.option('-i', '--interactive', is_flag=True, help='Interactive refinement mode')
@click.option('--auto-context', is_flag=True, help='Include dependencies and related files')
@click.option('--max-files', type=int, default=10, help='Maximum files to process (default: 10)')
@click.pass_context
def gen_docs(
    ctx: click.Context,
    paths: tuple,
    output: Optional[str],
    api: Optional[str],
    interactive: bool,
    auto_context: bool,
    max_files: int
) -> None:
    """Generate documentation for files.
    
    Can generate docs for multiple files or directories:
    
      cdc generate docs file1.py file2.py
      cdc generate docs src/
    """
    console = ctx.obj['console']
    from claude_dev_cli.path_utils import expand_paths
    
    try:
        if not paths:
            console.print("[yellow]No files specified. Provide file paths.[/yellow]")
            return
        
        files = expand_paths(list(paths), max_files=max_files)
        if not files:
            console.print("[yellow]No files found.[/yellow]")
            return
        
        # Output only works with single file
        if output and len(files) > 1:
            console.print("[yellow]Warning: --output only works with single file. Ignoring output option.[/yellow]")
            output = None
        
        if len(files) > 1:
            console.print(f"\n[bold]Generating docs for {len(files)} file(s):[/bold]")
            for f in files[:5]:
                console.print(f"  • {f}")
            if len(files) > 5:
                console.print(f"  ... and {len(files) - 5} more")
            console.print()
        
        # Build combined prompt
        files_content = ""
        for file_path in files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                files_content += f"\n\n## File: {file_path}\n\n```\n{content}\n```\n"
            except Exception as e:
                console.print(f"[yellow]Warning: Could not read {file_path}: {e}[/yellow]")
        
        if auto_context:
            from claude_dev_cli.context import ContextGatherer
            
            with console.status("[bold blue]Gathering context..."):
                gatherer = ContextGatherer()
                context = gatherer.gather_for_file(files[0], include_git=False)
                context_info = context.format_for_prompt()
            
            console.print("[dim]✓ Context gathered (dependencies, related files)[/dim]")
            
            client = ClaudeClient(api_config_name=api)
            prompt = f"{context_info}\n\nFiles:{files_content}\n\nPlease generate comprehensive documentation for these files, including API reference, usage examples, and integration notes."
        else:
            with console.status(f"[bold blue]Generating documentation for {len(files)} file(s)..."):
                client = ClaudeClient(api_config_name=api)
                prompt = f"Files to document:{files_content}\n\nPlease generate comprehensive documentation for these files, including API reference, usage examples, and integration notes."
        
        result = client.call(prompt)
        
        if interactive:
            console.print("\n[bold]Initial Documentation:[/bold]\n")
            md = Markdown(result)
            console.print(md)
            
            client = ClaudeClient(api_config_name=api)
            conversation_context = [result]
            
            while True:
                console.print("\n[dim]Commands: 'save' to save and exit, 'exit' to discard, or ask for changes[/dim]")
                user_input = console.input("[cyan]You:[/cyan] ").strip()
                
                if user_input.lower() == 'exit':
                    console.print("[yellow]Discarded changes[/yellow]")
                    return
                
                if user_input.lower() == 'save':
                    result = conversation_context[-1]
                    break
                
                if not user_input:
                    continue
                
                refinement_prompt = f"Previous documentation:\n\n{conversation_context[-1]}\n\nUser request: {user_input}\n\nProvide the updated documentation."
                
                console.print("\n[bold green]Claude:[/bold green] ", end='')
                response_parts = []
                for chunk in client.call_streaming(refinement_prompt):
                    console.print(chunk, end='')
                    response_parts.append(chunk)
                console.print()
                
                result = ''.join(response_parts)
                conversation_context.append(result)
        
        if output:
            with open(output, 'w') as f:
                f.write(result)
            console.print(f"\n[green]✓[/green] Documentation saved to: {output}")
        elif not interactive:
            md = Markdown(result)
            console.print(md)
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@generate.command('code')
@click.option('--description', help='Inline code specification')
@click.option('-f', '--file', 'spec_file', type=click.Path(exists=True), help='Read specification from file')
@click.option('--pdf', type=click.Path(exists=True), help='Read specification from PDF')
@click.option('--url', help='Fetch specification from URL')
@click.option('-o', '--output', required=True, type=click.Path(), help='Output file or directory path (required)')
@click.option('--language', help='Target language (auto-detected from output extension)')
@click.option('-m', '--model', help='Model profile to use')
@click.option('-a', '--api', help='API config to use')
@click.option('-i', '--interactive', is_flag=True, help='Interactive refinement mode')
@click.option('--auto-context', is_flag=True, help='Include project context')
@click.option('--dry-run', is_flag=True, help='Preview without writing files')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompts')
@click.pass_context
def gen_code(
    ctx: click.Context,
    description: Optional[str],
    spec_file: Optional[str],
    pdf: Optional[str],
    url: Optional[str],
    output: str,
    language: Optional[str],
    model: Optional[str],
    api: Optional[str],
    interactive: bool,
    auto_context: bool,
    dry_run: bool,
    yes: bool
) -> None:
    """Generate code from a specification.
    
    Reads specification from text, file, PDF, or URL and generates complete code.
    
    Single file mode (output is file):
      cdc generate code --description "REST API client" -o client.py
      
    Multi-file mode (output is directory):
      cdc generate code --description "FastAPI app" -o my-api/
      cdc generate code --file spec.md -o project/
      
    Examples:
      cdc generate code --file spec.md -o implementation.go
      cdc generate code --pdf requirements.pdf -o app.js
      cdc generate code --url https://example.com/spec -o service/ --dry-run
    """
    console = ctx.obj['console']
    from claude_dev_cli.input_sources import get_input_content
    from pathlib import Path
    
    try:
        # Get specification content
        spec_content, source_desc = get_input_content(
            description=description,
            file_path=spec_file,
            pdf_path=pdf,
            url=url,
            console=console
        )
        
        # Detect language from output extension if not specified
        if not language:
            ext = Path(output).suffix.lstrip('.')
            language_map = {
                'py': 'Python',
                'js': 'JavaScript',
                'ts': 'TypeScript',
                'go': 'Go',
                'rs': 'Rust',
                'java': 'Java',
                'cpp': 'C++',
                'c': 'C',
                'cs': 'C#',
                'rb': 'Ruby',
                'php': 'PHP',
                'swift': 'Swift',
                'kt': 'Kotlin',
            }
            language = language_map.get(ext, ext.upper() if ext else None)
        
        # Detect if output is directory (multi-file mode)
        output_path = Path(output)
        is_directory = output.endswith('/') or output_path.is_dir()
        
        console.print(f"[cyan]Generating code from:[/cyan] {source_desc}")
        if language:
            console.print(f"[cyan]Target language:[/cyan] {language}")
        
        if is_directory:
            console.print(f"[cyan]Output directory:[/cyan] {output}")
            console.print(f"[cyan]Mode:[/cyan] Multi-file project generation\n")
        else:
            console.print(f"[cyan]Output file:[/cyan] {output}\n")
        
        # Build prompt (different for single vs multi-file)
        if is_directory:
            # Multi-file mode: request structured output
            prompt = f"Specification:\n\n{spec_content}\n\n"
            if language:
                prompt += f"Generate a complete, production-ready {language} project that implements this specification. "
            else:
                prompt += "Generate a complete, production-ready project that implements this specification. "
            prompt += """\n
Provide your response in this format:

## File: relative/path/to/file.ext
```language
// Complete file content
```

## File: another/file.ext
```language
// Complete file content
```

Include ALL necessary files: source code, configuration, dependencies, README, etc.
Use proper directory structure and include proper error handling, documentation, and best practices."""
        else:
            # Single file mode: simple prompt
            prompt = f"Specification:\n\n{spec_content}\n\n"
            if language:
                prompt += f"Generate complete, production-ready {language} code that implements this specification. "
            else:
                prompt += "Generate complete, production-ready code that implements this specification. "
            prompt += "Include proper error handling, documentation, and best practices."
        
        # Add context if requested
        if auto_context:
            from claude_dev_cli.context import ContextGatherer
            
            with console.status("[bold blue]Gathering project context..."):
                gatherer = ContextGatherer()
                # Gather context from current directory
                context = gatherer.gather_for_file(".", include_git=True)
                context_info = context.format_for_prompt()
            
            console.print("[dim]✓ Context gathered[/dim]")
            prompt = f"{context_info}\n\n{prompt}"
        
        # Generate code
        with console.status(f"[bold blue]Generating code..."):
            client = ClaudeClient(api_config_name=api)
            result = client.call(prompt, model=model)
        
        # Interactive refinement
        if interactive:
            console.print("\n[bold]Initial Code:[/bold]\n")
            console.print(result)
            
            client = ClaudeClient(api_config_name=api)
            conversation_context = [result]
            
            while True:
                console.print("\n[dim]Commands: 'save' to save and exit, 'exit' to discard, or ask for changes[/dim]")
                user_input = console.input("[cyan]You:[/cyan] ").strip()
                
                if user_input.lower() == 'exit':
                    console.print("[yellow]Discarded changes[/yellow]")
                    return
                
                if user_input.lower() == 'save':
                    result = conversation_context[-1]
                    break
                
                if not user_input:
                    continue
                
                # Get refinement
                refinement_prompt = f"Previous code:\n\n{conversation_context[-1]}\n\nUser request: {user_input}\n\nProvide the updated code."
                
                console.print("\n[bold green]Claude:[/bold green] ", end='')
                response_parts = []
                for chunk in client.call_streaming(refinement_prompt, model=model):
                    console.print(chunk, end='')
                    response_parts.append(chunk)
                console.print()
                
                result = ''.join(response_parts)
                conversation_context.append(result)
        
        # Save output
        if is_directory:
            # Multi-file mode: parse and write multiple files
            from claude_dev_cli.multi_file_handler import MultiFileResponse
            
            multi_file = MultiFileResponse()
            multi_file.parse_response(result, base_path=output_path)
            
            if not multi_file.files:
                console.print("[yellow]Warning: No files were detected in the response.[/yellow]")
                console.print("[dim]Falling back to single file output...[/dim]")
                # Save as single file anyway
                fallback_file = output_path / "generated_code.txt"
                output_path.mkdir(parents=True, exist_ok=True)
                fallback_file.write_text(result)
                console.print(f"\n[green]✓[/green] Output saved to: {fallback_file}")
                return
            
            # Validate paths
            errors = multi_file.validate_paths(output_path)
            if errors:
                console.print("[red]Path validation errors:[/red]")
                for error in errors:
                    console.print(f"  • {error}")
                sys.exit(1)
            
            # Show preview
            multi_file.preview(console, output_path)
            
            # Confirm or auto-accept
            if not yes and not dry_run:
                if not multi_file.confirm(console, output_path):
                    console.print("[yellow]Cancelled[/yellow]")
                    return
            
            # Write files
            multi_file.write_all(output_path, dry_run=dry_run, console=console)
            
            if dry_run:
                console.print("\n[yellow]Dry-run mode - no files were written[/yellow]")
            else:
                console.print(f"\n[green]✓[/green] Project created in: {output}")
        else:
            # Single file mode: simple write
            Path(output).write_text(result)
            console.print(f"\n[green]✓[/green] Code saved to: {output}")
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@generate.command('feature')
@click.argument('paths', nargs=-1, type=click.Path(exists=True))
@click.option('--description', help='Inline feature specification')
@click.option('-f', '--file', 'spec_file', type=click.Path(exists=True), help='Read specification from file')
@click.option('--pdf', type=click.Path(exists=True), help='Read specification from PDF')
@click.option('--url', help='Fetch specification from URL')
@click.option('--max-files', type=int, default=10, help='Maximum files to modify (default: 10)')
@click.option('-m', '--model', help='Model profile to use')
@click.option('-a', '--api', help='API config to use')
@click.option('-i', '--interactive', is_flag=True, help='Interactive refinement mode')
@click.option('--auto-context', is_flag=True, help='Include project context')
@click.option('--preview', is_flag=True, help='Preview changes without applying')
@click.option('--dry-run', is_flag=True, help='Show what would be changed without writing')
@click.option('--yes', '-y', is_flag=True, help='Apply changes without confirmation')
@click.pass_context
def gen_feature(
    ctx: click.Context,
    paths: tuple,
    description: Optional[str],
    spec_file: Optional[str],
    pdf: Optional[str],
    url: Optional[str],
    max_files: int,
    model: Optional[str],
    api: Optional[str],
    interactive: bool,
    auto_context: bool,
    preview: bool,
    dry_run: bool,
    yes: bool
) -> None:
    """Generate code to add a feature to existing project.
    
    Analyzes existing code and generates changes to implement a feature.
    
    Examples:
      cdc generate feature --description "Add authentication" src/
      cdc generate feature --file feature-spec.md
      cdc generate feature --pdf requirements.pdf --preview
      cdc generate feature --url https://example.com/spec src/
      cdc generate feature -f spec.md --dry-run
      cdc generate feature -f spec.md --yes
    """
    console = ctx.obj['console']
    from claude_dev_cli.input_sources import get_input_content
    from claude_dev_cli.path_utils import expand_paths, auto_detect_files
    
    try:
        # Get feature specification
        spec_content, source_desc = get_input_content(
            description=description,
            file_path=spec_file,
            pdf_path=pdf,
            url=url,
            console=console
        )
        
        # Determine files to analyze
        if paths:
            files = expand_paths(list(paths), max_files=max_files)
        else:
            files = auto_detect_files()
            if files:
                console.print(f"[dim]Auto-detected {len(files)} file(s) from project[/dim]")
        
        if not files:
            console.print("[yellow]No files found. Specify paths or run in a project directory.[/yellow]")
            return
        
        console.print(f"[cyan]Feature specification from:[/cyan] {source_desc}")
        console.print(f"[cyan]Analyzing:[/cyan] {len(files)} file(s)\n")
        
        # Show files
        if len(files) > 1:
            console.print(f"[bold]Files to analyze:[/bold]")
            for f in files[:5]:
                console.print(f"  • {f}")
            if len(files) > 5:
                console.print(f"  ... and {len(files) - 5} more")
            console.print()
        
        # Build codebase content
        codebase_content = ""
        for file_path in files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                codebase_content += f"\n\n## File: {file_path}\n\n```\n{content}\n```\n"
            except Exception as e:
                console.print(f"[yellow]Warning: Could not read {file_path}: {e}[/yellow]")
        
        # Build prompt with multi-file support
        prompt = f"Feature Specification:\n\n{spec_content}\n\n"
        prompt += f"Existing Codebase:{codebase_content}\n\n"
        prompt += "Analyze the existing code and provide the complete implementation.\n\n"
        prompt += "IMPORTANT: Structure your response with file markers:\n"
        prompt += "## File: path/to/file.ext\n"
        prompt += "```language\n"
        prompt += "// complete file content\n"
        prompt += "```\n\n"
        prompt += "Use '## Create: path/to/new.ext' for new files.\n"
        prompt += "Use '## Modify: path/to/existing.ext' for changes to existing files.\n"
        prompt += "Use '## Delete: path/to/old.ext' if files should be removed.\n\n"
        prompt += "Provide complete, working code for all affected files."
        
        # Add context if requested
        if auto_context:
            from claude_dev_cli.context import ContextGatherer
            
            with console.status("[bold blue]Gathering project context..."):
                gatherer = ContextGatherer()
                context = gatherer.gather_for_file(files[0], include_git=True)
                context_info = context.format_for_prompt()
            
            console.print("[dim]✓ Context gathered[/dim]")
            prompt = f"{context_info}\n\n{prompt}"
        
        # Generate feature implementation
        with console.status(f"[bold blue]Analyzing codebase and generating feature implementation..."):
            client = ClaudeClient(api_config_name=api)
            result = client.call(prompt, model=model)
        
        # Interactive refinement
        if interactive:
            from rich.markdown import Markdown
            md = Markdown(result)
            console.print(md)
            
            client = ClaudeClient(api_config_name=api)
            conversation_context = [result]
            
            while True:
                console.print("\n[dim]Ask for changes, 'save' to continue, or 'exit' to cancel[/dim]")
                user_input = console.input("[cyan]You:[/cyan] ").strip()
                
                if user_input.lower() == 'exit':
                    console.print("[yellow]Cancelled[/yellow]")
                    return
                
                if user_input.lower() == 'save':
                    result = conversation_context[-1]
                    break
                
                if not user_input:
                    continue
                
                # Get refinement
                refinement_prompt = f"Previous implementation:\n\n{conversation_context[-1]}\n\nUser request: {user_input}\n\nProvide the updated implementation with file markers."
                
                console.print("\n[bold green]Claude:[/bold green] ", end='')
                response_parts = []
                for chunk in client.call_streaming(refinement_prompt, model=model):
                    console.print(chunk, end='')
                    response_parts.append(chunk)
                console.print()
                
                result = ''.join(response_parts)
                conversation_context.append(result)
        
        # Parse multi-file response
        from claude_dev_cli.multi_file_handler import MultiFileResponse
        from pathlib import Path
        
        # Use current directory as base
        base_path = Path.cwd()
        
        multi_file = MultiFileResponse()
        multi_file.parse_response(result, base_path=base_path)
        
        if not multi_file.files:
            # No structured output detected, show markdown
            console.print("\n[yellow]No structured file output detected[/yellow]")
            from rich.markdown import Markdown
            md = Markdown(result)
            console.print(md)
            console.print("\n[dim]Apply the changes manually from the output above[/dim]")
            return
        
        # Validate paths
        errors = multi_file.validate_paths(base_path)
        if errors:
            console.print("[red]Path validation errors:[/red]")
            for error in errors:
                console.print(f"  • {error}")
            sys.exit(1)
        
        # Show preview
        multi_file.preview(console, base_path)
        
        # Handle preview/dry-run modes
        if preview or dry_run:
            console.print("\n[yellow]Preview mode - no changes applied[/yellow]")
            if preview:
                console.print("[dim]Remove --preview flag to apply changes[/dim]")
            return
        
        # Confirm or auto-accept
        if not yes:
            if not multi_file.confirm(console, base_path):
                console.print("[yellow]Cancelled[/yellow]")
                return
        
        # Write files
        multi_file.write_all(base_path, dry_run=False, console=console)
        
        console.print(f"\n[green]✓[/green] Feature implemented successfully")
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@main.command('review')
@click.argument('paths', nargs=-1, type=click.Path(exists=True))
@click.option('-a', '--api', help='API config to use')
@click.option('-i', '--interactive', is_flag=True, help='Interactive follow-up questions')
@click.option('--auto-context', is_flag=True, help='Automatically include git, dependencies, and related files')
@click.option('--max-files', type=int, default=20, help='Maximum files to review (default: 20)')
@click.pass_context
def review(
    ctx: click.Context,
    paths: tuple,
    api: Optional[str],
    interactive: bool,
    auto_context: bool,
    max_files: int
) -> None:
    """Review code for bugs and improvements.
    
    Can review multiple files, directories, or auto-detect git changes:
    
      cdc review file1.py file2.py    # Multiple files
      cdc review src/                 # Directory
      cdc review                      # Auto-detect git changes
    """
    console = ctx.obj['console']
    from claude_dev_cli.path_utils import expand_paths, auto_detect_files
    
    try:
        # Determine files to review
        if paths:
            # Expand paths (handles directories, multiple files)
            files = expand_paths(list(paths), max_files=max_files)
        else:
            # Auto-detect files from git
            files = auto_detect_files()
            if files:
                console.print(f"[dim]Auto-detected {len(files)} file(s) from git changes[/dim]")
        
        if not files:
            console.print("[yellow]No files to review. Specify files or make some changes.[/yellow]")
            return
        
        # Show files being reviewed
        if len(files) > 1:
            console.print(f"\n[bold]Reviewing {len(files)} file(s):[/bold]")
            for f in files[:10]:  # Show first 10
                console.print(f"  • {f}")
            if len(files) > 10:
                console.print(f"  ... and {len(files) - 10} more")
            console.print()
        
        # Build combined prompt for multiple files
        files_content = ""
        for file_path in files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                files_content += f"\n\n## File: {file_path}\n\n```\n{content}\n```\n"
            except Exception as e:
                console.print(f"[yellow]Warning: Could not read {file_path}: {e}[/yellow]")
        
        # Gather context if requested
        context_info = ""
        if auto_context:
            from claude_dev_cli.context import ContextGatherer
            
            with console.status("[bold blue]Gathering context..."):
                gatherer = ContextGatherer()
                # Use first file for context gathering
                context = gatherer.gather_for_review(files[0])
                context_info = context.format_for_prompt()
            
            console.print("[dim]✓ Context gathered (git, dependencies, tests)[/dim]")
        
        with console.status(f"[bold blue]Reviewing {len(files)} file(s)..."):
            client = ClaudeClient(api_config_name=api)
            if context_info:
                prompt = f"{context_info}\n\nFiles to review:{files_content}\n\nPlease review this code for bugs and improvements."
            else:
                prompt = f"Files to review:{files_content}\n\nPlease review this code for bugs, security issues, and improvements."
            result = client.call(prompt)
        
        md = Markdown(result)
        console.print(md)
        
        if interactive:
            console.print("\n[dim]Ask follow-up questions about the review, or 'exit' to quit[/dim]")
            
            while True:
                user_input = console.input("\n[cyan]You:[/cyan] ").strip()
                
                if user_input.lower() == 'exit':
                    break
                
                if not user_input:
                    continue
                
                follow_up_prompt = f"Code review:\n\n{result}\n\nFiles:{files_content}\n\nUser question: {user_input}"
                
                console.print("\n[bold green]Claude:[/bold green] ", end='')
                for chunk in client.call_streaming(follow_up_prompt):
                    console.print(chunk, end='')
                console.print()
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@main.command('debug')
@click.option('-f', '--file', type=click.Path(exists=True), help='File to debug')
@click.option('-e', '--error', help='Error message to analyze')
@click.option('-a', '--api', help='API config to use')
@click.option('--auto-context', is_flag=True, help='Automatically include git context and parse error details')
@click.pass_context
def debug(
    ctx: click.Context,
    file: Optional[str],
    error: Optional[str],
    api: Optional[str],
    auto_context: bool
) -> None:
    """Debug code and analyze errors."""
    console = ctx.obj['console']
    
    # Read from stdin if available
    stdin_content = None
    if not sys.stdin.isatty():
        stdin_content = sys.stdin.read().strip()
    
    error_text = error or stdin_content
    
    try:
        # Gather context if requested
        if auto_context and error_text:
            from claude_dev_cli.context import ContextGatherer
            
            with console.status("[bold blue]Gathering context..."):
                gatherer = ContextGatherer()
                file_path = Path(file) if file else None
                context = gatherer.gather_for_error(error_text, file_path=file_path)
                context_info = context.format_for_prompt()
            
            console.print("[dim]✓ Context gathered (error details, git context)[/dim]")
            
            # Use context-aware analysis
            client = ClaudeClient(api_config_name=api)
            enhanced_prompt = f"{context_info}\n\nPlease analyze this error and suggest fixes."
            result = client.call(enhanced_prompt)
        else:
            # Original behavior
            with console.status("[bold blue]Analyzing error..."):
                result = debug_code(
                    file_path=file,
                    error_message=error_text,
                    api_config_name=api
                )
        
        md = Markdown(result)
        console.print(md)
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@main.command('refactor')
@click.argument('paths', nargs=-1, type=click.Path(exists=True))
@click.option('-o', '--output', type=click.Path(), help='Output file path (single file only)')
@click.option('-a', '--api', help='API config to use')
@click.option('-i', '--interactive', is_flag=True, help='Interactive refinement mode')
@click.option('--auto-context', is_flag=True, help='Automatically include git, dependencies, and related files')
@click.option('--max-files', type=int, default=20, help='Maximum files to refactor (default: 20)')
@click.option('--preview', is_flag=True, help='Preview changes without applying')
@click.option('--dry-run', is_flag=True, help='Show what would be changed without writing')
@click.option('--yes', '-y', is_flag=True, help='Apply changes without confirmation')
@click.pass_context
def refactor(
    ctx: click.Context,
    paths: tuple,
    output: Optional[str],
    api: Optional[str],
    interactive: bool,
    auto_context: bool,
    max_files: int,
    preview: bool,
    dry_run: bool,
    yes: bool
) -> None:
    """Suggest refactoring improvements.
    
    Can refactor multiple files, directories, or auto-detect git changes:
    
      cdc refactor file1.py file2.py    # Multiple files
      cdc refactor src/                 # Directory
      cdc refactor                      # Auto-detect git changes
      cdc refactor src/ --dry-run       # Preview changes
      cdc refactor file.py --yes        # Apply without confirmation
    """
    console = ctx.obj['console']
    from claude_dev_cli.path_utils import expand_paths, auto_detect_files
    
    try:
        # Determine files to refactor
        if paths:
            files = expand_paths(list(paths), max_files=max_files)
        else:
            files = auto_detect_files()
            if files:
                console.print(f"[dim]Auto-detected {len(files)} file(s) from git changes[/dim]")
        
        if not files:
            console.print("[yellow]No files to refactor. Specify files or make some changes.[/yellow]")
            return
        
        # Output only works with single file
        if output and len(files) > 1:
            console.print("[yellow]Warning: --output only works with single file. Ignoring output option.[/yellow]")
            output = None
        
        # Show files being refactored
        if len(files) > 1:
            console.print(f"\n[bold]Refactoring {len(files)} file(s):[/bold]")
            for f in files[:10]:
                console.print(f"  • {f}")
            if len(files) > 10:
                console.print(f"  ... and {len(files) - 10} more")
            console.print()
        
        # Build combined prompt with multi-file support
        files_content = ""
        for file_path in files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                files_content += f"\n\n## File: {file_path}\n\n```\n{content}\n```\n"
            except Exception as e:
                console.print(f"[yellow]Warning: Could not read {file_path}: {e}[/yellow]")
        
        refactor_instructions = (
            "\n\nIMPORTANT: Structure your response with file markers:\n"
            "## File: path/to/file.ext\n"
            "```language\n"
            "// complete refactored file content\n"
            "```\n\n"
            "Use '## Modify: path/to/file.ext' to indicate files being refactored.\n"
            "Provide complete, working refactored code for all files.\n"
        )
        
        # Gather context if requested
        if auto_context:
            from claude_dev_cli.context import ContextGatherer
            
            with console.status("[bold blue]Gathering context..."):
                gatherer = ContextGatherer()
                context = gatherer.gather_for_file(files[0])
                context_info = context.format_for_prompt()
            
            console.print("[dim]✓ Context gathered[/dim]")
            
            client = ClaudeClient(api_config_name=api)
            prompt = f"{context_info}\n\nFiles:{files_content}\n\nPlease suggest refactoring improvements.{refactor_instructions}"
        else:
            with console.status(f"[bold blue]Analyzing {len(files)} file(s)..."):
                client = ClaudeClient(api_config_name=api)
                prompt = f"Files to refactor:{files_content}\n\nPlease suggest refactoring improvements focusing on code quality, maintainability, and performance.{refactor_instructions}"
        
        result = client.call(prompt)
        
        if interactive:
            console.print("\n[bold]Initial Refactoring:[/bold]\n")
            md = Markdown(result)
            console.print(md)
            
            conversation_context = [result]
            
            while True:
                console.print("\n[dim]Commands: 'save' to continue, 'exit' to discard, or ask for changes[/dim]")
                user_input = console.input("[cyan]You:[/cyan] ").strip()
                
                if user_input.lower() == 'exit':
                    console.print("[yellow]Discarded changes[/yellow]")
                    return
                
                if user_input.lower() == 'save':
                    result = conversation_context[-1]
                    break
                
                if not user_input:
                    continue
                
                refinement_prompt = f"Previous refactoring:\n\n{conversation_context[-1]}\n\nUser request: {user_input}\n\nProvide the updated refactoring with file markers."
                
                console.print("\n[bold green]Claude:[/bold green] ", end='')
                response_parts = []
                for chunk in client.call_streaming(refinement_prompt):
                    console.print(chunk, end='')
                    response_parts.append(chunk)
                console.print()
                
                result = ''.join(response_parts)
                conversation_context.append(result)
        
        # Handle single file output mode (legacy behavior)
        if output:
            if len(files) == 1:
                with open(output, 'w') as f:
                    f.write(result)
                console.print(f"\n[green]✓[/green] Refactored code saved to: {output}")
            else:
                console.print("[yellow]Warning: --output only works with single file. Using multi-file mode.[/yellow]")
                output = None
        
        # Parse multi-file response if output not specified
        if not output:
            from claude_dev_cli.multi_file_handler import MultiFileResponse
            from pathlib import Path
            
            # Use current directory as base
            base_path = Path.cwd()
            
            multi_file = MultiFileResponse()
            multi_file.parse_response(result, base_path=base_path)
            
            if not multi_file.files:
                # No structured output detected, show markdown
                if not interactive:
                    console.print("\n[yellow]No structured file output detected[/yellow]")
                    md = Markdown(result)
                    console.print(md)
                    console.print("\n[dim]Apply the changes manually from the output above[/dim]")
                return
            
            # Validate paths
            errors = multi_file.validate_paths(base_path)
            if errors:
                console.print("[red]Path validation errors:[/red]")
                for error in errors:
                    console.print(f"  • {error}")
                sys.exit(1)
            
            # Show preview
            multi_file.preview(console, base_path)
            
            # Handle preview/dry-run modes
            if preview or dry_run:
                console.print("\n[yellow]Preview mode - no changes applied[/yellow]")
                if preview:
                    console.print("[dim]Remove --preview flag to apply changes[/dim]")
                return
            
            # Confirm or auto-accept
            if not yes:
                if not multi_file.confirm(console, base_path):
                    console.print("[yellow]Cancelled[/yellow]")
                    return
            
            # Write files
            multi_file.write_all(base_path, dry_run=False, console=console)
            
            console.print(f"\n[green]✓[/green] Refactoring applied successfully")
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@main.group()
def git() -> None:
    """Git workflow helpers."""
    pass


@git.command('commit')
@click.option('-a', '--api', help='API config to use')
@click.option('--auto-context', is_flag=True, help='Include git history and branch context')
@click.pass_context
def git_commit(ctx: click.Context, api: Optional[str], auto_context: bool) -> None:
    """Generate commit message from staged changes."""
    console = ctx.obj['console']
    
    try:
        if auto_context:
            from claude_dev_cli.context import ContextGatherer
            
            with console.status("[bold blue]Gathering context..."):
                gatherer = ContextGatherer()
                # Get git context with recent commits and branch info
                git_context = gatherer.git.gather(include_diff=True)
                context_info = git_context.format_for_prompt()
            
            console.print("[dim]✓ Context gathered (branch, commits, diff)[/dim]")
            
            # Use context-aware commit message generation
            client = ClaudeClient(api_config_name=api)
            enhanced_prompt = f"{context_info}\n\nPlease generate a concise, conventional commit message for the staged changes. Follow best practices: imperative mood, clear scope, explain what and why."
            result = client.call(enhanced_prompt)
        else:
            with console.status("[bold blue]Analyzing changes..."):
                result = git_commit_message(api_config_name=api)
        
        console.print("\n[bold green]Suggested commit message:[/bold green]")
        console.print(Panel(result, border_style="green"))
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@git.command('review')
@click.option('-a', '--api', help='API config to use')
@click.option('--staged', is_flag=True, help='Review only staged changes')
@click.option('--branch', help='Review changes in branch (e.g., main..HEAD)')
@click.option('-i', '--interactive', is_flag=True, help='Interactive follow-up questions')
@click.pass_context
def git_review(
    ctx: click.Context,
    api: Optional[str],
    staged: bool,
    branch: Optional[str],
    interactive: bool
) -> None:
    """Review git changes.
    
    Examples:
      cdc git review --staged          # Review staged changes
      cdc git review                   # Review all changes
      cdc git review --branch main..HEAD  # Review branch changes
    """
    console = ctx.obj['console']
    from claude_dev_cli.path_utils import get_git_changes
    
    try:
        # Get changed files
        if branch:
            files = get_git_changes(commit_range=branch)
            scope = f"branch {branch}"
        elif staged:
            files = get_git_changes(staged_only=True)
            scope = "staged changes"
        else:
            files = get_git_changes(staged_only=False)
            scope = "all changes"
        
        if not files:
            console.print(f"[yellow]No changes found in {scope}.[/yellow]")
            return
        
        console.print(f"\n[bold]Reviewing {len(files)} changed file(s) from {scope}:[/bold]")
        for f in files[:10]:
            console.print(f"  • {f}")
        if len(files) > 10:
            console.print(f"  ... and {len(files) - 10} more")
        console.print()
        
        # Build files content
        files_content = ""
        for file_path in files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                files_content += f"\n\n## File: {file_path}\n\n```\n{content}\n```\n"
            except Exception as e:
                console.print(f"[yellow]Warning: Could not read {file_path}: {e}[/yellow]")
        
        # Review
        with console.status(f"[bold blue]Reviewing {len(files)} file(s)..."):
            client = ClaudeClient(api_config_name=api)
            prompt = f"Changed files in {scope}:{files_content}\n\nPlease review these git changes for bugs, security issues, code quality, and potential improvements. Focus on what changed and why it might be problematic."
            result = client.call(prompt)
        
        md = Markdown(result)
        console.print(md)
        
        if interactive:
            console.print("\n[dim]Ask follow-up questions about the review, or 'exit' to quit[/dim]")
            
            while True:
                user_input = console.input("\n[cyan]You:[/cyan] ").strip()
                
                if user_input.lower() == 'exit':
                    break
                
                if not user_input:
                    continue
                
                follow_up_prompt = f"Code review:\n\n{result}\n\nChanged files:{files_content}\n\nUser question: {user_input}"
                
                console.print("\n[bold green]Claude:[/bold green] ", end='')
                for chunk in client.call_streaming(follow_up_prompt):
                    console.print(chunk, end='')
                console.print()
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@main.group()
def context() -> None:
    """Context gathering tools and information."""
    pass


@context.command('summary')
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--include-git/--no-git', default=True, help='Include git context')
@click.option('--include-deps/--no-deps', default=True, help='Include dependencies')
@click.option('--include-tests/--no-tests', default=True, help='Include test files')
@click.pass_context
def context_summary(
    ctx: click.Context,
    file_path: str,
    include_git: bool,
    include_deps: bool,
    include_tests: bool
) -> None:
    """Show what context would be gathered for a file."""
    from claude_dev_cli.context import ContextGatherer
    from rich.table import Table
    
    console = ctx.obj['console']
    
    try:
        file_path_obj = Path(file_path)
        gatherer = ContextGatherer()
        
        # Gather context
        with console.status("[bold blue]Analyzing context..."):
            context = gatherer.gather_for_review(
                file_path_obj,
                include_git=include_git,
                include_tests=include_tests
            )
        
        # Display summary
        console.print(f"\n[bold cyan]Context Summary for:[/bold cyan] {file_path}\n")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Type", style="cyan")
        table.add_column("Content", style="white")
        table.add_column("Size", justify="right", style="yellow")
        table.add_column("Lines", justify="right", style="green")
        table.add_column("Truncated", justify="center", style="red")
        
        total_chars = 0
        total_lines = 0
        
        for item in context.items:
            lines = len(item.content.split('\n'))
            chars = len(item.content)
            truncated = "✓" if item.metadata.get('truncated') else ""
            
            # Format content preview
            if item.type == 'file':
                content = item.metadata.get('path', 'unknown')
                if item.metadata.get('is_test'):
                    content += " [TEST]"
            elif item.type == 'git':
                branch = item.metadata.get('branch', 'unknown')
                modified = item.metadata.get('modified_count', 0)
                content = f"Branch: {branch}, {modified} modified files"
            elif item.type == 'dependency':
                dep_files = item.metadata.get('dependency_files', [])
                content = f"{len(dep_files)} dependency files"
            else:
                content = item.type
            
            table.add_row(
                item.type.title(),
                content[:60] + "..." if len(content) > 60 else content,
                f"{chars:,}",
                f"{lines:,}",
                truncated
            )
            
            total_chars += chars
            total_lines += lines
        
        console.print(table)
        
        # Show totals
        console.print(f"\n[bold]Total:[/bold]")
        console.print(f"  Characters: [yellow]{total_chars:,}[/yellow]")
        console.print(f"  Lines: [green]{total_lines:,}[/green]")
        console.print(f"  Estimated tokens: [cyan]~{total_chars // 4:,}[/cyan] (rough estimate)")
        
        # Show any truncation warnings
        truncated_items = [item for item in context.items if item.metadata.get('truncated')]
        if truncated_items:
            console.print(f"\n[yellow]⚠ {len(truncated_items)} item(s) truncated to fit size limits[/yellow]")
        
        console.print(f"\n[dim]Use --auto-context with commands to include this context[/dim]")
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@main.command('usage')
@click.option('--days', type=int, help='Filter by days')
@click.option('--api', help='Filter by API config')
@click.pass_context
def usage(ctx: click.Context, days: Optional[int], api: Optional[str]) -> None:
    """Show API usage statistics."""
    console = ctx.obj['console']
    
    try:
        tracker = UsageTracker()
        tracker.display_usage(console, days=days, api_config=api)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@main.group()
def toon() -> None:
    """TOON format conversion tools."""
    pass


@toon.command('encode')
@click.argument('input_file', type=click.Path(exists=True), required=False)
@click.option('-o', '--output', type=click.Path(), help='Output file')
@click.pass_context
def toon_encode(ctx: click.Context, input_file: Optional[str], output: Optional[str]) -> None:
    """Convert JSON to TOON format."""
    console = ctx.obj['console']
    
    if not toon_utils.is_toon_available():
        console.print("[red]TOON support not installed.[/red]")
        console.print("Install with: [cyan]pip install claude-dev-cli[toon][/cyan]")
        sys.exit(1)
    
    try:
        import json
        
        # Read input
        if input_file:
            with open(input_file, 'r') as f:
                data = json.load(f)
        elif not sys.stdin.isatty():
            data = json.load(sys.stdin)
        else:
            console.print("[red]Error: No input provided[/red]")
            console.print("Usage: cdc toon encode [FILE] or pipe JSON via stdin")
            sys.exit(1)
        
        # Convert to TOON
        toon_str = toon_utils.to_toon(data)
        
        # Output
        if output:
            with open(output, 'w') as f:
                f.write(toon_str)
            console.print(f"[green]✓[/green] Converted to TOON: {output}")
        else:
            console.print(toon_str)
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@toon.command('decode')
@click.argument('input_file', type=click.Path(exists=True), required=False)
@click.option('-o', '--output', type=click.Path(), help='Output file')
@click.pass_context
def toon_decode(ctx: click.Context, input_file: Optional[str], output: Optional[str]) -> None:
    """Convert TOON format to JSON."""
    console = ctx.obj['console']
    
    if not toon_utils.is_toon_available():
        console.print("[red]TOON support not installed.[/red]")
        console.print("Install with: [cyan]pip install claude-dev-cli[toon][/cyan]")
        sys.exit(1)
    
    try:
        import json
        
        # Read input
        if input_file:
            with open(input_file, 'r') as f:
                toon_str = f.read()
        elif not sys.stdin.isatty():
            toon_str = sys.stdin.read()
        else:
            console.print("[red]Error: No input provided[/red]")
            console.print("Usage: cdc toon decode [FILE] or pipe TOON via stdin")
            sys.exit(1)
        
        # Convert from TOON
        data = toon_utils.from_toon(toon_str)
        
        # Output
        json_str = json.dumps(data, indent=2)
        if output:
            with open(output, 'w') as f:
                f.write(json_str)
            console.print(f"[green]✓[/green] Converted to JSON: {output}")
        else:
            console.print(json_str)
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@toon.command('info')
@click.pass_context
def toon_info(ctx: click.Context) -> None:
    """Show TOON format installation status and token savings info."""
    console = ctx.obj['console']
    
    if toon_utils.is_toon_available():
        console.print("[green]✓[/green] TOON format support is installed")
        console.print("\n[bold]About TOON:[/bold]")
        console.print("• Token-Oriented Object Notation")
        console.print("• 30-60% fewer tokens than JSON")
        console.print("• Optimized for LLM prompts")
        console.print("• Human-readable and lossless")
        console.print("\n[bold]Usage:[/bold]")
        console.print("  cdc toon encode data.json -o data.toon")
        console.print("  cdc toon decode data.toon -o data.json")
        console.print("  cat data.json | cdc toon encode")
    else:
        console.print("[yellow]TOON format support not installed[/yellow]")
        console.print("\nInstall with: [cyan]pip install claude-dev-cli[toon][/cyan]")
        console.print("\n[bold]Benefits:[/bold]")
        console.print("• Reduce API costs by 30-60%")
        console.print("• Faster LLM response times")
        console.print("• Same data, fewer tokens")


@main.group()
def template() -> None:
    """Manage custom prompt templates."""
    pass


@template.command('list')
@click.option('-c', '--category', help='Filter by category')
@click.option('--builtin', is_flag=True, help='Show only built-in templates')
@click.option('--user', is_flag=True, help='Show only user templates')
@click.pass_context
def template_list(
    ctx: click.Context,
    category: Optional[str],
    builtin: bool,
    user: bool
) -> None:
    """List available templates."""
    console = ctx.obj['console']
    config = Config()
    manager = TemplateManager(config.config_dir)
    
    templates = manager.list_templates(
        category=category,
        builtin_only=builtin,
        user_only=user
    )
    
    if not templates:
        console.print("[yellow]No templates found.[/yellow]")
        return
    
    from rich.table import Table
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Name", style="cyan")
    table.add_column("Category", style="green")
    table.add_column("Variables", style="yellow")
    table.add_column("Type", style="blue")
    table.add_column("Description")
    
    for tmpl in templates:
        vars_display = ", ".join(tmpl.variables) if tmpl.variables else "-"
        type_display = "🔒 Built-in" if tmpl.builtin else "📝 User"
        table.add_row(
            tmpl.name,
            tmpl.category,
            vars_display,
            type_display,
            tmpl.description
        )
    
    console.print(table)
    
    # Show categories
    categories = manager.get_categories()
    console.print(f"\n[dim]Categories: {', '.join(categories)}[/dim]")


@template.command('show')
@click.argument('name')
@click.pass_context
def template_show(ctx: click.Context, name: str) -> None:
    """Show template details."""
    console = ctx.obj['console']
    config = Config()
    manager = TemplateManager(config.config_dir)
    
    tmpl = manager.get_template(name)
    if not tmpl:
        console.print(f"[red]Template not found: {name}[/red]")
        sys.exit(1)
    
    console.print(Panel(
        f"[bold]{tmpl.name}[/bold]\n\n"
        f"[dim]{tmpl.description}[/dim]\n\n"
        f"Category: [green]{tmpl.category}[/green]\n"
        f"Type: {'🔒 Built-in' if tmpl.builtin else '📝 User'}\n"
        f"Variables: [yellow]{', '.join(tmpl.variables) if tmpl.variables else 'None'}[/yellow]",
        title="Template Info",
        border_style="blue"
    ))
    
    console.print("\n[bold]Content:[/bold]\n")
    console.print(Panel(tmpl.content, border_style="dim"))


@template.command('add')
@click.argument('name')
@click.option('-c', '--content', help='Template content (or use stdin)')
@click.option('-d', '--description', help='Template description')
@click.option('--category', default='general', help='Template category')
@click.pass_context
def template_add(
    ctx: click.Context,
    name: str,
    content: Optional[str],
    description: Optional[str],
    category: str
) -> None:
    """Add a new template."""
    console = ctx.obj['console']
    config = Config()
    manager = TemplateManager(config.config_dir)
    
    # Get content from stdin if not provided
    if not content:
        if sys.stdin.isatty():
            console.print("[yellow]Enter template content (Ctrl+D to finish):[/yellow]")
        content = sys.stdin.read().strip()
    
    if not content:
        console.print("[red]Error: No content provided[/red]")
        sys.exit(1)
    
    try:
        tmpl = Template(
            name=name,
            content=content,
            description=description,
            category=category
        )
        manager.add_template(tmpl)
        
        console.print(f"[green]✓[/green] Template added: {name}")
        if tmpl.variables:
            console.print(f"[dim]Variables: {', '.join(tmpl.variables)}[/dim]")
    
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@template.command('delete')
@click.argument('name')
@click.pass_context
def template_delete(ctx: click.Context, name: str) -> None:
    """Delete a user template."""
    console = ctx.obj['console']
    config = Config()
    manager = TemplateManager(config.config_dir)
    
    try:
        if manager.delete_template(name):
            console.print(f"[green]✓[/green] Template deleted: {name}")
        else:
            console.print(f"[red]Template not found: {name}[/red]")
            sys.exit(1)
    
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@template.command('use')
@click.argument('name')
@click.option('-a', '--api', help='API config to use')
@click.option('-m', '--model', help='Claude model to use')
@click.pass_context
def template_use(ctx: click.Context, name: str, api: Optional[str], model: Optional[str]) -> None:
    """Use a template with interactive variable input."""
    console = ctx.obj['console']
    config = Config()
    manager = TemplateManager(config.config_dir)
    
    tmpl = manager.get_template(name)
    if not tmpl:
        console.print(f"[red]Template not found: {name}[/red]")
        sys.exit(1)
    
    # Get variable values
    variables = {}
    if tmpl.variables:
        console.print(f"\n[bold]Template: {name}[/bold]")
        console.print(f"[dim]{tmpl.description}[/dim]\n")
        
        for var in tmpl.variables:
            value = console.input(f"[cyan]{var}:[/cyan] ").strip()
            variables[var] = value
    
    # Check for missing variables
    missing = tmpl.get_missing_variables(**variables)
    if missing:
        console.print(f"[red]Missing required variables: {', '.join(missing)}[/red]")
        sys.exit(1)
    
    # Render template
    prompt = tmpl.render(**variables)
    
    # Call Claude
    try:
        client = ClaudeClient(api_config_name=api)
        
        console.print("\n[bold green]Claude:[/bold green] ", end='')
        for chunk in client.call_streaming(prompt, model=model):
            console.print(chunk, end='')
        console.print()
    
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        sys.exit(1)


@main.group()
def ollama() -> None:
    """Manage Ollama local models."""
    pass


@ollama.command('list')
@click.option('-a', '--api', help='Ollama config to use (default: local ollama)')
@click.pass_context
def ollama_list(ctx: click.Context, api: Optional[str]) -> None:
    """List available Ollama models."""
    console = ctx.obj['console']
    
    try:
        from claude_dev_cli.providers.ollama import OllamaProvider
        from claude_dev_cli.providers.base import ProviderConnectionError
        from claude_dev_cli.config import Config, ProviderConfig
        from rich.table import Table
        
        # Get config or use default local
        config = Config()
        provider_config = None
        if api:
            api_config = config.get_provider_config(api)
            if not api_config or api_config.provider != 'ollama':
                console.print(f"[red]Error: '{api}' is not an ollama config[/red]")
                sys.exit(1)
            provider_config = api_config
        else:
            # Use default local ollama
            provider_config = ProviderConfig(
                name="local",
                provider="ollama",
                base_url="http://localhost:11434"
            )
        
        provider = OllamaProvider(provider_config)
        
        with console.status("[bold blue]Fetching models from Ollama..."):
            models = provider.list_models()
        
        if not models:
            console.print("[yellow]No models found.[/yellow]")
            console.print("\nPull a model with: ollama pull mistral")
            console.print("Or use: cdc ollama pull mistral")
            return
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Model", style="cyan")
        table.add_column("Display Name")
        table.add_column("Context", justify="right")
        table.add_column("Cost", justify="right")
        table.add_column("Capabilities")
        
        for model in models:
            capabilities = ", ".join(model.capabilities)
            table.add_row(
                model.model_id,
                model.display_name,
                f"{model.context_window:,}",
                "[green]FREE[/green]",
                capabilities
            )
        
        console.print(table)
        console.print(f"\n[dim]Found {len(models)} model(s)[/dim]")
        
    except ProviderConnectionError:
        console.print("[red]Error: Cannot connect to Ollama[/red]")
        console.print("\nMake sure Ollama is running:")
        console.print("  ollama serve")
        console.print("\nOr install Ollama from: https://ollama.ai")
        sys.exit(1)
    except ImportError:
        console.print("[red]Error: Ollama provider not installed[/red]")
        console.print("Install with: pip install 'claude-dev-cli[ollama]'")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@ollama.command('pull')
@click.argument('model')
@click.pass_context
def ollama_pull(ctx: click.Context, model: str) -> None:
    """Pull an Ollama model.
    
    Examples:
      cdc ollama pull mistral
      cdc ollama pull codellama
      cdc ollama pull mixtral
    """
    console = ctx.obj['console']
    
    console.print(f"[yellow]Pulling {model} via Ollama CLI...[/yellow]")
    console.print("[dim]This will use the 'ollama pull' command directly[/dim]\n")
    
    import subprocess
    try:
        # Use ollama CLI directly - it shows progress
        result = subprocess.run(
            ['ollama', 'pull', model],
            check=True
        )
        
        if result.returncode == 0:
            console.print(f"\n[green]✓[/green] Successfully pulled {model}")
            console.print(f"\nUse it with: cdc ask -m {model} 'your question'")
    except FileNotFoundError:
        console.print("[red]Error: ollama command not found[/red]")
        console.print("\nInstall Ollama from: https://ollama.ai")
        sys.exit(1)
    except subprocess.CalledProcessError:
        console.print(f"[red]Error: Failed to pull {model}[/red]")
        sys.exit(1)


@ollama.command('show')
@click.argument('model')
@click.pass_context
def ollama_show(ctx: click.Context, model: str) -> None:
    """Show details about an Ollama model.
    
    Examples:
      cdc ollama show mistral
      cdc ollama show codellama
    """
    console = ctx.obj['console']
    
    import subprocess
    try:
        # Use ollama CLI for detailed info
        result = subprocess.run(
            ['ollama', 'show', model],
            capture_output=True,
            text=True,
            check=True
        )
        
        console.print(result.stdout)
    except FileNotFoundError:
        console.print("[red]Error: ollama command not found[/red]")
        console.print("\nInstall Ollama from: https://ollama.ai")
        sys.exit(1)
    except subprocess.CalledProcessError:
        console.print(f"[red]Error: Model '{model}' not found[/red]")
        console.print(f"\nPull it first: cdc ollama pull {model}")
        sys.exit(1)


@main.group()
def warp() -> None:
    """Warp terminal integration."""
    pass


@warp.command('export-workflows')
@click.option('-o', '--output', type=click.Path(), help='Output directory')
@click.pass_context
def warp_export_workflows(ctx: click.Context, output: Optional[str]) -> None:
    """Export Warp workflows for claude-dev-cli commands."""
    console = ctx.obj['console']
    
    try:
        from claude_dev_cli.warp_integration import export_builtin_workflows
        
        config = Config()
        output_dir = Path(output) if output else config.config_dir / "warp" / "workflows"
        
        created_files = export_builtin_workflows(output_dir)
        
        console.print(f"[green]✓[/green] Exported {len(created_files)} Warp workflows to:")
        console.print(f"  {output_dir}")
        console.print("\n[bold]Workflows:[/bold]")
        for file in created_files:
            console.print(f"  • {file.name}")
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@warp.command('export-launch-configs')
@click.option('-o', '--output', type=click.Path(), help='Output file path')
@click.pass_context
def warp_export_launch_configs(ctx: click.Context, output: Optional[str]) -> None:
    """Export Warp launch configurations."""
    console = ctx.obj['console']
    
    try:
        from claude_dev_cli.warp_integration import export_launch_configs
        
        config = Config()
        output_path = Path(output) if output else config.config_dir / "warp" / "launch_configs.json"
        
        export_launch_configs(output_path)
        
        console.print(f"[green]✓[/green] Exported Warp launch configurations to:")
        console.print(f"  {output_path}")
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@main.group()
def workflow() -> None:
    """Manage and run workflows."""
    pass


@workflow.command('run')
@click.argument('workflow_file', type=click.Path(exists=True))
@click.option('--var', '-v', multiple=True, help='Set variables (key=value)')
@click.pass_context
def workflow_run(
    ctx: click.Context,
    workflow_file: str,
    var: tuple
) -> None:
    """Run a workflow from YAML file."""
    console = ctx.obj['console']
    
    # Parse variables
    variables = {}
    for v in var:
        if '=' in v:
            key, value = v.split('=', 1)
            variables[key] = value
    
    try:
        from claude_dev_cli.workflows import WorkflowEngine
        
        engine = WorkflowEngine(console=console)
        workflow_path = Path(workflow_file)
        
        context = engine.execute(workflow_path, initial_vars=variables)
        
        # Show summary
        if context.step_results:
            console.print("\n[bold]Results Summary:[/bold]")
            for step_name, result in context.step_results.items():
                status = "[green]✓[/green]" if result.success else "[red]✗[/red]"
                console.print(f"{status} {step_name}")
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@workflow.command('list')
@click.pass_context
def workflow_list(ctx: click.Context) -> None:
    """List available workflows."""
    console = ctx.obj['console']
    config = Config()
    workflow_dir = config.config_dir / "workflows"
    
    from claude_dev_cli.workflows import list_workflows
    workflows = list_workflows(workflow_dir)
    
    if not workflows:
        console.print("[yellow]No workflows found.[/yellow]")
        console.print(f"\nCreate workflows in: {workflow_dir}")
        return
    
    from rich.table import Table
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Name", style="cyan")
    table.add_column("Steps", style="yellow")
    table.add_column("Description")
    
    for wf in workflows:
        table.add_row(
            wf['name'],
            str(wf['steps']),
            wf['description']
        )
    
    console.print(table)
    console.print(f"\n[dim]Workflow directory: {workflow_dir}[/dim]")


@workflow.command('show')
@click.argument('workflow_file', type=click.Path(exists=True))
@click.pass_context
def workflow_show(ctx: click.Context, workflow_file: str) -> None:
    """Show workflow details."""
    console = ctx.obj['console']
    
    try:
        from claude_dev_cli.workflows import WorkflowEngine
        
        engine = WorkflowEngine(console=console)
        workflow = engine.load_workflow(Path(workflow_file))
        
        console.print(Panel(
            f"[bold]{workflow.get('name', 'Unnamed')}[/bold]\n\n"
            f"[dim]{workflow.get('description', 'No description')}[/dim]\n\n"
            f"Steps: [yellow]{len(workflow.get('steps', []))}[/yellow]",
            title="Workflow Info",
            border_style="blue"
        ))
        
        # Show steps
        steps = workflow.get('steps', [])
        if steps:
            console.print("\n[bold]Steps:[/bold]\n")
            for i, step in enumerate(steps, 1):
                step_name = step.get('name', f'step-{i}')
                step_type = 'command' if 'command' in step else 'shell' if 'shell' in step else 'set'
                console.print(f"  {i}. [cyan]{step_name}[/cyan] ({step_type})")
                
                if step.get('approval_required'):
                    console.print(f"     [yellow]⚠ Requires approval[/yellow]")
                if 'if' in step:
                    console.print(f"     [dim]Condition: {step['if']}[/dim]")
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@workflow.command('validate')
@click.argument('workflow_file', type=click.Path(exists=True))
@click.pass_context
def workflow_validate(ctx: click.Context, workflow_file: str) -> None:
    """Validate workflow syntax."""
    console = ctx.obj['console']
    
    try:
        from claude_dev_cli.workflows import WorkflowEngine
        
        engine = WorkflowEngine(console=console)
        workflow = engine.load_workflow(Path(workflow_file))
        
        # Basic validation
        errors = []
        
        if 'name' not in workflow:
            errors.append("Missing 'name' field")
        
        if 'steps' not in workflow:
            errors.append("Missing 'steps' field")
        elif not isinstance(workflow['steps'], list):
            errors.append("'steps' must be a list")
        else:
            for i, step in enumerate(workflow['steps'], 1):
                if not any(k in step for k in ['command', 'shell', 'set']):
                    errors.append(f"Step {i}: Must have 'command', 'shell', or 'set'")
        
        if errors:
            console.print("[red]✗ Validation failed:[/red]\n")
            for error in errors:
                console.print(f"  • {error}")
            sys.exit(1)
        else:
            console.print(f"[green]✓[/green] Workflow is valid: {workflow.get('name')}")
            console.print(f"  Steps: {len(workflow.get('steps', []))}")
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == '__main__':
    main(obj={})
