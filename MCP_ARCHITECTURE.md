# BoostIA MCP Architecture

## Overview

BoostIA est transformé en **serveur MCP (Model Context Protocol)** pour intégration native dans Claude et Claude Code.

```
Claude / Claude Code
        │
        ├── stdio protocol
        ▼
┌─────────────────────────────────────┐
│ BoostIA MCP Server                  │
├─────────────────────────────────────┤
│ Tools:                              │
│ • generate_text(template_id, ...)   │
│ • list_templates()                  │
└──────────────────┬──────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
    Ollama              Templates (22)
    (phi4)              + Tones (3)
```

## Architecture Technique

### 1. **Serveur MCP** (`app/mcp_server.py`)

Le serveur expose **2 tools principaux**:

#### Tool: `generate_text`
```json
{
  "template_id": "email_relance",
  "context": "Relance de facturation n°2024-001",
  "tone": "formel"
}
```

Retourne: texte généré en streaming via Ollama

#### Tool: `list_templates`
```json
{}
```

Retourne: liste des 22 templates avec descriptions

### 2. **Dépendances Réutilisées**

- `app/llm_client.py` → Client Ollama async (inchangé)
- `app/templates.py` → 22 templates + logique tonalité (inchangé)
- `app/config.py` → Configuration (.env) (inchangé)

### 3. **Démarrage**

```bash
# Installation
pip install -r requirements.txt

# Démarrage du serveur
python run_mcp.py

# Ou via Claude Code
# Configure .claude/settings.local.json et reload
```

## Intégration Claude Code

### Configuration (`.claude/settings.local.json`)

```json
{
  "mcpServers": {
    "boostia": {
      "command": "python",
      "args": ["run_mcp.py"]
    }
  }
}
```

### Utilisation dans Claude Code

```
# Claude détecte automatiquement BoostIA
/generate_text template_id=email_relance context="Relance client" tone=direct

# Ou liste les templates
/list_templates
```

## Roadmap Phase 2: Auth + Subscription

```python
# Quotas légers (SQLite)
class UserQuota:
    user_id: str
    daily_limit: int = 10  # gratuit
    subscription: Literal["free", "pro"]
    used_today: int
```

**Resources MCP** (pour l'authentification):

```json
{
  "uri": "boostia://user/{user_id}",
  "mimeType": "application/json",
  "content": {
    "daily_limit": 10,
    "used_today": 3,
    "subscription": "free"
  }
}
```

## Performance

- **First token**: ~2s (Phi4 sur RTX 3050 Ti)
- **Streaming**: SSE via stdio MCP
- **Latency**: <100ms pour list_templates
- **Memory**: ~4GB VRAM (Ollama + modèle)

## Fichiers Clés

| Fichier | Rôle |
|---------|------|
| `app/mcp_server.py` | Serveur MCP principal |
| `run_mcp.py` | Point d'entrée |
| `.claude/settings.local.json` | Config Claude Code |
| `requirements.txt` | Dépendances (+ `mcp`) |

## Prochaines Étapes

1. ✅ Serveur MCP de base
2. Test avec Claude Code
3. Quotas utilisateur (phase 2)
4. Intégration authentification (phase 2)
5. Distribution via package MCP registry
