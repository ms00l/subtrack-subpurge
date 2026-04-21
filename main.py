"""
Standard library imports here
    -os for interacting with the operating system
    -json used for parsing output from MKVToolNix, returning media data
    -subprocess for running command line programs, specifically mkvmerge
    -threading for running tasks in background
    -time used for pausing code to wait for process to finish
    """
import os
import json
import subprocess
import threading
import time
import shutil

"""
GUI & Filesystem imports here
    -tkinter for core of the GUI and then its specific UI widgets
    -pathlib for handling file paths
    -custom sun valley theme because im a dark mode kind of guy
"""
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
from pathlib import Path
import sv_ttk

""" ToolTip class to handle on-hover infomation boxes"""
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        # using bind for when cursor enters or leaves
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        # get current coordinates of widget
        x, y, cx, cy = self.widget.bbox("insert")

        # offset for where the popup shows (bottom right of the cursor)
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20

        # create a new window on top
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        # stripping standard window borders/title
        tw.wm_overrideredirect(True)
        # utilize coordinates
        tw.wm_geometry(f"+{x}+{y}")

        # creating the label then pack puts the label into the tooltip
        label = ttk.Label(tw, text=self.text, background="#333333", foreground="#ffffff", relief=tk.SOLID, borderwidth=1, padding=(5,2))
        label.pack()

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None
    
""" Main app class"""
class SubpurgeApp:
    def __init__(self, root):
        self.root = root

        self.root.title("Subtrack-Subpurge - MKV Batch Cleaner")
        self.root.geometry("950x800")
        self.root.minsize(800, 650)

        # using tkinter variable StringVar to auto update UI for text
        # these variables are used for the input/output directories
        self.input_dir = tk.StringVar()
        self.output_dir = tk.StringVar()

        """
        --- OS check ---
        checking if OS is windows or linux/mac largely assuming installed globally
        """
        if os.name == 'nt':
            self.mkvmerge_path = r"C:\Program Files\MKVToolNix\mkvmerge.exe"
        else:
            self.mkvmerge_path = "mkvmerge"

        self._verify_mkvmerge()

        # default languages user wants to keep
        self.keep_langs_var = tk.StringVar(value="eng,und")
        # protect_same_dir_var used for same folder checkbox
        self.protect_same_dir_var = tk.BooleanVar(value=True)
        
        # adding listeners to overwrite checkbox
        self.input_dir.trace_add("write", self._toggle_overwrite_checkbox)
        self.output_dir.trace_add("write", self._toggle_overwrite_checkbox)
        
        # threading.Event used to stop background loops if set to True
        # then using a variable to keep track of whatever subprocess is running
        self.cancel_flag = threading.Event()
        self.current_process = None
        
        """
        remnants of the first iteration of this program, relatively unnecessary/unused 
        moreso here for the user if futher logging is needed. not even sure if logs 
        actually record properly LOL
        FIXME add button to utilize this or not later
        """
        self.tracking_dir = Path.cwd() / "reports"
        self.report_file = self.tracking_dir / "subtrack_report.txt"

        # build the UI and set the theme
        self._build_ui()
        sv_ttk.set_theme("dark")
    
    def _verify_mkvmerge(self):
        """Check to see if mkvmerge exists. If not, prompts the user to find it."""
        # checking if the path exists or its in the system path
        if not Path(self.mkvmerge_path).exists() and not shutil.which(self.mkvmerge_path):
            messagebox.showwarning(
                "MKVToolNix Missing",
                "Could not find mkvmerge.exe in the default location. \n\nPlease locate it manually."
            )
            # open file browser targeting executables
            custom_path = filedialog.askopenfilename(
                title="Locate mkvmerge.exe",
                filetypes=[("Executable Files", "*.exe")] if os.name == 'nt' else [("All Files", "*.*")]
            )

            if custom_path:
                self.mkvmerge_path = os.path.normpath(custom_path)
            else:
                # if hitting cancel on file browser, shut down app
                self.root.destroy()
                exit()
    
    def _build_ui(self):

        # set the font and create the main container frame 
        default_font = ("Ubuntu", 10)
        main_frame = ttk.Frame(self.root, padding="20 20 20 20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Instructions Frame ---
        # create a bordered box using LabelFrame to hold instructions
        # instructions are just a long string stored in var then create label and pack
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

        # calling helper function to build the i/o directory rows
        self._add_path_row(settings_frame, "Input Directory:", self.input_dir, 0, default_font)
        self._add_path_row(settings_frame, "Output Directory:", self.output_dir, 1, default_font)

        # ttk.Entry class used to setup input field for tracking languages user wants to keep
        ttk.Label(settings_frame, text="Languages to KEEP:", font=default_font).grid(row=2, column=0, sticky=tk.W, pady=8, padx=(0, 15))
        lang_entry = ttk.Entry(settings_frame, textvariable=self.keep_langs_var, width=50, font=default_font)
        lang_entry.grid(row=2, column=1, pady=8, sticky=tk.EW)
        ttk.Label(settings_frame, text="(e.g., eng,und,jpn)", font=("Ubuntu", 9, "italic"), foreground="#888888").grid(row=2, column=2, padx=(15, 0), pady=8, sticky=tk.W)

        # building overwrite checkbox that is hidden initially
        self.protect_chk = ttk.Checkbutton(
            settings_frame,
            text="Keep original file?",
            variable=self.protect_same_dir_var
        )
        # attaches tooltip for overwrite checkbox
        # no .grid() here as _toggle_overwrite_checkbox remains hidden until i/o matches
        ToolTip(self.protect_chk,"Checked: Saves as '_clean.mkv'. Unchecked: Overwrites original file.")

        # --- Controls Frame ---
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=(0, 15))

        # build and pack for the scan, clean, cancel and clear log buttons
        self.scan_btn = ttk.Button(controls_frame, text="Run Subtrack (Scan)", command=self.start_scan, cursor="hand2")
        self.scan_btn.pack(side=tk.LEFT, padx=(0, 10))
        self.clean_btn = ttk.Button(controls_frame, text="Run Subpurge (Clean)", command=self.start_clean, state=tk.DISABLED, cursor="hand2")
        self.clean_btn.pack(side=tk.LEFT, padx=(0, 10))
        self.cancel_btn = ttk.Button(controls_frame, text="Stop / Cancel", command=self.cancel_action, state=tk.DISABLED, cursor="hand2")
        self.cancel_btn.pack(side=tk.LEFT)
        ToolTip(self.cancel_btn, "WARNING: Cancelling mid-purge will abort the current file.")
        self.clear_btn = ttk.Button(controls_frame, text="Clear Log", command=self.clear_log, cursor="hand2")
        self.clear_btn.pack(side=tk.RIGHT)

        # --- Progress Bar & storage savings ---
        # set up variable to track from 0.0 to 100.0 then creating and packing the visual loading bar (ttk.Progressbar)
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress.pack(fill=tk.X)

        # UI label for savings tracker
        self.savings_var = tk.StringVar(value="Total space saved: 0.00 MB")
        ttk.Label(main_frame, textvariable=self.savings_var, font=("Ubuntu", 10, "bold"), foreground="#4CAF50").pack(side=tk.BOTTOM, pady=(10,0))

        # just some welcome text into the console log provided to user (tab 1)
        self.log("Welcome to Subtrack-Subpurge v1.3")
        self.log("Select directories, set your keep languages, any other settings, and click 'Run Subtrack'.\n" + "-" * 60)

        # --- Tabbed Interface ---
        # creating Notebook widget allows clickable tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # Tab 1: Live Log
        self.log_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.log_tab, text="Live Activity Log")
        # utilizing ScrolledText for built in scrollbar
        self.console = scrolledtext.ScrolledText(
            self.log_tab, wrap=tk.WORD, state=tk.DISABLED, 
            font=("Consolas", 10), bg="#1c1c1c", fg="#e0e0e0",
            insertbackground="white", relief=tk.FLAT, padx=10, pady=10
        )
        self.console.pack(fill=tk.BOTH, expand=True)

        # Tab 2: Review Queue
        # this tab is for users who want to go through and check for specific files
        self.queue_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.queue_tab, text="Review Queue")

        # using Treeview creates a spread of 3 columns
        self.tree = ttk.Treeview(self.queue_tab, columns=("include", "file", "tracks"), show="headings", selectmode="browse")
        self.tree.heading("include", text="Include")
        self.tree.heading("file", text="File Name")
        self.tree.heading("tracks", text="Foreign Tracks Found")
        self.tree.column("include", width=80, anchor=tk.CENTER)
        self.tree.column("file", width=400)
        self.tree.column("tracks", width=300)

        # select all button anchored at the bottom
        bottom_queue_frame = ttk.Frame(self.queue_tab)
        bottom_queue_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(0,5))
        ttk.Label(bottom_queue_frame, text="Click the [X] or [ ] to select/deselect files for purging.", font=("Ubuntu", 9, "italic")).pack(side=tk.LEFT)
        self.toggle_all_btn = ttk.Button(bottom_queue_frame, text="Select / Deselect All", command=self.toggle_all, cursor="hand2")
        self.toggle_all_btn.pack(side=tk.RIGHT)
        # packing Treeview to take all remaining space above the bottom frame
        self.tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(0, 10))
        # binding the select all button to toggle function
        self.tree.bind('<ButtonRelease-1>', self.toggle_selection)

    # Helper function for I/O directory rows
    def _add_path_row(self, parent, label_text, string_var, row, font):
        ttk.Label(parent, text=label_text, font=font).grid(row=row, column=0, sticky=tk.W, pady=8, padx=(0, 15))
        entry = ttk.Entry(parent, textvariable=string_var, width=50, font=font)
        entry.grid(row=row, column=1, pady=8, sticky=tk.EW)
        
        # function for opening a file browser dialog
        def browse():
            path = filedialog.askdirectory()
            # if statement for normalizing path and updating the text box
            if path: string_var.set(os.path.normpath(path))
        # creating browse button, linking it to browse function
        ttk.Button(parent, text="Browse", command=browse, cursor="hand2").grid(row=row, column=2, padx=(15, 0), pady=8, sticky=tk.EW)
        # text box stretches if window gets resized
        parent.columnconfigure(1, weight=1)
    
    def toggle_all(self):
        # get all rows (children) in treeview spreadsheet
        children = self.tree.get_children()
        if not children: 
            return

        # check if every item is currently checked
        all_checked = all(self.tree.item(item, "values")[0] == "[X]" for item in children)

        # if all_checked, uncheck them else check all
        new_state = "[ ]" if all_checked else "[X]"
        # then loop through every row and update first column to new state
        for item in children:
            vals = list(self.tree.item(item, "values")) # get vals
            vals[0] = new_state # change first column
            self.tree.item(item, values=vals) # save back to tree

    def _toggle_overwrite_checkbox(self, *args):
        # strip trailing spaces from the paths in text boxes
        in_path = self.input_dir.get().strip()
        out_path = self.output_dir.get().strip()

        # if statement for comparing directories arent empty
        if in_path and out_path and os.path.normpath(in_path) == os.path.normpath(out_path):
            # force overwrite checkbox to appear on screen
            self.protect_chk.grid(row=3,column=0,columnspan=3,sticky=tk.W,pady=(8,0))
        else:
            # hides without destroying data
            self.protect_chk.grid_remove()

    def log(self, message):
        """Helper function to print text to the user console log (tab 1) from any background thread"""
        def update_text():
            # unlock the text box, insert the message, scroll to the bottom, lock text box
            self.console.config(state=tk.NORMAL)
            self.console.insert(tk.END, message + "\n")
            self.console.see(tk.END)
            self.console.config(state=tk.DISABLED)
        # use root.after to force UI thread to update the text, preventing crashes
        self.root.after(0, update_text)

    def clear_log(self):
        """wipes the user console log clean"""
        self.console.config(state=tk.NORMAL)
        self.console.delete(1.0, tk.END)
        self.console.config(state=tk.DISABLED)

    def toggle_selection(self, event):
        """Simulates a checkbox by toggling [X] and [ ] when the first column is clicked."""
        # check exactly where the mouse clicked inside the treeview
        region = self.tree.identify("region", event.x, event.y)
        # if user didnt click an actual cell, ignore
        if region != "cell": return
        column = self.tree.identify_column(event.x)
        
        if column == "#1": # The 'include' column
            # get specific row user clicked
            item = self.tree.focus()
            if item:
                # grab the values
                vals = list(self.tree.item(item, "values"))
                # Flip the check state
                vals[0] = "[ ]" if vals[0] == "[X]" else "[X]"
                # save the values
                self.tree.item(item, values=vals)

    def cancel_action(self):
        """Function to stop the process when button is pressed"""
        self.log("\n[!] CANCELLATION REQUESTED - Stopping safe-state... [!]")
        # set the variable for current subprocess to True, breaking background loop
        self.cancel_flag.set()
        # if mkvmerge is currently mid-process, force kill
        if self.current_process:
            self.current_process.terminate()

    def on_scan_complete(self, files_found_count):
        """Runs automatically when the background scan thread finishes"""
        # re-enable scan button, disable cancel button, reset progress bar
        self.scan_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)
        self.progress_var.set(0)
        
        # if files have languages not specified, enable subpurge button
        if files_found_count > 0:
            self.clean_btn.config(state=tk.NORMAL)
            # trigger the popup window asking users if they want to review the queue
            review = messagebox.askyesno(
                "Scan Complete", 
                f"Found {files_found_count} files needing cleanup.\n\nWould you like to review the queue before purging?"
            )
            # If user clicks Yes, switch to the Queue tab. If No, do nothing and stay on the Log.
            if review:
                self.notebook.select(self.queue_tab)
        # if no files/excess languages found
        else:
            self.log("Scan finished. No files needed cleaning.")

    # ==========================================
    # PHASE 1: SUBTRACK (SCANNING)
    # ==========================================
    def start_scan(self):
        # validation for user selecting an input dir
        if not self.input_dir.get():
            self.log("[WARNING] Please select an Input Directory first.")
            return
        
        # disable buttons while scanning, stop button set to normal to allow user to stop the scan
        self.scan_btn.config(state=tk.DISABLED)
        self.clean_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        self.cancel_flag.clear()
        
        # clear queue spreadsheet
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # start the actual scanning loop in a separate bg thread so UI doesnt freeze
        threading.Thread(target=self._scan_process, daemon=True).start()

    def _scan_process(self):
        # creating the reporting directory in case it doesnt exist
        self.tracking_dir.mkdir(parents=True, exist_ok=True)
        # turn string path into a real Path obj
        input_path = Path(self.input_dir.get())
        # define file types to look at
        # FIXME und, avi, and unintentionally creating silent mkvs
        video_extensions = {".mkv", ".mp4", ".avi"}

        # get raw str of kept languages, default to eng and und if empty
        raw_langs = self.keep_langs_var.get()
        if not raw_langs.strip(): raw_langs = "eng,und"
        # create lowercase set of languages
        safe_languages = {lang.strip().lower() for lang in raw_langs.split(",")}

        self.log(f"--- STARTING SUBTRACK SCAN ---")
        
        # use rglob to recursively find every file in the folder and its subfolders
        all_files = list(input_path.rglob("*"))
        # count how many of those files are actually video file types program designed to care about
        total_files = len([f for f in all_files if f.suffix.lower() in video_extensions])
        processed_count = 0
        files_found_count = 0

        # loop through every file found
        for file in all_files:
            # if user hits cancel, break loop
            if self.cancel_flag.is_set(): break

            # if the file is a video
            if file.suffix.lower() in video_extensions:
                # build the command to identify the file in JSON format : 'mkvmerge -J "movie.mkv"'
                command = [self.mkvmerge_path, "-J", str(file)]
                try:
                    # run command and capture output text but if on windows do not open endless cmd prompt windows
                    if os.name == 'nt':
                        self.current_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', creationflags=subprocess.CREATE_NO_WINDOW)
                    else:
                        self.current_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')

                    stdout, stderr = self.current_process.communicate()
                    
                    # Returncode 0 means mkvmerge successfully read the file without crashing
                    if self.current_process.returncode == 0:
                        # convert the text output into a python dictionary
                        media_info = json.loads(stdout)
                        foreign_tracks = []
                        
                        # loop through every audio/subtitle track inside the MKV file
                        for track in media_info.get("tracks", []):
                            track_type = track.get("type")
                            if track_type in ("audio", "subtitles"):
                                # get its language code. if it doesnt have one, assume 'und'
                                lang = track.get("properties", {}).get("language", "und")
                                # if language is not in our kept languages, flag it
                                if lang not in safe_languages:
                                    foreign_tracks.append(f"{lang}")
                        # if unwanted languages/tracks found
                        if foreign_tracks:
                            # join them into a readable string and log the flag
                            tracks_str = ", ".join(foreign_tracks)
                            self.log(f"[FLAGGED] {file.name}")
                            # insert the movie into the review queue spreadsheet, check it by default
                            self.root.after(0, lambda f=file, t=tracks_str: self.tree.insert("", tk.END, iid=str(f), values=("[X]", f.name, t)))
                            files_found_count += 1
                # log any errors
                except Exception as e:
                    self.log(f"[ERROR] Failed reading {file.name}")
                # update progress bar
                processed_count += 1
                self.root.after(0, lambda p=(processed_count/max(1, total_files))*100: self.progress_var.set(p))
        
        # set scan to over by clearing active process tracking variable and calling completion function
        self.current_process = None
        self.log(f"\n--- SCAN COMPLETE ---")
        self.root.after(0, lambda: self.on_scan_complete(files_found_count))
    
    # ==========================================
    # PHASE 2: SUBPURGE (CLEANING)
    # ==========================================
    def start_clean(self):
        # validation for output dir selected, lock buttons
        if not self.output_dir.get():
            self.log("[WARNING] Please select an Output Directory first.")
            return
        self.scan_btn.config(state=tk.DISABLED)
        self.clean_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        self.cancel_flag.clear()
        # switch to log tab for user to watch progress
        self.notebook.select(self.log_tab)
        # start the bg cleaning thread
        threading.Thread(target=self._clean_process, daemon=True).start()

    def _clean_process(self):
        self.log("--- STARTING SUBPURGE ---")
        self.total_saved_bytes = 0
        # create output dir if doesnt exist
        output_base_path = Path(self.output_dir.get())
        output_base_path.mkdir(parents=True, exist_ok=True)

        # loop through the treeview and only grab files that where first column was selected
        files_to_process = []
        for item in self.tree.get_children():
            if self.tree.item(item, "values")[0] == "[X]":
                files_to_process.append(item)

        # store number of files to var, if everything deselected cancel out and reuse UI reset
        total_files = len(files_to_process)
        if total_files == 0:
            self.log("Queue is empty or all items deselected. Nothing to clean.\n")
            self.root.after(0, lambda: self.on_scan_complete(0))
            return

        # format kept languages for the mkvmerge command line, eng, und used again if nothing
        raw_langs = self.keep_langs_var.get()
        if not raw_langs.strip(): raw_langs = "eng,und"
        mkvmerge_langs = ",".join([lang.strip().lower() for lang in raw_langs.split(",")])

        # loop through every flagged file, stopping if canceled and skipping file if missing
        for index, item_id in enumerate(files_to_process):
            if self.cancel_flag.is_set(): break
            file = Path(item_id)
            if not file.exists():
                self.log(f"  [SKIPPED] File missing: {file.name}")
                continue
            self.log(f"Purging: {file.name}...")

            # no audio track prevent check here
            safe_languages = {lang.strip().lower for lang in raw_langs.split(',')}
            try:
                # running JSON check
                check_cmd = [self.mkvmerge_path, "-J", str(file)]
                cflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                check_process = subprocess.Popen(check_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', creationflags=cflags)
                stdout, _ = check_process.communicate()

                if check_process.returncode == 0:
                    media_info = json.loads(stdout)
                    safe_audio_count = 0

                    # count how many audio tracks match users keep list
                    for track in media_info.get("tracks", []):
                        if track.get("type") == "audio":
                            lang = track.get("properties", {}).get("language", "und")
                            if lang in safe_languages:
                                safe_audio_count += 1
                    
                    # if purging would leave 0 audio tracks this is the abort
                    if safe_audio_count == 0:
                        self.log(f"  [ERROR] Aborted: Purging would leave this file with 0 audio tracks!")
                        # set uncheck in the review queue
                        self.root.after(0, lambda i=item_id: self.tree.set(i, "include", "[ ]"))
                        continue
            except Exception as e:
                self.log(f"  [ERROR] Pre-check failed: {e}")
                continue

            # predict the new file name/automatically converting to mkv
            out_file = output_base_path / file.with_suffix('.mkv').name

            # --- Overwrite if statement to delete original files regarding keep original files? checkbox
            is_overwrite = False
            # if same path
            if out_file.resolve() == file.resolve():
                # if keep original file checked
                if self.protect_same_dir_var.get():
                    # modify name to append '_clean' and log for user clarity
                    out_file = output_base_path / f"{file.stem}_clean.mkv"
                    self.log(f"  [INFO] Appending '_clean' to protect original file.")
                else:
                    # checkbox is UNCHECKED, render new file as temp file by appending '_temp'
                    out_file = output_base_path / f"{file.stem}_temp.mkv"
                    # flag for swap later
                    is_overwrite = True
                    self.log(f"  [INFO] Overwrite Mode: Processing to temp file...")

            out_file.parent.mkdir(parents=True, exist_ok=True)
            original_size = file.stat().st_size
            # building command array for mkvmerge
            command = [
                self.mkvmerge_path,
                "-o", str(out_file), # define output file
                "--audio-tracks", mkvmerge_langs, # which audio to keeo
                "--subtitle-tracks", mkvmerge_langs, # which subtitles to keep
                str(file) # define input file
            ]

            try:
                # launch command (using same os check in _scan_process) and while the command is running check if the user hit cancel
                if os.name == 'nt':
                    self.current_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    self.current_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                while self.current_process.poll() is None:
                    if self.cancel_flag.is_set():
                        self.current_process.terminate()
                        self.log(f"  [ABORTED] {file.name} was killed mid-process.")
                        # clean any half-baked file if user hits cancel mid-overwrite
                        if out_file.exists():
                            out_file.unlink()
                        break
                    time.sleep(0.5)
                
                # if process finished without being cancelled
                if not self.cancel_flag.is_set():
                    # --- return code validation
                    if self.current_process.returncode == 0:
                        # if doing a true overwrite
                        if is_overwrite:
                            try:
                                file.unlink() # delete the og file
                                out_file.rename(file) # rename the temp file to the og name
                                out_file = file # update var for success log
                            except Exception as e:
                                self.log(f"  [ERROR] Could not replace original file: {e}")
                        self.log(f"  [SUCCESS] Saved to -> {out_file.name}")

                        # calculate the space saved
                        new_size = out_file.stat().st_size
                        saved = original_size - new_size

                        if saved > 0:
                            self.total_saved_bytes += saved

                            if self.total_saved_bytes > 1024**3:
                                display_txt = f"Total space saved: {self.total_saved_bytes/(1024**3):.2f} GB"
                            else:
                                display_txt = f"Total space saved: {self.total_saved_bytes/(1024**2):.2f} MB"
                            self.root.after(0, lambda d=display_txt: self.savings_var.set(d))
                        # remove file from review queue
                        self.root.after(0, lambda i=item_id: self.tree.delete(i))
                    # if return code is NOT 0, something is broken
                    else:
                        # Catch MKVMerge error text
                        _, stderr_data = self.current_process.communicate()
                        err_msg = stderr_data.decode('utf-8', errors='ignore').strip() if stderr_data else "Unknown MKVToolNix error."
                        self.log(f"  [ERROR] mkvmerge rejected {file.name}")
                        self.log(f"         Reason: {err_msg}")
                        # delete any temp files that failed
                        if is_overwrite and out_file.exists():
                            out_file.unlink()
                    
            except Exception as e:
                self.log(f"  [ERROR] Failed to process {file.name}")
                self.log(f"         Reason: {e}")
                
            self.root.after(0, lambda p=((index+1)/total_files)*100: self.progress_var.set(p))

        self.current_process = None
        self.log("\n--- SUBPURGE FINISHED ---\n")
        messagebox.showinfo("Purge Complete", f"All {total_files} items purged successfully.")
        
        # Reset UI securely on the main thread
        def final_reset():
            self.scan_btn.config(state=tk.NORMAL)
            self.cancel_btn.config(state=tk.DISABLED)
            self.progress_var.set(0)
            # re-enable the clean button if there are still items left in queue
            if self.tree.get_children():
                self.clean_btn.config(state=tk.NORMAL)
        self.root.after(0, final_reset)

if __name__ == "__main__":
    root = tk.Tk() # initialize tkinter
    app = SubpurgeApp(root) # pass it to class
    root.mainloop() # start infinite loop that listens to mouse clicks