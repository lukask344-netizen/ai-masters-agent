# 🤖 AI Masters Agent — Návod k nasazení

## Co agent umí

- Odpovídá na text i hlasové zprávy (v češtině)
- Posílá emaily jako info@ai-masters.eu — vždy se tě nejdřív zeptá
- Pamatuje si kontext přes konverzace (SQLite)
- Ranní briefing: `/rano`
- Ukládá si fakty: `/zapamatuj kontakt Jana = jana@klinika.cz`

---

## KROK 1 — Vytvoř Telegram bota (2 minuty)

1. Otevři Telegram, najdi **@BotFather**
2. Napiš `/newbot`
3. Zvol jméno: např. `AI Masters Agent`
4. Zvol username: např. `ai_masters_lukas_bot`
5. BotFather ti dá **token** — zkopíruj ho

Zjisti své **Telegram User ID**:
- Napiš zprávu botovi **@userinfobot**
- Zkopíruj číslo z pole `Id`

---

## KROK 2 — Claude API klíč

1. Jdi na https://console.anthropic.com
2. API Keys → Create Key
3. Zkopíruj klíč (začíná `sk-ant-`)

---

## KROK 3 — Nasazení na Railway (zdarma)

### Možnost A: Railway (doporučeno — 500 hodin/měsíc zdarma)

1. Jdi na https://railway.app a přihlas se (GitHub účet stačí)
2. **New Project** → **Deploy from GitHub repo**
3. Nahraj složku `ai_agent` na GitHub (nebo použij Railway CLI)
4. V Railway: **Variables** → přidej všechny proměnné z `.env.example`
5. Railway automaticky spustí `python main.py`

### Možnost B: Lokálně na počítači (pro test)

```bash
cd ai_agent
pip install -r requirements.txt
cp .env.example .env
# Vyplň .env svými klíči
python main.py
```

---

## KROK 4 — Vyplň .env

Přejmenuj `.env.example` na `.env` a vyplň:

| Proměnná | Kde ji získáš |
|---|---|
| `TELEGRAM_TOKEN` | @BotFather → /newbot |
| `ALLOWED_USER_ID` | @userinfobot |
| `ANTHROPIC_API_KEY` | console.anthropic.com |
| `SMTP_PASS` | heslo od Endory (info@ai-masters.eu) |
| `OPENAI_API_KEY` | platform.openai.com (volitelné, pro hlas) |

---

## Příkazy v Telegramu

| Příkaz | Co dělá |
|---|---|
| `/start` | Přivítání |
| `/rano` | Ranní briefing — co dnes dělat |
| `/reset` | Smaže konverzační historii |
| `/zapamatuj klíč = hodnota` | Uloží si fakt |

---

## Jak s agentem mluvit

**Akvizice:**
> "Napiš email 1 pro Omni Dent Clinic Praha, kontakt info@omnidentclinic.cz"

Agent navrhne email → zobrazí náhled → zeptá se ANO/NE → odešle

**Hlasová zpráva:**
Pošli hlasovku v češtině, agent přepíše a odpoví

**Paměť:**
> "/zapamatuj PRIMED Clinic = odeslán Email 1 dne 19.5.2026"

---

## Architektura souborů

```
ai_agent/
├── main.py          ← hlavní bot, Telegram handlers
├── brain.py         ← Claude claude-sonnet-4-6, systémový prompt, logika
├── memory.py        ← SQLite paměť (konverzace + fakty + akce)
├── email_agent.py   ← odesílání emailů přes SMTP
├── config.py        ← načítání .env proměnných
├── requirements.txt
├── .env.example     ← šablona pro .env
└── NAVOD.md         ← tento soubor
```
