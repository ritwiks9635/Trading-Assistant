from graphs.dual_pipeline import build_dual_pipeline
from core.schemas import TradingState
from dotenv import load_dotenv
from datetime import datetime, timezone
import uuid

load_dotenv()  

if __name__ == "__main__":
    user_input = input("💬 Ask something (e.g. 'I have $100, what to buy today?'):\n> ")

    pipeline = build_dual_pipeline()

    initial_state = TradingState(
        symbol="AAPL",
        user_query=user_input,
        run_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc)
    )

    raw = pipeline.invoke(initial_state)
    final_state = TradingState(**raw)

    print("\n[🤖 Assistant Response]")
    print(final_state.user_response)

    if final_state.trade_signal:
        print("\n[📊 Trade Signal]")
        print(final_state.trade_signal)

    if final_state.executed_trade:
        print("\n[✅ Executed Trade]")
        print(final_state.executed_trade)