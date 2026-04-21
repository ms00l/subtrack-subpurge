# Subtrack-Subpurge MKV Batch Cleaner

Subtrack-Subpurge is a lightweight, two-step Python utility designed to scan massive MKV video libraries and surgically strip out unwanted foreign audio and subtitle tracks, saving you significant hard drive space.

Built with a modern GUI, Subtrack-Subpurge leverages the incredible speed of MKVToolNix to remux files without re-encoding them—meaning it processes movies as fast as your hard drive can write them.

## Features
* **Drag & Drop Omni-Scanner:** Seamlessly drag and drop entire folders, individual video files, or a chaotic mix of both directly into the app. Subtrack-Subpurge will instantly sort and queue them.
* **Storage Savings Tracker:** Watch your recovered hard drive space climb in real-time with a live "GBs Saved" counter during the purge process.
* **Two-Step Safety System:** Scans your library first and builds an interactive UI queue. You can review exactly what will be deleted before making any permanent changes.
* **0-Audio Track Safeguard:** Built-in logic prevents the app from accidentally muting your videos. If a purge would result in a file with zero audio tracks, the app automatically aborts that file and flags it.
* **Customizable Targets:** Tell the app exactly which 3-letter language codes to keep (e.g., `eng`, `spa`, `jpn`). It strips everything else.
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

* **Duplicate Language Tags:** Subtrack-Subpurge strictly filters by the 3-letter language code. If a movie contains a main English track (`eng`) and an English Director's Commentary (`eng`), the app cannot distinguish between the two and will keep both. 
* **The `und` (Undetermined) Trap:** By default, Subtrack-Subpurge keeps `eng,und` tracks. Because many release groups lazily leave foreign tracks unlabelled, they default to `und`. Subtrack-Subpurge will see these foreign tracks as "safe" and skip the file. 
  * *Workaround:* Remove `und` from your keep list (just use `eng`), but **VERIFY YOUR FILES FIRST**, as some main English tracks are also lazily tagged as `und`.

## 📝 Changelog

### v1.4.0 (Current)
* **Drag & Drop Integration:** Completely overhauled the input system with `tkinterdnd2`. You can now drag files and folders directly from your OS into the app.
* **Omni-Scanner Engine:** The backend scanner was rewritten to support mixed inputs. You can now process single files, multiple files, or massive folders all in the same batch.
* **File Size Savings Tracker:** Added a real-time UI counter that calculates the exact byte difference between your original and cleaned files, displaying total MBs/GBs recovered.

### v1.3.1 
* **Mid-Purge Cancel Safety:** Pressing "Stop/Cancel" mid-purge now actively hunts down and deletes the broken, half-written `.mkv` file it was currently processing.
* **Silent Backgrounding (Windows):** Fixed an issue where `mkvmerge` would spawn a flashing Command Prompt window for every single file scanned on Windows.
* **0-Audio Track Safeguard:** The app now runs a pre-check before purging. If your language settings would result in a completely silent video, it skips the file and logs an error.
* **Dynamic MKVToolNix Locator:** If `mkvmerge.exe` isn't in its default directory, the app now prompts the user with a file browser to locate it manually instead of crashing.
* **Persistent Progress Bar:** Fixed a UI bug where resizing the window would push the progress bar off the screen.

### v1.3.0
* **Same-Folder Protection & True Overwrite:** Added a "Keep original file?" toggle to safely append `_clean` to files, or execute a true overwrite via temp-file swapping.
* **Smart Error Handling:** Strict validation of MKVToolNix return codes. Failures now print exact system errors to the log.
* **Queue Management:** Added a "Select / Deselect All" smart toggle button to the Review Queue.

### Future Roadmap (v1.5.0)
* **Middle-Click Auto-Scroll:** Bind middle-mouse wheel clicks to the Log and Queue for buttery smooth navigation of massive libraries.
* **Smart `und` (Undetermined) Logic:** Highlight files with undetermined tracks in yellow inside the Review Queue as a visual warning.
* **Persistent Configuration:** Save user preferences (Input/Output paths, Keep Languages) to a `config.json` file so they load automatically on the next launch.