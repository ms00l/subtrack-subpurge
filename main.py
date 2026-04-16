import os
import json
import subprocess
import threading
import time
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
from pathlib import Path
import sv_ttk

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = ttk.Label(tw, text=self.text, background="#333333", foreground="#ffffff", relief=tk.SOLID, borderwidth=1, padding=(5,2))
        label.pack()

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None
    
class SubpurgeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Subtrack-Subpurge - MKV Batch Cleaner")
        self.root.geometry("950x800")
        self.root.minsize(800, 650)

        self.input_dir = tk.StringVar()
        self.output_dir = tk.StringVar()

        # --- OS check ---
        if os.name == 'nt':
            self.mkvmerge_path = r"C:\Program Files\MKVToolNix\mkvmerge.exe"
        else:
            self.mkvmerge_path = "mkvmerge"

        self.keep_langs_var = tk.StringVar(value="eng,und")
        # protect_same_dir_var used for same folder checkbox
        self.protect_same_dir_var = tk.BooleanVar(value=True)
        self.input_dir.trace_add("write", self._toggle_overwrite_checkbox)
        self.output_dir.trace_add("write", self._toggle_overwrite_checkbox)
        
        self.cancel_flag = threading.Event()
        self.current_process = None
        
        self.tracking_dir = Path.cwd() / "reports"
        self.report_file = self.tracking_dir / "subtrack_report.txt"

        self._build_ui()
        sv_ttk.set_theme("dark")
    
    def _build_ui(self):
        default_font = ("Ubuntu", 10)

        main_frame = ttk.Frame(self.root, padding="20 20 20 20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Instructions Frame ---
        instructions_frame = ttk.LabelFrame(main_frame, text="How to Use Subtrack-Subpurge", padding="15 15 15 15")

        instructions_frame.pack(fill=tk.X, pady=(0,20))

        instructions_text = ("Subtrack-Subpurge is an automated batch tool that scans your MKV library and strips out unwanted "
            "audio and subtitle tracks to save space.\n\n"
            "Step 1: Select the Input Directory containing the files you want to scan.\n"
            "Step 2: Select an Output Directory where the new, cleaned files will be saved.\n"
            "Step 3: Define the 3-letter language codes you want to KEEP (e.g., eng, spa, jpn).\n"
            "Step 4: Click 'Run Subtrack' to generate a queue of files that need cleaning.\n"
            "Step 5: Click 'Run Subpurge' to execute the queue and strip the tracks."
        )

        ttk.Label(instructions_frame, text=instructions_text, font=default_font, justify=tk.LEFT, wraplength=800).pack(fill=tk.X)


        # --- Settings Frame ---
        settings_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="15 15 15 15")
        settings_frame.pack(fill=tk.X, pady=(0, 15))

        self._add_path_row(settings_frame, "Input Directory:", self.input_dir, 0, default_font)
        self._add_path_row(settings_frame, "Output Directory:", self.output_dir, 1, default_font)

        ttk.Label(settings_frame, text="Languages to KEEP:", font=default_font).grid(row=2, column=0, sticky=tk.W, pady=8, padx=(0, 15))
        lang_entry = ttk.Entry(settings_frame, textvariable=self.keep_langs_var, width=50, font=default_font)
        lang_entry.grid(row=2, column=1, pady=8, sticky=tk.EW)
        ttk.Label(settings_frame, text="(e.g., eng,und,jpn)", font=("Ubuntu", 9, "italic"), foreground="#888888").grid(row=2, column=2, padx=(15, 0), pady=8, sticky=tk.W)

        self.protect_chk = ttk.Checkbutton(
            settings_frame,
            text="Keep original file?",
            variable=self.protect_same_dir_var
        )
        # attaches tooltip for checkbox
        ToolTip(self.protect_chk,"Checked: Saves as '_clean.mkv'. Unchecked: Overwrites original file.")
        # no .grid() here _toggle_overwrite_checkbox auto grids when i/o matches

        # --- Controls Frame ---
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=(0, 15))

        self.scan_btn = ttk.Button(controls_frame, text="Run Subtrack (Scan)", command=self.start_scan, cursor="hand2")
        self.scan_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.clean_btn = ttk.Button(controls_frame, text="Run Subpurge (Clean)", command=self.start_clean, state=tk.DISABLED, cursor="hand2")
        self.clean_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.cancel_btn = ttk.Button(controls_frame, text="Stop / Cancel", command=self.cancel_action, state=tk.DISABLED, cursor="hand2")
        self.cancel_btn.pack(side=tk.LEFT)

        self.clear_btn = ttk.Button(controls_frame, text="Clear Log", command=self.clear_log, cursor="hand2")
        self.clear_btn.pack(side=tk.RIGHT)

        # --- Tabbed Interface ---
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # Tab 1: Live Log
        self.log_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.log_tab, text="Live Activity Log")
        self.console = scrolledtext.ScrolledText(
            self.log_tab, wrap=tk.WORD, state=tk.DISABLED, 
            font=("Consolas", 10), bg="#1c1c1c", fg="#e0e0e0",
            insertbackground="white", relief=tk.FLAT, padx=10, pady=10
        )
        self.console.pack(fill=tk.BOTH, expand=True)

        # Tab 2: Review Queue
        self.queue_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.queue_tab, text="Review Queue")

        # added an "include" column for checkboxes
        self.tree = ttk.Treeview(self.queue_tab, columns=("include", "file", "tracks"), show="headings", selectmode="browse")
        self.tree.heading("include", text="Include")
        self.tree.heading("file", text="File Name")
        self.tree.heading("tracks", text="Foreign Tracks Found")

        self.tree.column("include", width=80, anchor=tk.CENTER)
        self.tree.column("file", width=400)
        self.tree.column("tracks", width=300)

        bottom_queue_frame = ttk.Frame(self.queue_tab)
        bottom_queue_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(0,5))

        ttk.Label(bottom_queue_frame, text="Click the [X] or [ ] to select/deselect files for purging.", font=("Ubuntu", 9, "italic")).pack(side=tk.LEFT)
        self.toggle_all_btn = ttk.Button(bottom_queue_frame, text="Select / Deselect All", command=self.toggle_all, cursor="hand2")
        self.toggle_all_btn.pack(side=tk.RIGHT)

        self.tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(0, 10))

        self.tree.bind('<ButtonRelease-1>', self.toggle_selection)
        # --- Progress Bar ---
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress.pack(fill=tk.X)

        self.log("Welcome to Subtrack-Subpurge v1.2")
        self.log("Select directories, set your keep languages, any other settings, and click 'Run Subtrack'.\n" + "-" * 60)

    def _add_path_row(self, parent, label_text, string_var, row, font):
        ttk.Label(parent, text=label_text, font=font).grid(row=row, column=0, sticky=tk.W, pady=8, padx=(0, 15))
        entry = ttk.Entry(parent, textvariable=string_var, width=50, font=font)
        entry.grid(row=row, column=1, pady=8, sticky=tk.EW)
        
        def browse():
            path = filedialog.askdirectory()
            if path: string_var.set(os.path.normpath(path))

        ttk.Button(parent, text="Browse", command=browse, cursor="hand2").grid(row=row, column=2, padx=(15, 0), pady=8, sticky=tk.EW)
        parent.columnconfigure(1, weight=1)
    
    # --- Helper Functions ---
    def toggle_all(self):
        children = self.tree.get_children()
        if not children: 
            return

        # check if every item is currently checked
        all_checked = all(self.tree.item(item, "values")[0] == "[X]" for item in children)

        # if all_checked, uncheck them else check all
        new_state = "[ ]" if all_checked else "[X]"
        for item in children:
            vals = list(self.tree.item(item, "values"))
            vals[0] = new_state
            self.tree.item(item, values=vals)

    def _toggle_overwrite_checkbox(self, *args):
        in_path = self.input_dir.get().strip()
        out_path = self.output_dir.get().strip()

        # if statement for comparing directories arent empty
        if in_path and out_path and os.path.normpath(in_path) == os.path.normpath(out_path):
            self.protect_chk.grid(row=3,column=0,columnspan=3,sticky=tk.W,pady=(8,0))
        else:
            # hides without destroying
            self.protect_chk.grid_remove()
    def log(self, message):
        def update_text():
            self.console.config(state=tk.NORMAL)
            self.console.insert(tk.END, message + "\n")
            self.console.see(tk.END)
            self.console.config(state=tk.DISABLED)
        self.root.after(0, update_text)

    def clear_log(self):
        self.console.config(state=tk.NORMAL)
        self.console.delete(1.0, tk.END)
        self.console.config(state=tk.DISABLED)

    def toggle_selection(self, event):
        """Simulates a checkbox by toggling [X] and [ ] when the first column is clicked."""
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell": return
        column = self.tree.identify_column(event.x)
        
        if column == "#1": # The 'include' column
            item = self.tree.focus()
            if item:
                vals = list(self.tree.item(item, "values"))
                # Flip the check state
                vals[0] = "[ ]" if vals[0] == "[X]" else "[X]"
                self.tree.item(item, values=vals)

    def cancel_action(self):
        self.log("\n[!] CANCELLATION REQUESTED - Stopping safe-state... [!]")
        self.cancel_flag.set()
        if self.current_process:
            self.current_process.terminate()

    def on_scan_complete(self, files_found_count):
        self.scan_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)
        self.progress_var.set(0)
        
        if files_found_count > 0:
            self.clean_btn.config(state=tk.NORMAL)
            # NEW: Trigger the Popup Window
            review = messagebox.askyesno(
                "Scan Complete", 
                f"Found {files_found_count} files needing cleanup.\n\nWould you like to review the queue before purging?"
            )
            # If user clicks Yes, switch to the Queue tab. If No, do nothing and stay on the Log.
            if review:
                self.notebook.select(self.queue_tab)
        else:
            self.log("Scan finished. No files needed cleaning.")

    # ==========================================
    # PHASE 1: SUBTRACK (SCANNING)
    # ==========================================
    def start_scan(self):
        if not self.input_dir.get():
            self.log("[WARNING] Please select an Input Directory first.")
            return
        
        self.scan_btn.config(state=tk.DISABLED)
        self.clean_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        self.cancel_flag.clear()
        
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        threading.Thread(target=self._scan_process, daemon=True).start()

    def _scan_process(self):
        self.tracking_dir.mkdir(parents=True, exist_ok=True)
        input_path = Path(self.input_dir.get())
        video_extensions = {".mkv", ".mp4", ".avi"}

        raw_langs = self.keep_langs_var.get()
        if not raw_langs.strip(): raw_langs = "eng,und"
        safe_languages = {lang.strip().lower() for lang in raw_langs.split(",")}

        self.log(f"--- STARTING SUBTRACK SCAN ---")
        
        all_files = list(input_path.rglob("*"))
        total_files = len([f for f in all_files if f.suffix.lower() in video_extensions])
        processed_count = 0
        files_found_count = 0

        for file in all_files:
            if self.cancel_flag.is_set(): break

            if file.suffix.lower() in video_extensions:
                command = [self.mkvmerge_path, "-J", str(file)]
                try:
                    self.current_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
                    stdout, stderr = self.current_process.communicate()
                    
                    if self.current_process.returncode == 0:
                        media_info = json.loads(stdout)
                        foreign_tracks = []
                        
                        for track in media_info.get("tracks", []):
                            track_type = track.get("type")
                            if track_type in ("audio", "subtitles"):
                                lang = track.get("properties", {}).get("language", "und")
                                if lang not in safe_languages:
                                    foreign_tracks.append(f"{lang}")

                        if foreign_tracks:
                            tracks_str = ", ".join(foreign_tracks)
                            self.log(f"[FLAGGED] {file.name}")
                            # Initialize with "[X]" as default checked
                            self.root.after(0, lambda f=file, t=tracks_str: self.tree.insert("", tk.END, iid=str(f), values=("[X]", f.name, t)))
                            files_found_count += 1

                except Exception as e:
                    self.log(f"[ERROR] Failed reading {file.name}")

                processed_count += 1
                self.root.after(0, lambda p=(processed_count/max(1, total_files))*100: self.progress_var.set(p))

        self.current_process = None
        self.log(f"\n--- SCAN COMPLETE ---")
        self.root.after(0, lambda: self.on_scan_complete(files_found_count))
    
    # ==========================================
    # PHASE 2: SUBPURGE (CLEANING)
    # ==========================================
    def start_clean(self):
        if not self.output_dir.get():
            self.log("[WARNING] Please select an Output Directory first.")
            return
            
        self.scan_btn.config(state=tk.DISABLED)
        self.clean_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        self.cancel_flag.clear()
        
        self.notebook.select(self.log_tab)
        threading.Thread(target=self._clean_process, daemon=True).start()

    def _clean_process(self):
        self.log("--- STARTING SUBPURGE ---")
        output_base_path = Path(self.output_dir.get())
        output_base_path.mkdir(parents=True, exist_ok=True)

        # Filter: Only grab files that have the "[X]" in the first column
        files_to_process = []
        for item in self.tree.get_children():
            if self.tree.item(item, "values")[0] == "[X]":
                files_to_process.append(item)

        total_files = len(files_to_process)

        if total_files == 0:
            self.log("Queue is empty or all items deselected. Nothing to clean.\n")
            self.root.after(0, lambda: self.on_scan_complete(0)) # Reuse UI reset
            return

        raw_langs = self.keep_langs_var.get()
        if not raw_langs.strip(): raw_langs = "eng,und"
        mkvmerge_langs = ",".join([lang.strip().lower() for lang in raw_langs.split(",")])

        for index, item_id in enumerate(files_to_process):
            if self.cancel_flag.is_set(): break

            file = Path(item_id)
            if not file.exists():
                self.log(f"  [SKIPPED] File missing: {file.name}")
                continue

            self.log(f"Purging: {file.name}...")
            out_file = output_base_path / file.with_suffix('.mkv').name

            # --- Overwrite if statement to delete original files regarding keep original files? checkbox
            is_overwrite = False
            if out_file.resolve() == file.resolve():
                if self.protect_same_dir_var.get():
                    # checkbox is CHECKED so keep original, append _clean
                    out_file = output_base_path / f"{file.stem}_clean.mkv"
                    self.log(f"  [INFO] Appending '_clean' to protect original file.")
                else:
                    # checkbox is UNCHECKED:
                    out_file = output_base_path / f"{file.stem}_temp.mkv"
                    is_overwrite = True
                    self.log(f"  [INFO] Overwrite Mode: Processing to temp file...")

            out_file.parent.mkdir(parents=True, exist_ok=True)

            command = [
                self.mkvmerge_path,
                "-o", str(out_file),
                "--audio-tracks", mkvmerge_langs,
                "--subtitle-tracks", mkvmerge_langs,
                str(file)
            ]

            try:
                self.current_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                while self.current_process.poll() is None:
                    if self.cancel_flag.is_set():
                        self.current_process.terminate()
                        self.log(f"  [ABORTED] {file.name} was killed mid-process.")
                        # clean temp file if user hits cancel mid-overwrite
                        if is_overwrite and out_file.exists():
                            out_file.unlink()
                        break
                    time.sleep(0.5)
                
                if not self.cancel_flag.is_set():
                    # --- return code validation
                    if self.current_process.returncode == 0:
                        # if doing a true overwrite, swap the files
                        if is_overwrite:
                            try:
                                file.unlink()
                                out_file.rename(file)
                                out_file = file
                            except Exception as e:
                                self.log(f"  [ERROR] Could not replace original file: {e}")
                        self.log(f"  [SUCCESS] Saved to -> {out_file.name}")
                        self.root.after(0, lambda i=item_id: self.tree.delete(i))
                    else:
                        # Catch MKVMerge errors
                        _, stderr_data = self.current_process.communicate()
                        err_msg = stderr_data.decode('utf-8', errors='ignore').strip() if stderr_data else "Unknown MKVToolNix error."
                        self.log(f"  [ERROR] mkvmerge rejected {file.name}")
                        self.log(f"         Reason: {err_msg}")
                        if is_overwrite and out_file.exists():
                            out_file.unlink() # Cleanup failed temp file
                    
            except Exception as e:
                self.log(f"  [ERROR] Failed to process {file.name}")
                self.log(f"         Reason: {e}")
                
            self.root.after(0, lambda p=((index+1)/total_files)*100: self.progress_var.set(p))

        self.current_process = None
        self.log("\n--- SUBPURGE FINISHED ---\n")
        messagebox.showinfo("Purge Complete", f"All {total_files} items purged successfully.")
        
        # Reset UI securely
        def final_reset():
            self.scan_btn.config(state=tk.NORMAL)
            self.cancel_btn.config(state=tk.DISABLED)
            self.progress_var.set(0)
            if self.tree.get_children():
                self.clean_btn.config(state=tk.NORMAL)
        self.root.after(0, final_reset)

if __name__ == "__main__":
    root = tk.Tk()
    app = SubpurgeApp(root)
    root.mainloop()