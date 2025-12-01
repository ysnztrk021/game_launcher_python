import os
from dataclasses import dataclass
from typing import List, Optional

import customtkinter as ctk
from tkinter import messagebox
from PIL import Image

# Windows / raccourcis & GDI
import win32com.client
import win32gui
import win32ui
import win32con
import win32api

# Windows / SHGetFileInfo (via ctypes)
import ctypes
from ctypes import wintypes

# -----------------------------
# CONFIG : chemins à adapter si besoin
# -----------------------------
GAMES_DIR = r"C:\Users\yasin\Desktop\JEUX"
LAUNCHERS_DIR = r"C:\Users\yasin\Desktop\LAUNCHERS"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_CACHE_DIR = os.path.join(BASE_DIR, "icon_cache")

os.makedirs(ICON_CACHE_DIR, exist_ok=True)

# -----------------------------
# Modèle
# -----------------------------
@dataclass
class Item:
    name: str
    path: str        # chemin du raccourci (.lnk / .exe / .url)
    kind: str        # "game" ou "launcher"
    target: Optional[str]  # chemin réel de la cible (.exe) si on l'a


# -----------------------------
# Utilitaires
# -----------------------------
def slugify(name: str) -> str:
    s = name.lower()
    for ch in r"\/:*?\"<>|":
        s = s.replace(ch, " ")
    return "_".join(s.split())


# -----------------------------
# Résolution des raccourcis
# -----------------------------
def resolve_shortcut_target(path: str) -> Optional[str]:
    """
    Si c'est un .lnk, récupère la cible (.exe).
    Sinon, si c'est déjà un .exe/.url, renvoie tel quel.
    (On l'utilise surtout pour info / futur ; pour les icônes,
     on interroge le .lnk directement.)
    """
    lower = path.lower()
    try:
        if lower.endswith(".lnk"):
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortcut(path)
            target = shortcut.Targetpath
            if target and os.path.exists(target):
                return target
            return None
        elif lower.endswith(".exe") or lower.endswith(".url"):
            return path
    except Exception as e:
        print(f"[LNK] Erreur résolution {path}: {e}")
    return None


# -----------------------------
# Scan des dossiers JEUX / LAUNCHERS
# -----------------------------
def scan_folder(folder: str, kind: str) -> List[Item]:
    items: List[Item] = []
    if not os.path.isdir(folder):
        return items

    for entry in os.listdir(folder):
        full_path = os.path.join(folder, entry)
        if not os.path.isfile(full_path):
            continue

        lower = entry.lower()
        if not (lower.endswith(".lnk") or lower.endswith(".url") or lower.endswith(".exe")):
            continue

        name = os.path.splitext(entry)[0]
        target = resolve_shortcut_target(full_path)
        items.append(Item(name=name, path=full_path, kind=kind, target=target))

    return items


def scan_all() -> List[Item]:
    games = scan_folder(GAMES_DIR, "game")
    launchers = scan_folder(LAUNCHERS_DIR, "launcher")
    return games + launchers


def launch_item(path: str):
    try:
        os.startfile(path)
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de lancer :\n{path}\n\n{e}")


# -----------------------------
# Extraction des icônes Windows (SHGetFileInfo sur le FICHIER .lnk)
# -----------------------------

SHGFI_ICON = 0x100
SHGFI_LARGEICON = 0x0  # 32x32

class SHFILEINFO(ctypes.Structure):
    _fields_ = [
        ("hIcon", wintypes.HICON),
        ("iIcon", wintypes.INT),
        ("dwAttributes", wintypes.DWORD),
        ("szDisplayName", wintypes.WCHAR * 260),
        ("szTypeName", wintypes.WCHAR * 80),
    ]


def extract_icon_png(file_path: str, out_path: str) -> Optional[str]:
    """
    Extrait l'icône d'un fichier (EXE, LNK, etc.) via SHGetFileInfo
    et la sauvegarde en PNG dans out_path.
    On passe le .lnk pour avoir la même icône que l'Explorateur.
    """
    try:
        if not os.path.exists(file_path):
            print(f"[ICON] Fichier inexistant : {file_path}")
            return None

        shinfo = SHFILEINFO()
        res = ctypes.windll.shell32.SHGetFileInfoW(
            ctypes.c_wchar_p(file_path),
            0,
            ctypes.byref(shinfo),
            ctypes.sizeof(shinfo),
            SHGFI_ICON | SHGFI_LARGEICON,
        )

        if res == 0:
            print(f"[ICON] Impossible d'obtenir l'icône : {file_path}")
            return None

        hicon = shinfo.hIcon
        if not hicon:
            return None

        # Convert HICON -> PIL
        ico_x = win32api.GetSystemMetrics(win32con.SM_CXICON)
        ico_y = win32api.GetSystemMetrics(win32con.SM_CYICON)

        hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
        hbmp = win32ui.CreateBitmap()
        hbmp.CreateCompatibleBitmap(hdc, ico_x, ico_y)
        hdc_mem = hdc.CreateCompatibleDC()
        hdc_mem.SelectObject(hbmp)
        hdc_mem.DrawIcon((0, 0), hicon)

        bmpinfo = hbmp.GetInfo()
        bmpstr = hbmp.GetBitmapBits(True)

        img = Image.frombuffer(
            "RGB",
            (bmpinfo["bmWidth"], bmpinfo["bmHeight"]),
            bmpstr,
            "raw",
            "BGRX",
            0,
            1,
        )

        img.save(out_path)
        win32gui.DestroyIcon(hicon)
        print(f"[ICON] Icône extraite -> {out_path}")
        return out_path

    except Exception as e:
        print(f"[ICON] Erreur extraction {file_path}: {e}")
        return None


# -----------------------------
# UI avec customtkinter
# -----------------------------
class GameLauncherApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        self.title("Game Launcher (Python)")
        self.geometry("1100x650")
        self.minsize(900, 500)

        # Etat
        self.all_items: List[Item] = scan_all()
        self.filter_kind = "all"  # "all" / "game" / "launcher"
        self.search_text = ""

        # Cache images CTkImage (en mémoire)
        self.image_cache: dict[str, ctk.CTkImage] = {}

        # Layout principal
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self._build_header()
        self._build_filters()
        self._build_list()

        self.refresh_list()

    # ---------- Récupération de l'icône pour un item ----------

    def _get_ctk_icon_for_item(self, item: Item) -> ctk.CTkImage:
        """
        1. Cherche dans le cache en mémoire
        2. Cherche un PNG dans icon_cache/<slug>.png
        3. Sinon, extrait depuis le .lnk / .exe avec SHGetFileInfo
        4. Sinon, fallback carré coloré
        """
        cache_key = slugify(item.name)
        cache_path = os.path.join(ICON_CACHE_DIR, cache_key + ".png")

        # Cache mémoire
        if cache_key in self.image_cache:
            return self.image_cache[cache_key]

        # Cache fichier
        if os.path.exists(cache_path):
            try:
                img = Image.open(cache_path)
                cimg = ctk.CTkImage(light_image=img, dark_image=img, size=(80, 80))
                self.image_cache[cache_key] = cimg
                return cimg
            except Exception as e:
                print(f"[ICON CACHE] Erreur lecture {cache_path}: {e}")

        # Extraction depuis le FICHIER lui-même (lnk, exe, etc.)
        extracted = extract_icon_png(item.path, cache_path)
        if extracted and os.path.exists(extracted):
            try:
                img = Image.open(extracted)
                cimg = ctk.CTkImage(light_image=img, dark_image=img, size=(80, 80))
                self.image_cache[cache_key] = cimg
                return cimg
            except Exception as e:
                print(f"[ICON] Erreur lecture {extracted}: {e}")

        # Fallback : carré coloré (vert = jeu, bleu = launcher)
        color = "#22c55e" if item.kind == "game" else "#0ea5e9"
        img = Image.new("RGB", (80, 80), color)
        cimg = ctk.CTkImage(light_image=img, dark_image=img, size=(80, 80))
        self.image_cache[cache_key] = cimg
        return cimg

    # ---------- UI parts ----------

    def _build_header(self):
        header = ctk.CTkFrame(self)
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
        header.columnconfigure(0, weight=0)
        header.columnconfigure(1, weight=1)

        title_label = ctk.CTkLabel(
            header,
            text="🎮 Game Launcher",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        title_label.grid(row=0, column=0, sticky="w", padx=(10, 20), pady=10)

        self.search_entry = ctk.CTkEntry(
            header,
            placeholder_text="Rechercher un jeu ou un launcher...",
        )
        self.search_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=10)
        self.search_entry.bind("<KeyRelease>", self.on_search_change)

    def _build_filters(self):
        filters = ctk.CTkFrame(self)
        filters.grid(row=1, column=0, sticky="ew", padx=10, pady=(5, 5))

        self.btn_all = ctk.CTkButton(
            filters,
            text="🌐 Tous",
            command=lambda: self.set_filter("all"),
            width=100,
        )
        self.btn_all.grid(row=0, column=0, padx=5, pady=5)

        self.btn_games = ctk.CTkButton(
            filters,
            text="🎮 Jeux",
            command=lambda: self.set_filter("game"),
            width=100,
        )
        self.btn_games.grid(row=0, column=1, padx=5, pady=5)

        self.btn_launchers = ctk.CTkButton(
            filters,
            text="🚀 Launchers",
            command=lambda: self.set_filter("launcher"),
            width=120,
        )
        self.btn_launchers.grid(row=0, column=2, padx=5, pady=5)

        self.btn_rescan = ctk.CTkButton(
            filters,
            text="🔄 Rafraîchir",
            command=self.rescan_items,
            width=120,
        )
        self.btn_rescan.grid(row=0, column=3, padx=5, pady=5)

    def _build_list(self):
        container = ctk.CTkFrame(self)
        container.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))

        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        self.scroll_frame = ctk.CTkScrollableFrame(container)
        self.scroll_frame.grid(row=0, column=0, sticky="nsew")

    # ---------- Events ----------

    def set_filter(self, kind: str):
        self.filter_kind = kind
        self.refresh_list()

    def on_search_change(self, event=None):
        self.search_text = self.search_entry.get().strip().lower()
        self.refresh_list()

    def rescan_items(self):
        self.all_items = scan_all()
        self.refresh_list()

    # ---------- Logic ----------

    def get_filtered_items(self) -> List[Item]:
        items = self.all_items

        if self.filter_kind in ("game", "launcher"):
            items = [i for i in items if i.kind == self.filter_kind]

        if self.search_text:
            txt = self.search_text
            items = [
                i for i in items
                if txt in i.name.lower() or txt in i.path.lower()
            ]

        return items

    def refresh_list(self):
        for child in self.scroll_frame.winfo_children():
            child.destroy()

        items = self.get_filtered_items()

        if not items:
            lbl = ctk.CTkLabel(
                self.scroll_frame,
                text="Aucun élément trouvé.\n\nVérifie les dossiers :\n"
                     f"{GAMES_DIR}\n{LAUNCHERS_DIR}",
                justify="center",
            )
            lbl.pack(padx=20, pady=20)
            return

        max_cols = 3
        for index, item in enumerate(items):
            row = index // max_cols
            col = index % max_cols

            card = ctk.CTkFrame(self.scroll_frame, corner_radius=10)
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=8, pady=8)

            top_frame = ctk.CTkFrame(inner, fg_color="transparent")
            top_frame.pack(fill="x")

            icon = self._get_ctk_icon_for_item(item)
            icon_label = ctk.CTkLabel(top_frame, text="", image=icon)
            icon_label.pack(side="left", padx=(0, 8))

            title = ctk.CTkLabel(
                top_frame,
                text=item.name,
                font=ctk.CTkFont(size=16, weight="bold"),
            )
            title.pack(side="left", anchor="w")

            kind_text = "Jeu" if item.kind == "game" else "Launcher"
            subtitle = ctk.CTkLabel(
                inner,
                text=kind_text,
                font=ctk.CTkFont(size=12),
                text_color=("gray70", "gray60"),
            )
            subtitle.pack(anchor="w", pady=(4, 0))

            path_label = ctk.CTkLabel(
                inner,
                text=item.path,
                font=ctk.CTkFont(size=11),
                text_color=("gray80", "gray70"),
                wraplength=300,
                justify="left",
            )
            path_label.pack(anchor="w", pady=(4, 8))

            btn = ctk.CTkButton(
                inner,
                text="▶ Lancer",
                command=lambda p=item.path: launch_item(p),
                fg_color="#22c55e",
                hover_color="#16a34a",
            )
            btn.pack(fill="x", pady=(0, 4))


def main():
    app = GameLauncherApp()
    app.mainloop()


if __name__ == "__main__":
    main()
