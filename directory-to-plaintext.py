import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import hashlib

# Simple tooltip class for Tkinter widgets to fix issues viewing the tooltips
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.id = None
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(500, self.showtip)

    def unschedule(self):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None

    def showtip(self):
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert") or (0, 0, 0, 0)
        x = x + self.widget.winfo_rootx() + 25
        y = y + self.widget.winfo_rooty() + 20
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tw,
            text=self.text,
            justify=tk.LEFT,
            background="#ffffe0",  # Light yellow background
            foreground="#000000",  # Black text
            relief=tk.SOLID,
            borderwidth=1,
            font=("tahoma", "8", "normal"),
        )
        label.pack(ipadx=4, ipady=2)

    def hidetip(self):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None


def safe_listdir(path):
    try:
        return sorted(os.listdir(path))
    except Exception as e:
        return [f"[Error reading {path}: {e}]"]

def get_folder_tree_raw(path):
    return [os.path.join(root, name) for root, dirs, files in os.walk(path) for name in dirs + files]

def build_tree_json(path):
    tree = {}
    for item in safe_listdir(path):
        full_path = os.path.join(path, item)
        if os.path.isdir(full_path):
            tree[item] = build_tree_json(full_path)
        else:
            tree[item] = None
    return tree

def hash_folder_content(path):
    """
    Generate a hash representing the folder content for change detection.
    It walks the folder and hashes paths + file modification times.
    """
    hash_md5 = hashlib.md5()
    for root, dirs, files in os.walk(path):
        for name in sorted(dirs + files):
            full_path = os.path.join(root, name)
            try:
                stat = os.stat(full_path)
                hash_md5.update(full_path.encode('utf-8'))
                hash_md5.update(str(stat.st_mtime).encode('utf-8'))
                hash_md5.update(str(stat.st_size).encode('utf-8'))
            except Exception:
                continue
    return hash_md5.hexdigest()

def update_output(*args):
    if not selected_folder[0]:
        copy_button.config(state="disabled")
        status_label.config(text="No folder selected")
        return

    folder_path = selected_folder[0]
    base_name = os.path.basename(folder_path)
    format_selected = format_var.get()

    raw_paths = folder_tree_cache["raw"]
    tree_json = folder_tree_cache["json"]

    if format_selected == "Raw":
        output = "[\n" + ",\n".join(f"    {repr(p)}" for p in raw_paths) + "\n]"
    elif format_selected == "Plaintext":
        def text_tree(json_tree, indent=""):
            lines = []
            items = list(json_tree.items())
            for i, (name, subtree) in enumerate(items):
                prefix = "└── " if i == len(items) - 1 else "├── "
                lines.append(indent + prefix + name)
                if subtree is not None:
                    extension = "    " if i == len(items) - 1 else "│   "
                    lines.extend(text_tree(subtree, indent + extension))
            return lines
        output = "\n".join([base_name] + text_tree(tree_json))
    elif format_selected == "Markdown":
        def md_tree(json_tree, level=0):
            lines = []
            for name, subtree in json_tree.items():
                lines.append(f"{'  ' * level}- {name}")
                if subtree is not None:
                    lines.extend(md_tree(subtree, level + 1))
            return lines
        output = "\n".join(["# " + base_name] + md_tree(tree_json))
    elif format_selected == "JSON":
        output = json.dumps({base_name: tree_json}, indent=2)
    elif format_selected == "CSV":
        output = "\n".join(raw_paths)
    elif format_selected == "HTML":
        def html_tree(json_tree):
            html_parts = ["<ul>"]
            for name, subtree in json_tree.items():
                html_parts.append(f"<li>{name}")
                if subtree is not None:
                    html_parts.append(html_tree(subtree))
                html_parts.append("</li>")
            html_parts.append("</ul>")
            return "".join(html_parts)
        output = html_tree(tree_json)
    elif format_selected == "XML":
        def xml_tree(name, subtree, indent="  "):
            lines = [f'{indent}<folder name="{name}">']
            for child_name, child_tree in subtree.items():
                if child_tree is None:
                    lines.append(f'{indent}  <file name="{child_name}" />')
                else:
                    lines.extend(xml_tree(child_name, child_tree, indent + "  "))
            lines.append(f'{indent}</folder>')
            return lines
        output = "\n".join([f'<folder name="{base_name}">'] + xml_tree(base_name, tree_json, "  ")[1:])
    else:
        output = "Unknown format selected."

    text_area.config(state=tk.NORMAL)
    text_area.delete("1.0", tk.END)
    text_area.insert(tk.END, output)
    text_area.config(state=tk.DISABLED)
    copy_button.config(state="normal")
    status_label.config(text=f"Folder: {folder_path}")

def select_folder():
    folder_path = filedialog.askdirectory()
    if folder_path:
        selected_folder[0] = folder_path
        refresh_cache()
        update_output()
        start_auto_refresh()

def refresh_cache():
    folder_path = selected_folder[0]
    if folder_path:
        folder_tree_cache["raw"] = get_folder_tree_raw(folder_path)
        folder_tree_cache["json"] = build_tree_json(folder_path)
        folder_tree_cache["hash"] = hash_folder_content(folder_path)

def auto_refresh_check():
    folder_path = selected_folder[0]
    if folder_path:
        current_hash = hash_folder_content(folder_path)
        if current_hash != folder_tree_cache.get("hash"):
            refresh_cache()
            update_output()
            status_label.config(text=f"Folder changed: {folder_path} (Auto-refreshed)")
    root.after(5000, auto_refresh_check)

def start_auto_refresh():
    if not getattr(root, "_auto_refresh_running", False):
        root._auto_refresh_running = True
        root.after(5000, auto_refresh_check)

def copy_to_clipboard():
    content = text_area.get("1.0", tk.END).strip()
    if content:
        root.clipboard_clear()
        root.clipboard_append(content)
        messagebox.showinfo("Copied", "Text copied to clipboard!")

def save_to_file():
    content = text_area.get("1.0", tk.END).strip()
    if not content:
        messagebox.showwarning("No Content", "There is no content to save.")
        return
    file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                             filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
    if file_path:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Saved", f"Output saved to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file:\n{e}")

# --- GUI Setup ---
root = tk.Tk()
root.title("Folder Tree Viewer")
root.minsize(700, 600)

selected_folder = [None]
folder_tree_cache = {"raw": [], "json": {}, "hash": None}

default_font = ("Segoe UI", 10)

frame = tk.Frame(root, padx=20, pady=10)
frame.pack(fill=tk.X)

btn_select = tk.Button(frame, text="Select Folder", command=select_folder, font=default_font)
btn_select.pack(side=tk.LEFT)
ToolTip(btn_select, "Select a folder to display its tree structure")

tk.Label(frame, text="Output Format:", font=default_font).pack(side=tk.LEFT, padx=(20, 5))

format_var = tk.StringVar(value="Plaintext")
formats = ["Raw", "Plaintext", "Markdown", "JSON", "CSV", "HTML", "XML"]
for fmt in formats:
    rb = tk.Radiobutton(frame, text=fmt, variable=format_var, value=fmt, command=update_output, font=default_font)
    rb.pack(side=tk.LEFT, padx=5)

text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=90, height=30, font=("Consolas", 11),
                                      bg="#1e1e1e", fg="#d4d4d4", insertbackground="white", state=tk.DISABLED)
text_area.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

button_frame = tk.Frame(root, pady=10)
button_frame.pack()

copy_button = tk.Button(button_frame, text="Copy to Clipboard", command=copy_to_clipboard, state="disabled", font=default_font)
copy_button.pack(side=tk.LEFT, padx=10)
ToolTip(copy_button, "Copy the displayed output to clipboard")

save_button = tk.Button(button_frame, text="Save to File", command=save_to_file, font=default_font)
save_button.pack(side=tk.LEFT, padx=10)
ToolTip(save_button, "Save the displayed output to a text file")

status_label = tk.Label(root, text="No folder selected", font=("Segoe UI", 9), fg="gray")
status_label.pack(pady=(0, 10))

root.mainloop()
