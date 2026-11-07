import subprocess
import re
import sys
import os
import httpx
import time

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

def main():
    cloudflared_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "cloudflared.exe"))
    print(f"Starting Cloudflare tunnel with {cloudflared_path} to http://127.0.0.1:8001 ...")
    
    proc = subprocess.Popen(
        [cloudflared_path, "tunnel", "--url", "http://127.0.0.1:8001"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    tunnel_url = None
    url_regex = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")

    for line in iter(proc.stdout.readline, ''):
        print(line, end="")
        match = url_regex.search(line)
        if match:
            tunnel_url = match.group(0)
            print("\n" + "="*60)
            print(f"🚀 CLOUDFLARE TUNNEL ONLINE: {tunnel_url}")
            print("="*60 + "\n")
            
            # Save to tunnel_url.txt
            with open(os.path.join(os.path.dirname(__file__), "tunnel_url.txt"), "w") as f:
                f.write(tunnel_url)

            # Update Telegram Bot persistent Menu Button
            try:
                res = httpx.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/setChatMenuButton",
                    json={
                        "menu_button": {
                            "type": "web_app",
                            "text": "⚡ Downloader",
                            "web_app": {"url": tunnel_url}
                        }
                    },
                    timeout=15.0
                ).json()
                print("Set Telegram Menu Button response:", res)
            except Exception as e:
                print("Failed to set menu button:", e)

            # Also register Webhook so bot chat works instantly
            try:
                wb_res = httpx.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
                    json={
                        "url": f"{tunnel_url}/api/telegram/webhook",
                        "drop_pending_updates": True,
                    },
                    timeout=15.0
                ).json()
                print("Set Telegram Webhook response:", wb_res)
            except Exception as e:
                print("Failed to set webhook:", e)

            # Update .env
            env_path = os.path.join(os.path.dirname(__file__), ".env")
            with open(env_path, "w") as f:
                f.write(f"TELEGRAM_BOT_TOKEN={BOT_TOKEN}\nWEBAPP_URL={tunnel_url}\nPORT=8001\n")

    # Keep cloudflared alive
    proc.wait()

if __name__ == "__main__":
    main()
