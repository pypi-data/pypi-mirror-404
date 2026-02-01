import os

def init_command(args):
    os.makedirs("src", exist_ok=True)
    os.makedirs("tests", exist_ok=True)

    with open("README.md", "w") as f:
        f.write("# New cmdz Project\n")

    print("✅ Project initialized")