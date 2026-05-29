import os
import sys
import typer
from typing import Optional
from src.db import init_db, get_db, Lead
from src.core.ingest import ingest_csv
from src.core.review import interactive_review_loop
from src.core.send import send_emails

app = typer.Typer(help="Website-Audit Sales Automation CLI")

@app.callback()
def callback():
    """
    Initializes the database and application state before any command executes.
    """
    init_db()

@app.command()
def ingest(
    csv_path: str = typer.Option(..., "--csv", "-c", help="Path to the CSV file containing leads"),
):
    """
    Ingest leads from a CSV file. Parses name, website, and email, normalized URLs,
    and runs deduplication and suppression checks.
    """
    if not os.path.exists(csv_path):
        typer.echo(f"Error: CSV file not found at {csv_path}", err=True)
        raise typer.Exit(code=1)
        
    db_gen = get_db()
    db = next(db_gen)
    try:
        typer.echo(f"Ingesting leads from {csv_path}...")
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            stats = ingest_csv(db, f)
            
        typer.echo("\n--- Ingestion Summary ---")
        typer.echo(f"Total rows in CSV:  {stats['total']}")
        typer.echo(f"Successfully imported: {stats['imported']} (status: pending)")
        typer.echo(f"Duplicates skipped:    {stats['duplicates']}")
        typer.echo(f"Suppressed (opt-out):  {stats['suppressed']} (status: suppressed)")
        typer.echo(f"Failed (invalid format): {stats['failed']} (status: failed)")
        typer.echo("-------------------------")
    except Exception as e:
        typer.echo(f"Error during ingestion: {str(e)}", err=True)
        raise typer.Exit(code=1)
    finally:
        db.close()

@app.command()
def status():
    """
    Show a summary of lead statuses in the database.
    """
    db_gen = get_db()
    db = next(db_gen)
    try:
        from sqlalchemy import func
        counts = db.query(Lead.status, func.count(Lead.id)).group_by(Lead.status).all()
        typer.echo("\n--- Database Lead Status Summary ---")
        if not counts:
            typer.echo("No leads in the database yet.")
        else:
            for status, count in counts:
                typer.echo(f" {status:<20}: {count}")
        typer.echo("------------------------------------")
    except Exception as e:
        typer.echo(f"Error checking status: {str(e)}", err=True)
        raise typer.Exit(code=1)
    finally:
        db.close()

@app.command()
def scrape(
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Max number of leads to scrape"),
):
    """
    Runs the website scraper stage. Crawls homepage & internal subpages using Playwright Chromium
    and captures screenshots.
    """
    import asyncio
    from src.core.scrape import run_scraper
    
    db_gen = get_db()
    db = next(db_gen)
    try:
        typer.echo("Starting website scraper...")
        stats = asyncio.run(run_scraper(db, limit))
        typer.echo("\n--- Scraper Run Summary ---")
        typer.echo(f"Total leads processed: {stats['total']}")
        typer.echo(f"Successfully scraped:  {stats['success']}")
        typer.echo(f"Failed scrapes:        {stats['failed']}")
        typer.echo("---------------------------")
    except Exception as e:
        typer.echo(f"Error during scraping: {str(e)}", err=True)
        raise typer.Exit(code=1)
    finally:
        db.close()

@app.command()
def analyze(
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Max number of leads to analyze"),
):
    """
    Runs the objective website analysis and service mapping stage. Queries PageSpeed,
    checks HTML elements, and maps findings to sold services.
    """
    import asyncio
    from src.core.analyze import run_analysis
    
    db_gen = get_db()
    db = next(db_gen)
    try:
        typer.echo("Starting website analysis...")
        stats = asyncio.run(run_analysis(db, limit))
        typer.echo("\n--- Analysis Run Summary ---")
        typer.echo(f"Total leads analyzed: {stats['total']}")
        typer.echo(f"Successfully analyzed: {stats['success']}")
        typer.echo(f"Skipped (no findings): {stats['skipped']}")
        typer.echo(f"Failed audits:         {stats['failed']}")
        typer.echo("----------------------------")
    except Exception as e:
        typer.echo(f"Error during analysis: {str(e)}", err=True)
        raise typer.Exit(code=1)
    finally:
        db.close()

@app.command()
def generate(
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Max number of leads to generate emails for"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Override default model"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Override default provider"),
):
    """
    Runs the email generation stage. Calls LLM with grounded prompt and validator,
    appends compliant CAN-SPAM footers.
    """
    import asyncio
    from src.core.generate import run_email_generation
    
    db_gen = get_db()
    db = next(db_gen)
    try:
        typer.echo("Starting email generation...")
        stats = asyncio.run(run_email_generation(db, limit, model, provider))
        typer.echo("\n--- Email Generation Summary ---")
        typer.echo(f"Total leads processed:  {stats['total']}")
        typer.echo(f"Successfully drafted:   {stats['success']}")
        typer.echo(f"Failed drafts/ground:   {stats['failed']}")
        typer.echo("--------------------------------")
    except Exception as e:
        typer.echo(f"Error during email generation: {str(e)}", err=True)
        raise typer.Exit(code=1)
    finally:
        db.close()

@app.command()
def bakeoff(
    sample: int = typer.Option(5, "--sample", "-s", help="Number of leads to sample for comparison"),
    models: Optional[str] = typer.Option(None, "--models", help="Comma-separated list of model:provider strings (e.g. claude-sonnet-4-6:anthropic,gpt-5.4-mini:openai)"),
):
    """
    Runs A/B LLM comparison (bake-off) for selected leads and prints results side-by-side.
    """
    import asyncio
    from src.llm.bakeoff import run_model_comparison
    
    db_gen = get_db()
    db = next(db_gen)
    try:
        typer.echo("Running LLM Model Bake-off comparison...")
        models_list = None
        if models:
            models_list = [m.strip() for m in models.split(",")]
            
        results = asyncio.run(run_model_comparison(db, sample, models_list))
        if not results:
            typer.echo("Bake-off generated no results. Make sure you have analyzed leads.")
            return
            
        for res in results:
            typer.echo(f"\n==========================================")
            typer.echo(f"LEAD ID {res['lead_id']}: {res['lead_name']} ({res['website_url']})")
            typer.echo(f"==========================================")
            for run in res["runs"]:
                typer.echo(f"\n--- Model: {run['model']} ({run['provider']}) ---")
                typer.echo(f"Latency:      {run['latency_s']}s")
                typer.echo(f"Est. Cost:    ${run['estimated_cost_usd']}")
                typer.echo(f"Subject line: {run['subject']}")
                typer.echo(f"Body preview:\n{run['body'][:300]}...")
                typer.echo(f"------------------------------------------")
    except Exception as e:
        typer.echo(f"Error during bake-off: {str(e)}", err=True)
        raise typer.Exit(code=1)
    finally:
        db.close()

@app.command()
def review():
    """
    Start the interactive review console. Approve, reject, or edit email drafts before sending.
    """
    db_gen = get_db()
    db = next(db_gen)
    try:
        stats = interactive_review_loop(db)
        typer.echo("\n--- Review Session Summary ---")
        typer.echo(f"Total drafts processed: {stats['total']}")
        typer.echo(f"Approved:              {stats['approved']}")
        typer.echo(f"Rejected:              {stats['rejected']}")
        typer.echo(f"Skipped/Unresolved:    {stats['skipped']}")
        typer.echo("------------------------------")
    except Exception as e:
        typer.echo(f"Error during review: {str(e)}", err=True)
        raise typer.Exit(code=1)
    finally:
        db.close()

@app.command()
def send(
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Max number of emails to send"),
    dry_run: Optional[bool] = typer.Option(None, "--dry-run/--real-run", help="Override config dry_run setting to force real/simulated send"),
):
    """
    Runs the send orchestration stage. Enforces daily caps, real-time suppression, and CAN-SPAM verification.
    """
    import asyncio
    
    db_gen = get_db()
    db = next(db_gen)
    try:
        typer.echo("Starting email send runner...")
        stats = asyncio.run(send_emails(db, limit=limit, dry_run=dry_run))
        typer.echo("\n--- Email Send Summary ---")
        typer.echo(f"Total candidates:      {stats['total']}")
        typer.echo(f"Successfully sent:     {stats['sent']}")
        typer.echo(f"Suppressed (opt-out):  {stats['suppressed']}")
        typer.echo(f"Failed sending:        {stats['failed']}")
        typer.echo(f"Daily limit hit:       {stats['cap_hit']}")
        typer.echo("--------------------------")
    except Exception as e:
        typer.echo(f"Error during sending: {str(e)}", err=True)
        raise typer.Exit(code=1)
    finally:
        db.close()

if __name__ == "__main__":
    app()
