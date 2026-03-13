#!/usr/bin/env python3
"""
retry.py — Retry decorator and Circuit Breaker for Business Agents Platform.

Usage:

    from agent_runtime.retry import with_retry, CircuitBreaker

    @with_retry(max_attempts=3, backoff_seconds=2)
    def call_sap_api(endpoint, payload):
        ...

    cb = CircuitBreaker(failure_threshold=3, reset_timeout=300)
    result = cb.call(call_sap_api, endpoint, payload)

with_retry:
    Retries the decorated function on any exception.
    Backoff is exponential: attempt 1 waits backoff_seconds,
    attempt 2 waits backoff_seconds * 2, etc.
    After max_attempts the last exception is re-raised.

CircuitBreaker:
    Tracks consecutive failures. After failure_threshold failures the
    circuit opens and CircuitOpenError is raised immediately without
    calling the wrapped function. The circuit resets after reset_timeout
    seconds have elapsed since the last failure. State is persisted in
    agent-runtime/circuit_state.json so it survives process restarts.

Both components log their behaviour to agent-runtime/retry.log.
"""

from __future__ import annotations

import functools
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional, TypeVar

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

RUNTIME_DIR     = os.path.dirname(os.path.abspath(__file__))
RETRY_LOG       = os.path.join(RUNTIME_DIR, "retry.log")
CIRCUIT_STATE   = os.path.join(RUNTIME_DIR, "circuit_state.json")

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

_handler = logging.FileHandler(RETRY_LOG)
_handler.setFormatter(logging.Formatter("%(asctime)s [RETRY] %(levelname)s %(message)s"))
_stdout_handler = logging.StreamHandler(sys.stdout)
_stdout_handler.setFormatter(logging.Formatter("%(asctime)s [RETRY] %(levelname)s %(message)s"))

_log = logging.getLogger("retry")
_log.setLevel(logging.INFO)
if not _log.handlers:
    _log.addHandler(_handler)
    _log.addHandler(_stdout_handler)

# ---------------------------------------------------------------------------
# Circuit Breaker state helpers
# ---------------------------------------------------------------------------

def _load_circuit_state() -> Dict[str, Any]:
    if os.path.exists(CIRCUIT_STATE):
        try:
            with open(CIRCUIT_STATE) as fh:
                return json.load(fh)
        except Exception:
            pass
    return {}


def _save_circuit_state(state: Dict[str, Any]) -> None:
    try:
        with open(CIRCUIT_STATE, "w") as fh:
            json.dump(state, fh, indent=2)
    except Exception as exc:
        _log.error("Could not persist circuit state: %s", exc)


# ---------------------------------------------------------------------------
# with_retry decorator
# ---------------------------------------------------------------------------

F = TypeVar("F", bound=Callable[..., Any])


def with_retry(max_attempts: int = 3, backoff_seconds: float = 2.0) -> Callable[[F], F]:
    """Decorator factory that adds retry-with-exponential-backoff to a function.

    Parameters
    ----------
    max_attempts:
        Total number of attempts (including the first call).
    backoff_seconds:
        Base wait time in seconds. Wait doubles on each retry.
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exc: Optional[Exception] = None
            for attempt in range(1, max_attempts + 1):
                try:
                    result = func(*args, **kwargs)
                    if attempt > 1:
                        _log.info(
                            "Function '%s' succeeded on attempt %d/%d.",
                            func.__name__, attempt, max_attempts,
                        )
                    return result
                except Exception as exc:
                    last_exc = exc
                    wait = backoff_seconds * (2 ** (attempt - 1))
                    if attempt < max_attempts:
                        _log.warning(
                            "Function '%s' failed on attempt %d/%d: %s. "
                            "Retrying in %.1f s...",
                            func.__name__, attempt, max_attempts, exc, wait,
                        )
                        time.sleep(wait)
                    else:
                        _log.error(
                            "Function '%s' failed after %d attempt(s): %s. "
                            "Giving up.",
                            func.__name__, max_attempts, exc,
                        )
            raise last_exc  # type: ignore[misc]
        return wrapper  # type: ignore[return-value]
    return decorator


# ---------------------------------------------------------------------------
# CircuitBreaker
# ---------------------------------------------------------------------------

class CircuitOpenError(Exception):
    """Raised when a CircuitBreaker is open and the call is blocked."""


class CircuitBreaker:
    """Simple circuit breaker with file-backed state persistence.

    Parameters
    ----------
    name:
        Unique identifier for this circuit (defaults to 'default').
    failure_threshold:
        Number of consecutive failures that trips the circuit.
    reset_timeout:
        Seconds after the last failure before the circuit closes again.
    """

    def __init__(
        self,
        name: str = "default",
        failure_threshold: int = 3,
        reset_timeout: float = 300.0,
    ) -> None:
        self.name              = name
        self.failure_threshold = failure_threshold
        self.reset_timeout     = reset_timeout

    # --- State accessors ---

    def _get_state(self) -> Dict[str, Any]:
        all_state = _load_circuit_state()
        return all_state.get(self.name, {"failures": 0, "last_failure_ts": None, "open": False})

    def _set_state(self, state: Dict[str, Any]) -> None:
        all_state = _load_circuit_state()
        all_state[self.name] = state
        _save_circuit_state(all_state)

    # --- Public API ---

    @property
    def is_open(self) -> bool:
        state = self._get_state()
        if not state.get("open", False):
            return False
        # Check if reset_timeout has elapsed since last failure
        last_ts = state.get("last_failure_ts")
        if last_ts is None:
            return False
        elapsed = time.time() - last_ts
        if elapsed >= self.reset_timeout:
            _log.info(
                "Circuit '%s' reset after %.0f s (threshold=%d s).",
                self.name, elapsed, self.reset_timeout,
            )
            self._reset()
            return False
        return True

    def _record_failure(self) -> None:
        state = self._get_state()
        state["failures"]        = state.get("failures", 0) + 1
        state["last_failure_ts"] = time.time()
        if state["failures"] >= self.failure_threshold:
            state["open"] = True
            _log.warning(
                "Circuit '%s' opened after %d consecutive failure(s).",
                self.name, state["failures"],
            )
        else:
            _log.warning(
                "Circuit '%s' failure %d/%d.",
                self.name, state["failures"], self.failure_threshold,
            )
        self._set_state(state)

    def _record_success(self) -> None:
        state = self._get_state()
        if state.get("failures", 0) > 0:
            _log.info("Circuit '%s' success — resetting failure count.", self.name)
        self._reset()

    def _reset(self) -> None:
        self._set_state({"failures": 0, "last_failure_ts": None, "open": False})

    def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Call *func* through the circuit breaker.

        Raises CircuitOpenError if the circuit is currently open.
        """
        if self.is_open:
            state = self._get_state()
            elapsed = time.time() - (state.get("last_failure_ts") or 0)
            remaining = max(0.0, self.reset_timeout - elapsed)
            raise CircuitOpenError(
                f"Circuit '{self.name}' is open. "
                f"Retry in {remaining:.0f}s."
            )
        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as exc:
            self._record_failure()
            raise
