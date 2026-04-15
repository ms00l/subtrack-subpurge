import os
import subprocess
from pathlib import Path

# --- CONFIGURATION ---
QUEUE_FILE = os.path.expanduser("~/Desktop/prjs/subtrack_subpurge/reports/subtrack_queue.txt")
OUTPUT_DIR = os.path.expanduser("~/Desktop/prjs/subtrack_subpurge/stripped") # Where the cleaned files will go
MKVMERGE_PATH = "mkvmerge"

LANGUAGES_TO_KEEP = "eng,und"

def run_cleaner():
    queue_path = Path(QUEUE_FILE)
    output_base_path = Path(OUTPUT_DIR)
    
    if not queue_path.exists():
        print(f"Error: Could not find {QUEUE_FILE}. Run Subtrack first.")
        return

    output_base_path.mkdir(parents=True, exist_ok=True)

    # Read the files to process from the Subtrack queue
    with open(queue_path, "r", encoding="utf-8") as q:
        files_to_process = [line.strip() for line in q if line.strip()]

    if not files_to_process:
        print("Queue is empty. Nothing to clean.")
        return

    print(f"Cleaner starting. Found {len(files_to_process)} files in the queue.\n")

    for file_str in files_to_process:
        file = Path(file_str)
        
        if not file.exists():
            print(f"  [SKIPPED] File no longer exists: {file}")
            continue

        print(f"Processing: {file.name}")

        # Try to maintain some folder structure by using the file's parent folder name
        # (Since the queue just has absolute paths, we put it in OutputDir/ParentFolderName/File.mkv)
        out_file = output_base_path / file.parent.name / file.with_suffix('.mkv').name
        out_file.parent.mkdir(parents=True, exist_ok=True)

        command = [
            MKVMERGE_PATH,
            "-o", str(out_file),
            "--audio-tracks", LANGUAGES_TO_KEEP,
            "--subtitle-tracks", LANGUAGES_TO_KEEP,
            str(file)
        ]

        try:
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            full_path = os.path.abspath("Dummy_Test_Movie.mkv")
            print(f"  [SUCCESS] Cleaned and saved as {out_file.name}")
            print(f"\nLocated in: {full_path}")
            # --- STORAGE OVERRIDE ---
            # Uncomment the line below ONLY if you want to delete the original 
            # file after the cleaned version is successfully created.
            # os.remove(file)
            
        except subprocess.CalledProcessError as e:
            print(f"  [ERROR] Failed processing {file.name}")
            print(f"  Details: {e.stderr.decode('utf-8', errors='ignore')}")

if __name__ == "__main__":
    run_cleaner()