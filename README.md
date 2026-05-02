# BoostIA

Assistant de rédaction professionnelle **100 % local**. Construit sur
[Ollama](https://ollama.com), FastAPI et un frontend HTML/JS sans framework.
Aucune donnée ne quitte la machine sur laquelle BoostIA tourne.

## Cas d'usage v1

- E-mail de relance, remerciement, refus poli, demande
- Compte-rendu de réunion à partir de notes brutes
- Message commercial bref

Trois tonalités au choix : **formel**, **neutre**, **direct**.

## Pré-requis

- Python 3.11 ou supérieur
- [Ollama](https://ollama.com/download) installé et démarré
- Un modèle téléchargé (par défaut : `qwen2.5:3b-instruct`)

```bash
ollama pull qwen2.5:3b-instruct
```

> **Choix du modèle.** Sur une carte 4 Go VRAM (RTX 3050 Ti par ex.),
> `qwen2.5:3b-instruct` (Q4) tient entièrement en VRAM et tourne
> à ~40 tokens/s. Pour gagner en qualité au prix de la vitesse, essayez
> `qwen2.5:7b-instruct` (offload partiel CPU/GPU, ~10 tokens/s).

## Démarrage rapide (développement local)

### Linux / macOS

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

### Windows (PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8000
```

L'interface est ensuite disponible sur **http://localhost:8000**.

## Démarrage avec Docker (production-like)

```bash
docker compose up --build
```

Au premier démarrage, téléchargez le modèle dans le conteneur Ollama :

```bash
docker exec -it boostia-ollama ollama pull qwen2.5:3b-instruct
```

## Architecture

```
┌────────────┐    HTTP     ┌──────────────┐    HTTP     ┌─────────┐
│ Navigateur │ ──────────▶ │ FastAPI (Py) │ ──────────▶ │ Ollama  │
│  (HTML/JS) │   /api/*    │  streaming   │ /api/chat   │ (local) │
└────────────┘   ◀────SSE──┘              ◀────────────┘         │
```

- Le frontend (HTML/JS) est **servi par FastAPI** : pas de configuration CORS
  nécessaire en local, pas de mixed-content, pas de build step.
- Le streaming **Server-Sent Events** (SSE) affiche le texte au fur et à
  mesure de la génération — le premier mot apparaît typiquement en moins
  d'une seconde, plutôt que d'attendre 15 s la fin.
- Le client LLM (`app/llm_client.py`) est volontairement isolé : pour
  remplacer Ollama par un autre moteur (vLLM, TGI, OpenAI-compatible…),
  un seul fichier à toucher.

## Structure du projet

```
BoostIA/
├── app/
│   ├── __init__.py
│   ├── main.py            # FastAPI : routes + montage du frontend
│   ├── config.py          # pydantic-settings (.env)
│   ├── llm_client.py      # client async Ollama avec streaming
│   ├── templates.py       # 6 templates métier × 3 tonalités
│   └── logging_config.py  # structlog (logs JSON)
├── web/
│   ├── index.html
│   ├── style.css
│   └── app.js             # appel SSE + rendu progressif
├── tests/
│   └── test_templates.py
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Configuration

Toutes les variables sont dans `.env` (voir `.env.example`) :

| Variable                  | Défaut                       | Description                                |
|---------------------------|------------------------------|--------------------------------------------|
| `OLLAMA_BASE_URL`         | `http://localhost:11434`     | URL d'Ollama                               |
| `MODEL_NAME`              | `qwen2.5:3b-instruct`        | Modèle utilisé                             |
| `REQUEST_TIMEOUT_SECONDS` | `120`                        | Timeout des appels Ollama                  |
| `DEFAULT_TEMPERATURE`     | `0.4`                        | Température de génération                  |
| `DEFAULT_TOP_P`           | `0.9`                        | Nucleus sampling                           |
| `LOG_LEVEL`               | `INFO`                       | `DEBUG`, `INFO`, `WARNING`, `ERROR`        |
| `CORS_ORIGINS`            | `[]`                         | Origines autorisées (JSON)                 |

## Logs

Logs JSON (via `structlog`) sur la sortie standard. Chaque génération est
tracée avec :

- `request_id` (identifiant aléatoire de 12 caractères)
- `template_id`, `tone`, `context_len`
- `output_chars`, `elapsed_seconds`

> **Confidentialité.** Aucun log ne contient le contenu du prompt
> utilisateur ni la réponse générée — seulement leurs métadonnées
> (longueur, durée). C'est un choix : pour un déploiement on-prem chez
> un client sensible, on peut garder ce comportement par défaut et offrir
> un mode "audit complet" opt-in.

## Tests

```bash
pytest
```

## Endpoints API

| Méthode | URL              | Rôle                                                                           |
|---------|------------------|--------------------------------------------------------------------------------|
| GET     | `/api/health`    | Sonde de santé + nom du modèle configuré                                       |
| GET     | `/api/templates` | Liste des templates disponibles                                                |
| POST    | `/api/generate`  | Génération streaming SSE (`{template_id, context, tone}`)                      |

### Format SSE (`/api/generate`)

```
data: {"delta": "Bonjour"}

data: {"delta": " Madame"}

event: done
data: {"output_chars": 312, "elapsed_seconds": 4.21}
```

En cas d'erreur côté modèle :

```
event: error
data: {"error": "Ollama HTTP 500: ..."}
```

## Roadmap

- **V2** : édition de templates par l'utilisateur final (UI), historique
  persistant (SQLite), export Markdown/PDF, raffinement itératif
  ("plus court", "plus formel").
- **V3** : authentification simple, multi-utilisateurs, packaging Helm chart
  pour un déploiement Kubernetes on-prem.
