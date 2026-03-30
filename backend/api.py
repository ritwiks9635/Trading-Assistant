import uuid
from datetime import datetime, timezone
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from graphs.dual_pipeline import build_dual_pipeline
from core.schemas import TradingState

# --- App ---
app = FastAPI(
    title="Trading Assistant API",
    description="AI-powered trading assistant backend",
    version="1.0.0"
)

# ✅ Allow React frontend (localhost:3000) to talk to FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


pipeline = build_dual_pipeline()


# --- Error Handling Middleware ---
@app.middleware("http")
async def add_error_handling(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": "Something went wrong. Please try again later."}
        )


# --- Request / Response Models ---
class ChatRequest(BaseModel):
    query: str
    symbol: str = "AAPL"


class ChatResponse(BaseModel):
    response: str


# --- REST Endpoint ---
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Single response endpoint (returns only assistant text)."""
    initial_state = TradingState(
        symbol=request.symbol,
        user_query=request.query,
        run_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc),
    )

    raw = pipeline.invoke(initial_state)
    final_state = TradingState(**raw)

    return ChatResponse(response=final_state.user_response or "")


# --- WebSocket Endpoint (streaming like ChatGPT) ---
@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            query = data.get("query")
            symbol = data.get("symbol", "AAPL")

            if not query:
                await websocket.send_json({"error": "Missing query"})
                continue

            initial_state = TradingState(
                symbol=symbol,
                user_query=query,
                run_id=str(uuid.uuid4()),
                timestamp=datetime.now(timezone.utc),
            )

            raw = pipeline.invoke(initial_state)
            final_state = TradingState(**raw)

            # --- Stream response ---
            if final_state.user_response:
                for token in final_state.user_response.split():
                    await websocket.send_json({"type": "token", "content": token})

            await websocket.send_json({
                "type": "final",
                "response": final_state.user_response or ""
            })

    except WebSocketDisconnect:
        print("🔌 Client disconnected")
    except Exception:
        await websocket.send_json({"error": "Something went wrong."})
        await websocket.close()


# --- Health Check ---
@app.get("/health")
async def health_check():
    return {"status": "ok"}
