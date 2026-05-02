# BoostIA

Assistant de rédaction professionnelle **100 % local**. Construit sur
[Ollama](https://ollama.com), FastAPI et un frontend HTML/JS sans framework.
Aucune donnée ne quitte la machine sur laquelle BoostIA tourne.

## Installation

### Option 1 : .EXE (Windows) — Plus simple

1. Téléchargez BoostIA depuis [GitHub Releases](https://github.com/votre-repo/BoostIA/releases)
2. Extrayez le `.zip`
3. Double-cliquez sur `BoostIA.exe`
4. Ollama doit être installé et le modèle `phi4` téléchargé

### Option 2 : Script d'installation (Windows)

1. Clonez ou téléchargez ce repo
2. Double-cliquez sur `setup.bat`
3. Suivez les instructions à l'écran

### Option 3 : Depuis les sources (développeurs)

```powershell
# Clonez le repo
git clone https://github.com/votre-repo/BoostIA.git
cd BoostIA

# Création environnement virtuel
python -m venv .venv
.venv\Scripts\Activate.ps1

# Installation dépendances
pip install -r requirements.txt
copy .env.example .env

# Téléchargement du modèle
ollama pull phi4

# Lancement
uvicorn app.main:app --port 8000
```

Ouvrez ensuite **http://localhost:8000**

## Pré-requis

- **Ollama** installé et démarré (https://ollama.com)
- **phi4** téléchargé automatiquement par setup ou manuellement :
  ```bash
  ollama pull phi4
  ```

> **Configuration matérielle recommandée** : RTX 3050 Ti (4 Go VRAM) ou plus.
> Le modèle `phi4` tourne correctement sur 4 Go VRAM (~2s premier token).

## Modèles disponibles

| Modèle | Taille | Performance |
|-------|--------|-------------|
| `phi4` (défaut) | ~7B | ~2s premier token, qualité française excellente |
| `qwen2.5:3b-instruct` | ~2B | Plus rapide mais qualité moindre |

Pour changer de modèle, modifiez `.env` :
```ini
MODEL_NAME=qwen2.5:3b-instruct
```

## Cas d'usage

22 templates disponibles :

- **E-mails pro** : relance, remerciement, refus poli, demande, premier contact, excuse, confirmation, annulation, négociation, feedback
- **Documents** : bio professionnelle, lettre de motivation, description de poste
- **Marketing** : message commercial, post LinkedIn, réponse avis client
- **Interne** : annonce équipe
- **Productivité** : compte-rendu de réunion, compacter un texte
- **Perso** : message à un proche, message rapide, liste de courses

Trois tonalités : **formel**, **neutre**, **direct**.

## Architecture

```
┌────────────┐    HTTP     ┌──────────────┐    HTTP     ┌─────────┐
│ Navigateur │ ──────────▶ │ FastAPI (Py) │ ──────────▶ │ Ollama  │
│  (HTML/JS) │   /api/*    │  streaming   │ /api/chat   │ (local) │
└────────────┘   ◀────SSE──┘              ◀────────────┘         │
```

## Structure du projet

```
BoostIA/
├── app/
│   ├── main.py            # FastAPI : routes + montage frontend
│   ├── config.py          # pydantic-settings (.env)
│   ├── llm_client.py     # client async Ollama
│   ├── templates.py      # 22 templates métier
│   └── history.py       # historique SQLite
├── web/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── setup.bat            # Installateur automatique
├── build.bat           # Construction .exe
└── requirements.txt
```

## Configuration

Variables dans `.env` :

| Variable | Défaut | Description |
|----------|-------|-------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | URL Ollama |
| `MODEL_NAME` | `phi4` | Modèle utilisé |
| `REQUEST_TIMEOUT_SECONDS` | `120` | Timeout |
| `DEFAULT_TEMPERATURE` | `0.4` | Température |

## API

| Méthode | URL | Rôle |
|--------|-----|------|
| GET | `/api/health` | Santé + modèle |
| GET | `/api/templates` | Liste templates |
| POST | `/api/generate` | Génération SSE |

## Construire le .EXE (développeurs)

```bash
.venv\Scripts\activate.bat
pip install pyinstaller
pyinstaller boostia.spec
```

Le `.exe` sera dans `dist/BoostIA.exe`

## Confidentialité

100 % local. Aucune donnée ne quitte votre machine. Les logs ne contiennent que des métadonnées (durée, taille), jamais le contenu des prompts ou réponses.

## License

MIT — Libre d'utilisation et de modification.