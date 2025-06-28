from collections import defaultdict
from tkinter import messagebox
from tkinter import ttk
from tqdm import tqdm
import tkinter as tk
import pandas as pd
# import numpy as np
import hashlib
import easyocr
import csv
import cv2
import os
import re

## Running via script
os.chdir(os.path.dirname(os.path.abspath(__file__)))

## Running via .app (MacOS)
import sys
def get_app_dir():
    # Inside PyInstaller bundle
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    # Running as a script
    return os.path.dirname(os.path.abspath(__file__))

## Running via .exe (Win)
#TODO

# === Constants ===
COLOR_MAP = {
    "Burning": "Red",
    "Luminous": "Yellow",
    "Drizzly": "Blue",
    "Tranquil": "Green",
    "Any": "White"
}
COLOR_HEX = {
    "Red": "#ff998b",
    "Yellow": "#d1ce2c",
    "Blue": "#62aff8",
    "Green": "#3eff3e",
    "White": "eeeeee"
}

# === Config. ===
# VIDEO_PATH = "relics.mp4"
# OUTPUT_CSV = "relics.csv"
# DEBUG_DIR = "debug_frames"
VIDEO_PATH = os.path.join(get_app_dir(), "relics.mp4")
OUTPUT_CSV = os.path.join(get_app_dir(), "relics.csv")
DEBUG_DIR = os.path.join(get_app_dir(), "debug_frames")
DEBUG = False
FRAME_SKIP = 3

print("Looking for CSV at:", os.path.abspath(OUTPUT_CSV))
reader = easyocr.Reader(['en'], gpu=True)

# === Regions ===
ROIS = { 
    # Works for 1080p:
    "name":  (770, 810, 1060, 1400),
    "slot1": (810, 880, 1105, 1700),
    "slot2": (870, 940, 1105, 1700),
    "slot3": (930, 1000, 1105, 1700),
}


def normalize_text(text):
    if not text:
        return ""
    text = re.sub(r'\s{2,}', ' ', text)
    replacements = {
        "art'$": "art's",
        "art’": "Art",  
        "’": "'",
        "armament'$": "armament's",
        "armament' ": "armament's ",
        "armament'": "armament's",
        "armaments": "armament's",
        "armament s": "armament's",
        "armament'":"armament's",
        "armament'ss":"armament's",
        "armament$":"armament's",
        "Fexpedition": "expedition",
        "Fexpeditions": "expeditions",
        "of. expedition":"of expedition",
        "of, expedition":"of expedition",
        "of = expedition":"of expedition",
        "Endureat":"Endure at",
        "Poison Moth Flightat": "Poison Moth Flight at",
        "landing . critical":"landing a critical",
        "landing : critical":"landing a critical",
        "landing. critical":"landing a critical",
        "etc:":"etc.",
        "Two ~Handing":"Two-Handing",
        "Fability":"ability",
        "shop'":"shop",
        "shop-":"shop",
        "'shop":"shop",
        "shop.":"shop",
        "slecp":"sleep",
        "slecp'":"sleep",
        "'purchases":"purchases",
        "'s $":"'s",
        "'$":"'s",
        "' $":"'s",
        " $":"'s",
        " ' ":" ",
        "[[":"[",
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    return text.strip()

def extract_text_easyocr(img):
    if img is None or img.size == 0:
        return ""
    results = reader.readtext(img, detail=0, paragraph=True)
    return ' '.join(results).replace('\n', ' ').strip()

def crop_frame(frame, region):
    y1, y2, x1, x2 = region
    h, w = frame.shape[:2]
    return frame[max(0,y1):min(h,y2), max(0,x1):min(w,x2)]

def hash_relic(name, *slots):
    parts = [name.strip().lower()] + [s.strip().lower() for s in slots]
    full_text = "|".join(parts)     # aka {name}|{slot1}|{slot2}|{slot3}
    return hashlib.sha256(full_text.encode()).hexdigest()

def update_relics_csv():
    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        print(f"❌ Could not open video: {VIDEO_PATH}")
        return False  
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames == 0:
        print(f"❌ Video has 0 frames. Corrupt?")
        return False
    
    print(f"\n🎥 Processing video ({total_frames} frames)...")
    if DEBUG and not os.path.exists(DEBUG_DIR):
        os.makedirs(DEBUG_DIR)

    relics, seen_hashes = [], set()
    with tqdm(total=total_frames, desc="Processing", unit="frame") as pbar:
        frame_idx = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % FRAME_SKIP != 0:
                frame_idx += 1
                pbar.update(1)
                continue

            name  = normalize_text(extract_text_easyocr(crop_frame(frame, ROIS["name"])))
            slot1 = normalize_text(extract_text_easyocr(crop_frame(frame, ROIS["slot1"])))
            slot2 = normalize_text(extract_text_easyocr(crop_frame(frame, ROIS["slot2"])))
            slot3 = normalize_text(extract_text_easyocr(crop_frame(frame, ROIS["slot3"])))

            relic_hash = hash_relic(name, slot1, slot2, slot3)
            if relic_hash in seen_hashes:
                frame_idx += 1
                pbar.update(1)
                continue
            seen_hashes.add(relic_hash)
            relics.append({"Name": name, "Slot 1": slot1, "Slot 2": slot2, "Slot 3": slot3})
            frame_idx += 1
            pbar.update(1)

    cap.release()
    pd.DataFrame(relics).to_csv(OUTPUT_CSV, index=False)
    print(f"\n✅ Done! {len(relics)} unique relics saved to '{OUTPUT_CSV}'")
    return True  # Indicate success

def detect_delimiter(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        sample = f.readline()
        return '\t' if '\t' in sample else ','

def load_relics_by_color(file_path):
    delimiter = detect_delimiter(file_path)
    relics_by_color = {color: [] for color in COLOR_MAP.values()}
    with open(file_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=delimiter)
        for row in reader:
            if not row or len(row) < 2:
                continue  # Skip empty or malformed rows
            name = row[0].strip()
            parts = name.split()
            if len(parts) >= 2:
                color_key = parts[1]
                color = COLOR_MAP.get(color_key)
                if color:
                    slot_items = [cell.strip() for cell in row[1:4] if cell.strip()]
                    for slot in slot_items:
                        relics_by_color[color].append((slot, (name, slot_items)))
    return relics_by_color

class RelicSelector(tk.Tk):
    def __init__(self, relics_by_color):
        super().__init__()
        ### window setup
        self.title("Relic Selector by Dev")
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "relic_icon.png")
        try:
            icon_img = tk.PhotoImage(file=icon_path)
            self.iconphoto(False, icon_img)
        except Exception as e:
            print(f"⚠️ Could not load icon: {e}")
        self.minsize(900, 320)

        ### content setup
        self.relics_by_color = relics_by_color
        self.color_vars = [tk.StringVar() for _ in range(3)]
        self.search_vars = [tk.StringVar() for _ in range(3)]
        self.relic_lookup = [{} for _ in range(3)]
        self.relic_cycle_index = [{} for _ in range(3)]
        self.selected_relics = [[], [], []]
        self.dropdown_lists = [[] for _ in range(3)]
        self.result_boxes = []
        self.search_entries = []
        self.color_menus = []
        self.name_labels = [None, None, None] # Selected Relic Name
        self.slot_labels = [[None]*3 for _ in range(3)] # Selected Relic Attr
        self.style = ttk.Style()

        self.build_ui()
        self.focus_force()

    def build_ui(self):
        FRAME_WIDTH = 360
        WIDGET_PADX = 6

        # Main container
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        main_frame = tk.Frame(self)
        main_frame.grid(row=0, column=0, pady=10, sticky="nsew")
        main_frame.grid_rowconfigure(0, weight=1)
        for i in range(3):
            main_frame.grid_columnconfigure(i, weight=1, minsize=180)

        # Columns
        column_frames = []
        for i in range(3):
            col = tk.Frame(main_frame)#, width=FRAME_WIDTH)
            col.grid(row=0, column=i, padx=WIDGET_PADX, pady=5, sticky="nsew")
            # col.grid_propagate(False)
            column_frames.append(col)

        for i, col_frame in enumerate(column_frames):
            # Lock top rows to natural height
            col_frame.grid_rowconfigure(0, weight=0)
            col_frame.grid_rowconfigure(1, weight=0)
            col_frame.grid_rowconfigure(2, weight=0)
            col_frame.grid_rowconfigure(3, weight=1)  # Only listbox grows
            col_frame.grid_rowconfigure(4, weight=0)  # name label row
            col_frame.grid_columnconfigure(0, weight=1)
            
            # Label
            tk.Label(col_frame, text=f"Relic {i+1} Color:", font=("Comic Sans", 10, "bold")).grid(row=0, column=0, sticky="ew", padx=WIDGET_PADX, pady=(0, 2))

            # Dropdown color
            style_name = f"Custom{i}.TCombobox"
            self.style.theme_use('default')
            self.style.configure(style_name, foreground="black", fieldbackground="white", background="white")
            self.style.map(style_name, fieldbackground=[('readonly', "white")])

            color_menu = ttk.Combobox(col_frame, textvariable=self.color_vars[i], values=list(COLOR_MAP.values()),
                                    state="readonly", style=style_name)
            color_menu.grid(row=1, column=0, sticky="ew", padx=WIDGET_PADX, pady=(0, 4))
            color_menu.bind("<<ComboboxSelected>>", lambda e, idx=i: self.update_relic_list(idx))
            self.color_menus.append((color_menu, style_name))

            # Search entry
            entry = ttk.Entry(col_frame, textvariable=self.search_vars[i])
            entry.grid(row=2, column=0, sticky="ew", padx=WIDGET_PADX, pady=(0, 4))
            entry.bind("<KeyRelease>", lambda e, idx=i: self.filter_results(idx))
            self.search_entries.append(entry)

            # Listbox
            result_box = tk.Listbox(col_frame)
            result_box.grid(row=3, column=0, sticky="nsew", padx=WIDGET_PADX, pady=(0, 0))
            result_box.bind("<<ListboxSelect>>", lambda e, idx=i: self.select_relic(idx))
            result_box.bind("<d>", lambda e, idx=i: self.cycle_relic(idx, forward=True))
            result_box.bind("<a>", lambda e, idx=i: self.cycle_relic(idx, forward=False))
            self.result_boxes.append(result_box)

        # Shared container for name labels and the 3x3 grid
        grid_container = tk.Frame(self, width=930)
        grid_container.grid(row=1, column=0, pady=10)
        for col in range(3):
            grid_container.grid_columnconfigure(col, minsize=300, weight=1)

        # Name labels (row 0)
        for col in range(3):
            name_label = tk.Label(grid_container, text="—", font=("Comic Sans", 15, "bold"), anchor="center")
            name_label.grid(row=0, column=col, padx=WIDGET_PADX, sticky="ew")
            self.name_labels[col] = name_label

        # Relic attribute grid (rows 1–3)
        for row in range(3):
            for col in range(3):
                label = tk.Label(grid_container, text="—", relief="groove", anchor="w", justify="left",
                                padx=6, font=("Comic Sans", 10), height=2, wraplength=275)
                label.grid(row=row + 1, column=col, padx=WIDGET_PADX, pady=4, sticky="ew")
                self.slot_labels[row][col] = label


        # Update button at the bottom
        update_button = tk.Button(self, text="Update Relics", command=self.on_update_click,
                                  font=("Comic Sans", 10, "bold"), bg="#dddddd")
        update_button.grid(row=3, column=0, pady=10)

    def on_update_click(self):
        success = update_relics_csv()
        if not success:
            tk.messagebox.showerror("Error", f"Failed to process video.\nMake sure '{VIDEO_PATH}' is in the folder and playable.")
            return

        self.relics_by_color = load_relics_by_color(OUTPUT_CSV)
        for i in range(3):
            self.update_relic_list(i)

    def update_relic_list(self, index):
        color = self.color_vars[index].get()
        if color == "White":
            # Collect all relics from all color buckets
            all_entries = []
            for bucket in self.relics_by_color.values():
                all_entries.extend(bucket)
        else:
            all_entries = self.relics_by_color.get(color, [])
        # print("Selected relics:", self.selected_relics)
        used_groups = [frozenset(r[1]) for i, r in enumerate(self.selected_relics) if i != index and r]
        slot_to_groups = defaultdict(list)
        for slot, (relic_name, full_group) in all_entries:
            if any(set(full_group) == used for used in used_groups):
                continue
            slot_to_groups[slot].append((relic_name, full_group))

        self.relic_lookup[index] = {}
        self.relic_cycle_index[index] = {}
        display_entries = []

        for slot, group_list in slot_to_groups.items():
            label = slot
            if len(group_list) > 1:
                label = f"{slot} (1/{len(group_list)})"
            display_entries.append(label)
            self.relic_lookup[index][label] = group_list
            self.relic_cycle_index[index][label] = 0

        self.dropdown_lists[index] = sorted(display_entries)
        self.update_listbox(index, self.dropdown_lists[index])
        self.update_color_style(index, color)

    def update_color_style(self, index, color):
        _, style_name = self.color_menus[index]
        bg = COLOR_HEX.get(color, "white")
        self.style.configure(style_name, fieldbackground=bg)
        self.style.map(style_name, fieldbackground=[('readonly', bg)])

    def update_listbox(self, index, entries):
        box = self.result_boxes[index]
        box.delete(0, tk.END)
        for item in entries:
            box.insert(tk.END, item)

    def filter_results(self, index):
        query = self.search_vars[index].get().lower()
        filtered = [slot for slot in self.dropdown_lists[index] if query in slot.lower()]
        self.update_listbox(index, filtered)

    def select_relic(self, index):
        selection = self.result_boxes[index].curselection()
        if selection:
            label = self.result_boxes[index].get(selection[0])
            relic_list = self.relic_lookup[index].get(label, [])
            idx = self.relic_cycle_index[index].get(label, 0)
            if relic_list:
                self.selected_relics[index] = (relic_list[idx][0], relic_list[idx][1]) # idx0 = name, idx1 = attributes
                self.refresh_display()
                for other_index in range(3):
                    if other_index != index:
                        self.update_relic_list(other_index)

    def cycle_relic(self, index, forward=True):
        box = self.result_boxes[index]
        selection = box.curselection()
        if not selection:
            return
        label = box.get(selection[0])
        if label not in self.relic_lookup[index]:
            return
        group_list = self.relic_lookup[index][label]
        if len(group_list) <= 1:
            return
        current_idx = self.relic_cycle_index[index].get(label, 0)
        new_idx = (current_idx + 1) % len(group_list) if forward else (current_idx - 1) % len(group_list)
        self.relic_cycle_index[index][label] = new_idx
        self.selected_relics[index] = group_list[new_idx]
        self.refresh_display()
        base_label = label.split(" (")[0]
        new_label = f"{base_label} ({new_idx+1}/{len(group_list)})"
        box.delete(selection[0])
        box.insert(selection[0], new_label)
        box.selection_set(selection[0])
        self.relic_lookup[index][new_label] = group_list
        self.relic_cycle_index[index][new_label] = new_idx
        if label != new_label:
            self.relic_lookup[index].pop(label, None)
            self.relic_cycle_index[index].pop(label, None)

    # def refresh_display(self):
    #     for col in range(3):
    #         relic = self.selected_relics[col]
    #         for row in range(3):
    #             text = relic[row] if row < len(relic) else "—"
    #             self.slot_labels[row][col].config(text=text)

    def refresh_display(self):
        for col in range(3):
            selection = self.selected_relics[col]
            if selection:
                name, attributes = selection
                self.name_labels[col].config(text=name)
                for row in range(3):
                    text = attributes[row] if row < len(attributes) else "—"
                    self.slot_labels[row][col].config(text=text)
            else:
                self.name_labels[col].config(text="—")
                for row in range(3):
                    self.slot_labels[row][col].config(text="—")


if __name__ == "__main__":
    if not os.path.exists(OUTPUT_CSV):
        print(f"❌ '{OUTPUT_CSV}' not found. Creating a blank one...")
        pd.DataFrame(columns=["Name", "Slot 1", "Slot 2", "Slot 3"]).to_csv(OUTPUT_CSV, index=False)
        print(f"✅ Blank '{OUTPUT_CSV}' created. Please click 'Update Relics' in the app to import your data.")
        # update_relics_csv() # update relics on launch if no csv

    relics = load_relics_by_color(OUTPUT_CSV)
    app = RelicSelector(relics)
    app.mainloop()
