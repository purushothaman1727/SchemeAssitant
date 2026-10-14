from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_embedder, get_llm, get_session, get_store
from app.core.config import get_settings
from app.core.limiter import limiter
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat import answer

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
@limiter.limit(get_settings().rate_limit_chat)
def chat(request: Request, req: ChatRequest, db: Session = Depends(get_session), store=Depends(get_store),
         embedder=Depends(get_embedder), llm=Depends(get_llm)) -> ChatResponse:
    return answer(db, store, embedder, llm, req)


@router.delete("/chat/sessions/{session_id}", status_code=204)
def delete_session(session_id: str, db: Session = Depends(get_session)) -> None:
    """Erase a stored conversation. The unguessable session id is the capability."""
    from sqlalchemy import delete

    from app.models import ChatMessage, ChatSession

    db.execute(delete(ChatMessage).where(ChatMessage.session_id == session_id))
    db.execute(delete(ChatSession).where(ChatSession.id == session_id))
    db.commit()
