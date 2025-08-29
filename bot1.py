import requests
from datetime import datetime
import pytz
import certifi

API_KEY = "b9f6ee5f94374112b9db3319f129a49f"
BASE_URL = "https://api.football-data.org/v4/competitions/SA/matches"
TELEGRAM_TOKEN = "8073099493:AAGtjmpjExCpRWXlrJiKeohtldZocPipGS8"
TELEGRAM_CHAT_ID = "-1003068867218"

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
        if m["status"] != "SCHEDULED":  # solo partite future
            continue
        home = m["homeTeam"]["name"]
        away = m["awayTeam"]["name"]
        dt_utc = datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00"))
        dt_local = dt_utc.astimezone(ROME_TZ)

        matches.append({
            "date": dt_local.strftime("%A %d/%m/%Y"),
            "time": dt_local.strftime("%H:%M"),
            "home": home,
            "away": away
        })

    return matches

def build_message(partite, stagione):
    if not partite:
        return "⚽ Nessuna partita futura trovata."
    lines = [f"📅 Prossime partite Serie A {stagione}/{stagione+1}:"]
    for m in partite[:10]:
        lines.append(f"{m['date']} {m['time']} — {m['home']} vs {m['away']}")
    return "\n".join(lines)

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
