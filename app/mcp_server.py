"""MCP Server pour BoostIA — expose les templates comme des tools Claude.

Phase 1 : core MCP avec 2 tools (generate_text + list_templates).
Reutilise la logique existante (OllamaClient, templates, config).
"""

from __future__ import annotations

import asyncio
from typing import Any

import structlog
from mcp.server import Server
from mcp.types import TextContent, Tool

from app.config import settings
from app.llm_client import OllamaClient, OllamaError
from app.logging_config import configure_logging
from app.templates import build_messages, get_template, list_templates

configure_logging()
logger = structlog.get_logger(__name__)

# --- Initialisation ---
server: Server = Server("boostia")
llm = OllamaClient()


# --- Tools ---
@server.list_tools()
async def list_boostia_tools() -> list[Tool]:
    """Expose les outils BoostIA accessibles depuis Claude."""
    return [
        Tool(
            name="generate_text",
            description=(
                "Genere un texte professionnel en francais via un template BoostIA "
                "(emails, lettres, posts marketing, comptes-rendus, etc.). "
                "Utilise un LLM local via Ollama (aucune donnee n'est envoyee a un service tiers)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "template_id": {
                        "type": "string",
                        "description": (
                            "ID du template a utiliser. Appelle d'abord list_templates "
                            "pour decouvrir les IDs disponibles."
                        ),
                    },
                    "context": {
                        "type": "string",
                        "description": (
                            "Contexte / faits a integrer dans le texte (noms, dates, montants, "
                            "objet du message, etc.). Le modele n'inventera rien hors de ce contexte."
                        ),
                        "minLength": 1,
                    },
                    "tone": {
                        "type": "string",
                        "enum": ["formel", "neutre", "direct"],
                        "description": "Tonalite du texte produit. Par defaut: neutre.",
                        "default": "neutre",
                    },
                    "model": {
                        "type": "string",
                        "description": (
                            "(Optionnel) ID du modele Ollama a utiliser (ex. 'phi4:latest'). "
                            "Si absent, utilise le modele configure par defaut."
                        ),
                    },
                },
                "required": ["template_id", "context"],
            },
        ),
        Tool(
            name="list_templates",
            description=(
                "Liste les templates BoostIA disponibles avec leur ID, label et description. "
                "A appeler avant generate_text pour choisir le bon template."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Dispatch vers le handler du tool demande."""
    try:
        if name == "generate_text":
            return await handle_generate_text(arguments)
        if name == "list_templates":
            return handle_list_templates()
        return [TextContent(type="text", text=f"Tool inconnu : {name!r}")]
    except KeyError as exc:
        return [TextContent(type="text", text=f"Template inconnu : {exc}")]
    except ValueError as exc:
        return [TextContent(type="text", text=f"Argument invalide : {exc}")]
    except OllamaError as exc:
        logger.error("ollama_error", error=str(exc))
        return [TextContent(type="text", text=f"Erreur Ollama : {exc}")]
    except Exception as exc:  # noqa: BLE001
        logger.exception("tool_error", tool=name)
        return [TextContent(type="text", text=f"Erreur interne : {exc}")]


async def handle_generate_text(args: dict[str, Any]) -> list[TextContent]:
    """Genere un texte en utilisant un template + Ollama."""
    template_id = (args.get("template_id") or "").strip()
    context = (args.get("context") or "").strip()
    tone = (args.get("tone") or "neutre").strip()
    model = args.get("model") or None

    if not template_id:
        raise ValueError("template_id est obligatoire")
    if not context:
        raise ValueError("context est obligatoire")
    if tone not in ("formel", "neutre", "direct"):
        raise ValueError(f"tone invalide : {tone!r} (attendu: formel|neutre|direct)")

    # Valide l'existence du template (leve KeyError si inconnu)
    get_template(template_id)

    logger.info(
        "mcp_generate_start",
        template_id=template_id,
        tone=tone,
        model=model or settings.model_name,
        context_len=len(context),
    )

    messages = build_messages(template_id, context, tone)

    # Aggrege le stream Ollama en une string complete (MCP attend une reponse unique)
    chunks: list[str] = []
    async for delta in llm.chat_stream(messages, model=model):
        chunks.append(delta)
    output = "".join(chunks).strip()

    logger.info("mcp_generate_done", template_id=template_id, output_chars=len(output))

    if not output:
        return [TextContent(type="text", text="(reponse vide du modele)")]
    return [TextContent(type="text", text=output)]


def handle_list_templates() -> list[TextContent]:
    """Retourne la liste des templates disponibles, formatee pour Claude."""
    templates = list_templates()

    lines = [f"# Templates BoostIA ({len(templates)} disponibles)\n"]
    for t in templates:
        lines.append(f"- **{t['id']}** — {t['label']}")
        lines.append(f"  {t['description']}\n")

    return [TextContent(type="text", text="\n".join(lines))]


# --- Main ---
async def main() -> None:
    """Lance le serveur MCP en mode stdio."""
    from mcp.server.stdio import stdio_server

    logger.info(
        "boostia_mcp_starting",
        default_model=settings.model_name,
        ollama_url=settings.ollama_base_url,
    )

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
