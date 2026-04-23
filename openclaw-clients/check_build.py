import subprocess
import sys

ssh_cmd = [
    "sshpass", "-p", "UbunTu12@.",
    "ssh", "-o", "StrictHostKeyChecking=no",
    "ubuntu@43.134.39.26",
    "gh run view --log-failed -R SxLiuYu/openclaw-clients 2>&1 | tail -50"
]

try:
    result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=30)
    print(result.stdout)
    print(result.stderr)
except FileNotFoundError:
    print("sshpass not found, trying alternative...")
    # Try using expect-like approach
    import pexpect
    child = pexpect.spawn('ssh ubuntu@43.134.39.26 "gh run view --log-failed -R SxLiuYu/openclaw-clients"')
    child.expect('password:')
    child.sendline('UbunTu12@.')
    print(child.read().decode())
except Exception as e:
    print(f"Error: {e}")