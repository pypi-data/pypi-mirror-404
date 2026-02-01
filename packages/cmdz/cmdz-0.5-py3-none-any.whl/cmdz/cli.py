import sys
from cmdz.commands.hello import hello_command
from cmdz.commands.version import version_command
from cmdz.commands.doctor import doctor_command
from cmdz.commands.vault import run_vault, build_list_cmd
from cmdz.commands.config import set_namespace, get_namespace

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
    elif command == "login":
        run_vault('vault login -method=oidc role="default"')
    elif command == "setns":
        set_namespace(sys.argv[2])
    elif command =="getns":
        get_namespace()
    elif command == "list":
        cmd=build_list_cmd(get_namespace,sys.argv[2],sys.args[3])
        run_vault(cmd)
    else:
        print("Unknown command")