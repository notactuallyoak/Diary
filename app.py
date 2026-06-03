# main GUI class

import datetime
import getpass
import os
import sys
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox

from config import *
from diary_manager import DiaryManager

class App:
    def __init__(self, root):
        self.root = root
        self.root.geometry("500x550")
        self.root.minsize(350, 250)

        # apply main window background
        self.root.configure(bg=WINDOW_BACKGROUND)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # state variables
        self.current_file_path = None
        self.last_active_minute = None
        self.current_font_size = CHAT_INITIAL_FONT_SIZE  # starts at size 12 from config

        self._build_ui()
        self.update_window_title()

    def _build_ui(self):
        # top navigation bar
        top_bar = tk.Frame(self.root, bg=WINDOW_BACKGROUND)
        top_bar.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(10, 0))

        new_btn = tk.Button(
            top_bar, text="New / Save As", command=self.create_new_diary,
            bg=NAV_BUTTON_BACKGROUND, fg=NAV_BUTTON_TEXT_COLOR,
            bd=0, padx=10, pady=5, font=NAV_BUTTON_FONT
        )
        new_btn.pack(side=tk.LEFT, padx=(0, 10))

        load_btn = tk.Button(
            top_bar, text="Load Diary", command=self.load_existing_diary,
            bg=NAV_BUTTON_BACKGROUND, fg=NAV_BUTTON_TEXT_COLOR,
            bd=0, padx=10, pady=5, font=NAV_BUTTON_FONT
        )
        load_btn.pack(side=tk.LEFT)

        # input box frame (packed BOTTOM first)
        input_frame = tk.Frame(self.root, bg=WINDOW_BACKGROUND)
        input_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        self.input_box = tk.Entry(
            input_frame,
            bg=INPUT_BG_COLOR, fg=INPUT_TEXT_COLOR, insertbackground=INPUT_CURSOR_COLOR,
            font=INPUT_FONT, bd=0, highlightthickness=5,
            highlightbackground=INPUT_BORDER_COLOR, highlightcolor=INPUT_BORDER_COLOR
        )
        self.input_box.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.input_box.bind("<Return>", self.send_message)

        send_btn = tk.Button(
            input_frame, text="Send", command=self.send_message,
            bg=SEND_BG_COLOR, fg=SEND_TEXT_COLOR,
            activebackground=SEND_HOVER_BG_COLOR, activeforeground=SEND_TEXT_COLOR,
            bd=0, padx=15, font=SEND_FONT
        )
        send_btn.pack(side=tk.RIGHT)

        # chat display Console (Packed LAST)
        self.chat_display = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD,
            bg=CHAT_BG_COLOR, fg=CHAT_TEXT_COLOR, insertbackground=CHAT_CURSOR_COLOR,
            font=(CHAT_FONT_FAMILY, self.current_font_size),
            bd=0, highlightthickness=0
        )
        self.chat_display.pack(side=tk.TOP, padx=10, pady=(10, 0), fill=tk.BOTH, expand=True)
        self.chat_display.config(state=tk.DISABLED)

        # bind zoom events
        self.chat_display.bind("<Control-MouseWheel>", self.zoom_text)
        self.chat_display.bind("<Control-Button-4>", self.zoom_text)
        self.chat_display.bind("<Control-Button-5>", self.zoom_text)

    def run(self):
        self.root.mainloop()

    # --- Window & UI Updates ---
    def update_window_title(self):
        if self.current_file_path:
            file_name = os.path.basename(self.current_file_path)
            self.root.title(f"Private Chat Stream - [{file_name}]")
        else:
            self.root.title("Private Chat Stream - [No File Loaded]")

    def zoom_text(self, event):
        if event.delta > 0 or event.num == 4:
            self.current_font_size += 1
        elif event.delta < 0 or event.num == 5:
            self.current_font_size = max(8, self.current_font_size - 1)

        # updates font size but keeps the family from config
        self.chat_display.configure(font=(CHAT_FONT_FAMILY, self.current_font_size))
        return "break"

    # --- File Operations ---
    def create_new_diary(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=FILE_EXTENSION,
            filetypes=[("Private Diary", f"*{FILE_EXTENSION}"), ("All Files", "*.*")],
            title="Create a New Diary"
        )
        if not file_path:
            return

        self.current_file_path = file_path
        self.last_active_minute = None

        self._clear_chat_display()
        self._save_current_state()
        self.update_window_title()

    def load_existing_diary(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Private Diary", f"*{FILE_EXTENSION}"), ("All Files", "*.*")],
            title="Open a Diary File"
        )
        if not file_path:
            return

        try:
            decoded_history = DiaryManager.load_from_file(file_path)
        except ValueError:
            messagebox.showerror("Error", "Cannot read file. It may be corrupted or not a valid diary file.")
            return
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read file:\n{str(e)}")
            return

        self.current_file_path = file_path
        self.last_active_minute = DiaryManager.parse_last_timestamp(decoded_history)

        self._clear_chat_display()
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, decoded_history)
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

        self.update_window_title()

    # --- Chat Logic ---
    def send_message(self, event=None):
        if not self.current_file_path:
            messagebox.showwarning("No File Active", "Please create or load a diary first.")
            return

        message = self.input_box.get().strip()
        if not message:
            return

        account_name = getpass.getuser()
        current_minute = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        full_text = self.chat_display.get("1.0", "end-1c").strip()

        if self.last_active_minute == current_minute and full_text:
            new_line = f"  ↳ {message}\n"
        else:
            prefix = "\n" if full_text else ""
            new_line = f"{prefix}[{current_minute}] {account_name}:\n  ↳ {message}\n"
            self.last_active_minute = current_minute

        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, new_line)
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

        self._save_current_state()
        self.input_box.delete(0, tk.END)

    # --- Helper Methods ---
    def _clear_chat_display(self):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete("1.0", tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def _save_current_state(self):
        full_history = self.chat_display.get("1.0", tk.END).strip() + "\n"
        try:
            DiaryManager.save_to_file(self.current_file_path, full_history)
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save diary!\n{str(e)}")

    def on_close(self):
        self.root.destroy()
        sys.exit()