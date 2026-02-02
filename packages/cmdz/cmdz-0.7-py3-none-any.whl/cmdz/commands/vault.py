import subprocess
import os

VAULT_ENV = {
    **os.environ,
    "VAULT_ADDR": "https://vault.carbon-npe.lowes.com"
}


def run_vault(cmd: str):
    print("VAULT >", cmd)
    # result = subprocess.run(
    #     cmd,
    #     shell=True,
    #     text=True,
    #     env=VAULT_ENV
    # )
    #
    # if result.returncode != 0:
    #     raise RuntimeError("Vault command failed")


def build_list_cmd(namespace: str, env: str, path: str):
    print("Env : ",env," Namespace : ", namespace)
    base = f"secrets/carbon/svcs/onprem/{namespace}/{env}/app"

    # normalize path
    if path == "/":
        return f"vault kv list {base}/"
    else:
        return f"vault kv list {base}{path}"
