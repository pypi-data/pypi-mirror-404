# fast-scaffold 🚀

CLI para gerar **scaffolding de projetos FastAPI** de forma rápida, padronizada e extensível.

O `fast-scaffold` cria a estrutura inicial de um projeto FastAPI a partir de **templates Mako**, permitindo evoluir facilmente para múltiplos tipos de scaffolds no futuro.

---

## ✨ Features

- 📦 CLI simples e rápida
- ⚡ Geração de projetos FastAPI em segundos
- 🧱 Estrutura baseada em templates (Mako)
- 🧩 Fácil de estender para novos scaffolds
- 🐍 Compatível com Python 3.13+

---

## 📦 Instalação

### Usando pipx (recomendado para CLIs)

```bash
pipx install fast-scaffold
```

Ou usando pip

```bash
pip install fast-scaffold
```

🚀 Uso rápido

Criar um novo projeto FastAPI:

```bash
fast-scaffold project init minha-api
```

Isso irá gerar a estrutura do projeto no diretório atual:

```text
minha-api/
├── pyproject.toml
├── README.md
└── app/
    └── main.py
```

🧠 Como funciona

O fast-scaffold utiliza templates Mako localizados dentro do pacote:

```text
fast_scaffold/
└── templates/
    └── project/
        ├── pyproject.toml.mako
        ├── README.md.mako
        └── app/
            └── main.py.mako
```