from __future__ import annotations

import atexit
import os
import threading
from typing import AsyncIterator, Callable, Dict, Iterable, List, Optional
import time

from ..common.errors import BrokerNotRegistered
from ..common.logging import get_logger
from .interfaces import BrokerAdapter
from .models import Account, Order, OrderReplaceRequest, OrderSubmitRequest, Position, Quote

BROKER_ALPACA = "alpaca"

# Global list to track background threads for order recording
# These threads MUST complete before the process exits to ensure orders are recorded
_pending_order_threads: List[threading.Thread] = []
_threads_lock = threading.Lock()


def _cleanup_pending_threads() -> None:
    """Wait for all pending order recording threads to complete.
    
    This is registered as an atexit handler to ensure orders are recorded
    even when the script exits quickly after placing orders.
    """
    with _threads_lock:
        threads = list(_pending_order_threads)
    
    if not threads:
        return
    
    logger = get_logger()
    alive_threads = [t for t in threads if t.is_alive()]
    
    if alive_threads:
        logger.info("cpz_waiting_for_order_recording", count=len(alive_threads))
        for t in alive_threads:
            try:
                # Wait up to 10 seconds per thread for order recording to complete
                t.join(timeout=10.0)
            except Exception:
                pass
    
    # Clean up completed threads
    with _threads_lock:
        _pending_order_threads[:] = [t for t in _pending_order_threads if t.is_alive()]


# Register cleanup handler to run when Python exits
atexit.register(_cleanup_pending_threads)


def wait_for_order_recording(timeout: float = 30.0) -> int:
    """Explicitly wait for all pending order recording threads to complete.
    
    Call this at the end of your strategy script if you want to ensure
    all orders are recorded before the script exits.
    
    Args:
        timeout: Maximum time to wait in seconds (default 30s)
    
    Returns:
        Number of threads that were waited on
    """
    with _threads_lock:
        threads = list(_pending_order_threads)
    
    if not threads:
        return 0
    
    alive_threads = [t for t in threads if t.is_alive()]
    if not alive_threads:
        return 0
    
    logger = get_logger()
    logger.info("cpz_waiting_for_order_recording", count=len(alive_threads), timeout=timeout)
    
    start = time.time()
    for t in alive_threads:
        remaining = timeout - (time.time() - start)
        if remaining <= 0:
            break
        try:
            t.join(timeout=remaining)
        except Exception:
            pass
    
    # Clean up completed threads
    with _threads_lock:
        _pending_order_threads[:] = [t for t in _pending_order_threads if t.is_alive()]
    
    return len(alive_threads)


class BrokerRouter:
    _registry: Dict[str, Callable[..., BrokerAdapter]] = {}

    def __init__(self) -> None:
        self._active: Optional[BrokerAdapter] = None
        self._active_name: Optional[str] = None
        self._active_kwargs: Dict[str, object] = {}
        # Optional CPZ platform client for order logging/credentials
        self._cpz_client: object | None = None

    @classmethod
    def register(cls, name: str, factory: Callable[..., BrokerAdapter]) -> None:
        cls._registry[name] = factory

    def list_brokers(self) -> list[str]:
        return list(self._registry.keys())

    @classmethod
    def default(cls) -> "BrokerRouter":
        if BROKER_ALPACA not in cls._registry:
            try:
                from .alpaca.adapter import AlpacaAdapter

                cls.register(BROKER_ALPACA, AlpacaAdapter.create)
            except Exception:
                pass
        return cls()

    def with_cpz_client(self, cpz_client: object) -> "BrokerRouter":
        """Inject a CPZ platform client instance for use in order logging.

        If not provided, the router will fall back to CPZAIClient.from_env().
        """
        self._cpz_client = cpz_client
        return self

    def use_broker(self, name: str, **kwargs: object) -> None:
        if name not in self._registry:
            raise BrokerNotRegistered(name)
        # Normalize kwargs for adapter factories
        if "environment" in kwargs and "env" not in kwargs:
            # Accept both styles; adapters typically expect "env"
            k = dict(kwargs)
            k["env"] = k.pop("environment")
            kwargs = k  # type: ignore[assignment]
        factory = self._registry[name]
        self._active = factory(**kwargs)
        self._active_name = name
        self._active_kwargs = dict(kwargs)

    def active_selection(self) -> Optional[tuple[str, Dict[str, object]]]:
        """Return the currently selected broker name and kwargs, or None if none selected."""
        if self._active_name is None:
            return None
        return self._active_name, dict(self._active_kwargs)

    def _require_active(self) -> BrokerAdapter:
        if self._active is None:
            if len(self._registry) == 1:
                _name, factory = next(iter(self._registry.items()))
                self._active = factory()
                # Keep metadata consistent for downstream logging
                self._active_name = _name
                self._active_kwargs = {}
                return self._active
            if os.getenv("ALPACA_API_KEY_ID"):
                self.use_broker(BROKER_ALPACA, env=os.getenv("ALPACA_ENV", "paper"))
            else:
                raise BrokerNotRegistered("<none>")
        assert self._active is not None
        return self._active

    def get_account(self) -> Account:
        return self._require_active().get_account()

    def get_positions(self) -> list[Position]:
        return self._require_active().get_positions()

    def submit_order(self, req: OrderSubmitRequest) -> Order:
        from ..common.cpz_ai import CPZAIClient

        broker_name = self._active_name or BROKER_ALPACA
        env = str(self._active_kwargs.get("env") or "") or "paper"
        account_id = str(self._active_kwargs.get("account_id") or "")

        # 1) Get CPZ client and account_id for order recording (non-blocking)
        # Skip synchronous order intent creation - it causes timeouts
        # We'll record the order AFTER broker confirmation in a background thread
        sb = None
        try:
            sb = CPZAIClient.from_env()
        except ValueError as ve:
            # Re-raise credential validation errors immediately - these are critical
            raise ValueError(f"CPZ API credentials validation failed: {ve}") from ve
        except Exception:
            # CPZ client unavailable - order will still be placed but not tracked
            pass
        
        # Get account_id if not provided
        if not account_id:
            try:
                account = self._require_active().get_account()
                account_id = getattr(account, "id", None) or getattr(account, "account_id", None) or ""
            except Exception:
                account_id = ""

        # 2) Send to broker FIRST - this is the priority
        order = self._require_active().submit_order(req)
        
        # 3) Record order in background thread (non-blocking)
        # This prevents API timeouts from slowing down order placement
        def record_order_async():
            try:
                if sb is None:
                    return
                order_status = getattr(order, "status", None) or "pending"
                if order_status.lower() not in ["pending", "filled", "canceled", "partially_filled", "accepted"]:
                    order_status = "pending"
                sb.record_order(
                    order_id=order.id,
                    symbol=req.symbol,
                    side=req.side.value,
                    qty=req.qty,
                    type=req.type.value,
                    time_in_force=req.time_in_force.value,
                    broker=broker_name,
                    env=env,
                    strategy_id=getattr(req, "strategy_id", ""),
                    status=order_status,
                    filled_at=(
                        getattr(order, "filled_at", None).isoformat()
                        if getattr(order, "filled_at", None)
                        else None
                    ),
                    account_id=account_id,
                )
            except Exception as exc:
                logger = get_logger()
                logger.warning("background_order_record_failed", error=str(exc))
        
        # Start background thread for order recording
        # IMPORTANT: daemon=False so thread completes even if main thread exits
        # Thread is tracked in _pending_order_threads so atexit handler can wait for it
        record_thread = threading.Thread(target=record_order_async, daemon=False)
        with _threads_lock:
            _pending_order_threads.append(record_thread)
        record_thread.start()
        
        # Skip the old intent-based logic since we now record directly after broker confirmation
        intent = None

        # Order recording is now handled in the background thread above
        # No synchronous API calls needed here - order already submitted to broker

        # 4) Optional background polling to sync fills (non-blocking)
        # This ensures order status and fills are kept in sync with broker
        def poll_order_status():
            try:
                poll_total = int(os.getenv("CPZ_POLL_TOTAL_SECONDS", "60"))
                poll_interval = float(os.getenv("CPZ_POLL_INTERVAL_SECONDS", "2"))
                enable_poll = os.getenv("CPZ_ENABLE_FILL_POLLING", "true").lower() != "false"
                if not enable_poll or poll_total <= 0:
                    return
                
                deadline = time.time() + poll_total
                while time.time() < deadline:
                    try:
                        cur = self._require_active().get_order(order.id)
                        # Check if order reached terminal state
                        if str(getattr(cur, "status", "")).lower() in {
                            "filled",
                            "canceled",
                            "partially_filled",
                        }:
                            # Update final status in database
                            if sb is not None:
                                sb.record_order(
                                    order_id=cur.id,
                                    symbol=req.symbol,
                                    side=req.side.value,
                                    qty=req.qty,
                                    type=req.type.value,
                                    time_in_force=req.time_in_force.value,
                                    broker=broker_name,
                                    env=env,
                                    strategy_id=getattr(req, "strategy_id", ""),
                                    status=getattr(cur, "status", "filled"),
                                    filled_at=(
                                        getattr(cur, "filled_at", None).isoformat()
                                        if getattr(cur, "filled_at", None)
                                        else None
                                    ),
                                    account_id=account_id,
                                )
                            break
                        time.sleep(poll_interval)
                    except Exception:
                        break
            except Exception:
                pass
        
        # Start polling in background thread (non-blocking)
        threading.Thread(target=poll_order_status, daemon=True).start()

        return order

    def get_order(self, order_id: str) -> Order:
        return self._require_active().get_order(order_id)

    def cancel_order(self, order_id: str) -> Order:
        return self._require_active().cancel_order(order_id)

    def replace_order(self, order_id: str, req: OrderReplaceRequest) -> Order:
        return self._require_active().replace_order(order_id, req)

    def stream_quotes(self, symbols: Iterable[str]) -> AsyncIterator[Quote]:
        active = self._require_active()
        return active.stream_quotes(symbols)

    # --- Data passthroughs ---
    def get_quotes(self, symbols: list[str]) -> list[Quote]:
        return self._require_active().get_quotes(symbols)

    def get_historical_data(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
        start: Optional[object] = None,
        end: Optional[object] = None,
    ) -> list[object]:
        # Types align with BrokerAdapter; keep signature flexible for call sites
        return self._require_active().get_historical_data(symbol, timeframe, limit, start, end)
