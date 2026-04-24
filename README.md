# Subtrack-Subpurge MKV Batch Cleaner

Subtrack-Subpurge is a lightweight, two-step Python utility designed to scan massive MKV video libraries and surgically strip out unwanted foreign audio and subtitle tracks, saving you significant hard drive space.

Built with a modern GUI, Subtrack-Subpurge leverages the incredible speed of MKVToolNix to remux files without re-encoding them—meaning it processes movies as fast as your hard drive can write them.

## Features
* **Smart Default Track Enforcer:** Automatically detects your kept audio and subtitle tracks and permanently hardcodes them as the "Default" tracks, ensuring media players (like Plex or VLC) play them instantly without manual selection.
* **Detailed Purge Receipts:** Generates an optional, non-intrusive summary window at the end of a purge detailing exactly which tracks were stripped from each individual file.
* **Drag & Drop Omni-Scanner:** Seamlessly drag and drop entire folders, individual video files, or a chaotic mix of both directly into the app. 
* **Storage Savings Tracker:** Watch your recovered hard drive space climb in real-time with a live "GBs Saved" counter.
* **0-Audio Track Safeguard:** Built-in logic prevents the app from accidentally muting your videos. If a purge would result in a file with zero audio tracks, the app automatically aborts that file and flags it.
* **Non-Destructive by Default:** Creates a clean copy of your MKV in a designated output folder, leaving your original file completely untouched (with an option for True Overwrite if preferred).

## Prerequisites
Before running Subtrack-Subpurge, you must have **MKVToolNix** installed on your system, as this script acts as a graphical wrapper for its powerful `mkvmerge` command-line tool.

* **Windows:** Download the installer from the [MKVToolNix website](https://mkvtoolnix.download/downloads.html#windows). The app will automatically find it.
* **Linux (Debian/Ubuntu):** `sudo apt install mkvtoolnix`
* **Python 3.6+**

## Installation

1. **Clone the repository:**
    git clone https://github.com/ms00l/subtrack-subpurge.git
    cd subtrack-subpurge

2. **Set up a virtual environment (Required for Linux, Recommended for Windows):**
    python3 -m venv venv
    source venv/bin/activate  # On Windows use: venv\Scripts\activate

3. **Install the dependencies:**
    pip install -r requirements.txt
    *(This automatically installs the `sv-ttk` dark theme and `tkinterdnd2` for drag-and-drop support).*

## How to Use

Launch the application from your terminal:
    python3 main.py

1. **Set Input/Output:** Drag and drop your MKV files or folders into the Input Directory box. Select an empty folder for the Output Directory.
2. **Set Languages:** Enter the 3-letter language codes you want to **KEEP**, separated by commas (e.g., `eng,und`). *Note: Keeping `und` (undetermined) is highly recommended so you don't accidentally strip English tracks that were improperly tagged.*
3. **Run Subtrack:** The app will scan your input and generate an interactive queue in the second tab.
4. **Run Subpurge:** Review your files, click Clean, and watch the Storage Savings Tracker count up as your files are remuxed!

## ⚠️ Disclaimer
While Subtrack-Subpurge is designed to be non-destructive by outputting to a new folder, always test batch automation tools on a small sample folder before pointing them at your entire media server!

### ⚠️ Known Issues
* **The `und` (Undetermined) Trap:** By default, Subtrack-Subpurge keeps `eng,und` tracks. Because many release groups lazily leave foreign tracks unlabelled, they default to `und`. Subtrack-Subpurge will see these foreign tracks as "safe" and skip the file. Remove `und` from your keep list to strip them, but VERIFY YOUR FILES FIRST.

## 📝 Changelog

### v1.5.0 (Current)
* **Default Track Enforcer:** The app now dynamically injects `--default-track` flags into the MKVToolNix command. Your kept Primary tracks are automatically hardcoded as the default tracks so media players no longer play silent videos.
* **Detailed Purge Receipts:** Added a custom summary popup window at the end of a session that provides a clean, copy-pasteable "receipt" of exactly which tracks were stripped from each file.
* **Smart Warning Catcher:** The app now safely accepts non-fatal `mkvmerge` warnings (like auto-repairing duplicate UIDs in dummy files) as successful purges instead of aborting them, and logs the specific warning in the UI.
* **Middle-Click Auto-Scroll:** Bound middle-mouse wheel clicks for buttery smooth "hand-grab" navigation in the Review Queue and Live Log.
* **Persistent Configuration:** Added a `config.json` save system. The app now silently remembers your Input/Output paths and Custom Languages between launches.
* **Bug Fix:** Resolved a critical logic error during "True Overwrite" that caused MKVToolNix to clone files instead of replacing them, fixing the Storage Savings Tracker math.

### v1.4.0 
* **Drag & Drop Integration:** Completely overhauled the input system with `tkinterdnd2`. 
* **Omni-Scanner Engine:** The backend scanner was rewritten to support single files, multiple files, or massive folders all in the same batch.
* **File Size Savings Tracker:** Added a real-time UI counter displaying total MBs/GBs recovered.

### v1.3.1 
* **Mid-Purge Cancel Safety:** Pressing "Stop/Cancel" mid-purge now actively hunts down and deletes broken, half-written `.mkv` files.
* **0-Audio Track Safeguard:** If your language settings would result in a completely silent video, it skips the file and logs an error.