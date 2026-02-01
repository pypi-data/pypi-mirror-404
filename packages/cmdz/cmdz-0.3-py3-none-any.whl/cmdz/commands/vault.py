import subprocess
import sys

def vault_put_command(args):
    """
    Usage:
    commandly vault-put <namespace> <env> <vault_file> <local_file>
    """

    if len(args) < 4:
        print(
            "Usage:\n"
            "  commandly vault-put <namespace> <env> <vault_file> <local_file>\n\n"
            "Example:\n"
            "  commandly vault-put iiq-schedulers-ns stg secrets.yml ./secrets-stage.yml"
        )
        return

    namespace = args[0]
    env = args[1]
    vault_file = args[2]
    local_file = args[3]

    vault_path = (
        f"secrets/carbon/svcs/onprem/"
        f"{namespace}/{env}/app/{vault_file}"
    )

    cmd = (
        f"vault kv put {vault_path} "
        f"@file=@{local_file}"
    )

    print("Running:")
    print(cmd)
    print()

    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print("Vault command failed")
        sys.exit(e.returncode)
vault_put_command(["a","a","a","a"])