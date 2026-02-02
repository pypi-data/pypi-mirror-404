"""AI chat commands for VirtualDojo CLI."""

import readline  # noqa: F401 - imported for side effect (enables input history)

import typer

from ..client import SyncVirtualDojoClient
from ..utils.output import console, print_error

app = typer.Typer(help="AI chat and conversations", no_args_is_help=True)


def _send_message(
    client: SyncVirtualDojoClient,
    message: str,
    conversation_id: str | None = None,
    show_conversation_id: bool = True,
    show_spinner: bool = False,
) -> str | None:
    """Send a message and display the response.

    Returns the conversation_id for maintaining context.
    """
    data = {"message": message}
    if conversation_id:
        data["conversation_id"] = conversation_id

    if show_spinner:
        with console.status("[dim]Thinking...[/dim]", spinner="dots"):
            result = client.post("/api/v1/ai/chat", data)
    else:
        result = client.post("/api/v1/ai/chat", data)

    response = result.get("response", "No response")
    conv_id = result.get("conversation_id")
    metadata = result.get("metadata", {})

    # Display the AI response
    console.print(f"\n[bold cyan]VirtualDojo:[/bold cyan] {response}")

    # Show citations if available
    citations = metadata.get("citations", [])
    if citations:
        console.print("\n[dim]Sources:[/dim]")
        for cite in citations:
            console.print(
                f"  - {cite.get('file_title', 'Unknown')} ({cite.get('relevance', 0):.0%})"
            )

    # Show conversation ID only in single-message mode
    if show_conversation_id and conv_id:
        console.print(f"\n[dim]Conversation ID: {conv_id}[/dim]")

    return conv_id


def _interactive_chat(client: SyncVirtualDojoClient) -> None:
    """Run interactive chat session."""
    from ..exceptions import AuthenticationError, TokenExpiredError

    console.print()
    console.print(
        "[bold cyan]VirtualDojo[/bold cyan] - Government Contracting Platform"
    )
    console.print("[dim]Press Ctrl+C to exit[/dim]")
    console.print()

    conversation_id: str | None = None
    interrupt_count = 0

    while True:
        try:
            # Get user input
            try:
                user_input = input("\033[1;32mYou:\033[0m ")
            except EOFError:
                # Handle Ctrl+D
                console.print("\n[dim]Goodbye![/dim]")
                break

            # Reset interrupt count after successful input
            interrupt_count = 0

            # Skip empty input
            if not user_input.strip():
                continue

            # Send message and get response
            conversation_id = _send_message(
                client,
                user_input.strip(),
                conversation_id=conversation_id,
                show_conversation_id=False,
                show_spinner=True,
            )
            console.print()

        except KeyboardInterrupt:
            interrupt_count += 1
            if interrupt_count >= 2:
                console.print("\n[dim]Goodbye![/dim]")
                break
            else:
                console.print("\n[dim]Press Ctrl+C again to exit[/dim]")

        except (TokenExpiredError, AuthenticationError) as e:
            # Auth errors are fatal - exit the chat
            print_error(e.message, e.hint)
            break

        except Exception as e:
            if hasattr(e, "message"):
                print_error(e.message, getattr(e, "hint", None))
            else:
                print_error(str(e))
            # Don't exit on other errors, let user try again
            console.print()


@app.command("chat")
def chat(
    message: str | None = typer.Argument(
        None, help="Message to send to AI (omit for interactive mode)"
    ),
    conversation_id: str | None = typer.Option(
        None,
        "--conversation",
        "-c",
        help="Continue an existing conversation by ID",
    ),
    profile: str | None = typer.Option(None, "--profile", "-p"),
) -> None:
    """Send a message to the AI assistant.

    Run without arguments to enter interactive chat mode.

    Examples:
        vdojo ai chat                                    # Interactive mode
        vdojo ai chat "How many accounts do I have?"     # Single message
        vdojo ai chat "What are my top deals?" -c abc123 # Continue conversation
    """
    try:
        client = SyncVirtualDojoClient(profile)

        if message is None:
            # Interactive mode
            _interactive_chat(client)
        else:
            # Single message mode (original behavior)
            _send_message(
                client,
                message,
                conversation_id=conversation_id,
                show_conversation_id=True,
            )

    except Exception as e:
        if hasattr(e, "message"):
            print_error(e.message, getattr(e, "hint", None))
        else:
            print_error(str(e))
        raise typer.Exit(1) from None


@app.command("conversations")
def list_conversations(
    limit: int = typer.Option(
        20, "--limit", "-l", help="Maximum conversations to return"
    ),
    profile: str | None = typer.Option(None, "--profile", "-p"),
) -> None:
    """List your AI conversations.

    Examples:
        vdojo ai conversations
        vdojo ai conversations --limit 10
    """
    try:
        client = SyncVirtualDojoClient(profile)
        result = client.get("/api/v1/ai/conversations", params={"limit": limit})

        conversations = result if isinstance(result, list) else result.get("data", [])

        if not conversations:
            console.print("[dim]No conversations found[/dim]")
            return

        from rich.table import Table

        table = Table(
            show_header=True, header_style="bold cyan", title="AI Conversations"
        )
        table.add_column("ID", style="dim")
        table.add_column("Title")
        table.add_column("Messages")
        table.add_column("Last Activity")

        for conv in conversations:
            table.add_row(
                str(conv.get("id", "-"))[:8] + "...",
                conv.get("title", "-")[:40],
                str(conv.get("message_count", 0)),
                str(conv.get("last_activity_at", "-"))[:19],
            )

        console.print(table)
        console.print(f"\n[dim]{len(conversations)} conversations[/dim]")

    except Exception as e:
        if hasattr(e, "message"):
            print_error(e.message, getattr(e, "hint", None))
        else:
            print_error(str(e))
        raise typer.Exit(1) from None


@app.command("history")
def conversation_history(
    conversation_id: str = typer.Argument(..., help="Conversation ID"),
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum messages to return"),
    profile: str | None = typer.Option(None, "--profile", "-p"),
) -> None:
    """View messages from a conversation.

    Examples:
        vdojo ai history abc-123-def
        vdojo ai history abc-123-def --limit 10
    """
    try:
        client = SyncVirtualDojoClient(profile)
        result = client.get(
            f"/api/v1/ai/conversations/{conversation_id}/messages",
            params={"limit": limit},
        )

        messages = result if isinstance(result, list) else result.get("data", [])

        if not messages:
            console.print("[dim]No messages found[/dim]")
            return

        console.print(f"\n[bold]Conversation: {conversation_id}[/bold]\n")

        for msg in messages:
            sender = msg.get("sender_type", "unknown")
            text = msg.get("message_text", "")
            sent_at = str(msg.get("sent_at", ""))[:19]

            if sender == "user":
                console.print(f"[bold green]You[/bold green] [dim]({sent_at})[/dim]")
            else:
                console.print(f"[bold cyan]AI[/bold cyan] [dim]({sent_at})[/dim]")

            console.print(f"  {text}\n")

    except Exception as e:
        if hasattr(e, "message"):
            print_error(e.message, getattr(e, "hint", None))
        else:
            print_error(str(e))
        raise typer.Exit(1) from None
