import hashlib, json, os, smtplib, ssl, requests
from email.message import EmailMessage
from pathlib import Path
from bs4 import BeautifulSoup

PAGES = json.loads(Path("pages.json").read_text())
STATE = Path("hashes.json")

def sha(x: bytes) -> str: return hashlib.sha256(x).hexdigest()

def load():  return json.loads(STATE.read_text()) if STATE.exists() else {}
def save(h): STATE.write_text(json.dumps(h, indent=2))

def fetch_hash(url, sel):
    html = requests.get(url, timeout=40, headers={"User-Agent": "GH-Monitor"}).text
    soup = BeautifulSoup(html, "lxml")
    node = soup.select_one(sel) if sel else soup
    content = node.get_text(" ", strip=True)
    return sha(content.encode())

def main():
    old, new, changed = load(), {}, []
    for item in PAGES:
        url, sel = item["url"], item.get("selector")
        try:
            h = fetch_hash(url, sel)
        except Exception as e:
            print(f"⚠️  {url} → {e}")
            continue
        new[url] = h
        if old.get(url) != h:
            changed.append(url)

    if changed:
        send_mail(changed)
    save(new)

def send_mail(urls):
    msg = EmailMessage()
    msg["Subject"] = f"[Agenzie] {len(urls)} pagine cambiate"
    msg["From"]    = os.environ["MAIL_FROM"]
    msg["To"]      = os.environ["MAIL_TO"]
    msg.set_content("Cambiamenti:\n" + "\n".join(urls))
    with smtplib.SMTP_SSL(os.environ["SMTP_HOST"], int(os.environ["SMTP_PORT"]), context=ssl.create_default_context()) as s:
        s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
        s.send_message(msg)

if __name__ == "__main__":
    main()