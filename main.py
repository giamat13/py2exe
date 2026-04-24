import subprocess
import sys
import os
import shutil

def run_command(command_list, stream_output=False):
    """Executes a command list safely without shell interpretation issues."""
    try:
        if stream_output:
            # Stream output directly to terminal in real time
            process = subprocess.Popen(
                command_list,
                stdout=sys.stdout,
                stderr=sys.stderr
            )
            process.wait()
            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, command_list)
        else:
            subprocess.check_call(command_list)
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n[!] Error occurred: {e}")
        return False

def setup_dependencies():
    """Ensures PyInstaller and Pillow are installed using the current interpreter."""
    try:
        import PyInstaller
        from PIL import Image
    except ImportError:
        print("\n--- Dependencies missing. Installing... ---")
        python_exe = shutil.which("python") or shutil.which("py") or sys.executable
        cmd = [python_exe, "-m", "pip", "install", "pyinstaller", "pillow"]
        run_command(cmd, stream_output=True)

def convert_to_ico(image_path, source_dir):
    try:
        from PIL import Image
        img = Image.open(image_path)
        ico_path = os.path.join(source_dir, "temp_icon.ico")
        icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        img.save(ico_path, format='ICO', sizes=icon_sizes)
        return ico_path
    except Exception as e:
        print(f"Warning: Icon conversion failed: {e}")
        return None

def main():
    setup_dependencies()

    input_path = ""
    exe_name_input = ""
    icon_input = ""

    # --- 1. CLI Arguments ---
    # Filter out any flag-style args (e.g. "-m") injected by the Windows Python launcher
    # when the script is invoked via `py2exe` (parsed as `py -2 exe` by the launcher).
    clean_args = [a for a in sys.argv[1:] if not a.startswith("-")]

    if len(clean_args) > 0:
        input_path = clean_args[0].strip().replace('"', '').replace("'", "")
        if len(clean_args) > 1:
            exe_name_input = clean_args[1].strip().replace('"', '').replace("'", "")
        if len(clean_args) > 2:
            icon_input = clean_args[2].strip().replace('"', '').replace("'", "")
    
    # --- 2. Input Logic ---
    if not input_path:
        input_path = input("Enter path to .py file or folder: ").strip().replace('"', '').replace("'", "")

    # Check if the file exists, if not try adding .py
    if not os.path.exists(input_path):
        if os.path.exists(input_path + ".py"):
            input_path += ".py"
        else:
            # Maybe the file is in the current directory?
            potential_path = os.path.join(os.getcwd(), input_path)
            if os.path.exists(potential_path):
                input_path = potential_path
            elif os.path.exists(potential_path + ".py"):
                input_path = potential_path + ".py"

    full_input_path = os.path.abspath(input_path)
    if not os.path.exists(full_input_path):
        print(f"Error: Path '{full_input_path}' not found.")
        return

    # --- 3. Directory Logic ---
    if os.path.isdir(full_input_path):
        source_dir = full_input_path
        files = [f for f in os.listdir(source_dir) if f.endswith('.py')]
        source_file = "main.py" if "main.py" in files else (files[0] if files else None)
    else:
        source_dir = os.path.dirname(full_input_path)
        source_file = os.path.basename(full_input_path)

    if not source_file:
        print("No Python file found.")
        return

    # --- 4. EXE Name ---
    default_name = os.path.splitext(source_file)[0]
    final_exe_name = exe_name_input or default_name
    if final_exe_name.lower().endswith(".exe"):
        final_exe_name = final_exe_name[:-4]

    # --- 5. Icon Logic ---
    icon_args = []
    temp_ico = None
    
    if not icon_input and len(clean_args) == 0:
        icon_input = input("Drag an image for icon (Enter to skip): ").strip().replace('"', '').replace("'", "")

    if icon_input:
        icon_input = os.path.abspath(icon_input.replace('"', '').replace("'", ""))
        if os.path.exists(icon_input):
            if icon_input.lower().endswith(".ico"):
                icon_args = ["--icon", icon_input]
            else:
                print("Converting image to icon...")
                temp_ico = convert_to_ico(icon_input, source_dir)
                if temp_ico: 
                    icon_args = ["--icon", temp_ico]

    # --- 6. Build ---
    # Move to the source directory so PyInstaller runs locally
    original_cwd = os.getcwd()
    os.chdir(source_dir)

    print(f"\nBuilding: {source_file} -> {final_exe_name}.exe...")
    
    # sys.executable is unreliable when launched via `py2exe` (the Windows launcher
    # parses `py2exe` as `py -2 exe`, corrupting argv and the executable path).
    # Prefer the pyinstaller CLI directly; fall back to `python -m PyInstaller`.
    pyinstaller_exe = shutil.which("pyinstaller")
    if pyinstaller_exe:
        build_cmd = [pyinstaller_exe]
    else:
        python_exe = shutil.which("python") or shutil.which("py") or sys.executable
        build_cmd = [python_exe, "-m", "PyInstaller"]

    build_cmd += [
        "--onefile",
        "--noconsole",
        "--clean",
        "--name", final_exe_name,
        source_file
    ]
    if icon_args:
        build_cmd.extend(icon_args)

    success = run_command(build_cmd, stream_output=True)

    # --- 7. Finalize ---
    dist_exe = os.path.join(source_dir, "dist", f"{final_exe_name}.exe")
    final_exe_path = os.path.join(source_dir, f"{final_exe_name}.exe")

    if success and os.path.exists(dist_exe):
        if os.path.exists(final_exe_path):
            os.remove(final_exe_path)
        shutil.move(dist_exe, final_exe_path)
        print("\n" + "="*40)
        print(f"SUCCESS! Created: {final_exe_path}")
        print("="*40)
    else:
        print("\nBuild failed.")

    # Cleanup
    print("Cleaning up temporary files...")
    for folder in ["build", "dist"]:
        p = os.path.join(source_dir, folder)
        if os.path.exists(p): shutil.rmtree(p, ignore_errors=True)
    
    spec_file = os.path.join(source_dir, f"{final_exe_name}.spec")
    if os.path.exists(spec_file): os.remove(spec_file)
    if temp_ico and os.path.exists(temp_ico): os.remove(temp_ico)

    os.chdir(original_cwd)
    if len(clean_args) == 0:
        input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()