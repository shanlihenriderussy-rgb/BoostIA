# BoostIA — Sécurité et protection du matériel

Ce document décrit les contrôles de sécurité et de protection des ressources mis en place dans BoostIA, et ceux à appliquer côté système (Windows + Ollama).

## 1. Contrôles côté application (déjà implémentés)

### 1.1 Concurrence limitée
Une seule génération à la fois (`MAX_CONCURRENT_GENERATIONS=1`). Si une 2e requête arrive pendant qu'une 1re est en cours, l'API renvoie une erreur 503 propre après 2 s d'attente. Évite de saturer la VRAM/CPU.

### 1.2 Rate limit par IP
10 générations / minute / IP par défaut (`RATE_LIMIT_PER_MINUTE=10`). Protège contre les boucles accidentelles et les abus. Sliding window en mémoire, sans dépendance externe.

### 1.3 Auth Bearer optionnelle
Si la variable `API_KEY` est définie dans `.env`, toute requête à `/api/generate` doit envoyer `Authorization: Bearer <key>`. Désactivée par défaut (usage local strict).

### 1.4 Logs sans contenu
Les logs JSON ne stockent **jamais** le prompt ni la réponse. Uniquement métadonnées : `request_id`, `client_ip`, `template_id`, `context_len`, `output_chars`, `elapsed_seconds`.

### 1.5 Validation des entrées
- `context` borné à 8000 caractères (Pydantic)
- Validation des `template_id` et `tone` avant traitement (échec rapide)
- Headers de réponse durcis : `Cache-Control`, `X-Content-Type-Options: nosniff`

---

## 2. Contrôles côté système (à appliquer une fois)

### 2.1 Binding sur localhost uniquement

**À vérifier** : uvicorn et Ollama doivent écouter uniquement sur `127.0.0.1`, pas sur `0.0.0.0` (= toutes les interfaces réseau, exposé au LAN).

```powershell
# uvicorn : par défaut bind 127.0.0.1, donc OK
uvicorn app.main:app --host 127.0.0.1 --port 8000

# Vérifier qui écoute sur les ports BoostIA
Get-NetTCPConnection -LocalPort 8000,11434 -ErrorAction SilentlyContinue |
  Select-Object LocalAddress,LocalPort,State,OwningProcess
```

`LocalAddress` doit être `127.0.0.1` ou `::1` (IPv6 localhost). Si vous voyez `0.0.0.0`, c'est exposé au réseau.

### 2.2 Pare-feu Windows

Bloquer explicitement les ports 8000 et 11434 en entrée depuis le réseau (en plus du binding localhost = défense en profondeur).

```powershell
# Règles bloquantes (à exécuter en PowerShell admin)
New-NetFirewallRule -DisplayName "Block BoostIA inbound 8000" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Block
New-NetFirewallRule -DisplayName "Block Ollama inbound 11434" -Direction Inbound -LocalPort 11434 -Protocol TCP -Action Block
```

Pour supprimer plus tard :
```powershell
Remove-NetFirewallRule -DisplayName "Block BoostIA inbound 8000"
Remove-NetFirewallRule -DisplayName "Block Ollama inbound 11434"
```

### 2.3 Configuration Ollama (préserve VRAM et thermique)

Ces variables d'environnement doivent être définies **avant de lancer Ollama** (donc avant que le service démarre au boot, ou en relançant le service).

```powershell
# Décharger le modèle après 5 min d'inactivité (libère la VRAM)
[System.Environment]::SetEnvironmentVariable('OLLAMA_KEEP_ALIVE', '5m', 'User')

# Une seule inférence en parallèle (évite saturation GPU)
[System.Environment]::SetEnvironmentVariable('OLLAMA_NUM_PARALLEL', '1', 'User')

# Pas de file d'attente longue (rejette si occupé)
[System.Environment]::SetEnvironmentVariable('OLLAMA_MAX_QUEUE', '2', 'User')
```

Puis **redémarrer Ollama** (clic droit sur l'icône lama dans la barre des tâches → Quit, puis relancer).

Vérifier la prise en compte :
```powershell
[System.Environment]::GetEnvironmentVariable('OLLAMA_KEEP_ALIVE','User')
```

### 2.4 Plan d'alimentation Windows

Pour un laptop, basculer en plan **Équilibré** (pas Performances élevées) limite la chauffe et l'usure batterie pendant les longues générations :

```powershell
# Lister les plans
powercfg /list
# Activer Équilibré (GUID standard)
powercfg /setactive 381b4222-f694-41f0-9685-ff5bb260df2e
```

### 2.5 Surveillance température GPU (recommandé)

Pendant les premières heures d'utilisation, gardez un œil sur la température GPU. Outils gratuits :

- **HWiNFO64** (https://www.hwinfo.com) — capteurs détaillés, gratuit
- **GPU-Z** (https://www.techpowerup.com/gpuz/) — léger, juste l'essentiel
- Ou simplement le Gestionnaire des tâches Windows : onglet **Performances → GPU 0**

Cible : la 3050 Ti reste en sécurité jusqu'à ~85 °C. Si vous voyez régulièrement >80 °C en génération soutenue, sortir le PC d'un sac, surélever le clavier, dépoussiérer les ventilations.

---

## 3. Variables d'environnement BoostIA (`.env`)

Ajout de 4 nouvelles variables pour la sécurité :

```ini
# Concurrence et rate limit
MAX_CONCURRENT_GENERATIONS=1
RATE_LIMIT_PER_MINUTE=10

# Auth optionnelle (vide = désactivée)
API_KEY=

# Ollama keep-alive (envoyé via env var au service Ollama lui-même)
OLLAMA_KEEP_ALIVE=5m
```

---

## 4. Ce qui n'a PAS été implémenté (et pourquoi)

- **HTTPS local** : sur localhost, sans intérêt (pas d'écoute réseau).
- **Sandboxing du process Python** : sur Windows, complexité disproportionnée pour un usage local. Les protections OS (UAC, antivirus) sont déjà en place.
- **Filtre PII avant envoi cloud** : utile uniquement si vous activez Ollama Cloud. À implémenter en V2 si besoin.
- **Audit logging détaillé** : on logge les métadonnées, pas le contenu. Suffisant tant que vous êtes l'unique utilisateur. Pour du multi-user, à étendre.

---

## 5. Si vous activez Ollama Cloud (rappel)

Activer un modèle `*-cloud` envoie vos prompts aux serveurs Ollama (US). Les contrôles ci-dessus ne protègent **pas** vos données dans ce cas — ils protègent uniquement votre matériel et l'accès local. Pour de vraies données client, restez en local. Pour des tests perso ou démos sur données fictives, le cloud est OK.
