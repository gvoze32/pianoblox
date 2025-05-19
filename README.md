# Pianoblox - Universal Virtual Piano Autoplayer

Pianoblox is a Python script designed to automatically play music sheets on virtual pianos, especially those found on platforms like Roblox. This script uses `tkinter` for the graphical user interface (GUI) and `pynput` to send keystrokes.

## Features

*   Plays music sheets pasted into the GUI.
*   Displays the next notes to be played.
*   "Reload Music / Start Over" button to restart the song or after changing sheets.
*   Configurable hotkeys (`-`, `=`, `[`, `]`) to play notes one by one.
*   AlwaysOnTop window for easy access.

## Requirements

*   Python 3
*   `pynput` (for keyboard control)
*   `tkinter` (standard GUI framework)

## Installation

1.  **Set up a Virtual Environment (Recommended):**
    It's highly recommended to use a virtual environment to manage project dependencies.
    *   Navigate to your project directory in the terminal.
    *   Create a virtual environment (e.g., named `venv`):
        ```bash
        python3 -m venv venv
        ```
    *   Activate the virtual environment:
        *   On macOS and Linux:
            ```bash
            source venv/bin/activate
            ```
        *   On Windows:
            ```bash
            venv\\Scripts\\activate
            ```
    You should see the virtual environment name (e.g., `(venv)`) in your terminal prompt.

2.  **GUI Library (tkinter):**
    *   On **Windows**, `tkinter` usually comes bundled with Python.
    *   On **macOS**:
        *   `tkinter` usually comes bundled with Python installations from python.org.
        *   If you are using Python installed via **Homebrew** and `tkinter` is missing, you might need to install it using:
            ```bash
            brew install python-tk
            ```
            (Ensure your Homebrew-installed Python is the one used in your virtual environment if you go this route).
    *   On **Linux**, `tkinter` often needs to be installed separately using your system's package manager. For example:
        *   Debian/Ubuntu: `sudo apt-get install python3-tk`
        *   Fedora: `sudo dnf install python3-tkinter`
    (These system-level installations of tkinter should be available to your virtual environment's Python interpreter).

3.  **Install the `pynput` library** using pip (within your activated virtual environment):
    ```bash
    pip install pynput
    ```

## Running Pianoblox

1.  Open your terminal or command prompt.
2.  **Activate your virtual environment** if you used one during installation:
    *   On macOS and Linux: `source venv/bin/activate`
    *   On Windows: `venv\\Scripts\\activate`
3.  Run the script using the command:
    ```bash
    python pianoblox.py 
    ```
    (Or `python3 pianoblox.py` if `python` doesn't point to Python 3 in your environment).

## How to Use

1.  **Run the Script**: After running the command above, a small window titled "Python Auto Piano Player (Universal)" will appear.
2.  **Copy Music Sheets**: Copy the music sheets you want to play. The expected format is plain text, where notes are separated by spaces or newlines. Notes played together (chords) can be grouped in square brackets, e.g., `[asd]`. Example:
    ```
    q w e [rt] y / [tyu] o p
    [4o] p s g f d
    5 a s d s
    ```
3.  **Paste Music Sheets**: Paste the copied sheets into the large text box in the script's window ("Paste Music Sheets Here:").
4.  **Click "Reload Music / Start Over"**: After pasting the music sheets, **always click the "Reload Music / Start Over" button**. This will load the new music and reset the position to the beginning of the song.
5.  **Activate Virtual Piano Window**: **Click on the virtual piano window (e.g., in Roblox)** to make it the active window. The script sends keystrokes to the currently active window.
6.  **Play with Hotkeys**: Press one of the defined hotkeys: `-`, `=`, `[`, or `]`. Each press will play the next note or chord. The "Next Notes:" area will show the remaining notes to be played.

## For macOS Users

If you are using macOS, you may need to grant specific permissions to Terminal or the Python application you are using to run the script. Without these permissions, the script will not be able to send keystrokes or monitor them across applications like Roblox.

1.  Open **System Settings**.
2.  Navigate to **Privacy & Security**.
3.  In this section, you may need to check and grant permissions in two places:
    *   **Accessibility**: Scroll down and select Accessibility. Find your **Terminal** app (or your IDE/Python launcher) in the list. Ensure the switch next to it is toggled **on**. If it's not there, click the `+` button to add it.
    *   **Input Monitoring**: Find and select Input Monitoring. Similarly, ensure your **Terminal** app (or IDE/Python launcher) is listed and enabled. If not, add it using the `+` button.
4.  You may need to restart the script after granting these permissions.

## Important Notes & Current Issues

*   **Hotkey Character Typing**: Currently, due to a diagnostic change to address issues with sequential note playing, the hotkey character you press (`-`, `=`, `[`, `]`) might also be typed into the active window (e.g., Roblox). This is a temporary side effect.
*   **Speed (Delay)**:
    *   `KEY_DELAY` (currently `0.1` seconds) at the top of the script controls the pause *after* a note is played, before the next note can be triggered. You can adjust this value if it feels too fast or too slow.
    *   There is also a `time.sleep(0.05)` delay before each keystroke is sent. This was added for stability.
*   **Numeric Notes**: If numeric notes (e.g., `4` in `[4o]` or `5` in `5 a s`) do not produce sound, first ensure that those number keys do produce sound when pressed manually on the virtual piano you are using. The script sends numeric characters as they are.

## Contributions

If you find a bug or have suggestions, please open an issue or submit a pull request. 