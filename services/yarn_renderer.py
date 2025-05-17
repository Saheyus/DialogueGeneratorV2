from __future__ import annotations

"""YarnRenderer — Convertit la sortie d'un LLM en fichier .yarn.

Cette implémentation s'appuie sur Jinja2 : un template est chargé puis
rendu avec le texte généré par le LLM et des métadonnées optionnelles.

Exemple d'usage :

```python
renderer = YarnRenderer()
content = renderer.render(llm_output, {"title": "Intro", "tags": "auto"})
with open("Assets/Dialogues/generated/intro.yarn", "w", encoding="utf-8") as f:
    f.write(content)
```
"""

from pathlib import Path
from typing import Dict, Mapping

from jinja2 import Environment, FileSystemLoader, select_autoescape


class YarnRenderer:
    """Service de rendu de fichiers Yarn à partir d'un template Jinja2."""

    DEFAULT_TEMPLATE_NAME = "yarn_template.j2"

    def __init__(
        self,
        template_dir: Path | str | None = None,
        template_name: str = DEFAULT_TEMPLATE_NAME,
    ) -> None:
        # Chemin du dossier contenant les templates Jinja2
        self._template_dir = (
            Path(template_dir) if template_dir is not None else Path(__file__).parent.parent / "templates"
        ).resolve()
        self._env = Environment(
            loader=FileSystemLoader(str(self._template_dir)),
            autoescape=select_autoescape(enabled_extensions=("j2",)),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self._template = self._env.get_template(template_name)

    # ---------------------------------------------------------------------
    # API publique
    # ---------------------------------------------------------------------
    def render(self, llm_output: str, metadata: Mapping[str, str] | None = None) -> str:
        """Retourne le contenu d'un fichier Yarn.

        Parameters
        ----------
        llm_output: str
            Le texte (déjà post-traité) produit par le LLM.
        metadata: Mapping[str, str] | None
            Métadonnées à insérer dans l'entête YAML du nœud Yarn
            (par exemple : title, tags…)
        """
        data = {
            "llm_output": llm_output.strip(),
            "metadata": dict(metadata or {}),
        }
        return self._template.render(**data) 