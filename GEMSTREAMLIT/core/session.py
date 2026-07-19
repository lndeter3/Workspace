"""Session state thread-safe in memoria (niente file su Streamlit Cloud)"""
import threading, time, random
from dataclasses import dataclass, field

@dataclass
class SessionState:
    cid:   str = ""
    rid:   str = ""
    rcid:  str = ""
    at:    str = ""
    bl:    str = ""
    fsid:  str = ""
    reqid: int = field(default_factory=lambda: random.randint(100_000, 900_000))
    turn:  int = 0
    toxic: bool = False
    web_search: bool = False
    last_query_time: float = 0.0
    last_fail_time:  float = 0.0
    consecutive_fast: int  = 0

class SessionManager:
    """Gestione sessioni multiple (una per utente Streamlit via session_id)"""
    _lock  = threading.Lock()
    _store: dict[str, SessionState] = {}

    THROTTLE   = 2.5
    MAX_TURNS  = 40
    RESET_EVERY = 8

    @classmethod
    def get(cls, sid: str) -> SessionState:
        with cls._lock:
            if sid not in cls._store:
                cls._store[sid] = SessionState()
            return cls._store[sid]

    @classmethod
    def reset_ids(cls, state: SessionState) -> None:
        state.cid = state.rid = state.rcid = ""
        state.toxic = False
        state.turn = 0

    @classmethod
    def throttle(cls, state: SessionState) -> float:
        """Ritorna i secondi di attesa necessari (già applica sleep)."""
        now   = time.time()
        elapsed = now - state.last_query_time
        if state.consecutive_fast >= 5:
            wait = min(3.0 + state.consecutive_fast * 0.5, 10.0)
        elif now - state.last_fail_time < 60:
            wait = 5.0
        else:
            wait = cls.THROTTLE

        remaining = max(0.0, wait - elapsed)
        if remaining > 0 and state.last_query_time > 0:
            time.sleep(remaining)

        state.last_query_time = time.time()
        if elapsed < 3.0:
            state.consecutive_fast += 1
        else:
            state.consecutive_fast = max(0, state.consecutive_fast - 1)
        return remaining

    @classmethod
    def pre_turn(cls, state: SessionState) -> None:
        state.turn += 1
        if state.turn % cls.RESET_EVERY == 0 and state.cid:
            cls.reset_ids(state)
        if state.turn > cls.MAX_TURNS:
            cls.reset_ids(state)