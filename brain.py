"""
Mozek agenta — komunikace s Claude claude-sonnet-4-6.
Zpracovává zprávy, rozhoduje o akcích, sestavuje systémový prompt.
"""
import json, datetime
import anthropic
import config
import memory

client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

SYSTEM_PROMPT = f"""Jsi {config.AGENT_NAME}, osobní AI asistent Lukáše Kadlečka.

IDENTITA A KONTEXT:
- Lukáš buduje byznys {config.OWNER_BUSINESS}
- Prodává AI agenty firmám — primární segment: {config.OWNER_SEGMENT}
- Cíl: {config.OWNER_GOAL}
- Emailová adresa pro akvizici: info@ai-masters.eu

TVOJE ROLE:
- Jsi Lukášův pravá ruka — komunikuješ VŽDY v češtině, stručně a jasně
- Pamatuješ si kontext z předchozích rozhovorů
- Pomáháš s akvizicí klinik (estetické kliniky, zubní centra, laser kliniky v CZ a SK)
- Připomínáš důležité úkoly a termíny
- Navrhujete akce (emaily, vyhledávání prospektů) — ale VŽDY čekáš na schválení

PRAVIDLA AKCÍ (CRITICAL):
- Než pošleš email nebo provedeš jakoukoli akci navenek, VŽDY nejdřív popiš co chceš udělat
- Nikdy neodesílej email bez explicitního "ANO" nebo "pošli" od Lukáše
- Po schválení použij funkci send_email

EMAILOVÁ SEKVENCE (3 kroky pro kliniky):
1. Email 1 — Profit Script (pondělí): diagnostika mrtvé zóny, ztráta ~200 000 Kč/7 500 EUR/měs
2. Email 2 — Value Drop (středa): Harvardská studie, 400% pokles konverzí
3. Email 3 — Break-up (pátek): exkluzivita pro region, síla odnětí

STYL KOMUNIKACE:
- Krátké, konkrétní odpovědi — Lukáš mluví z telefonu nebo auta
- Žádné zbytečné omluvy nebo vycpávky
- Pokud mluvíš o penězích, vždy uveď čísla (Kč nebo EUR)
- Navrhuj konkrétní další krok, neptej se obecně "jak mohu pomoci"

DOSTUPNÉ AKCE (odpověz JSON blokem pokud chceš akci provést):
{{"action": "send_email", "to": "email@klinika.cz", "subject": "...", "body": "..."}}
{{"action": "remind_me", "text": "...", "when": "zitra rano"}}
{{"action": "search_prospect", "query": "estetická klinika Praha"}}
"""

def build_facts_context() -> str:
    facts = memory.all_facts()
    if not facts:
        return ""
    lines = [f"- {k}: {v}" for k, v in facts.items()]
    return "\n\nPAMATUJI SI:\n" + "\n".join(lines)

def think(user_message: str) -> tuple[str, dict | None]:
    """
    Pošle zprávu Claudovi a vrátí (text_odpovědi, action_nebo_None).
    Pokud agent chce provést akci, vrátí ji jako dict pro schválení.
    """
    memory.save_message("user", user_message)
    history = memory.get_history(limit=30)

    system = SYSTEM_PROMPT + build_facts_context()
    system += f"\n\nDNES JE: {datetime.datetime.now().strftime('%A %d.%m.%Y %H:%M')}"

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system,
        messages=history
    )

    raw = response.content[0].text
    memory.save_message("assistant", raw)

    # Zkontroluj jestli agent chce provést akci (JSON blok)
    action = _extract_action(raw)
    if action:
        # Odstraň JSON z textu pro čistší zobrazení
        text = raw.replace(_find_json_block(raw), "").strip()
    else:
        text = raw

    return text, action

def _find_json_block(text: str) -> str:
    import re
    match = re.search(r'\{[^}]+\}', text, re.DOTALL)
    return match.group(0) if match else ""

def _extract_action(text: str) -> dict | None:
    block = _find_json_block(text)
    if not block:
        return None
    try:
        data = json.loads(block)
        if "action" in data:
            return data
    except Exception:
        pass
    return None

def morning_briefing() -> str:
    """Generuje ranní briefing pro Lukáše."""
    prompt = """Vygeneruj stručný ranní briefing pro Lukáše. Zahrň:
1. Dnešní prioritu (akvizice klinik — co poslat, komu)
2. Připomenutí emailové sekvence (komu dnes patří Den 1 / Den 3 / Den 5)
3. Motivační větu Architekta ze skriptu
Buď konkrétní, stručný. Max 5 vět."""

    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    )
    return resp.content[0].text
