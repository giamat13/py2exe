import subprocess
import sys
import os
import shutil
import ctypes

def is_admin():
    """Checks if the script is running with administrative privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_command(command):
    try:
        subprocess.check_call(command, shell=True)
        return True
    except subprocess.CalledProcessError:
        return False

def setup_pyinstaller():
    try:
        import PyInstaller
    except ImportError:
        print("--- PyInstaller not found. Installing... ---")
        run_command(f"{sys.executable} -m pip install pyinstaller")

def get_best_py_file(directory):
    files = [f for f in os.listdir(directory) if f.endswith('.py')]
    if not files: return None
    for p in ["main.py", "__main__.py"]:
        if p in files: return p
    
    print(f"\nMultiple files found in {directory}:")
    for i, f in enumerate(files):
        print(f"{i+1}) {f}")
    
    while True:
        try:
            choice = int(input("Select file number: ")) - 1
            if 0 <= choice < len(files): return files[choice]
        except ValueError: pass
        print("Invalid choice.")

def main():
    if not is_admin():
        print("!!! Warning: Script is not running as Admin. Some builds might fail !!!\n")

    setup_pyinstaller()

    input_path = ""
    exe_name_input = ""

    # --- 1. Handle Arguments ---
    if len(sys.argv) > 1:
        input_path = sys.argv[1].strip().replace('"', '').replace("'", "")
        if len(sys.argv) > 2:
            exe_name_input = sys.argv[2].strip().replace('"', '').replace("'", "")
    
    # --- 2. Interactive Input ---
    if not input_path:
        input_path = input("Enter path to .py file or folder: ").strip().replace('"', '').replace("'", "")

    if not os.path.exists(input_path) and not input_path.endswith(".py"):
        if os.path.exists(input_path + ".py"):
            input_path += ".py"

    if not os.path.exists(input_path):
        print(f"Error: Path '{input_path}' not found.")
        return

    # --- 3. Directory Logic ---
    if os.path.isdir(input_path):
        source_dir = os.path.abspath(input_path)
        source_file = get_best_py_file(source_dir)
    else:
        source_dir = os.path.abspath(os.path.dirname(input_path) or os.getcwd())
        source_file = os.path.basename(input_path)

    if not source_file: return

    # --- 4. EXE Name ---
    default_name = os.path.splitext(source_file)[0]
    if not exe_name_input:
        if len(sys.argv) == 1:
            exe_name_input = input(f"Enter EXE name (default '{default_name}'): ").strip()
    
    final_exe_name = exe_name_input if exe_name_input else default_name
    if final_exe_name.lower().endswith(".exe"):
        final_exe_name = final_exe_name[:-4]

    # --- 5. Advanced Options (Only if manual) ---
    console_flag = ""
    icon_flag = ""
    
    if len(sys.argv) == 1:
        # Windowed mode?
        hide_console = input("Hide console window (for GUI apps)? (y/n, default 'n'): ").lower() == 'y'
        if hide_console:
            console_flag = "--noconsole"
        
        # Icon?
        icon_path = input("Drag an .ico file here for the icon (or press Enter for none): ").strip().replace('"', '').replace("'", "")
        if icon_path and os.path.exists(icon_path):
            icon_flag = f'--icon="{icon_path}"'

    # --- 6. Build ---
    original_cwd = os.getcwd()
    os.chdir(source_dir)

    print(f"\nBuilding: {source_file} -> {final_exe_name}.exe...")
    
    # Final command assembly
    cmd = f'pyinstaller --onefile --clean {console_flag} {icon_flag} --name "{final_exe_name}" "{source_file}"'
    
    success = run_command(cmd)

    # --- 7. Move & Cleanup ---
    dist_path = os.path.join(source_dir, "dist", f"{final_exe_name}.exe")
    final_output_path = os.path.join(source_dir, f"{final_exe_name}.exe")

    if success and os.path.exists(dist_path):
        if os.path.exists(final_output_path):
            os.remove(final_output_path)
        shutil.move(dist_path, final_output_path)
        print("\n" + "="*40)
        print("SUCCESS!")
        print(f"File moved to: {final_output_path}")
        print("="*40)
    else:
        print("\nBuild failed.")

    print("Cleaning up temporary build files...")
    for folder in ["build", "dist"]:
        path = os.path.join(source_dir, folder)
        if os.path.exists(path): shutil.rmtree(path)
    
    spec_file = os.path.join(source_dir, f"{final_exe_name}.spec")
    if os.path.exists(spec_file): os.remove(spec_file)

    os.chdir(original_cwd)
    if len(sys.argv) <= 1:
        input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()