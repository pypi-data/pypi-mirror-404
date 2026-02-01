import os
import subprocess
from pathlib import Path
import shutil
from gitconfig_cli.utils import info, warn, error, load_config, save_config

SSH_DIR = Path.home() / ".ssh"
SSH_CONFIG = SSH_DIR / "config"


def _provider_host(provider: str) -> str:
    return {
        "github": "github.com",
        "gitlab": "gitlab.com",
        "bitbucket": "bitbucket.org",
    }.get(provider, provider)


def _key_path(provider: str, account: str, key_type: str) -> Path:
    return SSH_DIR / f"id_{provider}_{account}_{key_type}"


def add_ssh_account(
    provider: str,
    account: str,
    email: str,
    key_type: str,
    host: str | None,
    non_interactive: bool = False,
):
    SSH_DIR.mkdir(parents=True, exist_ok=True)

    cfg = load_config()
    if account in cfg["accounts"]:
        raise RuntimeError(f"Account '{account}' already exists")

    host_name = host or _provider_host(provider)
    key_path = _key_path(provider, account, key_type)

    info(f"Creating SSH key: {key_path}")

    cmd = [
        "ssh-keygen",
        "-t",
        key_type,
        "-f",
        str(key_path),
        "-C",
        email,
        "-N",
        "",
    ]

    if key_type == "rsa":
        warn("ssh-rsa is legacy and disabled by default on modern OpenSSH")
        cmd += ["-b", "4096"]

    subprocess.run(cmd, check=True)

    alias = f"{provider}-{account}"

    ssh_block = f"""
Host {alias}
    HostName {host_name}
    User git
    IdentityFile {key_path}
    IdentitiesOnly yes
"""

    if key_type == "rsa":
        ssh_block += """    PubkeyAcceptedAlgorithms +ssh-rsa
    HostkeyAlgorithms +ssh-rsa
"""

    SSH_CONFIG.touch(exist_ok=True)
    SSH_CONFIG.write_text(SSH_CONFIG.read_text() + ssh_block)

    cfg["accounts"][account] = {
        "provider": provider,
        "alias": alias,
        "email": email,
        "key": str(key_path),
        "type": key_type,
    }

    save_config(cfg)

    info(f"Account '{account}' added")
    info(f"Clone using: git clone git@{alias}:org/repo.git")


def list_ssh_accounts():
    cfg = load_config()
    if not cfg["accounts"]:
        warn("No SSH accounts configured")
        return

    for name, acc in cfg["accounts"].items():
        print(
            f"- {name} → {acc['provider']} ({acc['type']}) "
            f"[git@{acc['alias']}]"
        )


def remove_ssh_account(account: str):
    cfg = load_config()
    acc = cfg["accounts"].get(account)

    if not acc:
        raise RuntimeError(f"No such account '{account}'")

    key_path = Path(acc["key"])
    if key_path.exists():
        key_path.unlink(missing_ok=True)
        key_path.with_suffix(".pub").unlink(missing_ok=True)

    if SSH_CONFIG.exists():
        lines = SSH_CONFIG.read_text().splitlines()
        filtered = []
        skip = False

        for line in lines:
            if line.strip() == f"Host {acc['alias']}":
                skip = True
            elif skip and line.startswith("Host "):
                skip = False

            if not skip:
                filtered.append(line)

        SSH_CONFIG.write_text("\n".join(filtered) + "\n")

    del cfg["accounts"][account]
    save_config(cfg)

    info(f"Account '{account}' removed")


def test_ssh_account(account: str, verbose: bool = False):
    cfg = load_config()
    acc = cfg["accounts"].get(account)

    if not acc:
        error(f"No such account '{account}'")
        raise SystemExit(1)

    alias = acc["alias"]

    info(f"Testing SSH connection for '{account}'")
    info(f"→ ssh -T git@{alias}")

    cmd = ["ssh"]
    if verbose:
        cmd.append("-vvv")
    cmd += ["-T", f"git@{alias}"]

    result = subprocess.run(
        cmd,
        text=True,
        capture_output=True,
    )

    output = (result.stdout + result.stderr).strip()

    if "successfully authenticated" in output.lower() or "welcome" in output.lower():
        info("✅ SSH authentication successful")
        print(output)
        return

    warn("❌ SSH authentication failed")
    print(output)

    if not verbose:
        warn("Tip: re-run with --verbose for detailed SSH debug output")


def doctor():
    info("Running SSH diagnostics")

    # ssh binary
    if not shutil.which("ssh"):
        error("ssh not found in PATH")
        return

    # ~/.ssh
    if not SSH_DIR.exists():
        error("~/.ssh directory does not exist")
        return

    info("~/.ssh directory exists")

    # permissions
    perms = oct(SSH_DIR.stat().st_mode)[-3:]
    if perms != "700":
        warn(f"~/.ssh permissions are {perms}, should be 700")

    if SSH_CONFIG.exists():
        perms = oct(SSH_CONFIG.stat().st_mode)[-3:]
        if perms != "600":
            warn(f"~/.ssh/config permissions are {perms}, should be 600")
    else:
        warn("~/.ssh/config not found")

    # ssh-agent
    if "SSH_AUTH_SOCK" not in os.environ:
        warn("ssh-agent is not running")
    else:
        info("ssh-agent detected")

    info("Doctor check completed")
