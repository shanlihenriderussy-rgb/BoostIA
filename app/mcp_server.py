"""MCP Server pour BoostIA — expose les templates comme des tools Claude."""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

import structlog
from mcp.server import Server
from mcp.types import TextContent, Tool

from app.config import settings
from app.llm_client import OllamaClient, OllamaError
from app.logging_config import configure_logging
from app.templates import Tone, build_messages, list_templates

configure_logging()
logger = structlog.get_logger(__name__)

# --- Initialisation ---
server = Server("BoostIA")
llm = OllamaClient()


# --- Tools ---
@server.list_tools()
async def list_boostia_tools() -> list[Tool]:
    """Expose les 22 templates comme des tools MCP."""
    tools: list[Tool] = []

    # Tool: generate_text (interface universelle)
    tools.append(
        Tool(
            name="generate_text",
            description="Générer un texte professionnel avec un template BoostIA",
            inputSchema={
                "type": "object",
                "properties": {
                    "template_id": {
                        "type": "string",
                        "description": "ID du template (ex: 'email_relance', 'bio_pro')",
                    },
                    "context": {
                        "type": "string",
                        "description": "Contexte / données pour remplir le template",
                    },
                    "tone": {
                        "type": "string",
                        "enum": ["formel", "neutre", "direct"],
                        "description": "Tonalité du texte",
                        "default": "neutre",
                    },
                },
                "required": ["template_id", "context"],
            },
        )
    )

    # Tool: list_templates (découverte)
    tools.append(
        Tool(
            name="list_templates",
            description="Lister les 22 templates disponibles avec descriptions",
            inputSchema={"type": "object", "properties": {}},
        )
    )

    return tools


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Exécute un tool BoostIA."""
    try:
        if name == "generate_text":
            return await handle_generate_text(arguments)
        elif name == "list_templates":
            return handle_list_templates()
        else:
            raise ValueError(f"Unknown tool: {name}")
    except OllamaError as e:
        logger.error("ollama_error", error=str(e))
        return [TextContent(type="text", text=f"❌ Erreur Ollama: {e}")]
    except Exception as e:
        logger.error("tool_error", tool=name, error=str(e))
        return [TextContent(type="text", text=f"❌ Erreur: {e}")]


async def handle_generate_text(args: dict[str, Any]) -> list[TextContent]:
    """Génère du texte avec un template."""
    template_id = args.get("template_id")
    context = args.get("context")
    tone = args.get("tone", "neutre")

    if not template_id or not context:
        raise ValueError("template_id et context sont obligatoires")

    if tone not in ("formel", "neutre", "direct"):
        raise ValueError(f"Ton invalide: {tone}")

    # Récupère le template
    templates = list_templates()
    template = next((t for t in templates if t.id == template_id), None)

    if not template:
        raise ValueError(f"Template '{template_id}' non trouvé")

    logger.info("generate_text", template_id=template_id, tone=tone)

    # Construit les messages pour Ollama
    messages = build_messages(template, context, tone)

    # Génère le texte
    text = await llm.generate_complete(messages)

    return [TextContent(type="text", text=text)]


def handle_list_templates() -> list[TextContent]:
    """Liste tous les templates disponibles."""
    templates = list_templates()
    output = "📋 **Templates BoostIA (22)**\n\n"

    # Groupe par catégorie (heuristique simple: prefix avant underscore)
    categories: dict[str, list] = {}
    for t in templates:
        cat = t.id.split("_")[0].replace("-", " ").title()
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(t)

    for cat in sorted(categories.keys()):
        output += f"\n**{cat}**\n"
        for t in categories[cat]:
            output += f"- `{t.id}`: {t.label}\n"

    return [TextContent(type="text", text=output)]


# --- Main ---
async def main():
    """Lance le serveur MCP."""
    logger.info("boostia_mcp_starting", model=settings.model_name)

    async with server:
        await server.wait_for_shutdown()


if __name__ == "__main__":
    asyncio.run(main())
