import subprocess
def login_command(cmd):
    print("HERE ", cmd)
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            text=True
        )
    except Exception as e:
        print(f"Error running command: {e}")


login_command('vault login -method=oidc role="default"')
