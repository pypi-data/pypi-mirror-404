#!/usr/bin/env python3
"""
Bottle CLI - Get human feedback on your projects
pip install bottle-cli
"""

import os
import json
import random
import string
from pathlib import Path
from datetime import datetime

import typer
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from supabase import create_client, Client
import google.generativeai as genai

# =============================================================================
# CONFIGURATION - Hardcoded (safe with RLS)
# =============================================================================
# Replace with your actual Supabase credentials before publishing
SUPABASE_URL = "https://yaeyexvvbabgwyroeszs.supabase.co" 
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlhZXlleHZ2YmFiZ3d5cm9lc3pzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk5MTU5NzQsImV4cCI6MjA4NTQ5MTk3NH0.t07dNozpf86Xex4eprueulMnEKEoF3NPBuMZNaB7p1k"  # TODO: Replace with anon key (NOT service_role!)

# =============================================================================
# CLI SETUP
# =============================================================================
app = typer.Typer(help="🍾 Bottle - Get human feedback on your projects")
console = Console()

CONFIG_DIR = Path.home() / ".bottle"
CONFIG_FILE = CONFIG_DIR / "config.json"


# =============================================================================
# CONFIG HELPERS
# =============================================================================
def get_config() -> dict:
    """Load config from ~/.bottle/config.json"""
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}


def save_config(config: dict):
    """Save config to ~/.bottle/config.json"""
    CONFIG_DIR.mkdir(exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2))


# =============================================================================
# CLIENTS
# =============================================================================
def get_supabase() -> Client:
    """Get Supabase client (uses hardcoded credentials)."""
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def get_gemini() -> genai.GenerativeModel:
    """Get Gemini client (uses user's API key)."""
    config = get_config()
    key = config.get("gemini_key")
    
    if not key:
        # First-time setup: ask for key
        console.print("\n[bold]🔑 First time setup![/bold]")
        console.print("[dim]Get your free API key from: aistudio.google.com/apikey[/dim]\n")
        key = Prompt.ask("Gemini API key")
        config["gemini_key"] = key
        save_config(config)
        console.print("[green]✓ Saved![/green]\n")
    
    genai.configure(api_key=key)
    return genai.GenerativeModel("gemini-1.5-flash")


# =============================================================================
# USER MANAGEMENT
# =============================================================================
def get_or_create_user(sb: Client) -> dict:
    """Get existing user or create new one."""
    config = get_config()
    user_id = config.get("user_id")
    
    # Try to fetch existing user
    if user_id:
        result = sb.table("users").select("*").eq("id", user_id).execute()
        if result.data:
            return result.data[0]
    
    # Create new user with 3 starting tokens
    user_id = "user_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=12))
    
    result = sb.table("users").insert({
        "id": user_id,
        "tokens": 3.0,
        "created_at": datetime.utcnow().isoformat()
    }).execute()
    
    # Remember user_id locally
    config["user_id"] = user_id
    save_config(config)
    
    console.print(f"[green]✓ Welcome! You have 3 tokens to start.[/green]\n")
    return result.data[0]


# =============================================================================
# AI HELPERS
# =============================================================================
def analyze_url(model: genai.GenerativeModel, url: str) -> dict:
    """Use Gemini to analyze a URL and extract summary + tags."""
    prompt = f"""Analyze this web app/site: {url}

Return JSON only:
{{"summary": "2-3 sentence description", "tags": ["tag1", "tag2"], "stage": "mvp"}}

Tags should be like: saas, productivity, ai, dashboard, landing-page, e-commerce, developer-tool
Stage should be: idea, mvp, beta, or launched"""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Clean markdown code blocks if present
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        
        return json.loads(text)
    except:
        return {"summary": "", "tags": [], "stage": "unknown"}


def find_match(sb: Client, user_id: str, preference: str, my_tags: list) -> dict | None:
    """Find a project to review based on preference."""
    result = sb.table("projects") \
        .select("*") \
        .eq("status", "pending") \
        .neq("user_id", user_id) \
        .execute()
    
    if not result.data:
        return None
    
    projects = result.data
    
    if preference == "random" or not my_tags:
        return random.choice(projects)
    
    # Score by tag overlap
    scored = []
    for p in projects:
        overlap = len(set(p.get("tags") or []) & set(my_tags))
        scored.append((p, overlap))
    
    # Sort: similar = most overlap first, different = least overlap first
    scored.sort(key=lambda x: x[1], reverse=(preference == "similar"))
    return scored[0][0]


# =============================================================================
# COMMANDS
# =============================================================================
@app.command()
def submit(url: str = typer.Option(None, "--url", "-u")):
    """Submit your project for feedback."""
    sb = get_supabase()
    user = get_or_create_user(sb)
    
    # Check tokens
    if user["tokens"] < 1:
        console.print("[red]Not enough tokens! Review others to earn more.[/red]")
        console.print("Run: [bold]bottle review[/bold]")
        raise typer.Exit(1)
    
    # Get URL
    if not url:
        console.print("[bold]What's the URL of your project?[/bold]")
        url = Prompt.ask("URL")
    
    if not url.startswith("http"):
        url = "https://" + url
    
    # Analyze with AI
    model = get_gemini()
    
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), transient=True) as p:
        p.add_task("🤖 Analyzing...", total=None)
        analysis = analyze_url(model, url)
    
    summary = analysis.get("summary", "")
    tags = analysis.get("tags", [])
    stage = analysis.get("stage", "unknown")
    
    # Show analysis
    console.print(Panel(f"""
[bold]Summary:[/bold] {summary or '(none)'}
[bold]Tags:[/bold] {', '.join(tags) or '(none)'}
[bold]Stage:[/bold] {stage}
""", title="AI Analysis", style="cyan"))
    
    # Let user edit if needed
    if not summary or not Confirm.ask("Look right?", default=True):
        summary = Prompt.ask("Describe your project")
    
    # Feedback type
    console.print("\n[bold]What feedback do you want?[/bold]")
    console.print("  1. Is this idea worth pursuing?")
    console.print("  2. Roast my UI/UX")
    console.print("  3. General feedback")
    choice = Prompt.ask("Choose", choices=["1", "2", "3"], default="1")
    feedback_type = {"1": "idea", "2": "ux", "3": "general"}[choice]
    
    # Confirm
    if not Confirm.ask("\nSubmit? (costs 1 token)", default=True):
        raise typer.Exit(0)
    
    # Save to database
    project_id = "proj_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    
    sb.table("projects").insert({
        "id": project_id,
        "user_id": user["id"],
        "url": url,
        "summary": summary,
        "tags": tags,
        "stage": stage,
        "feedback_type": feedback_type,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat()
    }).execute()
    
    # Deduct token via RPC (secure)
    sb.rpc("deduct_token", {"p_user_id": user["id"]}).execute()
    
    console.print(f"\n[green]✓ Submitted![/green]")
    console.print(f"Tokens remaining: [yellow]{user['tokens'] - 1}[/yellow]")
    
    if Confirm.ask("\n💡 Review someone while you wait?", default=True):
        review()


@app.command()
def review(preference: str = typer.Option(None, "--match", "-m")):
    """Review someone else's project and earn tokens."""
    sb = get_supabase()
    user = get_or_create_user(sb)
    
    # Get user's tags for matching
    my_projects = sb.table("projects").select("tags").eq("user_id", user["id"]).execute()
    my_tags = []
    for p in my_projects.data:
        my_tags.extend(p.get("tags") or [])
    my_tags = list(set(my_tags))
    
    # Ask preference
    if not preference:
        console.print("\n[bold]What do you want to review?[/bold]")
        console.print("  1. Similar to what I build")
        console.print("  2. Something different")
        console.print("  3. Surprise me")
        choice = Prompt.ask("Choose", choices=["1", "2", "3"], default="3")
        preference = {"1": "similar", "2": "different", "3": "random"}[choice]
    
    # Find project
    project = find_match(sb, user["id"], preference, my_tags)
    
    if not project:
        console.print("[yellow]No projects to review right now![/yellow]")
        raise typer.Exit(0)
    
    # Show project
    console.print(Panel(f"""
[bold]🔗 URL:[/bold] {project['url']}

[bold]📝 Summary:[/bold]
{project['summary']}

[bold]🏷️ Tags:[/bold] {', '.join(project.get('tags') or [])}
[bold]❓ Looking for:[/bold] {project['feedback_type']} feedback
""", title="🍾 Project to Review", style="blue"))
    
    console.print("\n[cyan]→ Open the URL in your browser[/cyan]")
    
    if not Confirm.ask("\nReady to give feedback?", default=True):
        raise typer.Exit(0)
    
    # Collect feedback
    console.print("\n[bold]Your feedback:[/bold]")
    console.print("[dim]Type, then press Enter twice to submit:[/dim]\n")
    
    lines = []
    while True:
        line = input()
        if line == "" and lines:
            break
        lines.append(line)
    
    feedback = "\n".join(lines)
    
    if len(feedback) < 20:
        console.print("[red]Too short! Please give meaningful feedback.[/red]")
        raise typer.Exit(1)
    
    # Save feedback
    sb.table("feedback").insert({
        "project_id": project["id"],
        "reviewer_id": user["id"],
        "content": feedback,
        "created_at": datetime.utcnow().isoformat()
    }).execute()
    
    # Update project status
    sb.table("projects").update({"status": "reviewed"}).eq("id", project["id"]).execute()
    
    # Award tokens via RPC (secure)
    sb.rpc("award_token", {"p_user_id": user["id"], "p_amount": 0.5}).execute()
    
    console.print(f"\n[green]✓ Feedback sent! +0.5 tokens[/green]")
    
    if Confirm.ask("\nReview another?", default=False):
        review()


@app.command()
def inbox():
    """Check feedback on your projects."""
    sb = get_supabase()
    user = get_or_create_user(sb)
    
    # Get user's projects
    projects = sb.table("projects") \
        .select("*") \
        .eq("user_id", user["id"]) \
        .order("created_at", desc=True) \
        .execute().data
    
    if not projects:
        console.print("[yellow]No projects yet.[/yellow]")
        console.print("Run: [bold]bottle submit[/bold]")
        raise typer.Exit(0)
    
    # Show list
    console.print("\n[bold]Your projects:[/bold]\n")
    
    for i, p in enumerate(projects, 1):
        fb_count = len(
            sb.table("feedback")
            .select("id")
            .eq("project_id", p["id"])
            .execute().data
        )
        color = "green" if fb_count > 0 else "yellow"
        status = f"{fb_count} feedback" if fb_count else "waiting..."
        console.print(f"  [{color}]{i}.[/{color}] {p['summary'][:50]}... ({status})")
    
    # Select project
    console.print()
    choice = Prompt.ask("View feedback for", default="1")
    
    try:
        project = projects[int(choice) - 1]
    except:
        raise typer.Exit(0)
    
    # Get feedback
    feedback_list = sb.table("feedback") \
        .select("*") \
        .eq("project_id", project["id"]) \
        .execute().data
    
    if not feedback_list:
        console.print("[yellow]No feedback yet.[/yellow]")
        raise typer.Exit(0)
    
    # Show feedback
    for i, fb in enumerate(feedback_list, 1):
        console.print(Panel(fb["content"], title=f"Feedback #{i}", style="green"))
        
        # Rate feedback (gives reviewer bonus)
        if not fb.get("rated") and Confirm.ask("Was this helpful?", default=True):
            sb.table("feedback").update({"rated": True}).eq("id", fb["id"]).execute()
            sb.rpc("award_token", {"p_user_id": fb["reviewer_id"], "p_amount": 0.5}).execute()
            console.print("[green]✓ Reviewer got +0.5 bonus![/green]")


@app.command()
def tokens():
    """Check your token balance."""
    sb = get_supabase()
    user = get_or_create_user(sb)
    
    # Fetch fresh balance
    fresh = sb.table("users").select("tokens").eq("id", user["id"]).execute().data[0]
    
    console.print(f"\n🪙 [bold]Tokens: {fresh['tokens']}[/bold]\n")
    console.print("[dim]Earn:[/dim]  Review (+0.5) • Get thumbs up (+0.5)")
    console.print("[dim]Spend:[/dim] Submit for feedback (-1)")


@app.command()
def setup():
    """Reconfigure your Gemini API key."""
    config = get_config()
    
    console.print("\n[bold]🔑 Gemini API Setup[/bold]")
    console.print("[dim]Get your free key from: aistudio.google.com/apikey[/dim]\n")
    
    key = Prompt.ask("Gemini API key", default=config.get("gemini_key", ""))
    config["gemini_key"] = key
    save_config(config)
    
    console.print("[green]✓ Saved![/green]")


if __name__ == "__main__":
    app()