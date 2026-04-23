import subprocess
import sys
import os
import shutil
import ctypes

def run_command(command):
    try:
        subprocess.check_call(command, shell=True)
        return True
    except subprocess.CalledProcessError:
        return False

def setup_dependencies():
    try:
        import PyInstaller
        from PIL import Image
    except ImportError:
        print("--- Installing missing dependencies... ---")
        run_command(f"{sys.executable} -m pip install pyinstaller pillow")

def convert_to_ico(image_path, source_dir):
    try:
        from PIL import Image
        img = Image.open(image_path)
        ico_path = os.path.join(source_dir, "temp_icon.ico")
        icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        img.save(ico_path, format='ICO', sizes=icon_sizes)
        return ico_path
    except Exception as e:
        print(f"Warning: Could not convert image to icon: {e}")
        return None

def main():
    setup_dependencies()

    input_path = ""
    exe_name_input = ""
    icon_input = ""

    # --- 1. Handle Arguments (CLI Support) ---
    if len(sys.argv) > 1:
        input_path = os.path.abspath(sys.argv[1].strip().replace('"', '').replace("'", ""))
        if len(sys.argv) > 2:
            exe_name_input = sys.argv[2].strip().replace('"', '').replace("'", "")
        if len(sys.argv) > 3:
            icon_input = os.path.abspath(sys.argv[3].strip().replace('"', '').replace("'", ""))
    
    # --- 2. Interactive Input if not provided ---
    if not input_path:
        input_path = input("Enter path to .py file or folder: ").strip().replace('"', '').replace("'", "")
        input_path = os.path.abspath(input_path)

    if not os.path.exists(input_path) and not input_path.endswith(".py"):
        if os.path.exists(input_path + ".py"):
            input_path += ".py"

    if not os.path.exists(input_path):
        print(f"Error: Path '{input_path}' not found.")
        return

    # --- 3. Directory Logic ---
    if os.path.isdir(input_path):
        source_dir = input_path
        files = [f for f in os.listdir(source_dir) if f.endswith('.py')]
        source_file = "main.py" if "main.py" in files else (files[0] if files else None)
    else:
        source_dir = os.path.dirname(input_path)
        source_file = os.path.basename(input_path)

    if not source_file:
        print("No Python file found.")
        return

    # --- 4. EXE Name ---
    default_name = os.path.splitext(source_file)[0]
    final_exe_name = (exe_name_input if exe_name_input else (input(f"Enter EXE name (default '{default_name}'): ").strip() or default_name))
    final_exe_name = final_exe_name[:-4] if final_exe_name.lower().endswith(".exe") else final_exe_name

    # --- 5. Icon Logic (Now handles both CLI and Interactive) ---
    icon_flag = ""
    temp_ico = None
    
    # If icon was not provided in CLI, ask for it
    if not icon_input and len(sys.argv) <= 3:
        icon_input = input("Drag an image (PNG, JPG, ICO) for the icon (Enter to skip): ").strip().replace('"', '').replace("'", "")
        if icon_input:
            icon_input = os.path.abspath(icon_input)

    if icon_input and os.path.exists(icon_input):
        if icon_input.lower().endswith(".ico"):
            icon_flag = f'--icon="{icon_input}"'
        else:
            print("Converting image to icon...")
            temp_ico = convert_to_ico(icon_input, source_dir)
            if temp_ico:
                icon_flag = f'--icon="{temp_ico}"'

    # --- 6. Build ---
    original_cwd = os.getcwd()
    os.chdir(source_dir)

    print(f"\nBuilding: {source_file} -> {final_exe_name}.exe...")
    cmd = f'pyinstaller --onefile --clean {icon_flag} --name "{final_exe_name}" "{source_file}"'
    
    success = run_command(cmd)

    # --- 7. Move & Cleanup ---
    dist_exe = os.path.join(source_dir, "dist", f"{final_exe_name}.exe")
    final_exe = os.path.join(source_dir, f"{final_exe_name}.exe")

    if success and os.path.exists(dist_exe):
        if os.path.exists(final_exe): os.remove(final_exe)
        shutil.move(dist_exe, final_exe)
        print("\n" + "="*40 + f"\nSUCCESS! File: {final_exe}\n" + "="*40)
    else:
        print("\nBuild failed.")

    # Cleanup
    for folder in ["build", "dist"]:
        path = os.path.join(source_dir, folder)
        if os.path.exists(path): shutil.rmtree(path)
    
    spec_file = os.path.join(source_dir, f"{final_exe_name}.spec")
    if os.path.exists(spec_file): os.remove(spec_file)
    if temp_ico and os.path.exists(temp_ico): os.remove(temp_ico)

    os.chdir(original_cwd)
    if len(sys.argv) <= 1: input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()