import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog, ttk
import re
import time
import threading
import os
import sys
import codecs
import random

try:
    from pynput import keyboard
except ImportError:
    print("The 'pynput' library is required. Please install it via: pip install pynput")
    messagebox.showerror("Dependency Missing", "The 'pynput' library is required.\nPlease install it via: pip install pynput")
    exit()

# --- Global Variables ---
current_idx_cleaned = 0
current_idx_raw_display = 0
piano_music_raw_cache = ""
piano_music_cleaned_cache = ""

KEY_DELAY = 0.1
HOTKEY_CHARS = {'-', '=', '[', ']'} 

# --- Number to QWERTY letter mapping ---
NUM_TO_LETTER_MAP = {
    '1': 'q', '2': 'w', '3': 'e', '4': 'r', '5': 't',
    '6': 'y', '7': 'u', '8': 'i', '9': 'o', '0': 'p'
}

# --- MIDI Playback Variables ---
isPlaying = False
storedIndex = 0
elapsedTime = 0
playback_speed = 1.0
origionalPlaybackSpeed = 1.0
speedMultiplier = 2.0
infoTuple = None
heldNotes = {}
legitModeActive = False

conversionCases = {'!': '1', '@': '2', '£': '3', '$': '4', '%': '5', '^': '6', '&': '7', '*': '8', '(': '9', ')': '0'}

kb_controller = keyboard.Controller()

root = None
piano_music_input_widget = None
next_notes_display_widget = None
keyboard_listener_object = None
midi_listbox = None
speed_label = None
autoplay_button = None
status_label = None

# --- Core Logic Functions ---
def update_music_caches():
    """Reads music from input, updates raw and cleaned caches. Returns True if changed."""
    global piano_music_raw_cache, piano_music_cleaned_cache, current_idx_cleaned, current_idx_raw_display
    
    if not piano_music_input_widget:
        return False

    current_raw_music = piano_music_input_widget.get("1.0", tk.END).strip()
    
    if current_raw_music != piano_music_raw_cache:
        piano_music_raw_cache = current_raw_music
        piano_music_cleaned_cache = re.sub(r"[\s/]", "", piano_music_raw_cache)
        current_idx_cleaned = 0
        current_idx_raw_display = 0
        return True
    return False

def reset_progress_state():
    """Resets playback indices and clears the 'Next Notes' display."""
    global current_idx_cleaned, current_idx_raw_display
    current_idx_cleaned = 0
    current_idx_raw_display = 0
    if next_notes_display_widget:
        next_notes_display_widget.config(state="normal")
        next_notes_display_widget.delete("1.0", tk.END)
        next_notes_display_widget.config(state="disabled")

def handle_reset_button():
    """Action for the Reload Music / Start Over button."""
    global isPlaying, storedIndex, elapsedTime, status_label
    
    update_music_caches() 
    reset_progress_state()
    
    isPlaying = False
    storedIndex = 0
    elapsedTime = 0
    if autoplay_button:
        autoplay_button.config(text="Start Autoplay")
    
    if status_label:
        status_label.config(text="Music reloaded and playback reset")

def translate_notes_for_typing(notes_to_translate):
    """Translates number characters in a string to their corresponding QWERTY letters."""
    translated_chars = []
    for char in notes_to_translate:
        translated_chars.append(NUM_TO_LETTER_MAP.get(char, char))
    return "".join(translated_chars)

def play_next_note_action():
    """Plays the next note based on the current state and input music."""
    global current_idx_cleaned, current_idx_raw_display, piano_music_raw_cache, piano_music_cleaned_cache, status_label

    if update_music_caches(): 
        reset_progress_state()

    raw_music = piano_music_raw_cache
    cleaned_music = piano_music_cleaned_cache

    if not cleaned_music:
        print("[Debug] play_next_note_action: No cleaned music to play.")
        if status_label:
            status_label.config(text="No music to play")
        return

    if current_idx_cleaned >= len(cleaned_music):
        print("[Debug] play_next_note_action: End of song reached.")
        reset_progress_state()
        if next_notes_display_widget:
            next_notes_display_widget.config(state="normal")
            next_notes_display_widget.delete("1.0", tk.END)
            next_notes_display_widget.insert(tk.END, "♪ End of song. Press hotkey to play again or Reset. ♪")
            next_notes_display_widget.config(state="disabled")
        if status_label:
            status_label.config(text="End of song reached")
        return

    match = re.match(r"(\[.*?]|.)", cleaned_music[current_idx_cleaned:])
    if match:
        note_token = match.group(1)
        keys_to_send_original = note_token.strip("[]")
        
        keys_to_send = translate_notes_for_typing(keys_to_send_original)

        current_idx_cleaned += len(note_token)
        print(f"[Debug] play_next_note_action: Raw token: '{note_token}', Original for typing: '{keys_to_send_original}', Translated for typing: '{keys_to_send}', new clean_idx: {current_idx_cleaned}")

        while (current_idx_raw_display < len(raw_music) and 
               raw_music[current_idx_raw_display] in " \n\r/"):
            current_idx_raw_display += 1
        
        if current_idx_raw_display < len(raw_music):
            current_idx_raw_display += len(note_token)
        
        if next_notes_display_widget:
            next_notes_display_widget.config(state="normal")
            next_notes_display_widget.delete("1.0", tk.END)
            safe_display_start_idx = min(current_idx_raw_display, len(raw_music))
            next_notes_str = raw_music[safe_display_start_idx : safe_display_start_idx + 90]
            next_notes_display_widget.insert(tk.END, next_notes_str)
            next_notes_display_widget.config(state="disabled")

        if status_label:
            status_label.config(text=f"Playing note: {keys_to_send_original}")

        if keys_to_send: 
            time.sleep(0.05)
            kb_controller.type(keys_to_send)
        
        time.sleep(KEY_DELAY)

# --- Hotkey Listener ---
def on_key_press(key):
    """Callback for pynput keyboard listener for keypresses."""
    global root
    print(f"[Debug] on_key_press: Key {key} pressed.")
    
    if key in [keyboard.Key.delete, keyboard.Key.home, keyboard.Key.end, 
               keyboard.Key.page_up, keyboard.Key.page_down]:
        handle_midi_keypress(key)
        
    try:
        pressed_char = key.char
        if pressed_char and pressed_char in HOTKEY_CHARS:
            print(f"[Debug] on_key_press: Hotkey '{pressed_char}' detected.")
            if root:
                print("[Debug] on_key_press: Scheduling play_next_note_action via root.after_idle()")
                root.after_idle(play_next_note_action)
    except AttributeError:
        pass
        
    return True

def start_keyboard_listener():
    global keyboard_listener_object
    keyboard_listener_object = keyboard.Listener(on_press=on_key_press, daemon=True)
    keyboard_listener_object.start()

# --- GUI Setup ---
def setup_and_run_gui():
    global root, piano_music_input_widget, next_notes_display_widget, keyboard_listener_object
    global midi_listbox, speed_label, autoplay_button, status_label

    print("[Debug] setup_and_run_gui: Initializing GUI...")
    root = tk.Tk()
    root.title("Pianoblox - Universal Piano Autoplayer")
    root.wm_attributes("-topmost", 1)
    
    bg_color = "#f5f5f5"
    header_color = "#2c3e50"
    accent_color = "#3498db"
    button_color = "#2980b9"
    button_text_color = "white"
    section_bg = "#ffffff"
    border_color = "#bdc3c7"
    
    root.configure(bg=bg_color)
    
    style = ttk.Style()
    style.configure("TFrame", background=bg_color)
    style.configure("Section.TFrame", background=section_bg, relief="solid", borderwidth=1)
    style.configure("TButton", background=button_color, foreground=button_text_color, font=("Arial", 10, "bold"))
    style.map("TButton", background=[("active", accent_color)])
    style.configure("TLabel", background=bg_color, font=("Arial", 10))
    style.configure("Header.TLabel", background=header_color, foreground="white", font=("Arial", 14, "bold"), padding=10)
    style.configure("Section.TLabel", background=section_bg, font=("Arial", 11, "bold"), padding=5)
    
    main_container = ttk.Frame(root, style="TFrame", padding=10)
    main_container.pack(fill=tk.BOTH, expand=True)
    
    header_frame = tk.Frame(main_container, bg=header_color, height=60)
    header_frame.pack(fill=tk.X, padx=2, pady=(0, 10))
    
    title_label = tk.Label(header_frame, text="Pianoblox", font=("Arial", 22, "bold"), 
                           bg=header_color, fg="white")
    title_label.pack(side=tk.LEFT, padx=15, pady=10)
    
    subtitle_label = tk.Label(header_frame, text="Universal Piano Autoplayer", 
                            font=("Arial", 12), bg=header_color, fg="#ecf0f1")
    subtitle_label.pack(side=tk.LEFT, padx=5, pady=10)
    
    input_frame = ttk.Frame(main_container, style="Section.TFrame", padding=10)
    input_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=5)
    
    ttk.Label(input_frame, text="Paste Music Sheets Here (or Load MIDI File):", 
             style="Section.TLabel").pack(anchor="w", pady=(0, 5))
    
    piano_music_input_widget = scrolledtext.ScrolledText(
        input_frame, height=8, width=65, wrap=tk.WORD, 
        font=("Consolas", 11), borderwidth=1,
        background="white", foreground="#2c3e50"
    )
    piano_music_input_widget.pack(fill=tk.BOTH, expand=True, pady=5)
    piano_music_input_widget.insert(tk.INSERT, "Example: q w e [rt] y / [tyu] o p")
    
    midi_frame = ttk.Frame(main_container, style="Section.TFrame", padding=10)
    midi_frame.pack(fill=tk.BOTH, padx=2, pady=5)
    
    ttk.Label(midi_frame, text="Available MIDI files in /midi/ folder:", 
             style="Section.TLabel").pack(anchor="w", pady=(0, 5))
    
    midi_list_frame = ttk.Frame(midi_frame)
    midi_list_frame.pack(fill=tk.BOTH, expand=True)
    
    midi_listbox = tk.Listbox(
        midi_list_frame, height=6, 
        font=("Consolas", 10),
        background="white", foreground="#2c3e50",
        borderwidth=1, relief="solid",
        selectbackground=accent_color, selectforeground="white"
    )
    midi_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    scrollbar = tk.Scrollbar(midi_list_frame, orient="vertical")
    scrollbar.config(command=midi_listbox.yview)
    scrollbar.pack(side=tk.RIGHT, fill="y")
    midi_listbox.config(yscrollcommand=scrollbar.set)
    
    refresh_midi_list()
    
    midi_button_frame = ttk.Frame(midi_frame, padding=(0, 10, 0, 0))
    midi_button_frame.pack(fill=tk.X)
    
    load_midi_button = ttk.Button(
        midi_button_frame, text="Load Selected MIDI", 
        command=load_selected_midi, style="TButton"
    )
    load_midi_button.pack(side=tk.LEFT, padx=(0, 5))
    
    browse_midi_button = ttk.Button(
        midi_button_frame, text="Browse for MIDI...", 
        command=browse_for_midi, style="TButton"
    )
    browse_midi_button.pack(side=tk.LEFT)
    
    control_frame = ttk.Frame(main_container, style="Section.TFrame", padding=10)
    control_frame.pack(fill=tk.BOTH, padx=2, pady=5)
    
    ttk.Label(control_frame, text="Autoplay Controls:", 
             style="Section.TLabel").pack(anchor="w", pady=(0, 5))
    
    shortcuts_frame = ttk.Frame(control_frame)
    shortcuts_frame.pack(fill=tk.X, pady=5)
    
    shortcut_text = "DELETE: Start/Stop | HOME: Rewind | END: Next | PAGE UP/DOWN: Speed"
    ttk.Label(shortcuts_frame, text=shortcut_text, 
             background=section_bg, font=("Arial", 9)).pack(anchor="w")
    
    speed_frame = ttk.Frame(control_frame, padding=(0, 5))
    speed_frame.pack(fill=tk.X)
    
    speed_label = tk.Label(
        speed_frame, text=f"Speed: {playback_speed:.2f}x", 
        font=("Arial", 11, "bold"), bg=section_bg
    )
    speed_label.pack(side=tk.LEFT, padx=(0, 10))
    
    speed_buttons_frame = ttk.Frame(speed_frame)
    speed_buttons_frame.pack(side=tk.LEFT)
    
    speed_down_btn = ttk.Button(
        speed_buttons_frame, text="Slower", 
        command=slow_down, width=8, style="TButton"
    )
    speed_down_btn.pack(side=tk.LEFT, padx=(0, 5))
    
    speed_up_btn = ttk.Button(
        speed_buttons_frame, text="Faster", 
        command=speed_up, width=8, style="TButton"
    )
    speed_up_btn.pack(side=tk.LEFT)
    
    autoplay_button = ttk.Button(
        speed_frame, text="Start Autoplay", 
        command=toggle_autoplay, width=15, style="TButton"
    )
    autoplay_button.pack(side=tk.RIGHT)
    
    manual_frame = ttk.Frame(main_container, style="Section.TFrame", padding=10)
    manual_frame.pack(fill=tk.BOTH, padx=2, pady=5)
    
    ttk.Label(manual_frame, text="Manual Play Mode:", 
             style="Section.TLabel").pack(anchor="w", pady=(0, 5))
    
    manual_info_frame = ttk.Frame(manual_frame)
    manual_info_frame.pack(fill=tk.X, pady=(0, 10))
    
    ttk.Label(manual_info_frame, text="Hotkeys (one note per press): -, =, [, ]", 
             background=section_bg, font=("Arial", 10)).pack(anchor="w")
    
    reset_button = ttk.Button(
        manual_frame, text="Reload Music / Start Over", 
        command=handle_reset_button, style="TButton"
    )
    reset_button.pack(anchor="w")
    
    notes_frame = ttk.Frame(main_container, style="Section.TFrame", padding=10)
    notes_frame.pack(fill=tk.BOTH, padx=2, pady=5)
    
    ttk.Label(notes_frame, text="Next Notes:", 
             style="Section.TLabel").pack(anchor="w", pady=(0, 5))
    
    next_notes_display_widget = tk.Text(
        notes_frame, height=3, width=65, state="disabled", 
        font=("Consolas", 11), relief="solid", borderwidth=1,
        background="white", foreground="#2c3e50"
    )
    next_notes_display_widget.pack(fill=tk.BOTH, expand=True)
    
    status_frame = tk.Frame(main_container, bg="#34495e", height=25)
    status_frame.pack(fill=tk.X, padx=2, pady=(5, 0))

    global status_label
    status_label = tk.Label(
        status_frame, text="Ready", font=("Arial", 9),
        bg="#34495e", fg="white", anchor="w"
    )
    status_label.pack(fill=tk.X, padx=10, pady=3)
    
    if piano_music_input_widget:
        print("[Debug] setup_and_run_gui: Performing initial music cache update and progress reset.")
        update_music_caches()
        reset_progress_state()

    print("[Debug] setup_and_run_gui: Starting keyboard listener...")
    keyboard_listener_object = keyboard.Listener(on_press=on_key_press, daemon=True)
    keyboard_listener_object.start()

    def on_closing():
        if messagebox.askokcancel("Exit", "Are you sure you want to exit?"):
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    print("[Debug] setup_and_run_gui: Starting Tkinter mainloop.")
    
    if status_label:
        status_label.config(text="Ready - Use hotkeys to play or load a MIDI file")
        
    root.mainloop()

class MidiFile:
    startSequence = [
        [0x4D, 0x54, 0x68, 0x64],
        [0x4D, 0x54, 0x72, 0x6B],
        [0xFF]
    ]

    typeDict = {
        0x00: "Sequence Number",
        0x01: "Text Event",
        0x02: "Copyright Notice",
        0x03: "Sequence/Track Name",
        0x04: "Instrument Name",
        0x05: "Lyric",
        0x06: "Marker",
        0x07: "Cue Point",
        0x20: "MIDI Channel Prefix",
        0x2F: "End of Track",
        0x51: "Set Tempo",
        0x54: "SMTPE Offset",
        0x58: "Time Signature",
        0x59: "Key Signature",
        0x7F: "Sequencer-Specific Meta-event",
        0x21: "Prefix Port",
        0x20: "Prefix Channel",
        0x09: "Other text format [0x09]",
        0x08: "Other text format [0x08]",
        0x0A: "Other text format [0x0A]",
        0x0C: "Other text format [0x0C]"
    }

    def __init__(self, midi_file, verbose=False, debug=False):
        self.verbose = verbose
        self.debug = debug

        self.bytes = -1
        self.headerLength = -1
        self.headerOffset = 23
        self.format = -1
        self.tracks = -1
        self.division = -1
        self.divisionType = -1
        self.itr = 0
        self.runningStatus = -1
        self.tempo = 0

        self.midiRecord_list = []
        self.record_file = "midiRecord.json"
        self.midi_file = midi_file

        self.deltaTimeStarted = False
        self.deltaTime = 0

        self.key_press_count = 0

        self.virtualPianoScale = list("1!2@34$5%6^78*9(0qQwWeErtTyYuiIoOpPasSdDfgGhHjJklLzZxcCvVbBnm")

        self.startCounter = [0] * len(MidiFile.startSequence)

        self.runningStatusSet = False

        self.events = []
        self.notes = []
        self.success = False

        print("Processing", midi_file)
        try:
            with open(self.midi_file, "rb") as f:
                self.bytes = bytearray(f.read())
            self.readEvents()
            print(self.key_press_count, "notes processed")
            self.clean_notes()
            self.success = True
        finally:
            self.save_record(self.record_file)

    def checkStartSequence(self):
        for i in range(len(self.startSequence)):
            if len(self.startSequence[i]) == self.startCounter[i]:
                return True
        return False

    def skip(self, i):
        self.itr += i

    def readLength(self):
        contFlag = True
        length = 0
        while contFlag:
            if (self.bytes[self.itr] & 0x80) >> 7 == 0x1:
                length = (length << 7) + (self.bytes[self.itr] & 0x7F)
            else:
                contFlag = False
                length = (length << 7) + (self.bytes[self.itr] & 0x7F)
            self.itr += 1
        return length

    def readMTrk(self):
        length = self.getInt(4)
        self.log("MTrk len", length)
        self.readMidiTrackEvent(length)

    def readMThd(self):
        self.headerLength = self.getInt(4)
        self.log("HeaderLength", self.headerLength)
        self.format = self.getInt(2)
        self.tracks = self.getInt(2)
        div = self.getInt(2)
        self.divisionType = (div & 0x8000) >> 16
        self.division = div & 0x7FFF
        self.log("Format %d\nTracks %d\nDivisionType %d\nDivision %d" % (self.format, self.tracks, self.divisionType, self.division))

    def readText(self, length):
        s = ""
        start = self.itr
        while self.itr < length + start:
            s += chr(self.bytes[self.itr])
            self.itr += 1
        return s

    def readMidiMetaEvent(self, deltaT):
        type = self.bytes[self.itr]
        self.itr += 1
        length = self.readLength()

        try:
            eventName = self.typeDict[type]
        except:
            eventName = "Unknown Event " + str(type)

        self.log("MIDIMETAEVENT", eventName, "LENGTH", length, "DT", deltaT)
        if type == 0x2F:
            self.log("END TRACK")
            self.itr += 2
            return False
        elif type in [0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0C]:
            self.log("\t", self.readText(length))
        elif type == 0x51:
            tempo = round(60000000 / self.getInt(3))
            self.tempo = tempo

            self.notes.append([(self.deltaTime / self.division), "tempo=" + str(tempo)])
            self.log("\tNew tempo is", str(tempo))
        else:
            self.itr += length
        return True

    def readMidiTrackEvent(self, length):
        self.log("TRACKEVENT")
        self.deltaTime = 0
        start = self.itr
        continueFlag = True
        while length > self.itr - start and continueFlag:
            deltaT = self.readLength()
            self.deltaTime += deltaT

            if self.bytes[self.itr] == 0xFF:
                self.itr += 1
                continueFlag = self.readMidiMetaEvent(deltaT)
            elif self.bytes[self.itr] >= 0xF0 and self.bytes[self.itr] <= 0xF7:
                self.runningStatusSet = False
                self.runningStatus = -1
                self.log("RUNNING STATUS SET:", "CLEARED")
            else:
                self.readVoiceEvent(deltaT)
        self.log("End of MTrk event, jumping from", self.itr, "to", start + length)
        self.itr = start + length

    def readVoiceEvent(self, deltaT):
        if self.bytes[self.itr] < 0x80 and self.runningStatusSet:
            type = self.runningStatus
            channel = type & 0x0F
        else:
            type = self.bytes[self.itr]
            channel = self.bytes[self.itr] & 0x0F
            if 0x80 <= type <= 0xF7:
                self.log("RUNNING STATUS SET:", hex(type))
                self.runningStatus = type
                self.runningStatusSet = True
            self.itr += 1

        if type >> 4 == 0x9:
            key = self.bytes[self.itr]
            self.itr += 1
            velocity = self.bytes[self.itr]
            self.itr += 1

            map = key - 23 - 12 - 1
            while map >= len(self.virtualPianoScale):
                map -= 12
            while map < 0:
                map += 12

            if velocity == 0:
                self.log(self.deltaTime / self.division, "~" + self.virtualPianoScale[map])
                self.notes.append([(self.deltaTime / self.division), "~" + self.virtualPianoScale[map]])
            else:
                self.log(self.deltaTime / self.division, self.virtualPianoScale[map])
                self.notes.append([(self.deltaTime / self.division), self.virtualPianoScale[map]])
                self.key_press_count += 1

        elif type >> 4 == 0x8:
            key = self.bytes[self.itr]
            self.itr += 1
            velocity = self.bytes[self.itr]
            self.itr += 1

            map = key - 23 - 12 - 1
            while map >= len(self.virtualPianoScale):
                map -= 12
            while map < 0:
                map += 12

            self.log(self.deltaTime / self.division, "~" + self.virtualPianoScale[map])
            self.notes.append([(self.deltaTime / self.division), "~" + self.virtualPianoScale[map]])

        elif not type >> 4 in [0x8, 0x9, 0xA, 0xB, 0xD, 0xE]:
            self.log("VoiceEvent", hex(type), hex(self.bytes[self.itr]), "DT", deltaT)
            self.itr += 1
        else:
            self.log("VoiceEvent", hex(type), hex(self.bytes[self.itr]), hex(self.bytes[self.itr + 1]), "DT", deltaT)
            self.itr += 2

    def readEvents(self):
        while self.itr + 1 < len(self.bytes):
            for i in range(len(self.startCounter)):
                self.startCounter[i] = 0

            while self.itr + 1 < len(self.bytes) and not self.checkStartSequence():
                for i in range(len(self.startSequence)):
                    if self.bytes[self.itr] == self.startSequence[i][self.startCounter[i]]:
                        self.startCounter[i] += 1
                    else:
                        self.startCounter[i] = 0

                if self.itr + 1 < len(self.bytes):
                    self.itr += 1

                if self.startCounter[0] == 4:
                    self.readMThd()
                elif self.startCounter[1] == 4:
                    self.readMTrk()

    def log(self, *arg):
        if self.verbose or self.debug:
            for s in range(len(arg)):
                try:
                    print(str(arg[s]), end=" ")
                    self.midiRecord_list.append(str(arg[s]) + " ")
                except:
                    print("[?]", end=" ")
                    self.midiRecord_list.append("[?] ")
            print()
            if self.debug: input()
            self.midiRecord_list.append("\n")
        else:
            for s in range(len(arg)):
                try:
                    self.midiRecord_list.append(str(arg[s]) + " ")
                except:
                    self.midiRecord_list.append("[?] ")
            self.midiRecord_list.append("\n")

    def getInt(self, i):
        k = 0
        for n in self.bytes[self.itr:self.itr + i]:
            k = (k << 8) + n
        self.itr += i
        return k

    @staticmethod
    def round(i):
        up = int(i + 1)
        down = int(i - 1)
        if up - i < i - down:
            return up
        else:
            return down

    def clean_notes(self):
        self.notes = sorted(self.notes, key=lambda x: float(x[0]))

        if self.verbose:
            for x in self.notes:
                print(x)

        i = 0
        while i < len(self.notes) - 1:
            a_time, b_time = self.notes[i][0], self.notes[i + 1][0]
            if a_time == b_time:
                a_notes, b_notes = self.notes[i][1], self.notes[i + 1][1]
                if "tempo" not in a_notes and "tempo" not in b_notes and "~" not in a_notes and "~" not in b_notes:
                    self.notes[i][1] += self.notes[i + 1][1]
                    self.notes.pop(i + 1)
                else:
                    i += 1
            else:
                i += 1

        for q in range(len(self.notes)):
            letterDict = {}
            newline = []
            if not "tempo" in self.notes[q][1] and "~" not in self.notes[q][1]:
                for i in range(len(self.notes[q][1])):
                    if not (self.notes[q][1][i] in letterDict):
                        newline.append(self.notes[q][1][i])
                        letterDict[self.notes[q][1][i]] = True
                self.notes[q][1] = "".join(newline)
        return

    def save_song(self, song_file):
        import json
        print("Saving notes to", song_file)
        song_data = {
            "playback_speed": playback_speed,
            "notes": self.notes
        }
        with codecs.open(song_file, "w", encoding='utf-8') as f:
            json.dump(song_data, f, indent=2)
        return

    def save_sheet(self, sheet_file):
        import json
        print("Saving sheets to", sheet_file)
        sheet_data = []
        note_count = 0
        
        for timing, notes in self.notes:
            if not "tempo" in notes and "~" not in notes:
                if len(notes) > 1:
                    note = "[" + notes + "]"
                else:
                    note = notes
                
                sheet_data.append(note)
                note_count += 1
        
        with codecs.open(sheet_file, "w", encoding='utf-8') as f:
            json.dump(sheet_data, f, indent=2)
        return

    def save_record(self, record_file):
        import json
        print("Saving processing log to", record_file)
        with codecs.open(record_file, "w", encoding='utf-8') as f:
            json.dump(self.midiRecord_list, f, indent=2)
        return

# --- MIDI Playback Functions ---
def calculate_total_duration(notes):
    """Calculate the total duration of all notes."""
    total_duration = sum([note[0] for note in notes])
    return total_duration

def is_shifted(char_in):
    """Check if a character requires the shift key."""
    ascii_value = ord(char_in)
    if ascii_value >= 65 and ascii_value <= 90:
        return True
    if char_in in "!@#$%^&*()_+{}|:\"<>?":
        return True
    return False

def speed_up():
    """Increase playback speed."""
    global playback_speed, status_label
    playback_speed *= speedMultiplier
    if speed_label:
        speed_label.config(text=f"Speed: {playback_speed:.2f}x")
    print(f"Speeding up: Playback speed is now {playback_speed:.2f}x")
    if status_label:
        status_label.config(text=f"Speed increased to {playback_speed:.2f}x")

def slow_down():
    """Decrease playback speed."""
    global playback_speed, status_label
    playback_speed /= speedMultiplier
    if speed_label:
        speed_label.config(text=f"Speed: {playback_speed:.2f}x")
    print(f"Slowing down: Playback speed is now {playback_speed:.2f}x")
    if status_label:
        status_label.config(text=f"Speed decreased to {playback_speed:.2f}x")

def press_letter(str_letter):
    """Press a key on the keyboard."""
    if is_shifted(str_letter):
        if str_letter in conversionCases:
            str_letter = conversionCases[str_letter]
        kb_controller.release(str_letter.lower())
        kb_controller.press(keyboard.Key.shift)
        kb_controller.press(str_letter.lower())
        kb_controller.release(keyboard.Key.shift)
    else:
        kb_controller.release(str_letter)
        kb_controller.press(str_letter)
    return
    
def release_letter(str_letter):
    """Release a key on the keyboard."""
    if is_shifted(str_letter):
        if str_letter in conversionCases:
            str_letter = conversionCases[str_letter]
        kb_controller.release(str_letter.lower())
    else:
        kb_controller.release(str_letter)
    return

def process_midi_file():
    """Process the song.json file created by MIDI conversion."""
    global playback_speed
    import json
    try:
        with open("song.json", "r") as macro_file:
            song_data = json.load(macro_file)
            t_offset_set = False
            t_offset = 0
            
            if "playback_speed" in song_data:
                try:
                    playback_speed = float(song_data["playback_speed"])
                    print("Playback speed is set to %.2f" % playback_speed)
                    if speed_label:
                        speed_label.config(text=f"Speed: {playback_speed:.2f}x")
                except ValueError:
                    print("Error: Invalid playback speed value")
                    return None
            else:
                print("Error: Playback speed not found in JSON")
                return None

            tempo = None
            processed_notes = []
            
            for note_entry in song_data["notes"]:
                wait_to_press = float(note_entry[0])
                notes = note_entry[1]
                
                if 'tempo' in notes:
                    try:
                        tempo = 60 / float(notes.split("=")[1])
                    except ValueError:
                        print("Error: Invalid tempo value")
                        return None
                
                processed_notes.append([wait_to_press, notes])
                if not t_offset_set:
                    t_offset = wait_to_press
                    t_offset_set = True

            if tempo is None:
                print("Error: Tempo not specified")
                return None

        return [tempo, t_offset, processed_notes, []]
    except Exception as e:
        print(f"Error processing MIDI file: {e}")
        return None

def floor_to_zero(i):
    """Ensure a value is not negative."""
    if i > 0:
        return i
    else:
        return 0

def parse_midi_info():
    """Parse the MIDI info for playback."""
    global infoTuple
    tempo = infoTuple[0]
    notes = infoTuple[2][1:]
    
    i = 0
    while i < len(notes) - 1:
        note = notes[i]
        next_note = notes[i + 1]
        if "tempo" in note[1]:
            tempo = 60 / float(note[1].split("=")[1])
            notes.pop(i)

            note = notes[i]
            if i < len(notes) - 1:
                next_note = notes[i + 1]
        else:
            note[0] = (next_note[0] - note[0]) * tempo
            i += 1

    notes[len(notes) - 1][0] = 1.00

    return notes

def adjust_tempo_for_current_note():
    """Adjust tempo for the current note if needed."""
    global isPlaying, storedIndex, playback_speed, elapsedTime, legitModeActive
    if len(infoTuple) > 3:
        tempo_changes = infoTuple[3]

        for change in tempo_changes:
            if change[0] == storedIndex:
                new_tempo = change[1]
                playback_speed = new_tempo / origionalPlaybackSpeed
                if speed_label:
                    speed_label.config(text=f"Speed: {playback_speed:.2f}x")
                print(f"Tempo changed: New playback speed is {playback_speed:.2f}x")

def play_next_midi_note():
    """Plays the next MIDI note based on the current state."""
    global isPlaying, storedIndex, playback_speed, elapsedTime, legitModeActive, heldNotes
    global next_notes_display_widget, autoplay_button, status_label

    if not isPlaying:
        return

    adjust_tempo_for_current_note()
    
    notes = infoTuple[2]
    total_duration = calculate_total_duration(notes)

    if isPlaying and storedIndex < len(notes):
        note_info = notes[storedIndex]
        delay = floor_to_zero(note_info[0])
        note_keys = note_info[1]
        
        if legitModeActive:
            delay_variation = random.uniform(0.90, 1.10)
            delay *= delay_variation

            if random.random() < 0.05:
                if random.random() < 0.5 and len(note_keys) > 1:
                    note_keys = note_keys[1:]
                else:
                    if storedIndex == 0 or notes[storedIndex - 1][0] > 0.3:
                        delay += random.uniform(0.1, 0.5)

        elapsedTime += delay

        if next_notes_display_widget:
            next_notes_display_widget.config(state="normal")
            next_notes_display_widget.delete("1.0", tk.END)
            
            upcoming_notes = ""
            look_ahead = 10
            for i in range(storedIndex + 1, min(storedIndex + look_ahead + 1, len(notes))):
                if "tempo" not in notes[i][1] and "~" not in notes[i][1]:
                    if len(notes[i][1]) > 1:
                        upcoming_notes += "[" + notes[i][1] + "] "
                    else:
                        upcoming_notes += notes[i][1] + " "
                    
            next_notes_display_widget.insert(tk.END, upcoming_notes)
            next_notes_display_widget.config(state="disabled")

        if "~" in note_keys:
            for n in note_keys.replace("~", ""):
                release_letter(n)
                if n in heldNotes:
                    del heldNotes[n]
        else:
            for n in note_keys:
                press_letter(n)
                heldNotes[n] = note_info[0]

            threading.Timer(note_info[0] / playback_speed, release_held_notes, [note_keys]).start()

        if "~" not in note_keys:
            elapsed_mins, elapsed_secs = divmod(elapsedTime, 60)
            total_mins, total_secs = divmod(total_duration, 60)
            progress_text = f"[{int(elapsed_mins)}m {int(elapsed_secs)}s/{int(total_mins)}m {int(total_secs)}s] {note_keys}"
            print(progress_text)
            
            if status_label:
                status_label.config(text=f"Playing: {note_keys} ({int(elapsed_mins)}:{int(elapsed_secs):02d}/{int(total_mins)}:{int(total_secs):02d})")

        storedIndex += 1
        if delay == 0:
            play_next_midi_note()
        else:
            threading.Timer(delay / playback_speed, play_next_midi_note).start()
    elif storedIndex >= len(notes):
        isPlaying = False
        storedIndex = 0
        elapsedTime = 0
        if autoplay_button:
            autoplay_button.config(text="Start Autoplay")
        if status_label:
            status_label.config(text="Playback complete")

def release_held_notes(note_keys):
    """Release keys that have been held down for their duration."""
    global heldNotes
    for n in note_keys:
        if n in heldNotes:
            release_letter(n)
            if n in heldNotes:
                del heldNotes[n]

def rewind():
    """Rewind playback by 10 notes."""
    global storedIndex, status_label
    if storedIndex - 10 < 0:
        storedIndex = 0
    else:
        storedIndex -= 10
    print(f"Rewound to note {storedIndex}")
    if status_label:
        status_label.config(text=f"Rewound to note {storedIndex}")

def skip():
    """Skip forward by 10 notes."""
    global storedIndex, isPlaying, status_label
    if storedIndex + 10 > len(infoTuple[2]):
        isPlaying = False
        storedIndex = 0
    else:
        storedIndex += 10
    print(f"Skipped to note {storedIndex}")
    if status_label:
        status_label.config(text=f"Skipped to note {storedIndex}")

def toggle_autoplay():
    """Toggle autoplay on or off."""
    global isPlaying, autoplay_button, status_label
    isPlaying = not isPlaying
    
    if autoplay_button:
        if isPlaying:
            autoplay_button.config(text="Stop Autoplay")
            if status_label:
                status_label.config(text="Playing MIDI file...")
            play_next_midi_note()
        else:
            autoplay_button.config(text="Start Autoplay")
            if status_label:
                status_label.config(text="Autoplay stopped")
    else:
        if isPlaying:
            print("Starting autoplay...")
            play_next_midi_note()
        else:
            print("Stopping autoplay...")

def handle_midi_keypress(key):
    """Handle keyboard shortcuts for MIDI playback."""
    try:
        if key == keyboard.Key.delete:
            toggle_autoplay()
        elif key == keyboard.Key.home:
            rewind()
        elif key == keyboard.Key.end:
            skip()
        elif key == keyboard.Key.page_up:
            speed_up()
        elif key == keyboard.Key.page_down:
            slow_down()
    except AttributeError:
        pass
    return True

def load_midi_file(file_path=None):
    """Load and process a MIDI file."""
    global infoTuple, isPlaying, storedIndex, elapsedTime, sheet_file, song_file, status_label
    import json
    
    isPlaying = False
    storedIndex = 0
    elapsedTime = 0
    if autoplay_button:
        autoplay_button.config(text="Start Autoplay")
    
    if not file_path:
        file_path = filedialog.askopenfilename(
            initialdir="./midi",
            title="Select MIDI File",
            filetypes=(("MIDI files", "*.mid"), ("All files", "*.*"))
        )
    
    if not file_path:
        return

    if status_label:
        status_label.config(text=f"Loading MIDI file: {os.path.basename(file_path)}...")

    try:
        song_file = "song.json"
        sheet_file = "sheetConversion.json"
        
        midi = MidiFile(file_path)
        if midi.success:
            midi.save_song(song_file)
            midi.save_sheet(sheet_file)
            
            with open(sheet_file, "r") as f:
                sheet_data = json.load(f)
                sheet_content = ""
                note_count = 0
                
                for note in sheet_data:
                    sheet_content += f"{note} "
                    note_count += 1
                    if note_count % 8 == 0:
                        sheet_content += "\n"
                    if note_count % 32 == 0:
                        sheet_content += "\n\n"
                
                if piano_music_input_widget:
                    piano_music_input_widget.delete("1.0", tk.END)
                    piano_music_input_widget.insert(tk.INSERT, sheet_content)
            
            infoTuple = process_midi_file()
            if infoTuple is None:
                messagebox.showerror("Error", "Failed to process the MIDI file.")
                if status_label:
                    status_label.config(text="Error: Failed to process MIDI file")
                return
                
            infoTuple[2] = parse_midi_info()
            messagebox.showinfo("Success", f"MIDI file loaded: {os.path.basename(file_path)}")
            if status_label:
                status_label.config(text=f"MIDI file loaded: {os.path.basename(file_path)}")
        else:
            messagebox.showerror("Error", "Failed to process the MIDI file.")
            if status_label:
                status_label.config(text="Error: Failed to process MIDI file")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while loading the MIDI file: {str(e)}")
        if status_label:
            status_label.config(text="Error loading MIDI file")

def browse_for_midi():
    """Open a file dialog to select a MIDI file."""
    load_midi_file()

def load_selected_midi():
    """Load the selected MIDI file from the listbox."""
    global midi_listbox
    if not midi_listbox:
        return
        
    selection = midi_listbox.curselection()
    if not selection:
        messagebox.showinfo("Selection Required", "Please select a MIDI file from the list")
        return
        
    midi_folder = 'midi'
    midi_files = [f for f in os.listdir(midi_folder) if f.lower().endswith('.mid')]
    selected_file = midi_files[selection[0]]
    load_midi_file(os.path.join(midi_folder, selected_file))

def refresh_midi_list():
    """Refresh the list of available MIDI files."""
    global midi_listbox
    if not midi_listbox:
        return
        
    midi_listbox.delete(0, tk.END)
    
    midi_folder = 'midi'
    if not os.path.exists(midi_folder):
        os.makedirs(midi_folder)
        
    midi_files = [f for f in os.listdir(midi_folder) if f.lower().endswith('.mid')]
    for file in midi_files:
        midi_listbox.insert(tk.END, file)

def key_handler(key, is_press):
    """Handle keyboard events for both normal and MIDI playback."""
    global isPlaying
    
    if is_press and key in [keyboard.Key.delete, keyboard.Key.home, keyboard.Key.end, 
                      keyboard.Key.page_up, keyboard.Key.page_down]:
        handle_midi_keypress(key)
        return True
        
    if is_press:
        try:
            pressed_char = key.char
            if pressed_char and pressed_char in HOTKEY_CHARS:
                if root:
                    root.after_idle(play_next_note_action)
        except AttributeError:
            pass
            
    return True

def on_key_press(key):
    """Callback for pynput keyboard listener for keypresses."""
    return key_handler(key, True)

# --- Main Function ---
if __name__ == "__main__":
    print("[Debug] Script started in __main__.")
    
    midi_dir = "midi"
    if not os.path.exists(midi_dir):
        os.makedirs(midi_dir)
        print(f"[Debug] Created '{midi_dir}' directory for MIDI files")
    
    if os.path.exists("song.json") and os.path.exists("sheetConversion.json"):
        try:
            infoTuple = process_midi_file()
            if infoTuple:
                infoTuple[2] = parse_midi_info()
                print("[Debug] Found existing song data, will be available for autoplay.")
        except Exception as e:
            print(f"[Debug] Error reading existing song data: {e}")
    
    original_play_next_note_action = play_next_note_action
    def play_next_note_action_wrapper():
        print("[Debug] play_next_note_action: Called.")
        original_play_next_note_action()
    play_next_note_action = play_next_note_action_wrapper

    setup_and_run_gui() 