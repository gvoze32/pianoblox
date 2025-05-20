# Pianoblox - Universal Virtual Piano Autoplayer

Pianoblox is a universal virtual piano autoplayer that allows you to play notes on online piano applications automatically. It supports both manual note playing and MIDI file playback.

## Features

- Play virtual piano notes using hotkeys
- Load and play MIDI files automatically
- Adjustable playback speed
- Manual and automatic playback modes
- Support for online virtual piano platforms
- MIDI file management (import, delete)

## Requirements

- Python 3.6 or higher
- pynput library (for keyboard control)
- appdirs library (for application data management)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/pianoblox.git
   cd pianoblox
   ```

2. Install required dependencies:
   ```
   pip install pynput appdirs
   ```

3. Run the application:
   ```
   python pianoblox.py
   ```

## System Permissions

### Important Note for macOS Users

You need to grant permissions in System Settings > Privacy & Security for both:
- Accessibility
- Input Monitoring

This allows Pianoblox to control other applications and send keystrokes.

## Usage

### Manual Mode

1. Paste piano sheet notes in the text input area
2. Use the following hotkeys to play notes one by one:
   - `-` (minus key)
   - `=` (equals key)
   - `[` (left bracket)
   - `]` (right bracket)
3. The "Next Notes" display shows upcoming notes

### MIDI Playback

1. MIDI files are stored in your system's application data directory:
   - Windows: `%APPDATA%\PianoBlox\midi`
   - macOS: `~/Library/Application Support/PianoBlox/midi`
   - Linux: `~/.local/share/pianoblox/midi`
2. Use "Browse & Import..." to select and import MIDI files from anywhere on your system
3. Select a MIDI file from the list and click "Load Selected MIDI" to load it
4. Use the autoplay controls:
   - `DELETE`: Start/Stop playback
   - `HOME`: Rewind by 10 notes
   - `END`: Skip forward by 10 notes
   - `PAGE UP`: Increase playback speed
   - `PAGE DOWN`: Decrease playback speed
5. Or use the GUI buttons for Speed controls and Autoplay
6. To remove MIDI files from your collection, select a file and click "Delete Selected"

### Note Format

Notes should be in the format:
```
q w e [rt] y / [tyu] o p
```

Where:
- Single letters are individual notes
- Multiple letters in square brackets `[]` are chords
- Forward slash `/` is a visual separator (ignored during playback)

### Number to QWERTY Mapping

Numbers are automatically mapped to QWERTY keys:
- `1` → `q`
- `2` → `w`
- `3` → `e`
- ...and so on

## Troubleshooting

- **No notes being played**: Ensure the virtual piano window is active when using hotkeys
- **Permission issues**: Check that proper permissions are granted for keyboard control
- **MIDI errors**: Verify that MIDI files are valid and in standard format
- **Missing MIDI directory**: The application automatically creates all necessary directories the first time it runs

## License

This project is licensed under the MIT License - see the LICENSE file for details. 