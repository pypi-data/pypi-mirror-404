import sys
from cmdz.commands.check import check_command
from cmdz.commands.version import version_command
from cmdz.commands.doctor import doctor_command
from cmdz.commands.vault import run_vault, build_list_cmd
from cmdz.commands.config import set_namespace, get_namespace
from cmdz.valid import isValid
from cmdz.valid import invalid_message

def main():
    if len(sys.argv) < 2:
        print("Usage: cmdz <command>")
        print("Commands: hello, version, doctor")
        return

    command = sys.argv[1]

    if command == "hello":
        if(isValid(sys,2,2)):
            check_command()
    elif command == "version":
        if(isValid(sys,2,2)):
            version_command()
    elif command == "doctor":
        if(isValid(sys,2,2)):
            doctor_command()
    elif command == "login":
        if(isValid(sys,2,2)):
            run_vault('vault login -method=oidc role="default"')
    elif command == "setns":
        if(isValid(sys,3,3)):
            set_namespace(sys.argv[2])
    elif command =="getns":
        if(isValid(sys,2,2)):
            get_namespace()
    elif command == "list":
        if(isValid(sys,5,5)):
            cmd=build_list_cmd(get_namespace,sys.argv[2],sys.argv[3])
            run_vault(cmd)
    else:
        invalid_message()
        