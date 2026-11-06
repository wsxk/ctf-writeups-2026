from flask import Flask, request, jsonify, render_template
import paramiko
import secrets
import string
import os
import requests

app = Flask(__name__)

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "adminpass123")
TURNSTILE_SITE_KEY = os.environ.get("TURNSTILE_SITE_KEY")
TURNSTILE_SECRET_KEY = os.environ.get("TURNSTILE_SECRET_KEY")

def generate_string(length=12):
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))

def run_ssh_command(cmd):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect("git", port=22, username="admin", password=ADMIN_PASSWORD, timeout=5)
        stdin, stdout, stderr = client.exec_command(cmd)
        exit_code = stdout.channel.recv_exit_status()
        out = stdout.read().decode()
        err = stderr.read().decode()
        client.close()
        return exit_code == 0, out, err
    except Exception as e:
        return False, "", str(e)

@app.route("/")
def index():
    return render_template("index.html", turnstile_site_key=TURNSTILE_SITE_KEY)

@app.route("/register", methods=["POST"])
def register():
    try:
        body = request.get_json(silent=True) or {}
        token = body.get('turnstileToken')
        if not (TURNSTILE_SECRET_KEY and TURNSTILE_SITE_KEY):
            return jsonify({"error": "Turnstile not configured"}), 500
        if not token:
            return jsonify({"error": "Captcha token missing"}), 400
        verify_resp = requests.post(
            'https://challenges.cloudflare.com/turnstile/v0/siteverify',
            data={
                'secret': TURNSTILE_SECRET_KEY,
                'response': token,
                'remoteip': request.remote_addr,
            },
            timeout=5,
        )
        vr = verify_resp.json()
        if not vr.get('success'):
            return jsonify({"error": "Captcha verification failed"}), 400
    except Exception as e:
        return jsonify({"error": f"Captcha error: {e}"}), 500

    for _ in range(5):
        username = generate_string()
        ok, _, _ = run_ssh_command(f"id {username}")
        if not ok:
            break
    else:
        return jsonify({"error": "Failed to generate unique username"}), 500

    password = generate_string()
    ok, _, err = run_ssh_command(
        f"sudo useradd -m -s /bin/bash {username} && echo '{username}:{password}' | sudo chpasswd"
    )
    if not ok:
        return jsonify({"error": f"Failed to create user: {err}"}), 500

    return jsonify({
        "username": username,
        "password": password,
        "ssh_command": f"ssh {username}@git.ctf.pascalctf.it -p 2222",
        "hint": "Run 'mygit' to access the git tool"
    })

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
