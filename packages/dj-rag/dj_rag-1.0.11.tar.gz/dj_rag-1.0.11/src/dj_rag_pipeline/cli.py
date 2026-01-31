# src/dj_rag_pipeline/cli.py
import argparse
import shutil
from pathlib import Path
from importlib.resources import files, as_file

def create_env_file(project_path: Path):
    """
    Create a .env file in the new project with placeholder values.
    """
    env_content = """# Environment variables for your RAG project
PINECONE_API_KEY=xxxx
INDEX_NAME=xxxx
PINECONE_INDEX_HOST=xxxxxx
EMBEDDING_MODEL=nomic-ai/nomic-embed-text-v1.5
MAX_CHUNK_SIZE=1500
LLM_MODEL=xxxx
LLM_BASE_URL=xxxx
LLM_MAX_TOKENS=16384
LLM_PROVIDER=xxxx
_API_KEY=xxxxx
"""
    env_path = project_path / ".env"
    if not env_path.exists():
        env_path.write_text(env_content)
        print("✅ Created .env with placeholder values")
    else:
        print("⚠️ .env already exists — skipping")

def get_template_dir() -> Path:
    """
    Find the packaged 'project_skeleton' template directory inside this package.
    Uses importlib.resources API which works from wheels, sdist, or installed package.
    """
    # This points to dj_rag_pipeline/templates/project_skeleton
    tmpl = files("dj_rag_pipeline") / "templates" / "project_skeleton"
    # as_file gives a real filesystem path if inside a zip or wheel
    with as_file(tmpl) as real_path:
        return real_path

def init_project(project_name: str):
    """Copy project skeleton and create .env file."""
    target = Path.cwd() / project_name
    if target.exists():
        print(f"❌ Error: '{project_name}' already exists!")
        return

    template_dir = get_template_dir()
    shutil.copytree(template_dir, target)
    print(f"✅ Project '{project_name}' created at {target}")

    create_env_file(target)

def main():
    parser = argparse.ArgumentParser(prog="dj-rag")
    parser.add_argument("command", choices=["init"])
    parser.add_argument("name", help="Name of the project to create")
    args = parser.parse_args()

    if args.command == "init":
        init_project(args.name)
