import tkinter as tk
from tkinter import scrolledtext, messagebox
import re
import time
import threading

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

KEY_DELAY = 0.1  # seconds, as per original script
HOTKEY_CHARS = {'-', '=', '[', ']'} 

kb_controller = keyboard.Controller()

root = None
piano_music_input_widget = None
next_notes_display_widget = None
keyboard_listener_object = None

# --- Core Logic Functions ---

def update_music_caches():
    """Reads music from input, updates raw and cleaned caches. Returns True if changed."""
    global piano_music_raw_cache, piano_music_cleaned_cache, current_idx_cleaned, current_idx_raw_display
    
    if not piano_music_input_widget: # Widget not yet ready
        return False

    current_raw_music = piano_music_input_widget.get("1.0", tk.END).strip()
    
    if current_raw_music != piano_music_raw_cache:
        piano_music_raw_cache = current_raw_music
        piano_music_cleaned_cache = re.sub(r"[\s/]", "", piano_music_raw_cache)
        # If music changes, progress must be reset
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
    """Action for the Reset button."""
    update_music_caches() 
    reset_progress_state() 

def play_next_note_action():
    """Plays the next note based on the current state and input music."""
    global current_idx_cleaned, current_idx_raw_display, piano_music_raw_cache, piano_music_cleaned_cache

    # Always update caches if input text might have changed
    # and reset progress if the music actually changed.
    if update_music_caches(): 
        reset_progress_state() # Automatically reset if music changes

    raw_music = piano_music_raw_cache
    cleaned_music = piano_music_cleaned_cache

    if not cleaned_music:
        print("[Debug] play_next_note_action: No cleaned music to play.")
        return

    if current_idx_cleaned >= len(cleaned_music):
        print("[Debug] play_next_note_action: End of song reached.")
        reset_progress_state()
        if next_notes_display_widget:
            next_notes_display_widget.config(state="normal")
            next_notes_display_widget.insert(tk.END, "♪ End of song. Press hotkey to play again or Reset. ♪")
            next_notes_display_widget.config(state="disabled")
        return

    match = re.match(r"(\[.*?]|.)", cleaned_music[current_idx_cleaned:])
    if match:
        note_token = match.group(1)
        keys_to_send = note_token.strip("[]")

        current_idx_cleaned += len(note_token)
        print(f"[Debug] play_next_note_action: Attempting to type: '{keys_to_send}', new clean_idx: {current_idx_cleaned}")

        # Advance display index for raw music string
        # 1. Skip delimiter characters in raw_music
        while (current_idx_raw_display < len(raw_music) and 
               raw_music[current_idx_raw_display] in " \n\r/"):
            current_idx_raw_display += 1
        
        # 2. Advance past the current note token's representation in raw_music
        if current_idx_raw_display < len(raw_music):
            current_idx_raw_display += len(note_token)
        
        if next_notes_display_widget:
            next_notes_display_widget.config(state="normal")
            next_notes_display_widget.delete("1.0", tk.END)
            safe_display_start_idx = min(current_idx_raw_display, len(raw_music))
            next_notes_str = raw_music[safe_display_start_idx : safe_display_start_idx + 90]
            next_notes_display_widget.insert(tk.END, next_notes_str)
            next_notes_display_widget.config(state="disabled")

        if keys_to_send: 
            time.sleep(0.05) # Small delay to potentially help with window focus
            kb_controller.type(keys_to_send)
        
        time.sleep(KEY_DELAY)

# --- Hotkey Listener ---
def on_key_press(key):
    """Callback for pynput keyboard listener."""
    global root
    print(f"[Debug] on_key_press: Key {key} pressed.") # General key press log
    pressed_char = None
    try:
        pressed_char = key.char
    except AttributeError:
        pass # Not a character key

    if pressed_char and pressed_char in HOTKEY_CHARS:
        print(f"[Debug] on_key_press: Hotkey '{pressed_char}' detected.")
        if root: # Ensure GUI is available
             # Run in Tkinter's main thread
             print("[Debug] on_key_press: Scheduling play_next_note_action via root.after_idle()")
             root.after_idle(play_next_note_action)
        return True   # DIAGNOSTIC CHANGE: Always return True to see if listener continues
    return True  # Allow other keys

def start_keyboard_listener():
    global keyboard_listener_object
    # Create listener as a daemon thread so it exits automatically when the main program finishes
    keyboard_listener_object = keyboard.Listener(on_press=on_key_press, daemon=True)
    keyboard_listener_object.start()

# --- GUI Setup ---
def setup_and_run_gui():
    global root, piano_music_input_widget, next_notes_display_widget, keyboard_listener_object

    print("[Debug] setup_and_run_gui: Initializing GUI...")
    root = tk.Tk()
    root.title("Pianoblox - Universal Piano Autoplayer")
    root.wm_attributes("-topmost", 1) # To keep the window always on top

    tk.Label(root, text="Universal Virtual Piano Autoplayer", font=("Arial", 14, "bold")).pack(pady=(10,5))
    
    main_frame = tk.Frame(root, padx=10, pady=5)
    main_frame.pack(fill=tk.BOTH, expand=True)

    tk.Label(main_frame, text="Paste Music Sheets Here:", justify=tk.LEFT).pack(pady=(5,2), anchor="w")
    
    piano_music_input_widget = scrolledtext.ScrolledText(main_frame, height=10, width=65, wrap=tk.WORD, relief=tk.SOLID, borderwidth=1)
    piano_music_input_widget.pack(pady=5, fill="x", expand=True)
    piano_music_input_widget.insert(tk.INSERT, "Example: q w e [rt] y / [tyu] o p")

    tk.Label(main_frame, text="Hotkeys (one note per press): -, =, [, ]", justify=tk.LEFT).pack(pady=2, anchor="w")
    tk.Label(main_frame, text="Click 'Reset' after changing the song or to start from the beginning.", justify=tk.LEFT).pack(pady=2, anchor="w")
    
    tk.Label(main_frame, text="Next Notes:", justify=tk.LEFT).pack(pady=(10,2), anchor="w")
    next_notes_display_widget = tk.Text(main_frame, height=4, width=65, state="disabled", relief=tk.SOLID, borderwidth=1, wrap=tk.WORD, background="white", fg="black")
    next_notes_display_widget.pack(pady=5, fill="x", expand=True)

    reset_button = tk.Button(main_frame, text="Reload Music / Start Over", command=handle_reset_button, width=25, height=2)
    reset_button.pack(pady=10)
    
    # Initial setup
    if piano_music_input_widget: # Ensure widget exists
      print("[Debug] setup_and_run_gui: Performing initial music cache update and progress reset.")
      update_music_caches()
      reset_progress_state()

    print("[Debug] setup_and_run_gui: Starting keyboard listener...")
    start_keyboard_listener()

    def on_closing():
        if messagebox.askokcancel("Exit", "Are you sure you want to exit?"):
            # Listener is already a daemon, so no need to stop manually if daemon=True
            # if keyboard_listener_object:
            #     keyboard_listener_object.stop() 
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    print("[Debug] setup_and_run_gui: Displaying initial info message.")
    root.after(100, lambda: messagebox.showinfo("Information", 
                        "Ensure the virtual piano window is active for keystrokes to be sent.\n\n"
                        "On macOS: You may need to grant permissions in System Settings > Privacy & Security for both:\n"
                        "  - Accessibility\n"
                        "  - Input Monitoring\n"
                        "to allow Terminal/Python to control other applications.\n\n"
                        "Hotkeys: -, =, [, ]"))

    print("[Debug] setup_and_run_gui: Starting Tkinter mainloop.")
    root.mainloop()

if __name__ == "__main__":
    print("[Debug] Script started in __main__.")
    # Add a print statement at the very beginning of play_next_note_action
    original_play_next_note_action = play_next_note_action
    def play_next_note_action_wrapper():
        print("[Debug] play_next_note_action: Called.")
        original_play_next_note_action()
    play_next_note_action = play_next_note_action_wrapper

    setup_and_run_gui() 