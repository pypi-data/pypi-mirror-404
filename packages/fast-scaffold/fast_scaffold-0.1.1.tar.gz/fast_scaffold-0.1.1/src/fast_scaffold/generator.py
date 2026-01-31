from pathlib import Path
from mako.template import Template

BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates" / "project"


def generate_project(project_name: str):
    project_dir = Path.cwd() / project_name
    project_dir.mkdir(parents=True, exist_ok=False)

    context = {
        "project_name": project_name
    }

    for template_file in TEMPLATES_DIR.rglob("*.mako"):
        relative_path = template_file.relative_to(TEMPLATES_DIR)
        output_file = project_dir / relative_path.with_suffix("")

        output_file.parent.mkdir(parents=True, exist_ok=True)

        content = Template(filename=str(template_file)).render(**context)
        output_file.write_text(content, encoding="utf-8")

