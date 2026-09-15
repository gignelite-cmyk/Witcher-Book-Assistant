import json
import logging
import os
import queue
import threading
import tkinter as tk
import warnings

warnings.filterwarnings("ignore")
logging.getLogger("google").setLevel(logging.ERROR)
logging.getLogger("google.genai").setLevel(logging.ERROR)
os.environ["PYTHONWARNINGS"] = "ignore"

from google import genai
from google.genai import types
from PIL import ImageGrab
from pynput import mouse

CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {"result_width": 680, "result_height": 600, "font_size": 10}


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                return {**DEFAULT_CONFIG, **cfg}
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4)
    except Exception:
        pass


with open("key.txt", "r", encoding="utf-8") as f:
    API_KEY = f.read().strip()

TARGET_BUTTON = mouse.Button.x1

SYSTEM_INSTRUCTION = """
You are a Witcher book assistant. The user sends a screenshot of a book excerpt and may specify a target word or phrase.
Find the requested word or term on the screenshot and provide an analysis strictly following the structure below.

STRICT FORMATTING RULE:
DO NOT USE Markdown formatting! The symbols **, *, #, ###, _, ~~ are strictly prohibited.
The text is output into a plain text interface where formatting is not supported.
For emphasis, use UPPERCASE, indentations, and hyphens/dots for lists.

LANGUAGE RULE:
Detect the language of the book excerpt in the screenshot and write your ENTIRE response in that exact same language, including all structural section titles and descriptions. 
(For example, if the book text is in Russian, translate and write section headers like PRECISE DEFINITION or THREE INTERESTING FACTS into Russian. If it is in English, keep them in English, etc.)

RESPONSE STRUCTURE:

[TERM NAME IN UPPERCASE]

1. PRECISE DEFINITION (Translate this header into the book's language)
Meaning of the word and its context of usage in the text.

2. THREE INTERESTING FACTS (Translate this header into the book's language)
• First fact (universe lore or real-world history/etymology).
• Second fact.
• Third fact.

3. WITCHER LORE (Translate this header into the book's language)
Information from the bestiary, alchemy, heraldry, swordsmanship, or everyday life.

4. ELDER SPEECH (Translate this header into the book's language)
(Include this section ONLY if the term is an Elvish or magical word. In this case, provide its component breakdown. If it is a common word from the common tongue, completely omit and do not show the fourth section).

CRITICALLY IMPORTANT: Avoid any spoilers for future events in the books!
"""

client = genai.Client(api_key=API_KEY)
msg_queue = queue.Queue()


def call_gemini(image, user_text):
    try:
        if user_text:
            prompt_text = (
                f"Find the word or phrase '{user_text}' on the screenshot and analyze it."
            )
        else:
            prompt_text = (
                "Find a rare or unclear word or term in the excerpt and analyze it."
            )

        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=[image, prompt_text],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(
                    disable=True
                ),
            ),
        )
        msg_queue.put(("RESULT", response.text))
    except Exception as e:
        msg_queue.put(("RESULT", f"API Request Error: {e}"))


def process_screenshot():
    image = ImageGrab.grabclipboard()
    if image is None:
        print(
            "No image in clipboard! First capture a fragment (Win+Shift+S)."
        )
        return
    msg_queue.put(("INPUT_REQUIRED", image))


def on_click(x, y, button, pressed):
    if pressed and button == TARGET_BUTTON:
        process_screenshot()


def center_window(win, width, height):
    win.update_idletasks()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    x = (sw - width) // 2
    y = (sh - height) // 2
    win.geometry(f"{width}x{height}+{x}+{y}")


def ask_user_input(root, image, initial_text=""):
    dialog = tk.Toplevel(root)
    dialog.overrideredirect(True)
    dialog.configure(bg="#1a1a1c")
    dialog.attributes("-topmost", True)
    center_window(dialog, 480, 180)

    border_frame = tk.Frame(dialog, bg="#c9a050")
    border_frame.pack(fill=tk.BOTH, expand=True)

    main_frame = tk.Frame(border_frame, bg="#1a1a1c")
    main_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

    top_bar = tk.Frame(main_frame, bg="#1a1a1c")
    top_bar.pack(fill=tk.X, padx=5, pady=(5, 0))

    close_btn = tk.Label(
        top_bar,
        text="✕",
        font=("Segoe UI", 11),
        bg="#1a1a1c",
        fg="#8e8e93",
        cursor="hand2",
    )
    close_btn.pack(side=tk.RIGHT, padx=5)
    close_btn.bind("<Button-1>", lambda e: dialog.destroy())
    close_btn.bind("<Enter>", lambda e: close_btn.config(fg="#c9a050"))
    close_btn.bind("<Leave>", lambda e: close_btn.config(fg="#8e8e93"))

    def start_move(e):
        dialog.x = e.x
        dialog.y = e.y

    def do_move(e):
        x = dialog.winfo_x() + (e.x - dialog.x)
        y = dialog.winfo_y() + (e.y - dialog.y)
        dialog.geometry(f"+{x}+{y}")

    main_frame.bind("<Button-1>", start_move)
    main_frame.bind("<B1-Motion>", do_move)
    top_bar.bind("<Button-1>", start_move)
    top_bar.bind("<B1-Motion>", do_move)

    content_frame = tk.Frame(main_frame, bg="#1a1a1c", padx=20, pady=5)
    content_frame.pack(fill=tk.BOTH, expand=True)

    label = tk.Label(
        content_frame,
        text="Enter a term or leave empty for auto-search",
        font=("Segoe UI", 11, "bold"),
        bg="#1a1a1c",
        fg="#c9a050",
        anchor="center",
        justify="center",
    )
    label.pack(fill=tk.X, pady=(0, 14))

    entry_border = tk.Frame(content_frame, bg="#c9a050", bd=1)
    entry_border.pack(fill=tk.X, pady=(0, 12))

    entry = tk.Entry(
        entry_border,
        font=("Segoe UI", 10),
        bg="#252528",
        fg="#ffffff",
        insertbackground="#c9a050",
        relief=tk.FLAT,
        bd=5,
        justify="center",
    )
    entry.pack(fill=tk.X)
    if initial_text:
        entry.insert(0, initial_text)
    entry.focus_set()

    def paste_to_entry(event=None):
        try:
            clipboard_text = dialog.clipboard_get()
        except tk.TclError:
            return "break"

        entry.delete(0, tk.END)
        entry.insert(0, clipboard_text)
        return "break"

    entry.bind("<Control-v>", paste_to_entry)

    def submit():
        user_text = entry.get().strip()
        dialog.destroy()
        print("Analyzing excerpt...")
        threading.Thread(
            target=call_gemini, args=(image, user_text), daemon=True
        ).start()

    entry.bind("<Return>", lambda e: submit())

    btn = tk.Button(
        content_frame,
        text="FIND TERM",
        font=("Segoe UI", 9, "bold"),
        bg="#c9a050",
        fg="#1a1a1c",
        activebackground="#e0b868",
        activeforeground="#1a1a1c",
        relief=tk.FLAT,
        cursor="hand2",
        bd=0,
        pady=6,
        command=submit,
    )
    btn.pack(fill=tk.X)


def attach_resizers(popup, size=1, corner_size=1):
    min_w, min_h = 400, 300
    cfg = load_config()

    state = {
        "start_x": 0,
        "start_y": 0,
        "start_w": 0,
        "start_h": 0,
        "start_win_x": 0,
        "start_win_y": 0,
    }

    def start_resize(e):
        state["start_x"] = e.x_root
        state["start_y"] = e.y_root
        state["start_w"] = popup.winfo_width()
        state["start_h"] = popup.winfo_height()
        state["start_win_x"] = popup.winfo_x()
        state["start_win_y"] = popup.winfo_y()

    def save_size():
        cfg["result_width"] = popup.winfo_width()
        cfg["result_height"] = popup.winfo_height()
        save_config(cfg)

    def stop_resize(e):
        save_size()

    def resize_n(e):
        dy = e.y_root - state["start_y"]
        nh = max(min_h, state["start_h"] - dy)
        ny = state["start_win_y"] + (state["start_h"] - nh)
        popup.geometry(f"{state['start_w']}x{nh}+{state['start_win_x']}+{ny}")

    def resize_s(e):
        dh = e.y_root - state["start_y"]
        nh = max(min_h, state["start_h"] + dh)
        popup.geometry(
            f"{state['start_w']}x{nh}+{state['start_win_x']}+{state['start_win_y']}"
        )

    def resize_w(e):
        dx = e.x_root - state["start_x"]
        nw = max(min_w, state["start_w"] - dx)
        nx = state["start_win_x"] + (state["start_w"] - nw)
        popup.geometry(
            f"{nw}x{state['start_h']}+{nx}+{state['start_win_y']}"
        )

    def resize_e(e):
        dw = e.x_root - state["start_x"]
        nw = max(min_w, state["start_w"] + dw)
        popup.geometry(
            f"{nw}x{state['start_h']}+{state['start_win_x']}+{state['start_win_y']}"
        )

    def resize_nw(e):
        dx = e.x_root - state["start_x"]
        dy = e.y_root - state["start_y"]
        nw = max(min_w, state["start_w"] - dx)
        nh = max(min_h, state["start_h"] - dy)
        nx = state["start_win_x"] + (state["start_w"] - nw)
        ny = state["start_win_y"] + (state["start_h"] - nh)
        popup.geometry(f"{nw}x{nh}+{nx}+{ny}")

    def resize_ne(e):
        dx = e.x_root - state["start_x"]
        dy = e.y_root - state["start_y"]
        nw = max(min_w, state["start_w"] + dx)
        nh = max(min_h, state["start_h"] - dy)
        ny = state["start_win_y"] + (state["start_h"] - nh)
        popup.geometry(f"{nw}x{nh}+{state['start_win_x']}+{ny}")

    def resize_sw(e):
        dx = e.x_root - state["start_x"]
        dy = e.y_root - state["start_y"]
        nw = max(min_w, state["start_w"] - dx)
        nh = max(min_h, state["start_h"] + dy)
        nx = state["start_win_x"] + (state["start_w"] - nw)
        popup.geometry(f"{nw}x{nh}+{nx}+{state['start_win_y']}")

    def resize_se(e):
        dx = e.x_root - state["start_x"]
        dy = e.y_root - state["start_y"]
        nw = max(min_w, state["start_w"] + dx)
        nh = max(min_h, state["start_h"] + dy)
        popup.geometry(
            f"{nw}x{nh}+{state['start_win_x']}+{state['start_win_y']}"
        )

    b_top = tk.Frame(popup, bg="#c9a050", cursor="size_ns")
    b_top.place(relx=0, rely=0, relwidth=1.0, height=size)

    b_bottom = tk.Frame(popup, bg="#c9a050", cursor="size_ns")
    b_bottom.place(relx=0, rely=1.0, relwidth=1.0, height=size, anchor="sw")

    b_left = tk.Frame(popup, bg="#c9a050", cursor="size_we")
    b_left.place(relx=0, rely=0, relheight=1.0, width=size)

    b_right = tk.Frame(popup, bg="#c9a050", cursor="size_we")
    b_right.place(relx=1.0, rely=0, relheight=1.0, width=size, anchor="ne")

    c_nw = tk.Frame(
        popup,
        bg="#c9a050",
        width=corner_size,
        height=corner_size,
        cursor="size_nw_se",
    )
    c_nw.place(relx=0, rely=0)

    c_ne = tk.Frame(
        popup,
        bg="#c9a050",
        width=corner_size,
        height=corner_size,
        cursor="size_ne_sw",
    )
    c_ne.place(relx=1.0, rely=0, anchor="ne")

    c_sw = tk.Frame(
        popup,
        bg="#c9a050",
        width=corner_size,
        height=corner_size,
        cursor="size_ne_sw",
    )
    c_sw.place(relx=0, rely=1.0, anchor="sw")

    c_se = tk.Frame(
        popup,
        bg="#c9a050",
        width=corner_size,
        height=corner_size,
        cursor="size_nw_se",
    )
    c_se.place(relx=1.0, rely=1.0, anchor="se")

    handlers = [
        (b_top, resize_n),
        (b_bottom, resize_s),
        (b_left, resize_w),
        (b_right, resize_e),
        (c_nw, resize_nw),
        (c_ne, resize_ne),
        (c_sw, resize_sw),
        (c_se, resize_se),
    ]

    for widget, motion_fn in handlers:
        widget.bind("<Button-1>", start_resize)
        widget.bind("<B1-Motion>", motion_fn)
        widget.bind("<ButtonRelease-1>", stop_resize)


def show_result(root, text):
    cfg = load_config()
    curr_w = cfg.get("result_width", 680)
    curr_h = cfg.get("result_height", 600)
    curr_font_size = cfg.get("font_size", 10)

    popup = tk.Toplevel(root)
    popup.overrideredirect(True)
    popup.configure(bg="#1a1a1c")
    popup.attributes("-topmost", True)
    center_window(popup, curr_w, curr_h)

    border_frame = tk.Frame(popup, bg="#c9a050")
    border_frame.pack(fill=tk.BOTH, expand=True)

    main_frame = tk.Frame(border_frame, bg="#252528")
    main_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

    attach_resizers(popup, size=1, corner_size=1)

    top_bar = tk.Frame(main_frame, bg="#252528")
    top_bar.pack(fill=tk.X, padx=5, pady=(5, 0))

    close_btn = tk.Label(
        top_bar,
        text="✕",
        font=("Segoe UI", 11),
        bg="#252528",
        fg="#8e8e93",
        cursor="hand2",
    )
    close_btn.pack(side=tk.RIGHT, padx=(10, 5))

    def on_close():
        cfg["result_width"] = popup.winfo_width()
        cfg["result_height"] = popup.winfo_height()
        cfg["font_size"] = curr_font_size
        save_config(cfg)
        popup.destroy()

    close_btn.bind("<Button-1>", lambda e: on_close())
    close_btn.bind("<Enter>", lambda e: close_btn.config(fg="#c9a050"))
    close_btn.bind("<Leave>", lambda e: close_btn.config(fg="#8e8e93"))

    font_frame = tk.Frame(top_bar, bg="#252528")
    font_frame.pack(side=tk.RIGHT, padx=5)

    font_label = tk.Label(
        font_frame,
        text=f"{curr_font_size} pt",
        font=("Segoe UI", 9),
        bg="#252528",
        fg="#8e8e93",
    )

    def update_font(delta):
        nonlocal curr_font_size
        new_size = max(8, min(24, curr_font_size + delta))
        if new_size != curr_font_size:
            curr_font_size = new_size
            st.config(font=("Segoe UI", curr_font_size))
            font_label.config(text=f"{curr_font_size} pt")
            cfg["font_size"] = curr_font_size
            save_config(cfg)

    btn_minus = tk.Label(
        font_frame,
        text="A-",
        font=("Segoe UI", 9, "bold"),
        bg="#252528",
        fg="#8e8e93",
        cursor="hand2",
    )
    btn_minus.pack(side=tk.LEFT, padx=3)
    btn_minus.bind("<Button-1>", lambda e: update_font(-1))
    btn_minus.bind("<Enter>", lambda e: btn_minus.config(fg="#c9a050"))
    btn_minus.bind("<Leave>", lambda e: btn_minus.config(fg="#8e8e93"))

    font_label.pack(side=tk.LEFT, padx=3)

    btn_plus = tk.Label(
        font_frame,
        text="A+",
        font=("Segoe UI", 9, "bold"),
        bg="#252528",
        fg="#8e8e93",
        cursor="hand2",
    )
    btn_plus.pack(side=tk.LEFT, padx=3)
    btn_plus.bind("<Button-1>", lambda e: update_font(1))
    btn_plus.bind("<Enter>", lambda e: btn_plus.config(fg="#c9a050"))
    btn_plus.bind("<Leave>", lambda e: btn_plus.config(fg="#8e8e93"))

    def start_move(e):
        popup.x = e.x
        popup.y = e.y

    def do_move(e):
        x = popup.winfo_x() + (e.x - popup.x)
        y = popup.winfo_y() + (e.y - popup.y)
        popup.geometry(f"+{x}+{y}")

    top_bar.bind("<Button-1>", start_move)
    top_bar.bind("<B1-Motion>", do_move)

    st = tk.Text(
        main_frame,
        wrap=tk.WORD,
        font=("Segoe UI", curr_font_size),
        bg="#252528",
        fg="#e1e1e1",
        insertbackground="#c9a050",
        bd=0,
        padx=15,
        pady=15,
    )
    st.pack(fill=tk.BOTH, expand=True, padx=12, pady=(5, 12))
    st.insert(tk.END, text)

    def copy_selected(event=None):
        try:
            selected_text = st.get("sel.first", "sel.last")
        except tk.TclError:
            return "break"

        root.clipboard_clear()
        root.clipboard_append(selected_text)
        root.update()
        return "break"

    def select_all(event=None):
        st.tag_add(tk.SEL, "1.0", tk.END)
        st.mark_set(tk.INSERT, "1.0")
        return "break"

    st.bind("<Control-c>", copy_selected)
    st.bind("<Control-a>", select_all)

    def prevent_edit(event):
        return "break"

    st.bind("<KeyPress>", prevent_edit)


def check_queue(root):
    while not msg_queue.empty():
        msg_type, data = msg_queue.get()
        if msg_type == "INPUT_REQUIRED":
            ask_user_input(root, data)
        elif msg_type == "RESULT":
            show_result(root, data)

    root.after(100, check_queue, root)


os.system("cls" if os.name == "nt" else "clear")

root = tk.Tk()
root.withdraw()

listener = mouse.Listener(on_click=on_click)
listener.start()

print("Script started!")
print("1. Select an area (Win+Shift+S)")
print("2. Click the lower side mouse button")
print("3. Press Ctrl + C in the terminal to exit")

root.after(100, check_queue, root)

try:
    root.mainloop()
except KeyboardInterrupt:
    os.system("cls" if os.name == "nt" else "clear")