"""Project initialization commands."""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Confirm
from pathlib import Path
import json

from ..client import AIandMeClient
from ..exceptions import NotAuthenticatedError, APIError

console = Console()


@click.command("init")
@click.option("--name", "-n", required=True, help="Project name")
@click.option("--prompt", "-p", type=click.Path(exists=True), help="Path to system prompt file")
@click.option("--endpoint", "-e", help="Bot endpoint URL to probe (domain must match your email domain)")
@click.option("--repo", "-r", type=click.Path(exists=True), help="Path to repository to scan")
@click.option("--openapi", "-o", type=click.Path(exists=True), help="Path to OpenAPI spec file")
@click.option("--description", "-d", help="Project description")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompts")
def init_project(name: str, prompt: str, endpoint: str, repo: str, openapi: str, description: str, yes: bool):
    """Initialize a new project with automatic scope extraction.

    Extract scope from various sources:

    \b
    --prompt    Extract from system prompt file
    --endpoint  Probe live bot endpoint
    --repo      Scan repository for prompts and tools
    --openapi   Parse OpenAPI/Swagger specification

    Examples:

    \b
    aiandme init --name "My Bot" --prompt ./system_prompt.txt
    aiandme init --name "My Bot" --endpoint https://api.example.com/chat
    aiandme init --name "My Bot" --repo ./my-agent --prompt ./prompts/system.txt
    """
    client = AIandMeClient()

    if not client.is_authenticated():
        console.print("[red]Not authenticated.[/red] Run 'aiandme login' first.")
        raise SystemExit(1)

    if not client.organisation_id:
        console.print("[yellow]No organisation selected.[/yellow]")
        console.print("Use 'aiandme switch <id>' to select an organisation first.")
        raise SystemExit(1)

    # Count how many extraction sources provided
    sources = [prompt, endpoint, repo, openapi]
    source_count = sum(1 for s in sources if s)

    if source_count == 0:
        console.print("[yellow]No extraction source provided.[/yellow]")
        console.print("Use --prompt, --endpoint, --repo, or --openapi to specify a source.")
        raise SystemExit(1)

    console.print(f"\n[bold]Initializing project:[/bold] {name}\n")

    # Extract scope from sources
    extracted_scope = None

    try:
        if prompt:
            extracted_scope = _extract_from_prompt(client, prompt)

        if endpoint:
            endpoint_scope = _extract_from_endpoint(client, endpoint)
            extracted_scope = _merge_scopes(extracted_scope, endpoint_scope)

        if repo:
            repo_scope = _extract_from_repo(client, repo)
            extracted_scope = _merge_scopes(extracted_scope, repo_scope)

        if openapi:
            openapi_scope = _extract_from_openapi(client, openapi)
            extracted_scope = _merge_scopes(extracted_scope, openapi_scope)

        if not extracted_scope:
            console.print("[red]Failed to extract scope from provided sources.[/red]")
            raise SystemExit(1)

        # Display extracted scope
        _display_scope(extracted_scope)

        # Confirm creation
        if not yes:
            if not Confirm.ask("\nCreate project with this scope?"):
                console.print("[yellow]Cancelled.[/yellow]")
                return

        # Create project
        with console.status("Creating project..."):
            project_data = {
                "name": name,
                "description": description or f"Project created via CLI from {_get_source_description(prompt, endpoint, repo, openapi)}",
                "scope": extracted_scope,
            }

            response = client.post("projects", data=project_data)

        project_id = response.get("id")
        console.print(Panel(
            f"[green]Project created successfully![/green]\n\n"
            f"ID: {project_id}\n"
            f"Name: {name}\n\n"
            f"[dim]Run 'aiandme projects use {project_id}' to select it.[/dim]",
            title="Project Created"
        ))

        # Optionally set as current project
        if yes or Confirm.ask("Set as current project?"):
            client.set_project(project_id)
            console.print(f"[green]Switched to project:[/green] {name}")

    except NotAuthenticatedError:
        console.print("[red]Not authenticated.[/red] Run 'aiandme login' first.")
        raise SystemExit(1)
    except APIError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)


def _extract_from_prompt(client: AIandMeClient, prompt_path: str) -> dict:
    """Extract scope from system prompt file."""
    console.print(f"[cyan]Extracting from prompt:[/cyan] {prompt_path}")

    path = Path(prompt_path)
    prompt_text = path.read_text()

    with console.status("Analyzing prompt..."):
        # Use the analyse endpoint
        response = client.post(
            "projects/analyse",
            data={
                "overall_business_scope": prompt_text,
                "intents": {
                    "permitted": "Extract from the prompt above",
                    "restricted": "Extract from the prompt above"
                }
            }
        )

    console.print("[green]✓[/green] Prompt analyzed")
    return response


def _extract_from_endpoint(client: AIandMeClient, endpoint_url: str) -> dict:
    """Extract scope by probing live bot endpoint via discovery API."""
    console.print(f"[cyan]Probing endpoint:[/cyan] {endpoint_url}")

    with console.status("Running discovery scan (this may take a minute)..."):
        try:
            # Call the discovery API
            response = client.post(
                "scan",
                data={"url": endpoint_url},
                include_project=False,
            )
        except APIError as e:
            console.print(f"[red]Discovery failed:[/red] {e}")
            return None

    # Response structure: {project, discovery, posture, scope}
    discovery = response.get("discovery", {})
    posture = response.get("posture", {})
    scope = response.get("scope")

    # Check discovery status
    scan_status = discovery.get("status")

    if scan_status == "no_widget":
        console.print("[yellow]No chat widget detected on the page.[/yellow]")
        console.print("[dim]Try providing the direct chat endpoint URL or use --prompt instead.[/dim]")
        return None

    if scan_status == "blocked":
        console.print(f"[yellow]Bot detection blocked access:[/yellow] {discovery.get('block_reason', 'unknown')}")
        console.print("[dim]The site may have anti-bot protection. Try using --prompt instead.[/dim]")
        return None

    if scan_status == "failed":
        console.print(f"[red]Discovery failed:[/red] {discovery.get('error', 'unknown error')}")
        return None

    # Display discovery results
    console.print("[green]✓[/green] Discovery complete\n")

    # Show capabilities from posture
    capabilities = posture.get("capabilities", {})
    if capabilities:
        cap_items = []
        if capabilities.get("has_memory"):
            cap_items.append("memory/account access")
        if capabilities.get("has_tools"):
            cap_items.append("can perform actions")
        if capabilities.get("has_rag"):
            cap_items.append("knowledge base access")
        if capabilities.get("has_external_apis"):
            cap_items.append("external API calls")
        if cap_items:
            console.print(f"[bold]Capabilities detected:[/bold] {', '.join(cap_items)}")

    # Show risk level from posture
    if posture.get("risk_level"):
        console.print(f"[bold]Risk level:[/bold] {posture.get('risk_level')}")

    # Show what the bot can/cannot do from discovery
    disc_capabilities = discovery.get("capabilities", {})
    can_do = disc_capabilities.get("can_do", [])
    cannot_do = disc_capabilities.get("cannot_do", [])
    if can_do:
        console.print(f"\n[green]Can do:[/green] {', '.join(can_do[:5])}")
    if cannot_do:
        console.print(f"[red]Cannot do:[/red] {', '.join(cannot_do[:5])}")

    # Return scope from response
    if scope:
        console.print("\n[green]✓[/green] Scope extracted from discovery")
        return scope

    # Fallback: build scope from capabilities analysis
    if can_do or cannot_do:
        console.print("\n[dim]Building scope from capability analysis...[/dim]")
        return {
            "overall_business_scope": posture.get("industry", "AI chatbot"),
            "intents": {
                "permitted": can_do,
                "restricted": cannot_do,
            }
        }

    console.print("[yellow]Could not extract scope from discovery.[/yellow]")
    return None


def _extract_from_repo(client: AIandMeClient, repo_path: str) -> dict:
    """Extract scope by scanning repository."""
    console.print(f"[cyan]Scanning repository:[/cyan] {repo_path}")

    from ..extractors.repo import RepoScanner

    scanner = RepoScanner(repo_path)

    with console.status("Scanning repository..."):
        scan_result = scanner.scan()

    if not scan_result:
        console.print("[yellow]No relevant files found in repository.[/yellow]")
        return None

    # Display found files
    console.print(f"\n[bold]Found {len(scan_result.get('files', []))} relevant files:[/bold]")
    for f in scan_result.get("files", [])[:5]:
        console.print(f"  • {f}")
    if len(scan_result.get("files", [])) > 5:
        console.print(f"  [dim]... and {len(scan_result.get('files', [])) - 5} more[/dim]")

    # Check if it's an agentic setup (has tools)
    if scan_result.get("tools"):
        console.print(f"\n[bold]Found {len(scan_result.get('tools', []))} tool definitions[/bold]")

        with console.status("Analyzing agentic configuration..."):
            response = client.post(
                "projects/analyse/agentic",
                data={
                    "system_prompt": scan_result.get("system_prompt", ""),
                    "tools": scan_result.get("tools", []),
                }
            )
    else:
        # Standard analysis
        combined_text = scan_result.get("system_prompt", "")
        if scan_result.get("readme"):
            combined_text += f"\n\nREADME:\n{scan_result.get('readme')}"

        with console.status("Analyzing repository content..."):
            response = client.post(
                "projects/analyse",
                data={
                    "overall_business_scope": combined_text,
                    "intents": {
                        "permitted": "Extract from the content above",
                        "restricted": "Extract from the content above"
                    }
                }
            )

    console.print("[green]✓[/green] Repository analyzed")
    return response


def _extract_from_openapi(client: AIandMeClient, openapi_path: str) -> dict:
    """Extract scope from OpenAPI specification."""
    console.print(f"[cyan]Parsing OpenAPI spec:[/cyan] {openapi_path}")

    from ..extractors.openapi import OpenAPIParser

    parser = OpenAPIParser(openapi_path)

    with console.status("Parsing specification..."):
        spec_result = parser.parse()

    if not spec_result:
        console.print("[yellow]Could not parse OpenAPI specification.[/yellow]")
        return None

    # Display found operations
    operations = spec_result.get("operations", [])
    console.print(f"\n[bold]Found {len(operations)} API operations:[/bold]")
    for op in operations[:5]:
        console.print(f"  • {op.get('method', 'GET')} {op.get('path', '')} - {op.get('summary', '')[:40]}")
    if len(operations) > 5:
        console.print(f"  [dim]... and {len(operations) - 5} more[/dim]")

    # Convert operations to scope
    permitted_intents = [
        f"{op.get('summary', op.get('operationId', 'Unknown operation'))}"
        for op in operations
    ]

    with console.status("Analyzing API capabilities..."):
        response = client.post(
            "projects/analyse",
            data={
                "overall_business_scope": spec_result.get("description", "API-based bot"),
                "intents": {
                    "permitted": "\n".join(permitted_intents),
                    "restricted": "Operations not defined in the API spec"
                }
            }
        )

    console.print("[green]✓[/green] OpenAPI spec analyzed")
    return response


def _merge_scopes(scope1: dict, scope2: dict) -> dict:
    """Merge two scope dictionaries."""
    if not scope1:
        return scope2
    if not scope2:
        return scope1

    # Merge intents
    merged = {
        "overall_business_scope": f"{scope1.get('overall_business_scope', '')}\n{scope2.get('overall_business_scope', '')}".strip(),
        "intents": {
            "permitted": scope1.get("intents", {}).get("permitted", []) + scope2.get("intents", {}).get("permitted", []),
            "restricted": scope1.get("intents", {}).get("restricted", []) + scope2.get("intents", {}).get("restricted", []),
        }
    }

    # Deduplicate
    if isinstance(merged["intents"]["permitted"], list):
        merged["intents"]["permitted"] = list(set(merged["intents"]["permitted"]))
    if isinstance(merged["intents"]["restricted"], list):
        merged["intents"]["restricted"] = list(set(merged["intents"]["restricted"]))

    return merged


def _display_scope(scope: dict):
    """Display extracted scope in a nice format."""
    console.print("\n[bold]Extracted Scope:[/bold]\n")

    # Business scope
    business_scope = scope.get("overall_business_scope", "")
    if business_scope:
        console.print(Panel(
            business_scope[:500] + ("..." if len(business_scope) > 500 else ""),
            title="Business Scope",
            border_style="blue"
        ))

    # Intents table
    intents = scope.get("intents", {})
    permitted = intents.get("permitted", [])
    restricted = intents.get("restricted", [])

    if permitted or restricted:
        table = Table(title="Intents")
        table.add_column("Type", style="bold")
        table.add_column("Intent")

        if isinstance(permitted, list):
            for intent in permitted[:10]:
                table.add_row("[green]Permitted[/green]", str(intent)[:60])
            if len(permitted) > 10:
                table.add_row("[green]Permitted[/green]", f"[dim]... and {len(permitted) - 10} more[/dim]")

        if isinstance(restricted, list):
            for intent in restricted[:10]:
                table.add_row("[red]Restricted[/red]", str(intent)[:60])
            if len(restricted) > 10:
                table.add_row("[red]Restricted[/red]", f"[dim]... and {len(restricted) - 10} more[/dim]")

        console.print(table)


def _get_source_description(prompt: str, endpoint: str, repo: str, openapi: str) -> str:
    """Get a description of the sources used."""
    sources = []
    if prompt:
        sources.append(f"prompt ({Path(prompt).name})")
    if endpoint:
        sources.append(f"endpoint ({endpoint})")
    if repo:
        sources.append(f"repo ({Path(repo).name})")
    if openapi:
        sources.append(f"openapi ({Path(openapi).name})")
    return ", ".join(sources)
