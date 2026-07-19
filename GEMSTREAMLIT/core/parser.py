"""Parser delle risposte binarie di Gemini StreamGenerate"""
import json, re
from typing import Optional

class GeminiParser:
    ERROR_CODES = {
        37:   "Web search vuoto",
        1000: "Errore server",
        1050: "Query non permessa",
        1096: "Rate limit / botguard",
        1097: "Query complessa / sessione scaduta",
        1103: "Rate limit",
        1104: "Policy violation",
        1155: "Modello richiede login",
        1200: "Timeout server",
        40400:"Sessione scaduta",
    }

    @classmethod
    def parse(cls, raw: str) -> tuple[str, dict]:
        """
        Restituisce (testo_risposta, ids)
        ids = {"cid":..., "rid":..., "rcid":...}
        Lancia ValueError con messaggio leggibile in caso di errore.
        """
        text = raw.lstrip()
        if text.startswith(")]}'"):
            text = text[4:].lstrip()

        blocks = cls._extract_blocks(text)
        candidates: list[str] = []

        for b in blocks:
            try:
                parsed = json.loads(b)
                for entry in parsed:
                    if (isinstance(entry, list) and len(entry) >= 3
                            and entry[0] == "wrb.fr" and entry[2]):
                        candidates.append(entry[2])
            except Exception:
                continue

        if not candidates:
            m = re.search(r'BardErrorInfo".*?\[(\d+)\]', raw)
            if m:
                code = int(m.group(1))
                msg  = cls.ERROR_CODES.get(code, f"Errore #{code}")
                raise ValueError(f"[{code}] {msg}")
            raise ValueError("Risposta vuota dal server")

        payload = max(candidates, key=len)
        try:
            inner = json.loads(payload)
        except json.JSONDecodeError as e:
            raise ValueError(f"Payload malformato: {e}")

        ids: dict = {"cid": "", "rid": "", "rcid": ""}
        try:
            ids["cid"] = inner[1][0] or ""
            ids["rid"] = inner[1][1] or ""
        except Exception:
            pass

        try:
            cand = inner[4][0]
            ids["rcid"] = cand[0] or ""
            answer_text  = cand[1][0]

            # Detect errore mascherato
            if answer_text and answer_text.startswith("[{") and len(answer_text) < 50:
                try:
                    pt = json.loads(answer_text)
                    if isinstance(pt, list) and pt and isinstance(pt[0], dict):
                        first = pt[0]
                        if "37" in first:
                            raise ValueError("Web search vuoto")
                except json.JSONDecodeError:
                    pass

            return answer_text, ids
        except ValueError:
            raise
        except Exception:
            return json.dumps(inner, ensure_ascii=False), ids

    @staticmethod
    def _extract_blocks(text: str) -> list[str]:
        blocks: list[str] = []
        i, n = 0, len(text)
        while i < n:
            while i < n and text[i] in " \r\n\t":
                i += 1
            if i >= n:
                break
            if text[i].isdigit():
                while i < n and text[i] != "\n":
                    i += 1
                continue
            if text[i] == "[":
                depth, start = 0, i
                while i < n:
                    if   text[i] == "[": depth += 1
                    elif text[i] == "]":
                        depth -= 1
                        if depth == 0:
                            i += 1
                            blocks.append(text[start:i])
                            break
                    i += 1
            else:
                i += 1
        return blocks