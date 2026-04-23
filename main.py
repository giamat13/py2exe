import subprocess
import sys
import os
import shutil

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
        print("PyInstaller not found. Installing...")
        run_command(f"{sys.executable} -m pip install pyinstaller")

def get_best_py_file(directory):
    files = [f for f in os.listdir(directory) if f.endswith('.py')]
    if not files: return None
    
    # Priority
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
    setup_pyinstaller()

    input_path = ""
    exe_name = ""

    # --- 1. Handle Arguments (CLI Support) ---
    # Usage: python main.py <source_file> <output_name>
    if len(sys.argv) > 1:
        input_path = sys.argv[1].strip().replace('"', '').replace("'", "")
        if len(sys.argv) > 2:
            exe_name = sys.argv[2].strip().replace('"', '').replace("'", "")
    
    # --- 2. Interactive Input if not provided ---
    if not input_path:
        input_path = input("Enter path to .py file or folder: ").strip().replace('"', '').replace("'", "")

    # Auto-append .py if file exists with that name
    if not os.path.exists(input_path) and not input_path.endswith(".py"):
        if os.path.exists(input_path + ".py"):
            input_path += ".py"

    if not os.path.exists(input_path):
        print(f"Error: Path '{input_path}' not found.")
        return

    # --- 3. Determine File and Directory ---
    if os.path.isdir(input_path):
        source_dir = os.path.abspath(input_path)
        source_file = get_best_py_file(source_dir)
        if not source_file:
            print("No .py files found.")
            return
    else:
        source_dir = os.path.abspath(os.path.dirname(input_path) or os.getcwd())
        source_file = os.path.basename(input_path)

    # --- 4. Handle Output Name ---
    if not exe_name:
        exe_name = input(f"Enter EXE name (default 'start'): ").strip() or "start"
    
    if exe_name.lower().endswith(".exe"):
        exe_name = exe_name[:-4]

    # --- 5. Execution ---
    original_cwd = os.getcwd()
    os.chdir(source_dir)

    print(f"\nBuilding: {source_file} -> {exe_name}.exe")
    # Using --clean to ensure fresh build
    cmd = f'pyinstaller --onefile --clean --name "{exe_name}" "{source_file}"'
    
    success = run_command(cmd)

    # --- 6. Cleanup & Move (The "Pro" Touch) ---
    dist_path = os.path.join(source_dir, "dist", f"{exe_name}.exe")
    final_output_path = os.path.join(source_dir, f"{exe_name}.exe")

    if success and os.path.exists(dist_path):
        # Move EXE to the input directory
        if os.path.exists(final_output_path):
            os.remove(final_output_path) # Remove old version if exists
        shutil.move(dist_path, final_output_path)
        
        print("\n" + "="*40)
        print(f"SUCCESS!")
        print(f"Output: {final_output_path}")
        print("="*40)
    else:
        print("\nBuild failed.")

    # Remove temporary PyInstaller mess
    print("Cleaning up temporary files...")
    for folder in ["build", "dist"]:
        folder_path = os.path.join(source_dir, folder)
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
    
    spec_file = os.path.join(source_dir, f"{exe_name}.spec")
    if os.path.exists(spec_file):
        os.remove(spec_file)

    os.chdir(original_cwd)
    if len(sys.argv) == 1: # Only pause if run manually (not via CLI)
        input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()