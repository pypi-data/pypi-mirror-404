import os
import json

CONFIG_DIR = os.path.expanduser("~/.cmdz")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")


def _ensure_dir():
    os.makedirs(CONFIG_DIR, exist_ok=True)


def set_namespace(namespace: str):
    _ensure_dir()
    with open(CONFIG_FILE, "w") as f:
        json.dump({"namespace": namespace}, f)
    print(f"Namespace set to: {namespace}")


def get_namespace() -> str:
    if not os.path.exists(CONFIG_FILE):
        raise RuntimeError("Namespace not set. Run: cmdz setns <namespace>")

    with open(CONFIG_FILE) as f:
        print(json.load(f)["namespace"])
