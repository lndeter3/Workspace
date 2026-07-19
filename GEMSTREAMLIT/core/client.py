"""GeminiClient ultra-ottimizzato per FastAPI/Streamlit."""
import re, json, random, time
from urllib.parse import quote
from curl_cffi import requests as cffi_requests

from .parser  import GeminiParser
from .prompt  import PromptEngineer
from .session import SessionState, SessionManager

class GeminiClient:
    UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
          "AppleWebKit/537.36 (KHTML, like Gecko) "
          "Chrome/131.0.0.0 Safari/537.36")
    BASE     = "https://gemini.google.com"
    APP      = "https://gemini.google.com/app"
    STREAM   = ("https://gemini.google.com/_/BardChatUi/data/"
                "assistant.lamda.BardFrontendService/StreamGenerate")
    COOKIE   = ("SOCS=CAESNggeEixib3FfYXNzaXN0YW50LWJhcmQtd2ViLXNlcnZlcl8yMDI2"
                "MDcwOS4wOV9wMBoCaXQgARoGCICyy9IG")
    TIMEOUT_BOOT = 15
    TIMEOUT_CHAT = 35

    def __init__(self):
        self._http = self._make_http()

    def _make_http(self) -> cffi_requests.Session:
        s = cffi_requests.Session(impersonate="chrome131")
        s.headers.update({
            "user-agent":      self.UA,
            "accept":          "*/*",
            "accept-language": "it-IT,it;q=0.9,en;q=0.8",
            "origin":          self.BASE,
            "referer":         self.BASE + "/",
            "x-same-domain":   "1",
        })
        s.cookies.update({"SOCS": self.COOKIE})
        return s

    # ------------------------------------------------------------------ #
    #  Bootstrap                                                           #
    # ------------------------------------------------------------------ #
    def bootstrap(self, state: SessionState) -> None:
        """Aggiorna bl / at / fsid nella state. Lancia su errore."""
        r = self._http.get(self.APP, timeout=self.TIMEOUT_BOOT)
        r.raise_for_status()
        html = r.text
        for name, attr in [("FdrFJe","fsid"), ("cfb2h","bl"), ("SNlM0e","at")]:
            m = re.search(rf'"{name}"\s*:\s*"([^"]+)"', html)
            if m:
                setattr(state, attr, m.group(1))
        if not state.bl:
            raise RuntimeError("Bootstrap: bl mancante (possibile CAPTCHA)")

    # ------------------------------------------------------------------ #
    #  Chat                                                                #
    # ------------------------------------------------------------------ #
    def chat(
        self,
        message:        str,
        state:          SessionState,
        use_engineer:   bool = True,
        force_complete: bool = True,
    ) -> tuple[str, list[str]]:
        """
        Ritorna (risposta_pulita, enhancements_tags).
        Gestisce throttle, session-reset e retry automatici.
        """
        # 1. Throttle adattivo
        SessionManager.throttle(state)
        SessionManager.pre_turn(state)

        # 2. Prompt Engineering
        original = message
        if use_engineer:
            message, tags = PromptEngineer.enhance(message)
        else:
            tags = []

        # 3. Retry loop
        last_err: Exception | None = None
        sess_reset = False

        for attempt in range(4):
            try:
                answer = self._send(message, state)
                answer = PromptEngineer.clean_response(answer)

                if force_complete:
                    answer = self._maybe_continue(original, answer, state)

                return answer, tags

            except ValueError as e:
                msg = str(e)
                # 1097 → reset sessione e riprova
                if "1097" in msg and not sess_reset:
                    SessionManager.reset_ids(state)
                    sess_reset = True
                    continue
                # 1096 → rate limit duro
                if "1096" in msg:
                    state.last_fail_time = time.time()
                    raise RuntimeError("Rate limit. Attendi 15-30 min.") from e
                raise RuntimeError(msg) from e

            except Exception as e:
                last_err = e
                if attempt < 3:
                    time.sleep(1)
                    continue
                break

        raise RuntimeError(f"Tentativi esauriti: {last_err}")

    # ------------------------------------------------------------------ #
    #  Internals                                                           #
    # ------------------------------------------------------------------ #
    def _send(self, message: str, state: SessionState) -> str:
        state.reqid += 100_000
        params = {
            "bl":      state.bl,
            "f.sid":   state.fsid or "-1",
            "hl":      "it",
            "_reqid":  str(state.reqid),
            "rt":      "c",
        }
        body = self._build_body(message, state)
        r = self._http.post(
            self.STREAM,
            params=params,
            data=body,
            headers={"content-type":
                     "application/x-www-form-urlencoded;charset=UTF-8"},
            timeout=self.TIMEOUT_CHAT,
        )
        if r.status_code != 200:
            raise ValueError(f"HTTP {r.status_code}")

        text, ids = GeminiParser.parse(r.text)
        # Aggiorna IDs nella state
        state.cid  = ids["cid"]  or state.cid
        state.rid  = ids["rid"]  or state.rid
        state.rcid = ids["rcid"] or state.rcid
        return text

    def _build_body(self, message: str, state: SessionState) -> str:
        msg_part = [message, 0, None, None, None, None, 0]
        ids_part = [state.cid, state.rid, state.rcid,
                    None, None, None, None, None, None, ""]
        inner  = [msg_part, ["it"], ids_part]
        outer  = [None, json.dumps(inner, ensure_ascii=False)]
        body   = "f.req=" + quote(json.dumps(outer, ensure_ascii=False), safe="")
        if state.at:
            body += "&at=" + quote(state.at, safe="")
        return body

    LIST_RE = re.compile(
        r'\b(\d{2,})\s+(?:titoli|giochi|film|libri|nomi|esempi|idee|cose|elementi|'
        r'items?|prodotti|canzoni|album|serie|prompt|domande|risposte)',
        re.IGNORECASE,
    )

    def _maybe_continue(
        self, original: str, answer: str, state: SessionState
    ) -> str:
        m = self.LIST_RE.search(original)
        if not m:
            return answer
        requested = int(m.group(1))
        if requested < 10:
            return answer

        found: set[int] = set()
        for mm in re.finditer(r'(?:^|\n)\s*(\d{1,4})[.\)]\s', answer):
            found.add(int(mm.group(1)))

        actual = max((x for x in found if x <= requested), default=0)
        if actual == 0 or actual >= requested * 0.85:
            return answer

        missing = requested - actual
        cont = (f"Continua dal numero {actual+1} fino al {requested}. "
                f"NON ripetere, solo i {missing} mancanti.")
        try:
            additional = self._send(cont, state)
            additional = PromptEngineer.clean_response(additional)
            return answer.rstrip() + "\n\n" + additional.strip()
        except Exception:
            return answer