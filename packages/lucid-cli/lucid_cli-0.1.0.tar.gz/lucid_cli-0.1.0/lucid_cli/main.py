import structlog
import typer
from lucid_cli import agent, auditor, auth, catalog, environment, passport

# Configure Structlog
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

app = typer.Typer(help="Lucid Platform CLI")

# New API-based commands
app.add_typer(auth.app, name="login", help="Authenticate with Lucid platform")
app.add_typer(agent.app, name="agent", help="Manage AI agents")
app.add_typer(environment.app, name="environment", help="Deploy LucidEnvironment CRDs")
app.add_typer(catalog.app, name="catalog", help="Browse app catalog")
app.add_typer(passport.app, name="passport", help="View AI passports")

# Auditor development
app.add_typer(auditor.app, name="auditor", help="Manage Lucid Auditors")

@app.callback()
def callback():
    """
    Lucid CLI - Secure AI Supply Chain Management.
    """
    pass

if __name__ == "__main__":
    app()
