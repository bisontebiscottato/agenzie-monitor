import hashlib, json, os, smtplib, ssl, sys
from email.message import EmailMessage
from pathlib import Path
import requests

URLS = [u.strip() for u in Path("urls.txt").read_text().splitlines() if u.strip()]
STATE = Path("hashes.json")

def sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()

def load_hashes():
    return json.loads(STATE.read_text()) if STATE.exists() else {}

def save_hashes(h):
    STATE.write_text(json.dumps(h, indent=2))

def send_alert(changed):
    msg = EmailMessage()
    msg["Subject"] = f"[Agenzie] {len(changed)} pagine cambiate"
    msg["From"]    = os.environ["MAIL_FROM"]
    msg["To"]      = os.environ["MAIL_TO"]
    msg.set_content("Cambiamenti:\n" + "\n".join(changed))
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(os.environ["SMTP_HOST"], int(os.environ["SMTP_PORT"]), context=ctx) as s:
        s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
        s.send_message(msg)

def main():
    old = load_hashes()
    new, diff = {}, []
    for url in URLS:
        try:
            html = requests.get(url, timeout=40, headers={"User-Agent":"GH-Monitor"}).content
        except Exception as e:
            print(f"Errore {url}: {e}", file=sys.stderr)
            continue
        h = sha(html)
        new[url] = h
        if old.get(url) != h:
            diff.append(url)
    if diff:
        send_alert(diff)
    save_hashes(new)

if __name__ == "__main__":
    main()
