import typer
from fast_scaffold.commands import project

app = typer.Typer(
    help="Fast Scaffold – gerador de projetos FastAPI"
)

app.add_typer(project.app, name="project")

def main():
    app()
