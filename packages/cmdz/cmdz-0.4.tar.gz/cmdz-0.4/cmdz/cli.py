import sys
from cmdz.commands.hello import hello_command
from cmdz.commands.version import version_command
from cmdz.commands.doctor import doctor_command
from cmdz.commands.addr import addr_command
from cmdz.commands.login import login_command

def main():
    if len(sys.argv) < 2:
        print("Usage: cmdz <command>")
        print("Commands: hello, version, doctor")
        return

    command = sys.argv[1]

    if command == "hello":
        hello_command()
    elif command == "version":
        version_command()
    elif command == "doctor":
        doctor_command()
    elif command == "addr":
        addr_command("export VAULT_ADDR=https://vault.carbon-npe.lowes.com")
    elif command == "login":
        login_command('vault login -method=oidc role="default"')
    else:
        print("Unknown command")