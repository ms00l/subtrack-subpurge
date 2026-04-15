import os
import json
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
from pathlib import Path
import sv_ttk

class SubpurgeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Subtrack-Subpurge - MKV Batch Cleaner")
        self.root.geometry("900x750") # Slightly taller to fit the new row
        self.root.minsize(750, 600)

        # Application State & Paths
        self.input_dir = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.mkvmerge_path = "mkvmerge" 
        
        # New variable for user-defined languages
        self.keep_langs_var = tk.StringVar(value="eng,und")
        
        # Internal Tracking
        self.tracking_dir = Path.cwd() / "reports"
        self.report_file = self.tracking_dir / "subtrack_report.txt"
        self.queue_file = self.tracking_dir / "subtrack_queue.txt"

        self._build_ui()
        sv_ttk.set_theme("dark")

    def _build_ui(self):
        default_font = ("Ubuntu", 10)

        main_frame = ttk.Frame(self.root, padding="20 20 20 20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Instructions Frame ---
        instructions_frame = ttk.LabelFrame(main_frame, text="How to Use Subtrack-Subpurge", padding="15 15 15 15")
        instructions_frame.pack(fill=tk.X, pady=(0, 20))

        instructions_text = (
            "Subtrack-Subpurge is an automated batch tool that scans your MKV library and strips out unwanted "
            "audio and subtitle tracks to save space.\n\n"
            "Step 1: Select the Input Directory containing the files you want to scan.\n"
            "Step 2: Select an Output Directory where the new, cleaned files will be saved.\n"
            "Step 3: Define the 3-letter language codes you want to KEEP (e.g., eng, spa, jpn).\n"
            "Step 4: Click '1. Run Subtrack' to generate a queue of files that need cleaning.\n"
            "Step 5: Click '2. Run Subpurge' to execute the queue and strip the tracks."
        )
        
        ttk.Label(instructions_frame, text=instructions_text, font=default_font, justify=tk.LEFT, wraplength=800).pack(fill=tk.X)

        # --- Settings Frame ---
        settings_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="15 15 15 15")
        settings_frame.pack(fill=tk.X, pady=(0, 20))

        self._add_path_row(settings_frame, "Input Directory (To Scan):", self.input_dir, 0, default_font)
        self._add_path_row(settings_frame, "Output Directory (Cleaned Files):", self.output_dir, 1, default_font)

        # --- NEW: Language Selection Row ---
        ttk.Label(settings_frame, text="Languages to KEEP:", font=default_font).grid(row=2, column=0, sticky=tk.W, pady=8, padx=(0, 15))
        lang_entry = ttk.Entry(settings_frame, textvariable=self.keep_langs_var, width=50, font=default_font)
        lang_entry.grid(row=2, column=1, pady=8, sticky=tk.EW)
        
        # Helper text so users know what format to use
        ttk.Label(settings_frame, text="(e.g., eng,und,jpn)", font=("Ubuntu", 9, "italic"), foreground="#888888").grid(row=2, column=2, padx=(15, 0), pady=8, sticky=tk.W)

        # --- Controls Frame ---
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=(0, 20))

        self.scan_btn = ttk.Button(controls_frame, text="1. Run Subtrack (Scan)", command=self.start_scan, cursor="hand2")
        self.scan_btn.pack(side=tk.LEFT, padx=(0, 15))

        self.clean_btn = ttk.Button(controls_frame, text="2. Run Subpurge (Clean)", command=self.start_clean, state=tk.DISABLED, cursor="hand2")
        self.clean_btn.pack(side=tk.LEFT)

        self.clear_btn = ttk.Button(controls_frame, text="Clear Log", command=self.clear_log, cursor="hand2")
        self.clear_btn.pack(side=tk.RIGHT)

        # --- Console Output ---
        log_frame = ttk.LabelFrame(main_frame, text="Console Log", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.console = scrolledtext.ScrolledText(
            log_frame, wrap=tk.WORD, state=tk.DISABLED, 
            font=("Consolas", 10), bg="#1c1c1c", fg="#e0e0e0",
            insertbackground="white", relief=tk.FLAT, padx=10, pady=10
        )
        self.console.pack(fill=tk.BOTH, expand=True)

        self.log("Welcome to Subpurge.")
        self.log("Configure your settings above and click 'Run Subtrack' to begin.")
        self.log(f"Reports and Queue files will be saved to: {self.tracking_dir}\n")
        self.log("-" * 60 + "\n")

    def _add_path_row(self, parent, label_text, string_var, row, font):
        ttk.Label(parent, text=label_text, font=font).grid(row=row, column=0, sticky=tk.W, pady=8, padx=(0, 15))
        entry = ttk.Entry(parent, textvariable=string_var, width=50, font=font)
        entry.grid(row=row, column=1, pady=8, sticky=tk.EW)
        
        def browse():
            path = filedialog.askdirectory()
            if path:
                string_var.set(os.path.normpath(path))

        ttk.Button(parent, text="Browse", command=browse, cursor="hand2").grid(row=row, column=2, padx=(15, 0), pady=8, sticky=tk.EW)
        parent.columnconfigure(1, weight=1)

    def log(self, message):
        def update_text():
            self.console.config(state=tk.NORMAL)
            self.console.insert(tk.END, message + "\n")
            self.console.see(tk.END)
            self.console.config(state=tk.DISABLED)
        self.root.after(0, update_text)

    # function for clearing console log
    def clear_log(self):
        self.console.config(state=tk.NORMAL)
        self.console.delete(1.0, tk.END)
        self.console.config(state=tk.DISABLED)
        self.log("Log cleared.\n" + "-" * 60 + "\n")

    # --- SCANNING ---
    def start_scan(self):
        if not self.input_dir.get():
            self.log("[WARNING] Please select an Input Directory first.\n")
            return
        
        self.scan_btn.config(state=tk.DISABLED)
        self.clean_btn.config(state=tk.DISABLED)
        threading.Thread(target=self._scan_process, daemon=True).start()

    def _scan_process(self):
        self.tracking_dir.mkdir(parents=True, exist_ok=True)
        input_path = Path(self.input_dir.get())
        video_extensions = {".mkv", ".mp4", ".avi"}
        flagged_files = []

        # Parse user languages securely (converts "eng, jpn" into {"eng", "jpn"})
        raw_langs = self.keep_langs_var.get()
        if not raw_langs.strip():
            raw_langs = "eng,und" # Fallback safety net
            
        safe_languages = {lang.strip().lower() for lang in raw_langs.split(",")}

        self.log(f"--- STARTING SUBTRACK SCAN ---")
        self.log(f"Scanning: {input_path}")
        self.log(f"Targeting files with tracks NOT IN: {', '.join(safe_languages)}\n")

        for file in input_path.rglob("*"):
            if file.suffix.lower() in video_extensions:
                command = [self.mkvmerge_path, "-J", str(file)]
                try:
                    result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
                    media_info = json.loads(result.stdout)
                    
                    foreign_tracks = []
                    for track in media_info.get("tracks", []):
                        track_type = track.get("type")
                        if track_type in ("audio", "subtitles"):
                            lang = track.get("properties", {}).get("language", "und")
                            
                            # Check against dynamic user list
                            if lang not in safe_languages:
                                track_name = track.get("properties", {}).get("track_name", "No Name")
                                foreign_tracks.append(f"{track_type.capitalize()} ({lang}): '{track_name}'")

                    if foreign_tracks:
                        flagged_files.append((str(file), foreign_tracks))
                        self.log(f"[FLAGGED] {file.name}")

                except Exception as e:
                    self.log(f"[ERROR] Failed reading metadata for {file.name}")

        with open(self.report_file, "w", encoding="utf-8") as f:
            if not flagged_files:
                f.write("No files with removable tracks found.\n")
            else:
                f.write(f"Subtrack found {len(flagged_files)} files needing cleanup:\n")
                f.write("="*60 + "\n\n")
                for filepath, tracks in flagged_files:
                    f.write(f"FILE: {filepath}\n")
                    for track in tracks:
                        f.write(f"  - {track}\n")
                    f.write("\n")

        with open(self.queue_file, "w", encoding="utf-8") as q:
            for filepath, _ in flagged_files:
                q.write(f"{filepath}\n")

        self.log(f"\n--- SCAN COMPLETE ---")
        self.log(f"Found {len(flagged_files)} files needing cleanup.")
        self.log(f"Report saved to: {self.report_file.name}\n")
        
        def enable_ui():
            self.scan_btn.config(state=tk.NORMAL)
            if flagged_files:
                self.clean_btn.config(state=tk.NORMAL)
        self.root.after(0, enable_ui)

    # --- CLEANING ---
    def start_clean(self):
        if not self.output_dir.get():
            self.log("[WARNING] Please select an Output Directory first.\n")
            return
            
        self.scan_btn.config(state=tk.DISABLED)
        self.clean_btn.config(state=tk.DISABLED)
        threading.Thread(target=self._clean_process, daemon=True).start()

    def _clean_process(self):
        self.log("--- STARTING SUBPURGE ---")
        output_base_path = Path(self.output_dir.get())
        output_base_path.mkdir(parents=True, exist_ok=True)

        if not self.queue_file.exists():
            self.log(f"[ERROR] Could not find {self.queue_file.name}. Run Subtrack first.\n")
            self.root.after(0, lambda: self.scan_btn.config(state=tk.NORMAL))
            return

        with open(self.queue_file, "r", encoding="utf-8") as q:
            files_to_process = [line.strip() for line in q if line.strip()]

        if not files_to_process:
            self.log("Queue is empty. Nothing to clean.\n")
            self.root.after(0, lambda: self.scan_btn.config(state=tk.NORMAL))
            return

        # Format user input for the mkvmerge command (needs to be comma separated without spaces)
        raw_langs = self.keep_langs_var.get()
        if not raw_langs.strip():
            raw_langs = "eng,und"
        mkvmerge_langs = ",".join([lang.strip().lower() for lang in raw_langs.split(",")])

        for file_str in files_to_process:
            file = Path(file_str)
            
            if not file.exists():
                self.log(f"  [SKIPPED] File missing: {file.name}")
                continue

            self.log(f"Purging: {file.name}...")

            out_file = output_base_path / file.with_suffix('.mkv').name
            out_file.parent.mkdir(parents=True, exist_ok=True)

            command = [
                self.mkvmerge_path,
                "-o", str(out_file),
                # Using the dynamically formatted language string here
                "--audio-tracks", mkvmerge_langs,
                "--subtitle-tracks", mkvmerge_langs,
                str(file)
            ]

            try:
                subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self.log(f"  [SUCCESS] Saved to -> {out_file.name}")
                
            except subprocess.CalledProcessError:
                self.log(f"  [ERROR] Failed to process {file.name}")

        self.log("\n--- SUBPURGE COMPLETE ---\n")
        
        def reset_ui():
            self.scan_btn.config(state=tk.NORMAL)
        self.root.after(0, reset_ui)

if __name__ == "__main__":
    root = tk.Tk()
    app = SubpurgeApp(root)
    root.mainloop()