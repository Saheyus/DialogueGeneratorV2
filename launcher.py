import subprocess
import sys
import importlib.metadata
import re

def install_dependencies():
    """
    Reads requirements.txt and installs any missing packages.
    """
    try:
        with open('requirements.txt', 'r') as f:
            requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except FileNotFoundError:
        print("Error: requirements.txt not found.")
        sys.exit(1)

    missing_packages = []
    for req in requirements:
        package_name = re.split(r'[=<>!~]', req)[0].strip()
        try:
            importlib.metadata.version(package_name)
        except importlib.metadata.PackageNotFoundError:
            # Clean requirement from comments
            clean_req = req.split('#')[0].strip()
            if clean_req:
                missing_packages.append(clean_req)

    if missing_packages:
        print(f"Installing missing packages: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', *missing_packages])
        except subprocess.CalledProcessError as e:
            print(f"Failed to install packages: {e}")
            sys.exit(1)

def main():
    """
    Main function to run the application.
    """
    install_dependencies()
    print("All dependencies are satisfied. Launching the application...")
    try:
        subprocess.run([sys.executable, 'main_app.py'], check=True)
    except FileNotFoundError:
        print("Error: main_app.py not found.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Application exited with an error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 