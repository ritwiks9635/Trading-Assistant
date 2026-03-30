from __future__ import annotations
from typing import Any, Iterable, Optional
from core.schemas import TradingState
from model.model import model
from utils.logger import log_info, log_error
from state.shared_state import shared_state


# -------------------------------
# Utility Helpers (Safe & Stable)
# -------------------------------

def _safe_get(obj: Any, key: str, default=None):
    try:
        if obj is None:
            return default
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)
    except Exception:
        return default


def _fmt_currency(x: Optional[float]) -> str:
    try:
        if x is None:
            return "N/A"
        return f"${float(x):,.2f}"
    except Exception:
        return "N/A"


def _fmt_pct(x: Optional[float], mult100_if_ratio: bool = True) -> str:
    try:
        if x is None:
            return "N/A"
        v = float(x)
        if mult100_if_ratio and abs(v) < 1:
            v *= 100
        return f"{round(v, 2)}%"
    except Exception:
        return "N/A"


def _join(parts: Iterable[str]) -> str:
    return " ".join(p.strip() for p in parts if p and str(p).strip())


# ----------------------------
# ETF Fallback Detection
# ----------------------------

def _is_etf_fallback(movers) -> bool:
    if not movers:
        return False
    etf_symbols = {"SPY", "QQQ", "VOO"}
    return all((_safe_get(m, "symbol") or "").upper() in etf_symbols for m in movers)


# ----------------------------
# Format Blocks
# ----------------------------

def _format_top_movers(movers) -> Optional[str]:
    if not movers:
        return None
    lines = []
    try:
        for m in movers[:6]:
            name = getattr(m, "name", None) or _safe_get(m, "symbol", "")
            symbol = (_safe_get(m, "symbol", "") or "").upper()
            price = _safe_get(m, "price")
            pct = _safe_get(m, "percent_change")

            if not symbol:
                continue

            lines.append(
                f"{name} ({symbol}) ~ {_fmt_currency(price)} ({_fmt_pct(pct, mult100_if_ratio=False)})"
            )
    except Exception:
        return None

    return "; ".join(lines) if lines else None


# ----------------------------
# 🔥 NEW: Deterministic Fundamental Answer
# ----------------------------

def _build_fundamental_response(stock) -> Optional[str]:
    if not stock:
        return None

    symbol = _safe_get(stock, "symbol", "")
    price = _safe_get(stock, "price")
    pe = _safe_get(stock, "pe_ratio")
    eps = _safe_get(stock, "eps")
    cap = _safe_get(stock, "market_cap")

    parts = []

    if symbol:
        parts.append(f"{symbol} is currently trading at {_fmt_currency(price)}.")

    if pe:
        parts.append(f"It has a P/E ratio of {round(float(pe), 2)}.")

    if eps:
        parts.append(f"Earnings per share (EPS) is {round(float(eps), 2)}.")

    if cap:
        parts.append(f"Market capitalization stands at {_fmt_currency(cap)}.")

    return _join(parts) if parts else None


def _build_stock_block(stock) -> Optional[str]:
    if not stock:
        return None

    get = stock.get if isinstance(stock, dict) else lambda k: getattr(stock, k, None)

    parts = []
    symbol = get("symbol")
    price = get("price")
    pe = get("pe_ratio")

    if symbol:
        parts.append(f"{symbol} is trading near {_fmt_currency(price)}.")
    if pe:
        parts.append(f"P/E {round(float(pe), 2)}.")

    return _join(parts) if parts else None


# ----------------------
# Global Report Node
# ----------------------

def report_node(state: TradingState) -> TradingState:
    try:
        if not isinstance(state, TradingState):
            raise TypeError("report_node expects TradingState")

        query = (state.user_query or "").strip()
        intent = getattr(state, "intent", None)

        movers = getattr(state, "top_movers", None)
        stock = getattr(state, "stock_insight", None)

        # ==============================
        # ✅ 1️⃣ TOP MOVERS (Deterministic)
        # ==============================
        if intent == "top_movers" and movers:
            movers_text = _format_top_movers(movers)

            if _is_etf_fallback(movers):
                state.user_response = (
                    "Live market movers are temporarily unavailable. "
                    "Using major ETFs as a proxy: "
                    f"{movers_text}"
                )
                return state

            if movers_text:
                state.user_response = movers_text
                return state

        # ==============================
        # ✅ 2️⃣ FUNDAMENTAL LOOKUP (NEW FIX)
        # ==============================
        if intent == "fundamental_lookup" and stock:
            response = _build_fundamental_response(stock)
            if response:
                state.user_response = response
                log_info("[ReportNode] Fundamental response served.")
                return state

        # ==============================
        # ✅ 3️⃣ STOCK INSIGHT FALLBACK
        # ==============================
        if stock:
            basic = _build_stock_block(stock)
            if basic:
                state.user_response = basic
                log_info("[ReportNode] Basic stock response served.")
                return state

        # ==============================
        # ✅ 4️⃣ LLM (LAST RESORT ONLY)
        # ==============================
        prompt = f"""
You are a professional financial analyst.
Provide a concise, factual response.

User Query: {query}
"""

        try:
            response = model.generate_content(prompt)
            text = getattr(response, "text", "").strip()

            if text:
                state.user_response = text
                return state
        except Exception as e:
            log_error(f"[ReportNode] LLM failed: {e}")

        # ==============================
        # ✅ 5️⃣ FINAL FALLBACK (NEVER EMPTY)
        # ==============================
        state.user_response = (
            "Relevant market data is currently limited. "
            "Please refine your query or try again shortly."
        )
        return state

    except Exception as e:
        log_error(f"[ReportNode] Critical Failure: {e}")
        state.user_response = "System error while generating response."
        return state