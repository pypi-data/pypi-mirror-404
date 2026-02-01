import json
import sys
from pathlib import Path

APP_NAME = "gitconfig-cli"
CONFIG_DIR = Path.home() / ".config" / APP_NAME
CONFIG_FILE = CONFIG_DIR / "config.json"


def ensure_config_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    ensure_config_dir()
    if not CONFIG_FILE.exists():
        return {"accounts": {}}
    return json.loads(CONFIG_FILE.read_text())


def save_config(cfg: dict):
    ensure_config_dir()
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))


def print_banner():
    print("🧰 gitconfig — Git & SSH multi-account CLI\n")


def info(msg: str):
    print(f"[+] {msg}")


def warn(msg: str):
    print(f"[!] {msg}")


def error(msg: str):
    print(f"[x] {msg}", file=sys.stderr)

def export_config(path: str | None):
    cfg = load_config()
    data = json.dumps(cfg, indent=2)

    if path:
        Path(path).write_text(data)
        info(f"Config exported to {path}")
    else:
        print(data)
