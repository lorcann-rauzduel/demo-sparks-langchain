"""Canal API web : une application FastAPI qui appelle le cas d'usage, comme les autres canaux."""

import secrets

from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.concurrency import run_in_threadpool
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

from assistant.application.assistant import Assistant
from assistant.domain.answer import ActionToApprove, Answer


class Question(BaseModel):
    user_id: str
    question: str


class Decision(BaseModel):
    user_id: str
    approved: bool


class Reply(BaseModel):
    answer: str
    sources: list[str]
    actions_to_approve: list[str]  # non vide : l'agent attend une décision, envoyée à POST /decide


def create_app(assistant: Assistant, api_key: str) -> FastAPI:
    api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

    # Sans clé ou avec une mauvaise clé : 401, avant tout appel au modèle
    def check_api_key(key: str | None = Security(api_key_header)) -> None:
        if key is None or not secrets.compare_digest(key, api_key):
            raise HTTPException(status_code=401, detail="Invalid or missing API key")

    app = FastAPI(title="Assistant LangChain", dependencies=[Depends(check_api_key)])

    @app.post("/ask")
    async def ask(request: Question) -> Reply:
        # Le cas d'usage est synchrone : il tourne hors de la boucle du serveur, qui reste disponible
        result = await run_in_threadpool(assistant.answer, api_user(request.user_id), request.question)
        return to_reply(result)

    @app.post("/decide")
    async def decide(request: Decision) -> Reply:
        # La décision reprend la conversation en pause de cet utilisateur
        result = await run_in_threadpool(assistant.decide, api_user(request.user_id), request.approved)
        return to_reply(result)

    return app


def api_user(user_id: str) -> str:
    # Préfixe du canal : un même identifiant sur deux canaux reste deux utilisateurs
    return f"api:{user_id}"


def to_reply(result: Answer | ActionToApprove) -> Reply:
    if isinstance(result, ActionToApprove):
        return Reply(answer="", sources=[], actions_to_approve=list(result.actions))
    return Reply(answer=result.text, sources=list(result.sources), actions_to_approve=[])
