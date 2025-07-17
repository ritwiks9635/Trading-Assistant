from graphs.dual_pipeline import build_dual_pipeline
from core.schemas import TradingState
from dotenv import load_dotenv
from datetime import datetime, timezone
import uuid
import json

load_dotenv()

def debug_dump_state(state: TradingState):
    print("\n[🧠 Full Final State Debug]")
    try:
        print(json.dumps(state.model_dump(), indent=2, default=str))
    except Exception as e:
        print(f"[ERROR dumping state]: {e}")
        print(state)

if __name__ == "__main__":
    user_input = input("💬 Ask something (e.g. 'I have $100, what to buy today?'):\n> ")

    pipeline = build_dual_pipeline()

    initial_state = TradingState(
        symbol="AAPL",
        user_query=user_input,
        run_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc),
    )

    print("[⚙️  Executing pipeline...]\n")
    raw = pipeline.invoke(initial_state)
    final_state = TradingState(**raw)

    print("\n[🤖 Assistant Response]")
    print(final_state.user_response or "[None / Empty Response]")

    if final_state.trade_signal:
        print("\n[📊 Trade Signal]")
        print(final_state.trade_signal)

    if final_state.executed_trade:
        print("\n[✅ Executed Trade]")
        print(final_state.executed_trade)

    debug_dump_state(final_state)
