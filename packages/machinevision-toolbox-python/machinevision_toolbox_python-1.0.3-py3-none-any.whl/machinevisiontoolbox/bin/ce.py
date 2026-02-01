#! /usr/bin/env python3
import subprocess

result = subprocess.run(["conda", "info", "--envs"], capture_output=True, text=True)
output = result.stdout
for line in output.splitlines():
    if line.startswith("#") or not line.strip():
        continue
    parts = line.split()
    envs = []
    if len(parts) >= 2 and parts[1] == "*":
        envs.append(parts[1] + parts[0])
    else:
        envs.append(parts[0])

    envs.sort(key=lambda s: s.lstrip("*").lower())

    for env in envs:
        result = subprocess.run(
            # ["conda", "list", "-n", env.lstrip("*"), "|", "grep", r"^python\s"],
            f"conda list -n {env.lstrip('*')} | grep '^python\\s'",
            capture_output=True,
            text=True,
            shell=True,
        )
        parts = result.stdout.split()
        print(f"{env:8s}: python {parts[1]}")
