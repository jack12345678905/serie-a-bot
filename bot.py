import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz
import certifi
import os

# === CONFIG ===
URL = "https://www.legaseriea.it/it/serie-a/calendario-e-risultati"

#TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
#TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
TELEGRAM_TOKEN = "8073099493:AAGtjmpjExCpRWXlrJiKeohtldZocPipGS8"
TELEGRAM_CHAT_ID = "-4679117538"
def get_matches():
    try:
        # Prima prova con certificati ufficiali
        r = requests.get(URL, timeout=20, verify=certifi.where())
    except requests.exceptions.SSLError:
        print("⚠️ Errore SSL, passo a verify=False (non sicuro).")
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        r = requests.get(URL, timeout=20, verify=False)

    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    matches = []
    rome_tz = pytz.timezone("Europe/Rome")

    for row in soup.select(".match-row"):
        try:
            home = row.select_one(".team-home .team-name").get_text(strip=True)
            away = row.select_one(".team-away .team-name").get_text(strip=True)

            dt_str = row.select_one(".match-info time")["datetime"]  # esempio: 2025-09-02T18:00:00
            dt_utc = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            dt_local = dt_utc.astimezone(rome_tz)

            matches.append({
                "date": dt_local.strftime("%A %d/%m/%Y"),
                "time": dt_local.strftime("%H:%M"),
                "home": home,
                "away": away
            })
        except Exception as e:
            print("Errore parsing riga:", e)

    return matches

def build_message(matches):
    if not matches:
        return "⚽ Nessuna partita trovata."
    lines = ["📅 *Prossime partite Serie A*"]
    for m in matches:  # solo le prime 10 per non allungare troppo
        lines.append(f"{m['date']} {m['time']} — {m['home']} vs {m['away']}")
    return "\n".join(lines)

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        # Primo tentativo: con certificati ufficiali
        r = requests.post(url, data=payload, timeout=20, verify=certifi.where())
        r.raise_for_status()
        return r.json()
    except requests.exceptions.SSLError:
        print("⚠️ Errore SSL, riprovo senza verifica certificato...")
        # Secondo tentativo: senza verifica SSL (non sicuro, ma funziona)
        r = requests.post(url, data=payload, timeout=20, verify=False)
        r.raise_for_status()
    return r.json()

if __name__ == "__main__":
    print("TOKEN:", TELEGRAM_TOKEN)
    print("CHAT_ID:", TELEGRAM_CHAT_ID)
    partite = get_matches()
    msg = build_message(partite)
    print(msg)  # debug console
    send_telegram(msg)
