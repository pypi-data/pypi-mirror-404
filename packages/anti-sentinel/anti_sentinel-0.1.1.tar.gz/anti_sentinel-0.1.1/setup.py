from setuptools import setup, find_packages
from pathlib import Path

# 1. Read the README.md file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

# 2. Setup the package
setup(
    name="anti_sentinel",
    version="0.1.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "typer",
        "rich",
        "fastapi",
        "uvicorn",
        "openai",
        "pyyaml",
        "python-dotenv",
        "mem0ai",
        "qdrant-client", # Needed for local vector store
        "google-genai",   # Gemini API client
        "jinja2",
        "aiosqlite",
        "mkdocs",
        "mkdocs-material",
        "mkdocstrings[python]"
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
    entry_points={
        'console_scripts': [
            # CHANGE 'sentinel' TO 'anti_sentinel'
            # Format: command_name = internal_module:function
            'anti_sentinel=anti_sentinel.cli:app', 
        ],
    },
)