import typer
import sys
from pathlib import Path
from rich.console import Console
import shutil
# We initialize the app
app = typer.Typer()
console = Console()

# --- CONFIGURATION ---
PROJECT_STRUCTURE = {
    "config": ["__init__.py", "agents.yaml", "database.yaml"],
    "app": {
        "agents": ["__init__.py"],
        "workflows": ["__init__.py"],
        "jobs": ["__init__.py"],
        "http": ["__init__.py"]
    },
    "public": [],
    "tests": ["__init__.py"]
}

DEFAULT_CONFIG_YAML = """
app_name: "{project_name}"
version: "0.1.0"
debug: true
llm:
  provider: "openai"
  model: "gpt-4o"
  temperature: 0.7
"""

# --- CRITICAL FIX: THE CALLBACK ---
@app.callback()
def callback():
    """
    Sentinel CLI Tool.
    """
    # This empty function forces Typer to treat this as a 
    # multi-command app, stopping it from running 'new' immediately.
    pass

# --- THE NEW COMMAND ---
@app.command()
def new(project_name: str):
    """
    Creates a new Sentinel project.
    """
    console.print(f"[bold]Debug:[/bold] Running 'new' command for {project_name}")
    
    base_path = Path.cwd() / project_name

    if base_path.exists():
        console.print(f"[bold red]Error:[/bold red] Directory '{project_name}' already exists!")
        raise typer.Exit(code=1)

    console.print(f"[bold green]Creating new Sentinel project:[/bold green] {project_name}...")

    # Create directories
    base_path.mkdir()
    create_structure(base_path, PROJECT_STRUCTURE)

    # Create root files
    create_file(base_path / "sentinel.yaml", DEFAULT_CONFIG_YAML.format(project_name=project_name))
    create_file(base_path / ".env", "OPENAI_API_KEY=your_key_here")

    import anti_sentinel
    # We navigate to anti_sentinel/static/docs
    core_path = Path(anti_sentinel.__file__).parent
    baked_docs_path = core_path / "static" / "docs"
    
    target_docs_path = base_path / "framework-docs"
    
    # --- DEBUG PRINTS ---
    console.print(f"🔎 DEBUG: Looking for docs source at: {baked_docs_path}")
    # --------------------

    if baked_docs_path.exists():
        console.print("📖 Unpacking framework documentation...")
        # dirs_exist_ok=True is safer in case folder was partially created
        shutil.copytree(baked_docs_path, target_docs_path, dirs_exist_ok=True)
    else:
        console.print("[yellow]⚠️ Warning: Pre-built docs not found in package. Skipping copy.[/yellow]")
        console.print(f"[yellow]  (Checked path: {baked_docs_path})[/yellow]")
    
    # Create main.py
    main_py_content = """# Entry point for your application
from anti_sentinel.core import SentinelApp

# Initialize the framework
app = SentinelApp(config_file="sentinel.yaml")

if __name__ == "__main__":
    app.boot()
"""
    create_file(base_path / "main.py", main_py_content)

    console.print(f"\n[bold blue]Success![/bold blue] Created {project_name}.")
    console.print(f"cd {project_name} && python main.py")

# --- HELPERS ---
def create_structure(base_path: Path, structure: dict):
    for name, content in structure.items():
        current_path = base_path / name
        if isinstance(content, dict):
            current_path.mkdir(exist_ok=True)
            create_structure(current_path, content)
        elif isinstance(content, list):
            current_path.mkdir(exist_ok=True)
            for file_name in content:
                create_file(current_path / file_name, "# Sentinel Generated File")

def create_file(path: Path, content: str):
    with open(path, "w") as f:
        f.write(content)

# DockerFile GENERATION COMMAND

DOCKERFILE_CONTENT = """
# Use official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies (needed for some python packages)
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .

# Install dependencies
# We install the local package in editable mode
RUN pip install --no-cache-dir -e .

# Expose port
EXPOSE 8000

# Start the application
CMD ["python", "main.py"]
"""

@app.command()
def docker():
    """
    Generates a Dockerfile for deployment.
    """
    docker_path = Path.cwd() / "Dockerfile"
    
    if docker_path.exists():
        console.print("[bold yellow]Warning:[/bold yellow] Dockerfile already exists.")
        return

    create_file(docker_path, DOCKERFILE_CONTENT)
    
    # Also create a .dockerignore to keep the image small
    dockerignore_content = "__pycache__\n*.pyc\n.env\n.git\n.venv\nsentinel_metrics.db"
    create_file(Path.cwd() / ".dockerignore", dockerignore_content)

    console.print("[bold green]Success![/bold green] Dockerfile created.")
    console.print("Run: [bold cyan]docker build -t my_agent .[/bold cyan]")

@app.command()
def build_docs():
    """
    Builds the documentation for the API.
    """
    import subprocess
    console.print("[bold cyan]Building Documentation...[/bold cyan]")
    try:
        # We run 'mkdocs build' as a subprocess
        subprocess.run(["mkdocs", "build"], check=True)
        console.print("[bold green]Success![/bold green] Docs built to 'site/' folder.")
    except Exception as e:
        console.print(f"[bold red]Error building docs:[/bold red] {e}")

@app.command()
def init_docs():
    """
    Creates the mkdocs.yml and docs/ folder.
    """
    # 1. Create mkdocs.yml
    mkdocs_content = """
site_name: Sentinel App
theme:
  name: material
  palette:
    primary: indigo
    accent: blue

plugins:
  - search
  - mkdocstrings:
      handlers:
        python:
          paths: [.]

nav:
  - Home: index.md
  - API Reference:
      - Agents: reference/agents.md
      - Workflows: reference/workflows.md
"""
    create_file(Path.cwd() / "mkdocs.yml", mkdocs_content)

    # 2. Create docs folder and index.md
    docs_dir = Path.cwd() / "docs"
    docs_dir.mkdir(exist_ok=True)
    
    index_content = """
# Welcome to My Sentinel App

This is the internal documentation for the application.

## Getting Started
Run `python main.py` to start the server.
"""
    create_file(docs_dir / "index.md", index_content)
    
    # 3. Create reference folder
    ref_dir = docs_dir / "reference"
    ref_dir.mkdir(exist_ok=True)
    
    create_file(ref_dir / "agents.md", "# Agents\n\n::: app.agents.writer.ContentWriterAgent")
    create_file(ref_dir / "workflows.md", "# Workflows\n\n::: app.workflows.news_flow")

    console.print("[bold green]Documentation structure created.[/bold green]")
    console.print("Run [bold cyan]sentinel build-docs[/bold cyan] to generate HTML.")

if __name__ == "__main__":
    # Debug print to ensure we are actually running
    # print(f"DEBUG ARGS: {sys.argv}") 
    app()