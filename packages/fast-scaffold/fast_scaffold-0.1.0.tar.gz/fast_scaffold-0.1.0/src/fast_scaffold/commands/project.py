import typer
from fast_scaffold.generator import generate_project

app = typer.Typer(help="Inicializa um novo projeto")

@app.command()
def init(
    name: str,
    docker: bool = typer.Option(False, "--docker", help="Adicionar Docker"),
):
    generate_project(name)
    typer.echo(f"✅ Projeto '{name}' criado")
