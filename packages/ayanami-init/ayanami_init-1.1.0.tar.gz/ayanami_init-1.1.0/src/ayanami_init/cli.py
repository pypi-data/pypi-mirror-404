import os
from pathlib import Path
import sys
import subprocess

def main():
    args = sys.argv[1:]
    
    if len(args) <= 0:
        print("You need to give the project path, the name of the root folder becomes the name of the project")
        return

    project_path = args[0]

    try:
        os.mkdir(f"{project_path}")
    except FileExistsError:
        print(f"Folder {project_path} already exists skipping file creation for it.")
        pass


    try:
        os.mkdir(f"{project_path}/lib")
        Path(f"{project_path}/lib/__init__.py").touch()
        Path(f"{project_path}/lib/module1.py").touch()
    except FileExistsError:
        print("Folder lib already exists skipping file creation for it.")
        pass

    try:
        os.mkdir(f"{project_path}/tests")
        Path(f"{project_path}/tests/__init__.py").touch()
        Path(f"{project_path}/tests/test_example.py").touch()
        
        with open(f"{project_path}/tests/test_example.py", "w") as file:
            file.write(
"""\
def test_basic_case():
    assert 5 == 5
""")

    except FileExistsError:
        print("Folder tests already exists skipping file creation for it.")
        pass


    os.chdir(project_path)

    subprocess.run(["uv", "init", "."])
    subprocess.run(["uv", "add", "--dev", "pytest"])
    subprocess.run(["uv", "add", "wrapt"])
    subprocess.run(["uv", "add", "icontract"])
if __name__ == "__main__":
    main()