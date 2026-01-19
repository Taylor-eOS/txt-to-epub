import tkinter as tk
from tkinter import messagebox
import re

CONTEXT_LENGTH = 30

def to_bold(num_str):
    bold_digits = {'0': '𝟎', '1': '𝟏', '2': '𝟐', '3': '𝟑', '4': '𝟒', '5': '𝟓', 
                   '6': '𝟔', '7': '𝟕', '8': '𝟖', '9': '𝟗'}
    return ''.join(bold_digits.get(ch, ch) for ch in num_str)

class FootnoteSelector(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Footnote Reference Selector")
        self.geometry("900x600")
        self.filename = "input_pre.txt"
        self.load_file()
        self.extract_tokens()
        self.create_widgets()

    def load_file(self):
        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                self.content = f.read()
        except Exception as e:
            messagebox.showerror("File Error", f"Could not load {self.filename}:\n{e}")
            self.content = ""

    def is_year(self, text):
        return bool(re.match(r"^(19[4-9]\d|20[0-2]\d)$", text))

    def extract_tokens(self):
        self.tokens = []
        header_ranges = [(m.start(), m.end()) for m in re.finditer(r"<h[123]>.*?</h[123]>", self.content, re.DOTALL)]
        tag_ranges = [(m.start(), m.end()) for m in re.finditer(r"<[^>]+>", self.content)]
        pattern = re.compile(r"\d+")
        forbidden = [" Millionen", " million", " Prozent", " percent", " pro", " 000", "000"]
        for m in pattern.finditer(self.content):
            if any(start <= m.start() <= end for start, end in header_ranges + tag_ranges):
                continue
            num_str = m.group()
            num_val = int(num_str) if num_str.isdigit() else None
            if num_val is None or self.is_year(num_str):
                continue
            following_text = self.content[m.end():m.end() + CONTEXT_LENGTH]
            if any(forbidden_str in following_text for forbidden_str in forbidden):
                continue  
            snippet = (self.content[max(0, m.start() - 33):m.start()] +
                       to_bold(num_str) +
                       self.content[m.end():min(len(self.content), m.end() + CONTEXT_LENGTH)])
            snippet = snippet.replace("\n", " ")
            self.tokens.append({
                "start": m.start(),
                "end": m.end(),
                "number": num_val,
                "text": num_str,
                "snippet": snippet,
                "is_year": False})

    def create_widgets(self):
        frame = tk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.listbox = tk.Listbox(frame, selectmode=tk.MULTIPLE, font=("Consolas", 10), exportselection=False)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.listbox.bind("<Button-1>", self.on_click)
        self.listbox.bind("<<ListboxSelect>>", self.on_selection_change)
        scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL, command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)
        for token in self.tokens:
            self.listbox.insert(tk.END, token["snippet"])
        button_frame = tk.Frame(self)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        process_button = tk.Button(button_frame, text="Apply <sup> Tags", command=self.apply_sup_tags)
        process_button.pack(side=tk.LEFT, padx=5)
        reload_button = tk.Button(button_frame, text="Reload File", command=self.reload_file)
        reload_button.pack(side=tk.LEFT, padx=5)
        quit_button = tk.Button(button_frame, text="Quit", command=self.destroy)
        quit_button.pack(side=tk.RIGHT, padx=5)

    def on_click(self, event):
        index = self.listbox.nearest(event.y)
        self.listbox.activate(index)
        self.listbox.selection_set(index)
        self.on_selection_change(None)
        return "break"

    def find_forward_consecutive_indices(self, anchor_index):
        result_indices = []
        anchor_token = self.tokens[anchor_index]
        anchor_number = anchor_token["number"]
        next_expected = anchor_number + 1
        current_search_start = anchor_index + 1
        while current_search_start < len(self.tokens):
            found = False
            for i in range(current_search_start, len(self.tokens)):
                token = self.tokens[i]
                if token["number"] == next_expected:
                    result_indices.append(i)
                    next_expected += 1
                    current_search_start = i + 1  
                    found = True
                    break  
            if not found:
                break
        return result_indices

    def on_selection_change(self, event):
        self.listbox.unbind("<<ListboxSelect>>")
        try:
            selected_indices = list(self.listbox.curselection())
            if not selected_indices:
                return
            try:
                anchor_index = self.listbox.index(tk.ACTIVE)
            except Exception:
                anchor_index = max(selected_indices)
            if anchor_index not in selected_indices:
                selected_indices.append(anchor_index)
            for i in range(anchor_index + 1, len(self.tokens)):
                self.listbox.selection_clear(i)
            forward_indices = self.find_forward_consecutive_indices(anchor_index)
            for idx in forward_indices:
                self.listbox.selection_set(idx)
        finally:
            self.listbox.bind("<<ListboxSelect>>", self.on_selection_change)

    def apply_sup_tags(self):
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            messagebox.showinfo("No Selection", "No tokens selected. Please select tokens to wrap in <sup> tags.")
            return
        selected_tokens = [self.tokens[i] for i in selected_indices]
        selected_tokens.sort(key=lambda t: t["start"])
        result_parts = []
        current_index = 0
        for token in selected_tokens:
            start, end = token["start"], token["end"]
            result_parts.append(self.content[current_index:start])
            result_parts.append(f"<sup>{token['text']}</sup>")
            current_index = end
        result_parts.append(self.content[current_index:])
        new_text = "".join(result_parts)
        output_filename = self.filename.replace(".txt", "_s.txt")
        try:
            with open(output_filename, "w", encoding="utf-8") as f:
                f.write(new_text)
            messagebox.showinfo("Success", f"Processed file saved as '{output_filename}'.")
        except Exception as e:
            messagebox.showerror("Write Error", f"Could not write output file:\n{e}")

    def reload_file(self):
        self.load_file()
        self.extract_tokens()
        self.listbox.delete(0, tk.END)
        for token in self.tokens:
            self.listbox.insert(tk.END, token["snippet"])

if __name__ == '__main__':
    app = FootnoteSelector()
    app.mainloop()

