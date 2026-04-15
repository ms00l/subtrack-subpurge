import os
import subprocess
import json
from pathlib import Path

# --- CONFIGURATION ---
INPUT_DIR = os.path.expanduser("~/Desktop/prjs/dummyMKV")
MKVMERGE_PATH = "mkvmerge"
TRACKING_DIR = Path(os.path.expanduser("~/Desktop/prjs/subtrack_subpurge/reports"))
REPORT_FILE = TRACKING_DIR / "subtrack_report.txt"
QUEUE_FILE = TRACKING_DIR / "subtrack_queue.txt"

SAFE_LANGUAGES = {"eng", "und"}

def run_subtrack():
    TRACKING_DIR.mkdir(parents=True, exist_ok=True)
    input_path = Path(INPUT_DIR)
    video_extensions = {".mkv", ".mp4", ".avi"} 
    flagged_files = []

    print(f"Running Subtrack on directory: {INPUT_DIR}...\n")

    for file in input_path.rglob("*"):
        if file.suffix.lower() in video_extensions:
            print(f"Checking: {file.name}")
            command = [MKVMERGE_PATH, "-J", str(file)]
            
            try:
                result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
                media_info = json.loads(result.stdout)
                
                foreign_tracks = []

                for track in media_info.get("tracks", []):
                    track_type = track.get("type")
                    if track_type in ("audio", "subtitles"):
                        properties = track.get("properties", {})
                        language = properties.get("language", "und")
                        
                        if language not in SAFE_LANGUAGES:
                            track_name = properties.get("track_name", "No Name")
                            foreign_tracks.append(f"{track_type.capitalize()} ({language}): '{track_name}'")

                if foreign_tracks:
                    flagged_files.append((str(file), foreign_tracks))

            except subprocess.CalledProcessError:
                print(f"  [ERROR] Could not read metadata for {file.name}")
            except json.JSONDecodeError:
                print(f"  [ERROR] Failed to parse JSON data for {file.name}")

    # Write the human-readable report
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        if not flagged_files:
            f.write("No files with foreign tracks found.\n")
        else:
            f.write(f"Subtrack found {len(flagged_files)} files needing cleanup:\n")
            f.write("="*60 + "\n\n")
            for filepath, tracks in flagged_files:
                f.write(f"FILE: {filepath}\n")
                for track in tracks:
                    f.write(f"  - {track}\n")
                f.write("\n")

    # Write the machine-readable queue for the cleaner tool
    with open(QUEUE_FILE, "w", encoding="utf-8") as q:
        for filepath, _ in flagged_files:
            q.write(f"{filepath}\n")

    print(f"\nSubtrack Complete!")
    print(f"Report saved to: {Path(REPORT_FILE).absolute()}")
    print(f"Queue saved to: {Path(QUEUE_FILE).absolute()}")

if __name__ == "__main__":
    run_subtrack()