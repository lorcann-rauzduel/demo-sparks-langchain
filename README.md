# Assistant d'entreprise avec LangChain

Un assistant qui répond aux questions des employés à partir des documents de l'entreprise, consulte une base de tickets, agit après validation et se souvient de chaque utilisateur. Un même cœur sert plusieurs canaux : le terminal, Discord et une API web.

Ce dépôt est **un exemple d'implémentation**, pas la seule façon de faire. Chaque brique repose sur un mécanisme de LangChain ou de LangGraph, rangée dans une architecture ports et adaptateurs pour pouvoir changer de modèle, de base ou de canal sans toucher au reste. On peut le reprendre tel quel, en garder une partie, ou s'en servir comme référence pour son propre projet.

## Les fonctionnalités

| Fonctionnalité | Ce qu'elle fait | Mécanisme | Fichier |
|---|---|---|---|
| Agent | Le modèle choisit lui-même ses outils | `create_agent` | `adapters/agent/company_agent.py` |
| Recherche dans les documents (RAG) | Répond à partir des documents, avec leurs sources | Chroma, outil `response_format="content_and_artifact"` | `adapters/agent/tools/search_company_documents.py` |
| Refus | « I don't know. » quand les documents ne répondent pas, sans source | Prompt système et règle du cœur | `application/assistant.py` |
| Base métier | Lit un ticket du support, en lecture seule | SQLite `mode=ro` | `adapters/agent/tools/tickets.py` |
| Mémoire court terme | Garde la conversation ; `/new` en ouvre une vierge | Checkpointer, un `thread_id` par conversation | `bootstrap.py` |
| Mémoire long terme | Retient les faits durables d'un utilisateur, d'une conversation à l'autre | Store, `ToolRuntime`, `dynamic_prompt` | `adapters/agent/tools/save_user_fact.py` |
| Résumé | Remplace les anciens messages par un résumé au-delà d'un seuil | `SummarizationMiddleware` | `adapters/agent/company_agent.py` |
| Réponse en continu | Affiche la réponse mot par mot | `stream_mode="messages"` | `adapters/agent/langchain_generator.py` |
| Validation humaine | Met l'agent en pause avant une action ; l'utilisateur valide ou refuse | `HumanInTheLoopMiddleware` | `adapters/agent/company_agent.py` |
| Droits par rôle | Retire l'outil `close_ticket` à qui n'est pas du support | Middleware `wrap_model_call`, contexte d'exécution | `adapters/agent/tools_for_role.py` |
| Limite d'appels | Au plus N appels au modèle par question | `ModelCallLimitMiddleware` | `adapters/agent/company_agent.py` |
| Canaux | Terminal, Discord (boutons de validation), API web | Points d'entrée Python, discord.py, FastAPI | `entrypoints/` |
| Traces | Chaque appel au modèle et aux outils, étape par étape | LangSmith | variables `LANGSMITH_*` |
| Évaluation | Un jeu de cas, un évaluateur, un score comparable d'un lancement à l'autre | `langsmith.Client.evaluate` | `entrypoints/evaluate.py` |

Les deux actions de l'agent sont des exemples : `submit_leave_request` est fictive et n'écrit nulle part, `close_ticket` modifie la base SQLite locale.

## Démarrer

Il faut Python 3.12 ou plus récent, et [uv](https://docs.astral.sh/uv/).

```bash
uv sync
cp .env.example .env
```

Dans `.env`, renseigner `GROQ_API_KEY` (clé gratuite sur [console.groq.com](https://console.groq.com/keys)). Pour un autre fournisseur, voir [Changer de modèle](#changer-de-modèle).

Indexer les documents de `corpus/`, une fois, puis après chaque changement de document :

```bash
uv run --env-file .env assistant-index
```

Lancer l'assistant dans le terminal :

```bash
uv run --env-file .env assistant terminal
```

À essayer :

| Question | Ce qu'elle montre |
|---|---|
| Quel est le plafond pour un repas ? | La réponse tirée des documents, suivie de ses sources |
| Quel est le salaire d'un consultant ? | Le refus, sans source |
| Où en est le ticket 4 ? puis Et sa priorité ? | La base métier, puis la mémoire de la conversation |
| Je travaille au bureau de Lyon. puis `/new`, puis Dans quelle ville est mon bureau ? | La mémoire long terme |
| Pose mes congés du 21 au 24 décembre 2026 | La validation humaine : répondre `o` ou `n` |
| Ferme le ticket 2 | Une action réservée au support (`SUPPORT_USERS`) |

Ligne vide pour quitter.

## Les canaux

Un canal traduit entre une plateforme et le cœur. Tous appellent le même cas d'usage, `Assistant`, avec un identifiant d'utilisateur préfixé par le canal (`terminal`, `discord:123`, `api:alice`).

### Terminal

```bash
uv run --env-file .env assistant terminal
```

`TERMINAL_STREAMING=off` affiche la réponse d'un bloc au lieu du flux.

### Discord

Le bot répond à tout message privé, et sur un serveur aux messages qui le mentionnent (`@NomDuBot ta question`). Quand l'agent veut agir, il affiche deux boutons, **Valider** et **Refuser**, que seul l'auteur de la demande peut cliquer.

1. **Un serveur de test.** Dans Discord, **+** dans la colonne de gauche, **Créer le mien**, puis **Pour moi et mes amis**.
2. **L'application.** Sur [discord.com/developers/applications](https://discord.com/developers/applications), **New Application**, un nom, puis **Create**. Ce nom est celui du bot.
3. **Le jeton.** Menu **Bot**, section **Token**, **Reset Token**, puis copier le jeton dans `.env`, ligne `DISCORD_TOKEN`. Discord ne l'affiche qu'une fois. Le jeton ne va jamais dans le code ni dans git ; s'il fuite, refaire **Reset Token**.
4. **L'invitation.** Menu **Installation** : cocher **Guild Install**, choisir **Discord Provided Link**, et dans **Default Install Settings** ajouter le scope `bot` et les permissions **View Channels** et **Send Messages**. Enregistrer, ouvrir l'**Install Link**, choisir le serveur de test, puis **Autoriser**.
5. **Lancer.**

   ```bash
   uv run --env-file .env assistant discord
   ```

   Le terminal affiche `Bot Discord connecté : NomDuBot#1234`, et le bot passe en ligne sur le serveur.

Le bot utilise les intents par défaut. Discord lui donne le texte des messages privés et des mentions sans l'intent privilégié **Message Content**, qu'il n'est donc pas nécessaire d'activer. Pour qu'un compte Discord ait le rôle support, ajouter `discord:<son identifiant>` à `SUPPORT_USERS` (l'identifiant se copie avec un clic droit sur le nom, après avoir activé le **Mode développeur** dans les paramètres avancés de Discord).

### API web

Renseigner `API_KEY` dans `.env`, avec une valeur longue et aléatoire, par exemple `openssl rand -hex 32`. Puis :

```bash
uv run --env-file .env assistant api
```

La documentation interactive est sur [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs). Chaque requête envoie la clé dans l'en-tête `X-API-Key` ; sans elle, l'API répond 401 avant tout appel au modèle.

```bash
curl -X POST http://127.0.0.1:8000/ask -H 'Content-Type: application/json' -H "X-API-Key: $API_KEY" \
  -d '{"user_id": "alice", "question": "Que faire en cas d erreur ERR-4012 ?"}'
```

```json
{"answer": "The ERR-4012 error means the VPN certificate on your device has expired…", "sources": ["securite.md"], "actions_to_approve": []}
```

Quand `actions_to_approve` n'est pas vide, l'agent attend une décision :

```bash
curl -X POST http://127.0.0.1:8000/decide -H 'Content-Type: application/json' -H "X-API-Key: $API_KEY" \
  -d '{"user_id": "alice", "approved": true}'
```

Pour rendre l'API accessible depuis une autre machine pendant un test, un tunnel suffit : `ngrok http 8000` ou `cloudflared tunnel --url http://localhost:8000`.

## Ajouter un canal

D'autres interfaces s'ajoutent facilement, comme Telegram, Slack, WhatsApp ou une page web, sans toucher au cœur. Un canal est un module dans `entrypoints/` avec une fonction `run(assistant, settings)`, déclaré par une ligne dans `pyproject.toml` :

```toml
[project.entry-points."assistant.channels"]
mon_canal = "assistant.entrypoints.mon_canal:run"
```

Le module reçoit un message, appelle `assistant.answer(user_id, question)`, puis affiche l'`Answer` ou demande la décision sur une `ActionToApprove` avec `assistant.decide(user_id, approved)`. `assistant.stream(...)` donne la réponse en continu. Le terminal (`entrypoints/terminal.py`) est le canal le plus court à prendre pour modèle. Ensuite :

```bash
uv sync
uv run --env-file .env assistant mon_canal
```

## Ajouter un outil

1. Une fonction décorée par `@tool` dans `adapters/agent/tools/`, avec une docstring qui dit **quand** l'appeler : c'est elle que le modèle lit pour choisir.
2. L'ajouter à la liste `tools` de `build_company_agent`, dans `adapters/agent/company_agent.py`.
3. Si l'outil agit, ajouter son nom à `interrupt_on` de `HumanInTheLoopMiddleware` ; s'il est réservé à un rôle, à `SUPPORT_ONLY_TOOLS` dans `adapters/agent/tools_for_role.py`.
4. Une ligne dans `prompts/system_prompt.md` si le modèle a besoin d'une consigne pour l'utiliser.

## Les traces LangSmith

LangSmith enregistre chaque appel : la question, les appels au modèle, les outils appelés avec leurs arguments et leurs résultats, le résumé, les tokens et la durée. C'est le premier endroit où regarder quand une réponse est fausse.

1. Créer un compte sur [smith.langchain.com](https://smith.langchain.com), puis **Settings**, **API Keys**, **Create API Key**.
2. Dans `.env` :

   ```bash
   LANGSMITH_TRACING=true
   LANGSMITH_API_KEY=lsv2_...
   LANGSMITH_PROJECT=company-assistant
   # Compte créé dans la région Europe seulement :
   # LANGSMITH_ENDPOINT=https://eu.api.smith.langchain.com
   ```

3. Relancer un canal et poser une question. La trace apparaît dans **Tracing**, projet `company-assistant`.

Aucune ligne de code n'est nécessaire : LangChain lit ces variables et envoie les traces lui-même. Pour partager une trace, l'ouvrir puis cliquer sur **Share** ; le lien est public, vérifier qu'il ne contient rien de confidentiel.

## L'évaluation

Le jeu de cas est dans `evaluation/cases.json` : une question et le texte attendu dans la réponse. Avec les traces LangSmith activées :

```bash
uv run --env-file .env assistant-evaluate
```

Au premier lancement, le dataset `company-assistant` est créé dans LangSmith. Chaque lancement devient une expérience, qu'on compare aux précédentes dans **Datasets & Experiments**. Chaque cas part d'un utilisateur neuf, pour qu'aucune mémoire ne passe d'un cas à l'autre.

Résultat observé le 26/11 : 4 cas sur 5. Le cas raté, le délai de pose des congés, répond 15 jours au lieu de 10 : la recherche a remonté la politique de 2025 au lieu de celle de 2026. C'est le genre d'échec que l'évaluation sert à trouver ; on le corrige par exemple en filtrant les documents par version.

Après une modification du jeu de cas, supprimer le dataset dans LangSmith, ou changer `EVALUATION_DATASET`, pour qu'il soit recréé.

## La configuration

Tous les réglages sont dans `.env` ; `.env.example` donne leurs valeurs par défaut.

| Variable | Rôle |
|---|---|
| `LLM_MODEL` | Le modèle, sous la forme `fournisseur:modèle` |
| `SYSTEM_PROMPT_FILE` | Le prompt système, versionné avec le code |
| `MAX_QUESTION_LENGTH` | Au-delà, la question est refusée sans appeler le modèle |
| `CORPUS_DIR`, `INDEX_DIR`, `EMBEDDING_MODEL`, `CHUNK_SIZE`, `CHUNK_OVERLAP`, `PASSAGES_PER_SEARCH` | Les documents et leur index |
| `TICKETS_DB`, `TICKETS_SEED` | La base des tickets, créée depuis `data/tickets.sql` si elle n'existe pas |
| `SUPPORT_USERS` | Les identifiants qui ont le rôle support, séparés par des virgules |
| `MODEL_CALL_LIMIT` | Le nombre maximum d'appels au modèle par question |
| `SUMMARY_TRIGGER_TOKENS`, `MESSAGES_KEPT_AFTER_SUMMARY` | Le seuil du résumé, et les messages gardés tels quels |
| `DISCORD_TOKEN` | Le jeton du bot Discord |
| `API_KEY`, `API_HOST`, `API_PORT` | L'API web |
| `TERMINAL_STREAMING` | `off` pour afficher la réponse d'un bloc |
| `LANGSMITH_*` | Les traces |

### Changer de modèle

`LLM_MODEL` accepte tout modèle reconnu par `init_chat_model`, avec le paquet d'intégration du fournisseur :

| Fournisseur | `LLM_MODEL` | Paquet | Clé |
|---|---|---|---|
| Groq | `groq:openai/gpt-oss-120b` | déjà installé | `GROQ_API_KEY` |
| Ollama, en local | `ollama:qwen3.5:0.8b` | déjà installé | aucune |
| Mistral | `mistralai:mistral-small-latest` | `uv add langchain-mistralai` | `MISTRAL_API_KEY` |
| OpenAI | `openai:<nom du modèle>` | `uv add langchain-openai` | `OPENAI_API_KEY` |
| Anthropic | `anthropic:claude-sonnet-5-5` | `uv add langchain-anthropic` | `ANTHROPIC_API_KEY` |

Un petit modèle local appelle mal les outils : il convient pour essayer, moins pour la validation humaine et les droits.

### En production

Les mémoires sont en mémoire vive : elles disparaissent au redémarrage. Dans `bootstrap.py`, remplacer `InMemorySaver` par `PostgresSaver` et `InMemoryStore` par `PostgresStore` (paquet `langgraph-checkpoint-postgres`). Les rôles viennent d'une liste dans `.env` ; en production, ils viendraient de l'annuaire de l'entreprise, par un autre adaptateur du port `UserRoles`.

## L'architecture

Ports et adaptateurs, rangés comme dans *Architecture Patterns with Python* (Percival et Gregory). Le cœur ne connaît ni LangChain, ni Discord, ni FastAPI : on peut changer de framework d'agent ou de canal sans le toucher.

```
src/assistant/
├── domain/                          les objets du cœur, sans framework
│   ├── answer.py                    Answer (texte + sources), Token, ActionToApprove
│   └── user.py                      User (identifiant + rôle)
├── application/                     le cas d'usage : aucun import de LangChain ni de Discord
│   ├── assistant.py                 Assistant : answer, stream, decide, et les règles avant le modèle
│   └── ports/                       ce dont le cas d'usage a besoin, décrit par son rôle
│       ├── answer_generator.py
│       ├── conversation_registry.py
│       └── user_roles.py
├── adapters/                        implémentent les ports (adaptateurs secondaires)
│   ├── agent/
│   │   ├── chat_model.py            le modèle, choisi par son nom
│   │   ├── company_agent.py         create_agent : le modèle, ses outils et ses middlewares
│   │   ├── agent_context.py         le contexte d'exécution : utilisateur et rôle
│   │   ├── tools_for_role.py        le middleware des droits
│   │   ├── tools/
│   │   │   ├── search_company_documents.py
│   │   │   ├── tickets.py           get_ticket_status, close_ticket
│   │   │   ├── save_user_fact.py    la mémoire long terme
│   │   │   └── submit_leave_request.py
│   │   └── langchain_generator.py   traduit les messages LangChain en objets du cœur
│   ├── conversations/in_memory.py   la conversation en cours de chaque utilisateur
│   ├── documents/chroma_index.py    la base vectorielle : indexer, ouvrir
│   ├── tickets/sqlite_tickets.py    la base métier
│   └── users/configured_roles.py    les rôles, lus dans les réglages
├── entrypoints/                     appellent le cas d'usage (adaptateurs primaires)
│   ├── terminal.py
│   ├── discord_bot/                 bot.py, approval.py (les boutons), messages.py
│   ├── web_api/                     app.py (FastAPI), server.py (uvicorn)
│   ├── index_documents.py           la commande assistant-index
│   ├── evaluate.py                  la commande assistant-evaluate
│   └── message_format.py            la réponse, puis ses sources
├── config/                          les réglages lus dans .env, un fichier par composant
├── bootstrap.py                     racine de composition : le seul endroit qui assemble
└── __main__.py                      la commande assistant : choisit le canal et le lance
```

- Les dépendances vont vers l'intérieur : `application/` ne connaît que `domain/` et ses ports ; les adaptateurs implémentent les ports ; `bootstrap.py` les assemble.
- L'identifiant et le rôle de l'utilisateur viennent du code, par le contexte d'exécution de l'agent, jamais du modèle ni du texte de la question.
- Un fichier, une responsabilité. `tests/` reprend la même arborescence.

## Tests

```bash
uv run pytest                                # le cœur, les canaux et les réglages, sans réseau
uv run --env-file .env pytest -m groq        # l'agent, avec le vrai modèle Groq
uv run ruff check . && uv run mypy src tests
```
