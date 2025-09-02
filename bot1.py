import requests
from datetime import datetime, timedelta
import pytz
import certifi
import os
from babel.dates import format_datetime

API_KEY = os.environ.get("API_KEY")
BASE_URL = "https://api.football-data.org/v4/competitions/SA/matches"
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

ROME_TZ = pytz.timezone("Europe/Rome")

def get_upcoming_matches(season: int):
    headers = {"X-Auth-Token": API_KEY}
    params = {"season": season}
    try:
        # Prima prova con certificati ufficiali
        r = requests.get(BASE_URL, headers=headers, params=params, timeout=20, verify = certifi.where())
    except requests.exceptions.SSLError:
        print("⚠️ Errore SSL, passo a verify=False (non sicuro).")
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        r = requests.get(BASE_URL, timeout=20, verify=False)
        print(r.status_code)
    print(r.text)
    data = r.json()

    matches = []
    for m in data.get("matches", []):
        if m["status"] != "TIMED":  # solo partite future
            continue
        home = m["homeTeam"]["shortName"]
        away = m["awayTeam"]["shortName"]
        dt_utc = datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00"))
        dt_local = dt_utc.astimezone(ROME_TZ)
        formatted = format_datetime(dt_local, "EEEE dd/MM/yyyy", locale='it')

        matches.append({
            "date": formatted,                                         #dt_local.strftime("%A %d/%m/%Y")
            "time": dt_local.strftime("%H:%M"),
            "home": home,
            "away": away
        })

    return matches

def build_message(partite, stagione):
    dt_now = datetime.now()
    delta =  timedelta(days = 11)
    f_date = dt_now + delta
    formatted_now = format_datetime(f_date, "EEEE dd/MM/yyyy", locale='it')
    if partite and partite[1]['date'] == formatted_now :
        lines = [f" RICORDATI LA FORMAZIONE\n\n 📅 Prossime partite Serie A {stagione}/{stagione+1}: \n"]
        for m in partite[:10]:
            lines.append(f"{m['date']} {m['time']} — {m['home']} vs {m['away']}")
        return "\n".join(lines)
    return "⚽ Nessuna partita futura trovata."

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
    r = requests.post(url, data=payload)
    r.raise_for_status()
    return r.json()

if __name__ == "__main__":
    stagione = 2025
    partite = get_upcoming_matches(stagione)
    msg = build_message(partite, stagione)
    print(msg)  # debug console
    send_telegram(msg)
