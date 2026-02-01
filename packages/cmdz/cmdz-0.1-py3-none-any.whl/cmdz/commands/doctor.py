import platform
import sys

def doctor_command():
    print("Doctor check")
    print("OS:", platform.system())
    print("Python:", sys.version.split()[0])