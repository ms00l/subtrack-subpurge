# Subtrack-Subpurge MKV Batch Cleaner

Subtrack-Subpurge is a lightweight, two-step Python utility designed to scan massive MKV video libraries and surgically strip out unwanted foreign audio and subtitle tracks, saving you significant hard drive space.

Built with a modern GUI, Subtrack-Subpurge leverages the incredible speed of MKVToolNix to remux files without re-encoding them—meaning it processes movies as fast as your hard drive can write them.

## Features
* **Two-Step Safety System:** Scans your library first and builds a text-based queue. You can review exactly what will be deleted before making any permanent changes.
* **Customizable Targets:** Tell the app exactly which 3-letter language codes to keep (e.g., `eng`, `spa`, `jpn`). It strips everything else.
* **Non-Destructive by Default:** Creates a clean copy of your MKV in a designated output folder, leaving your original file completely untouched.
* **Modern GUI:** Built with Python's native `tkinter` and stylized with the `sv-ttk` dark theme.
* **Threaded Processing:** The UI stays responsive while processing gigabytes of data in the background.

## Prerequisites
Before running Subtrack-Subpurge, you must have **MKVToolNix** installed on your system, as this script acts as a graphical wrapper for its powerful `mkvmerge` command-line tool.

* **Linux (Debian/Ubuntu):** `sudo apt install mkvtoolnix`
* Make sure `mkvmerge` is accessible in your system's global `$PATH` (Linux handles this automatically when installed via `apt`).
* **Python 3.6+**

## Installation

1. **Clone the repository:**
   `git clone https://github.com/ms00l/subtrack-subpurge.git`
   `cd subtrack-subpurge`

2. **Set up a virtual environment (Recommended):**
   `python3 -m venv venv`
   `source venv/bin/activate`

3. **Install the UI Theme:**
   `pip install sv-ttk`

## How to Use

Launch the application from your terminal:
`python3 main.py`

1. **Set Input/Output:** Select the folder containing your MKVs, and select an empty folder where you want the cleaned files to go.
2. **Set Languages:** Enter the 3-letter language codes you want to **KEEP**, separated by commas (e.g., `eng,und`). *Note: Keeping `und` (undetermined) is highly recommended so you don't accidentally strip English tracks that were improperly tagged by the creator.*
3. **Run Subtrack:** The app will scan your input folder and generate a `subtrack_queue.txt` file in the local `/reports` directory.
4. **Run Subpurge:** Once the scan is complete, click Clean. The app will read the queue and begin remuxing your files into the Output directory.

## ⚠️ Disclaimer
While Subtrack-Subpurge is designed to be non-destructive by outputting to a new folder, always test batch automation tools on a small sample folder before pointing them at your entire media server!

## 📝 Changelog

### v1.2.0 (Current)
* **OS-Aware Pathing:** Added dynamic path detection so Subtrack-Subpurge automatically finds the correct `mkvmerge` directory whether running on Linux or Windows.
* **Verbose Error Handling:** Un-hid the background exception blocks. If a file fails to process, the log now prints the exact system error instead of a generic failure message.
* **Interactive Review Queue:** Replaced the text-file queue with a tabbed GUI interface. Users can now visually review flagged files and use checkboxes `[X]` to include or exclude specific movies before purging.
* **Progress Bar Tracking:** Added a visual progress bar that tracks both the scanning and cleaning phases in real-time.
* **Emergency Stop / Cancel:** Added a cancellation event thread. Users can now safely abort the scanning or purging process mid-execution without corrupting files.

### v1.1.0
* **Clear Log Function:** Added a UI button to clear the console output.