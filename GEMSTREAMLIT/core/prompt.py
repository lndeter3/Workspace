"""Prompt Engineer + Response Cleaner — ported from gemini.py v13"""
import re

class PromptEngineer:
    LINKS_KW = ["link","url","sito","website","canale","channel","youtube","yt",
                "spotify","twitch","instagram","tiktok","facebook","twitter",
                "x.com","reddit","github","download","scarica"]
    RECENT_KW = ["oggi","ora","adesso","questa settimana","questo mese","stasera",
                 "recente","ultimo","nuovo","attuale","corrente","appena",
                 "today","now","recent","latest","current","this week"]
    LIST_RE   = re.compile(
        r'\b(\d{2,})\s+(?:titoli|giochi|film|libri|nomi|esempi|idee|cose|elementi|'
        r'items?|prodotti|canzoni|album|serie|prompt|domande|risposte|errori|bug|'
        r'problemi|miglioramenti|suggerimenti|fix|link|url|siti)',
        re.IGNORECASE
    )
    CLEAN_PATTERNS = [
        r'\n*A proposito, per sbloccare le funzionalità.*?\)\.',
        r'\n*Per sbloccare tutte le funzionalità.*?\)\.',
        r'\n*Nota: non posso inserire link esterni.*?\.',
        r'\n*\*Nota: non posso.*?\*',
        r'\n*http://googleusercontent\.com/[a-z_]+/\d+',
        r'\n*\*Nota: [^*]{5,200}\*',
        r'\n*Vuoi qualche consiglio su [^?]*\?',
        r'\n*Hai bisogno di aiuto per [^?]*\?',
        r'\n*Buon ascolto!',
        r'\n*Buona visione!',
    ]

    @classmethod
    def enhance(cls, prompt: str) -> tuple[str, list[str]]:
        low = prompt.lower()
        enhanced = prompt
        tags: list[str] = []

        # cleanup pipe markdown dalla UI
        if "| *" in prompt or "| -" in prompt:
            cleaned = re.sub(r'\|\s*\*\*|\|\s*\*|\|\s*-', '-', prompt)
            cleaned = cleaned.replace("|", "").strip()
            items = [l.strip("- *").strip()
                     for l in cleaned.split("\n") if l.strip().startswith(("-","*"))]
            enhanced = ("Riguardo questi elementi:\n" +
                        "\n".join(f"- {i}" for i in items) +
                        "\n\nDammi quello che ho chiesto in modo dettagliato."
                        if items else cleaned)
            tags.append("cleanup_markdown")
            low = enhanced.lower()

        # link → forza URL reali
        if any(k in low for k in cls.LINKS_KW):
            hint = (
                "\n\nIMPORTANTE - REQUISITI OBBLIGATORI PER I LINK:\n"
                "1. Cerca ATTIVAMENTE sul web i link ufficiali\n"
                "2. Fornisci URL COMPLETI e FUNZIONANTI (https://...)\n"
                "3. NON usare placeholder tipo 'cerca su youtube'\n"
                "4. NON scrivere 'non posso inserire link esterni'\n"
                "5. Formato Markdown: [Titolo](URL)\n"
            )
            enhanced += hint
            tags.append("web_links")

        # info recenti → forza web search
        elif any(k in low for k in cls.RECENT_KW):
            enhanced = ("Cerca sul web informazioni AGGIORNATE e VERIFICATE:\n\n"
                        + enhanced)
            tags.append("web_recent")

        # lista N elementi
        m = cls.LIST_RE.search(prompt)
        if m:
            n = int(m.group(1))
            if 10 <= n <= 200 and "esattamente" not in low:
                enhanced += (
                    f"\n\nREQUISITO: Fornisci ESATTAMENTE {n} elementi "
                    f"numerati da 1 a {n}. Non troncare, non scusarti."
                )
                tags.append(f"list_{n}")

        return enhanced, tags

    @classmethod
    def clean_response(cls, text: str) -> str:
        if not text:
            return text
        for pat in cls.CLEAN_PATTERNS:
            text = re.sub(pat, "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()