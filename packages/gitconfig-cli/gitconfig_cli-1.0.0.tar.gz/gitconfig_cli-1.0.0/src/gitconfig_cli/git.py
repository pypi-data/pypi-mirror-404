import subprocess
from gitconfig_cli.utils import info, error
from gitconfig_cli.utils import load_config


def configure_git_identity(name: str, email: str, scope: str):
    if scope == "global":
        args = ["git", "config", "--global"]
        info("Setting GLOBAL git identity")
    else:
        args = ["git", "config"]
        info("Setting LOCAL repository git identity")

    subprocess.run(args + ["user.name", name], check=True)
    subprocess.run(args + ["user.email", email], check=True)

    info(f"user.name  = {name}")
    info(f"user.email = {email}")


def use_account(account: str):
    cfg = load_config()
    acc = cfg["accounts"].get(account)

    if not acc:
        error(f"No such account '{account}'")
        raise SystemExit(1)

    # Ensure we are inside a git repo
    subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        check=True,
        stdout=subprocess.DEVNULL,
    )

    info(f"Using account '{account}' for this repository")

    subprocess.run(
        ["git", "config", "user.email", acc["email"]],
        check=True,
    )

    # Optional but recommended: mark SSH command explicitly
    subprocess.run(
        [
            "git",
            "config",
            "core.sshCommand",
            f"ssh -i {acc['key']} -o IdentitiesOnly=yes",
        ],
        check=True,
    )

    info(f"user.email = {acc['email']}")
    info(f"SSH key     = {acc['key']}")
