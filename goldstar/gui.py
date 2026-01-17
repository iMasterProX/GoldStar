from __future__ import annotations

import json
import re
import shutil
import uuid
from pathlib import Path
from typing import Dict, Optional

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

from .config import EXPECTED_PACKS
from .pack_ops import check_missing_packs, create_missing_packs, expected_pack_names
from .paths import default_root, normalize_root

DEFAULT_NAMESPACE = "blf"
BEHAVIOR_PACK_NAME = "BLF_CustomTest"
ARMOR_SAMPLES = [
    ("test_armor_helmet", "slot.armor.head", "default_helmet"),
    ("test_armor_chestplate", "slot.armor.chest", "default_chest"),
    ("test_armor_leggings", "slot.armor.legs", "default_leggings"),
    ("test_armor_boots", "slot.armor.feet", "default_boots"),
]

LANGUAGE_LABELS = {
    "ko": "한국어",
    "en": "English",
}

TEXT = {
    "ko": {
        "app_title": "GoldStar",
        "select_pack_title": "작업할 리소스팩을 선택하세요",
        "root_path_label": "리소스팩 경로",
        "browse_button": "찾기",
        "language_label": "언어",
        "missing_packs": "누락된 팩: {names}",
        "all_packs_present": "모든 BLF_ 팩이 확인되었습니다.",
        "missing_all_title": "리소스팩 생성",
        "missing_all_message": "BLF_ 리소스팩이 하나도 없습니다. 메타데이터 기반 최소 리소스팩을 생성할까요?",
        "create_failed": "생성 실패: {error}",
        "missing_pack_warning": "이 팩이 없습니다: {name}",
        "not_supported": "아직 지원하지 않습니다.",
        "hint_double_click": "더블클릭으로 선택",
        "custom_entity_title": "CustomEntity - 새 엔티티 생성",
        "field_entity_name": "엔티티 이름",
        "field_namespace": "아이덴티파이어 prefix",
        "namespace_hint": "비우면 blf",
        "field_model": "모델링 파일",
        "field_texture": "텍스처 파일",
        "field_anim_controller": "애니메이션 컨트롤러(선택)",
        "field_animation": "애니메이션(선택)",
        "field_icon": "아이콘 텍스처(선택)",
        "behavior_pack_checkbox": "테스트용 행동팩도 생성하겠습니까?",
        "back_button": "뒤로",
        "create_button": "생성",
        "select_button": "선택",
        "required_hint": "필수: 이름/모델링/텍스처",
        "invalid_name": "엔티티 이름은 영문 소문자/숫자/언더바만, 최대 20자입니다.",
        "invalid_prefix": "prefix는 영문 소문자만 가능합니다.",
        "missing_required": "필수 항목이 비었습니다: {fields}",
        "duplicate_name": "이미 쓰고 있는 이름입니다.",
        "file_not_found": "파일을 찾을 수 없습니다: {path}",
        "create_success": "생성 완료: {name}",
        "error_title": "오류",
        "warning_title": "경고",
        "info_title": "안내",
        "invalid_root": "리소스팩 경로가 없습니다: {path}",
    },
    "en": {
        "app_title": "GoldStar",
        "select_pack_title": "Select a resource pack to work on",
        "root_path_label": "Resource pack path",
        "browse_button": "Browse",
        "language_label": "Language",
        "missing_packs": "Missing packs: {names}",
        "all_packs_present": "All BLF_ packs detected.",
        "missing_all_title": "Create packs",
        "missing_all_message": "No BLF_ resource packs found. Create minimal metadata-based packs?",
        "create_failed": "Create failed: {error}",
        "missing_pack_warning": "Pack not found: {name}",
        "not_supported": "Not supported yet.",
        "hint_double_click": "Double-click to select",
        "custom_entity_title": "CustomEntity - New Entity",
        "field_entity_name": "Entity name",
        "field_namespace": "Identifier prefix",
        "namespace_hint": "Default is blf",
        "field_model": "Model file",
        "field_texture": "Texture file",
        "field_anim_controller": "Animation controller (optional)",
        "field_animation": "Animation (optional)",
        "field_icon": "Icon texture (optional)",
        "behavior_pack_checkbox": "Also create test behavior pack?",
        "back_button": "Back",
        "create_button": "Create",
        "select_button": "Select",
        "required_hint": "Required: name/model/texture",
        "invalid_name": "Entity name must be lowercase letters/numbers/underscore, max 20 chars.",
        "invalid_prefix": "Prefix must be lowercase letters only.",
        "missing_required": "Required fields missing: {fields}",
        "duplicate_name": "Name already in use.",
        "file_not_found": "File not found: {path}",
        "create_success": "Created: {name}",
        "error_title": "Error",
        "warning_title": "Warning",
        "info_title": "Info",
        "invalid_root": "Resource pack path not found: {path}",
    },
}

PACK_DESCS: Dict[str, Dict[str, str]] = {}
for pack in EXPECTED_PACKS:
    if isinstance(pack, dict):
        name = pack.get("name")
        desc = pack.get("desc")
        if isinstance(name, str) and isinstance(desc, dict):
            PACK_DESCS[name] = desc

class ListboxTooltip:
    def __init__(self, listbox: tk.Listbox, text_func) -> None:
        self.listbox = listbox
        self.text_func = text_func
        self.tip: Optional[tk.Toplevel] = None
        self.current_index: Optional[int] = None
        listbox.bind("<Motion>", self._on_motion)
        listbox.bind("<Leave>", self._hide)

    def _on_motion(self, event) -> None:
        if self.listbox.size() == 0:
            self._hide()
            return
        index = self.listbox.nearest(event.y)
        if index == self.current_index:
            return
        self.current_index = index
        try:
            name = self.listbox.get(index)
        except tk.TclError:
            self._hide()
            return
        text = self.text_func(name)
        if not text:
            self._hide()
            return
        self._show(text, event.x_root + 12, event.y_root + 12)

    def _show(self, text: str, x: int, y: int) -> None:
        self._hide()
        self.tip = tk.Toplevel(self.listbox)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self.tip,
            text=text,
            background="#ffffe0",
            relief="solid",
            borderwidth=1,
            justify="left",
            padx=6,
            pady=3,
        )
        label.pack()

    def _hide(self, event=None) -> None:
        if self.tip is not None:
            self.tip.destroy()
            self.tip = None
        self.current_index = None

class GoldStarApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.language_var = tk.StringVar(value="ko")
        self.language_label_var = tk.StringVar(value=LANGUAGE_LABELS["ko"])
        self.root_path_var = tk.StringVar(value=str(default_root()))

        self.entity_name_var = tk.StringVar()
        self.namespace_var = tk.StringVar(value=DEFAULT_NAMESPACE)
        self.model_path_var = tk.StringVar()
        self.texture_path_var = tk.StringVar()
        self.anim_controller_path_var = tk.StringVar()
        self.animation_path_var = tk.StringVar()
        self.icon_path_var = tk.StringVar()
        self.behavior_pack_var = tk.BooleanVar(value=False)

        self.base_dir = Path(__file__).resolve().parents[1]
        self.logo_path = self.base_dir / "logo.png"
        self.logo_image: Optional[tk.PhotoImage] = None
        self.logo_icon: Optional[tk.PhotoImage] = None

        self._asked_missing_for = set()
        self.current_frame: Optional[tk.Widget] = None
        self.current_view = "splash"

        self._load_logos()
        self.root.title(self._t("app_title"))
        if self.logo_icon:
            self.root.iconphoto(False, self.logo_icon)

        self._show_splash()

    def _t(self, key: str, **kwargs) -> str:
        lang = self.language_var.get()
        text = TEXT.get(lang, {}).get(key, TEXT.get("en", {}).get(key, key))
        if kwargs:
            return text.format(**kwargs)
        return text

    def _clear_frame(self) -> None:
        if self.current_frame is not None:
            self.current_frame.destroy()
            self.current_frame = None

    def _load_logos(self) -> None:
        self.logo_image = self._load_logo_image(260)
        self.logo_icon = self._load_logo_image(32)

    def _load_logo_image(self, max_size: int) -> Optional[tk.PhotoImage]:
        if not self.logo_path.is_file():
            return None
        if PIL_AVAILABLE:
            image = Image.open(self.logo_path).convert("RGBA")
            image.thumbnail((max_size, max_size), Image.LANCZOS)
            return ImageTk.PhotoImage(image)
        base = tk.PhotoImage(file=str(self.logo_path))
        return self._downscale_photoimage(base, max_size)

    def _downscale_photoimage(self, image: tk.PhotoImage, max_size: int) -> tk.PhotoImage:
        width = image.width()
        height = image.height()
        scale = max(width / max_size, height / max_size, 1)
        new_width = max(1, int(round(width / scale)))
        new_height = max(1, int(round(height / scale)))
        if new_width == width and new_height == height:
            return image
        result = tk.PhotoImage(width=new_width, height=new_height)
        step_x = width / new_width
        step_y = height / new_height
        for y in range(new_height):
            y0 = int(y * step_y)
            y1 = max(y0 + 1, int((y + 1) * step_y))
            for x in range(new_width):
                x0 = int(x * step_x)
                x1 = max(x0 + 1, int((x + 1) * step_x))
                color = self._sample_box_color(image, x0, y0, x1, y1)
                result.put(color, (x, y))
        return result

    def _sample_box_color(self, image: tk.PhotoImage, x0: int, y0: int, x1: int, y1: int) -> str:
        max_x = image.width() - 1
        max_y = image.height() - 1
        sample_points = [
            (x0, y0),
            (x1 - 1, y0),
            (x0, y1 - 1),
            (x1 - 1, y1 - 1),
            ((x0 + x1) // 2, (y0 + y1) // 2),
        ]
        r_total = 0
        g_total = 0
        b_total = 0
        count = 0
        for sx, sy in sample_points:
            sx = min(max(sx, 0), max_x)
            sy = min(max(sy, 0), max_y)
            color = image.get(sx, sy)
            r, g, b = self._color_to_rgb(color)
            r_total += r
            g_total += g
            b_total += b
            count += 1
        r = max(0, min(255, r_total // count))
        g = max(0, min(255, g_total // count))
        b = max(0, min(255, b_total // count))
        return f"#{r:02x}{g:02x}{b:02x}"

    def _color_to_rgb(self, color) -> tuple:
        if isinstance(color, tuple) and len(color) >= 3:
            return color[0], color[1], color[2]
        if isinstance(color, str):
            if color.startswith("#") and len(color) == 7:
                return int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
            if color.startswith("#") and len(color) == 13:
                return (
                    int(color[1:5], 16) // 257,
                    int(color[5:9], 16) // 257,
                    int(color[9:13], 16) // 257,
                )
        return 0, 0, 0

    def _show_splash(self) -> None:
        self._clear_frame()
        self.current_view = "splash"
        self.root.configure(background="white")
        frame = tk.Frame(self.root, bg="white")
        frame.pack(fill="both", expand=True)
        self.current_frame = frame

        if self.logo_image:
            logo_label = tk.Label(frame, image=self.logo_image, bg="white")
            logo_label.pack(expand=True)
        else:
            logo_label = tk.Label(frame, text=self._t("app_title"), bg="white")
            logo_label.pack(expand=True)

        self.progress = ttk.Progressbar(frame, mode="determinate", maximum=100)
        self.progress.pack(pady=12, padx=80, fill="x")
        self._progress_value = 0
        self.root.after(50, self._tick_progress)

    def _tick_progress(self) -> None:
        self._progress_value += 8
        self.progress["value"] = self._progress_value
        if self._progress_value >= 100:
            self.root.after(150, self._show_selector)
        else:
            self.root.after(40, self._tick_progress)

    def _show_selector(self) -> None:
        self._clear_frame()
        self.current_view = "selector"
        frame = ttk.Frame(self.root, padding=12)
        frame.pack(fill="both", expand=True)
        self.current_frame = frame
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(2, weight=1)

        title = ttk.Label(frame, text=self._t("select_pack_title"), font=("TkDefaultFont", 14, "bold"))
        title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        lang_label = ttk.Label(frame, text=self._t("language_label"))
        lang_label.grid(row=0, column=2, sticky="e", padx=(12, 4))
        lang_combo = ttk.Combobox(
            frame,
            textvariable=self.language_label_var,
            values=list(LANGUAGE_LABELS.values()),
            state="readonly",
            width=10,
        )
        lang_combo.grid(row=0, column=3, sticky="e")
        lang_combo.bind("<<ComboboxSelected>>", self._on_language_change)

        path_label = ttk.Label(frame, text=self._t("root_path_label"))
        path_label.grid(row=1, column=0, sticky="w")
        path_entry = ttk.Entry(frame, textvariable=self.root_path_var)
        path_entry.grid(row=1, column=1, columnspan=2, sticky="ew", padx=(8, 8))
        browse_button = ttk.Button(frame, text=self._t("browse_button"), command=self._browse_root)
        browse_button.grid(row=1, column=3, sticky="e")

        list_frame = ttk.Frame(frame)
        list_frame.grid(row=2, column=0, columnspan=4, sticky="nsew", pady=(12, 6))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        self.pack_listbox = tk.Listbox(list_frame, height=12)
        self.pack_listbox.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.pack_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.pack_listbox.configure(yscrollcommand=scrollbar.set)

        self.pack_listbox.bind("<Double-Button-1>", self._open_selected_pack)
        self.pack_listbox.bind("<Return>", self._open_selected_pack)

        self.pack_listbox.delete(0, tk.END)
        for name in expected_pack_names():
            self.pack_listbox.insert(tk.END, name)

        self.tooltip = ListboxTooltip(self.pack_listbox, self._pack_description)

        self.missing_label = ttk.Label(frame, text="", wraplength=580, foreground="#b00020")
        self.missing_label.grid(row=3, column=0, columnspan=4, sticky="w")

        hint = ttk.Label(frame, text=self._t("hint_double_click"))
        hint.grid(row=4, column=0, columnspan=4, sticky="w")

        self._refresh_pack_status(ask_create=True)

    def _on_language_change(self, event=None) -> None:
        selected = self.language_label_var.get()
        for code, label in LANGUAGE_LABELS.items():
            if label == selected:
                self.language_var.set(code)
                break
        self.root.title(self._t("app_title"))
        if self.current_view == "selector":
            self._show_selector()
        elif self.current_view == "entity":
            self._show_entity_creator()

    def _browse_root(self) -> None:
        path = filedialog.askdirectory()
        if not path:
            return
        self.root_path_var.set(path)
        self._refresh_pack_status(ask_create=True)

    def _refresh_pack_status(self, ask_create: bool = True) -> None:
        root_path = normalize_root(self.root_path_var.get())
        if not root_path.is_dir():
            self.missing_label.config(text=self._t("invalid_root", path=str(root_path)))
            return
        missing = check_missing_packs(root_path)
        if missing:
            self.missing_label.config(text=self._t("missing_packs", names=", ".join(missing)))
        else:
            self.missing_label.config(text=self._t("all_packs_present"))
        if ask_create and len(missing) == len(expected_pack_names()):
            key = str(root_path)
            if key not in self._asked_missing_for:
                self._asked_missing_for.add(key)
                if messagebox.askyesno(self._t("missing_all_title"), self._t("missing_all_message")):
                    try:
                        create_missing_packs(root_path, missing)
                        self._refresh_pack_status(ask_create=False)
                    except Exception as exc:
                        messagebox.showerror(self._t("error_title"), self._t("create_failed", error=str(exc)))

    def _pack_description(self, name: str) -> str:
        desc = PACK_DESCS.get(name, {})
        lang = self.language_var.get()
        return desc.get(lang) or desc.get("en") or ""

    def _open_selected_pack(self, event=None) -> None:
        selection = self.pack_listbox.curselection()
        if not selection:
            return
        name = self.pack_listbox.get(selection[0])
        root_path = normalize_root(self.root_path_var.get())
        pack_path = root_path / name
        if not pack_path.is_dir():
            messagebox.showwarning(self._t("warning_title"), self._t("missing_pack_warning", name=name))
            return
        if name == "BLF_CustomEntity":
            self._show_entity_creator()
        else:
            messagebox.showinfo(self._t("info_title"), self._t("not_supported"))

    def _show_entity_creator(self) -> None:
        self._clear_frame()
        self.current_view = "entity"
        frame = ttk.Frame(self.root, padding=12)
        frame.pack(fill="both", expand=True)
        self.current_frame = frame
        frame.columnconfigure(1, weight=1)

        title = ttk.Label(frame, text=self._t("custom_entity_title"), font=("TkDefaultFont", 14, "bold"))
        title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        lang_label = ttk.Label(frame, text=self._t("language_label"))
        lang_label.grid(row=0, column=2, sticky="e", padx=(12, 4))
        lang_combo = ttk.Combobox(
            frame,
            textvariable=self.language_label_var,
            values=list(LANGUAGE_LABELS.values()),
            state="readonly",
            width=10,
        )
        lang_combo.grid(row=0, column=3, sticky="e")
        lang_combo.bind("<<ComboboxSelected>>", self._on_language_change)

        row = 1
        ttk.Label(frame, text=self._t("field_entity_name")).grid(row=row, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.entity_name_var).grid(
            row=row, column=1, columnspan=3, sticky="ew", padx=(8, 0)
        )

        row += 1
        ttk.Label(frame, text=self._t("field_namespace")).grid(row=row, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.namespace_var).grid(row=row, column=1, sticky="ew", padx=(8, 0))
        ttk.Label(frame, text=self._t("namespace_hint")).grid(row=row, column=2, columnspan=2, sticky="w", padx=(8, 0))

        row += 1
        self._add_file_row(frame, row, self._t("field_model"), self.model_path_var, [("JSON", "*.json"), ("All files", "*.*")])
        row += 1
        self._add_file_row(frame, row, self._t("field_texture"), self.texture_path_var, [("Images", "*.png;*.tga"), ("All files", "*.*")])
        row += 1
        self._add_file_row(
            frame,
            row,
            self._t("field_anim_controller"),
            self.anim_controller_path_var,
            [("JSON", "*.json"), ("All files", "*.*")],
        )
        row += 1
        self._add_file_row(frame, row, self._t("field_animation"), self.animation_path_var, [("JSON", "*.json"), ("All files", "*.*")])
        row += 1
        self._add_file_row(frame, row, self._t("field_icon"), self.icon_path_var, [("Images", "*.png"), ("All files", "*.*")])

        row += 1
        ttk.Label(frame, text=self._t("required_hint")).grid(row=row, column=0, columnspan=4, sticky="w", pady=(6, 0))
        row += 1
        ttk.Checkbutton(frame, text=self._t("behavior_pack_checkbox"), variable=self.behavior_pack_var).grid(
            row=row, column=0, columnspan=4, sticky="w", pady=(6, 0)
        )

        row += 1
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=row, column=0, columnspan=4, sticky="e", pady=(12, 0))
        ttk.Button(button_frame, text=self._t("back_button"), command=self._show_selector).pack(side="left", padx=(0, 8))
        ttk.Button(button_frame, text=self._t("create_button"), command=self._create_entity).pack(side="left")

    def _add_file_row(self, parent, row: int, label_text: str, var: tk.StringVar, filetypes) -> None:
        ttk.Label(parent, text=label_text).grid(row=row, column=0, sticky="w")
        ttk.Entry(parent, textvariable=var).grid(row=row, column=1, columnspan=2, sticky="ew", padx=(8, 0))
        ttk.Button(parent, text=self._t("select_button"), command=lambda: self._choose_file(var, filetypes)).grid(
            row=row, column=3, sticky="e"
        )

    def _choose_file(self, var: tk.StringVar, filetypes) -> None:
        path = filedialog.askopenfilename(filetypes=filetypes)
        if path:
            var.set(path)

    def _create_entity(self) -> None:
        name = self.entity_name_var.get().strip()
        namespace = self.namespace_var.get().strip() or DEFAULT_NAMESPACE

        missing_fields = []
        if not name:
            missing_fields.append(self._t("field_entity_name"))
        if not self.model_path_var.get().strip():
            missing_fields.append(self._t("field_model"))
        if not self.texture_path_var.get().strip():
            missing_fields.append(self._t("field_texture"))
        if missing_fields:
            messagebox.showwarning(
                self._t("warning_title"),
                self._t("missing_required", fields=", ".join(missing_fields)),
            )
            return

        if len(name) > 20 or not re.fullmatch(r"[a-z0-9_]+", name):
            messagebox.showwarning(self._t("warning_title"), self._t("invalid_name"))
            return

        if not re.fullmatch(r"[a-z]+", namespace):
            messagebox.showwarning(self._t("warning_title"), self._t("invalid_prefix"))
            return

        model_source = Path(self.model_path_var.get().strip())
        if not model_source.is_file():
            messagebox.showerror(self._t("error_title"), self._t("file_not_found", path=str(model_source)))
            return

        texture_source = Path(self.texture_path_var.get().strip())
        if not texture_source.is_file():
            messagebox.showerror(self._t("error_title"), self._t("file_not_found", path=str(texture_source)))
            return

        animation_source = Path(self.animation_path_var.get().strip()) if self.animation_path_var.get().strip() else None
        if animation_source and not animation_source.is_file():
            messagebox.showerror(self._t("error_title"), self._t("file_not_found", path=str(animation_source)))
            return

        controller_source = (
            Path(self.anim_controller_path_var.get().strip())
            if self.anim_controller_path_var.get().strip()
            else None
        )
        if controller_source and not controller_source.is_file():
            messagebox.showerror(self._t("error_title"), self._t("file_not_found", path=str(controller_source)))
            return

        icon_source = Path(self.icon_path_var.get().strip()) if self.icon_path_var.get().strip() else None
        if icon_source and not icon_source.is_file():
            messagebox.showerror(self._t("error_title"), self._t("file_not_found", path=str(icon_source)))
            return

        root_path = normalize_root(self.root_path_var.get())
        if not root_path.is_dir():
            messagebox.showerror(self._t("error_title"), self._t("invalid_root", path=str(root_path)))
            return

        pack_root = root_path / "BLF_CustomEntity"
        if not pack_root.is_dir():
            messagebox.showerror(self._t("error_title"), self._t("missing_pack_warning", name="BLF_CustomEntity"))
            return

        entity_path = pack_root / "entity" / f"{name}.entity.json"
        if entity_path.exists():
            messagebox.showwarning(self._t("warning_title"), self._t("duplicate_name"))
            return

        try:
            self._generate_entity_files(
                pack_root,
                name,
                namespace,
                model_source,
                texture_source,
                animation_source,
                controller_source,
                icon_source,
            )
            if self.behavior_pack_var.get():
                behavior_pack = self._ensure_behavior_pack()
                self._create_behavior_entity(behavior_pack, name, namespace)
                self._create_behavior_spawn_item(behavior_pack, name, namespace)
                self._ensure_armor_samples(behavior_pack, namespace)
        except Exception as exc:
            messagebox.showerror(self._t("error_title"), str(exc))
            return

        messagebox.showinfo(self._t("info_title"), self._t("create_success", name=name))
        self._show_selector()

    def _generate_entity_files(
        self,
        pack_root: Path,
        name: str,
        namespace: str,
        model_source: Path,
        texture_source: Path,
        animation_source: Optional[Path],
        controller_source: Optional[Path],
        icon_source: Optional[Path],
    ) -> None:
        animations_dir = pack_root / "animations"
        controllers_dir = pack_root / "animation_controllers"
        entity_dir = pack_root / "entity"
        models_dir = pack_root / "models" / "entity"
        textures_entity_dir = pack_root / "textures" / "entity"
        textures_items_dir = pack_root / "textures" / "items"

        for path in [animations_dir, controllers_dir, entity_dir, models_dir, textures_entity_dir, textures_items_dir]:
            path.mkdir(parents=True, exist_ok=True)

        template_animation = animations_dir / "default_entity.animation.json"
        template_controller = controllers_dir / "default_entity.ac.json"
        template_entity = entity_dir / "default_entity.entity.json"
        template_icon = textures_items_dir / "default_entity.icon.png"

        animation_src = animation_source or template_animation
        controller_src = controller_source or template_controller
        if not animation_src.is_file():
            raise FileNotFoundError(self._t("file_not_found", path=str(animation_src)))
        if not controller_src.is_file():
            raise FileNotFoundError(self._t("file_not_found", path=str(controller_src)))
        if not template_entity.is_file():
            raise FileNotFoundError(self._t("file_not_found", path=str(template_entity)))

        anim_dest = animations_dir / f"{name}.animation.json"
        controller_dest = controllers_dir / f"{name}.ac.json"
        model_dest = models_dir / f"{name}.geo.json"
        texture_dest = textures_entity_dir / f"{name}{texture_source.suffix}"
        icon_dest = textures_items_dir / f"{name}.icon.png"

        self._copy_text_with_replace(animation_src, anim_dest, {"default_entity": name})
        self._copy_text_with_replace(controller_src, controller_dest, {"default_entity": name})

        model_text = model_source.read_text(encoding="utf-8")
        if "default_entity" in model_text:
            model_text = model_text.replace("default_entity", name)
        model_dest.write_text(model_text, encoding="utf-8")
        geo_identifier = self._get_geometry_identifier(model_dest) or f"geometry.{name}"

        shutil.copy2(texture_source, texture_dest)

        if icon_source and icon_source.is_file():
            shutil.copy2(icon_source, icon_dest)
        elif template_icon.is_file():
            shutil.copy2(template_icon, icon_dest)
        else:
            raise FileNotFoundError(self._t("file_not_found", path=str(template_icon)))

        entity_data = self._load_json(template_entity)
        client_entity = entity_data.setdefault("minecraft:client_entity", {})
        if not isinstance(client_entity, dict):
            client_entity = {}
            entity_data["minecraft:client_entity"] = client_entity
        description = client_entity.setdefault("description", {})
        if not isinstance(description, dict):
            description = {}
            client_entity["description"] = description

        description["identifier"] = f"{namespace}:{name}"
        description["textures"] = {"default": f"textures/entity/{name}"}
        description["geometry"] = {"default": geo_identifier}
        description["animations"] = {
            "setup": f"animation.{name}.setup",
            "normal": f"animation.{name}.normal",
            "default": f"animation.{name}.default",
            "skill1": f"animation.{name}.skill1",
            "skill2": f"animation.{name}.skill2",
            "skill3": f"animation.{name}.skill3",
            "skill4": f"animation.{name}.skill4",
            "skill5": f"animation.{name}.skill5",
        }
        description["scripts"] = {
            "animate": ["setup", "normal", f"controller.animation.{name}"]
        }
        description["spawn_egg"] = {"texture": name}

        self._write_json(entity_dir / f"{name}.entity.json", entity_data)
        self._ensure_item_texture_entry(pack_root, name)

    def _copy_text_with_replace(self, source: Path, destination: Path, replacements: Dict[str, str]) -> None:
        text = source.read_text(encoding="utf-8")
        for old, new in replacements.items():
            text = text.replace(old, new)
        destination.write_text(text, encoding="utf-8")

    def _load_json(self, path: Path) -> dict:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

    def _write_json(self, path: Path, data: dict) -> None:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def _get_geometry_identifier(self, path: Path) -> Optional[str]:
        data = self._load_json(path)
        geos = data.get("minecraft:geometry")
        if isinstance(geos, list) and geos:
            desc = geos[0].get("description")
            if isinstance(desc, dict):
                ident = desc.get("identifier")
                if isinstance(ident, str):
                    return ident
        return None

    def _ensure_item_texture_entry(self, pack_root: Path, name: str) -> None:
        item_texture_path = pack_root / "textures" / "item_texture.json"
        data = self._load_json(item_texture_path)
        if not isinstance(data, dict):
            data = {}
        texture_data = data.get("texture_data")
        if not isinstance(texture_data, dict):
            texture_data = {}
            data["texture_data"] = texture_data
        texture_data[name] = {"textures": f"textures/items/{name}.icon"}
        data.setdefault("texture_name", "atlas.items")
        data.setdefault("resource_pack_name", "vanilla")
        self._write_json(item_texture_path, data)

    def _ensure_behavior_pack(self) -> Path:
        root_path = normalize_root(self.root_path_var.get())
        behavior_root = root_path.parent / "development_behavior_packs"
        behavior_root.mkdir(parents=True, exist_ok=True)
        pack_dir = behavior_root / BEHAVIOR_PACK_NAME
        pack_dir.mkdir(parents=True, exist_ok=True)
        (pack_dir / "entities").mkdir(parents=True, exist_ok=True)
        (pack_dir / "items").mkdir(parents=True, exist_ok=True)

        manifest_path = pack_dir / "manifest.json"
        if not manifest_path.is_file():
            manifest = {
                "format_version": 2,
                "header": {
                    "name": BEHAVIOR_PACK_NAME,
                    "description": f"{BEHAVIOR_PACK_NAME} (generated by goldstar)",
                    "uuid": str(uuid.uuid4()),
                    "version": [1, 0, 0],
                    "min_engine_version": [1, 20, 0],
                },
                "modules": [
                    {
                        "type": "data",
                        "uuid": str(uuid.uuid4()),
                        "version": [1, 0, 0],
                    }
                ],
            }
            self._write_json(manifest_path, manifest)

        icon_path = pack_dir / "pack_icon.png"
        if not icon_path.is_file():
            icon_source = self._find_pack_icon_source()
            if icon_source:
                shutil.copy2(icon_source, icon_path)

        return pack_dir

    def _find_pack_icon_source(self) -> Optional[Path]:
        root_path = normalize_root(self.root_path_var.get())
        for name in expected_pack_names():
            icon_path = root_path / name / "pack_icon.png"
            if icon_path.is_file():
                return icon_path
        if self.logo_path.is_file():
            return self.logo_path
        return None

    def _build_behavior_entity(self, namespace: str, name: str) -> dict:
        return {
            "format_version": "1.20.0",
            "minecraft:entity": {
                "description": {
                    "identifier": f"{namespace}:{name}",
                    "is_spawnable": True,
                    "is_summonable": True,
                    "is_experimental": False,
                },
                "components": {
                    "minecraft:health": {"value": 1, "max": 1},
                    "minecraft:movement": {"value": 0},
                    "minecraft:collision_box": {"width": 0.6, "height": 1.8},
                    "minecraft:pushable": {
                        "is_pushable": False,
                        "is_pushable_by_piston": False,
                    },
                },
            },
        }

    def _build_behavior_spawn_item(self, namespace: str, name: str) -> dict:
        return {
            "format_version": "1.20.0",
            "minecraft:item": {
                "description": {"identifier": f"{namespace}:{name}_spawn"},
                "components": {
                    "minecraft:display_name": {"value": f"{name} spawn"},
                    "minecraft:icon": {"texture": name},
                    "minecraft:entity_placer": {"entity": f"{namespace}:{name}"},
                },
            },
        }

    def _build_behavior_armor_item(self, namespace: str, identifier: str, slot: str, icon: str) -> dict:
        return {
            "format_version": "1.20.0",
            "minecraft:item": {
                "description": {"identifier": f"{namespace}:{identifier}"},
                "components": {
                    "minecraft:display_name": {"value": identifier},
                    "minecraft:icon": {"texture": icon},
                    "minecraft:wearable": {"slot": slot},
                    "minecraft:armor": {"protection": 1},
                    "minecraft:durability": {"max_durability": 1},
                },
            },
        }

    def _create_behavior_entity(self, pack_dir: Path, name: str, namespace: str) -> None:
        entity_path = pack_dir / "entities" / f"{name}.json"
        if entity_path.exists():
            raise FileExistsError(self._t("duplicate_name"))
        self._write_json(entity_path, self._build_behavior_entity(namespace, name))

    def _create_behavior_spawn_item(self, pack_dir: Path, name: str, namespace: str) -> None:
        item_path = pack_dir / "items" / f"{name}_spawn.json"
        if item_path.exists():
            raise FileExistsError(self._t("duplicate_name"))
        self._write_json(item_path, self._build_behavior_spawn_item(namespace, name))

    def _ensure_armor_samples(self, pack_dir: Path, namespace: str) -> None:
        items_dir = pack_dir / "items"
        for identifier, slot, icon in ARMOR_SAMPLES:
            item_path = items_dir / f"{identifier}.json"
            if item_path.is_file():
                continue
            item_data = self._build_behavior_armor_item(namespace, identifier, slot, icon)
            self._write_json(item_path, item_data)


def main() -> None:
    root = tk.Tk()
    app = GoldStarApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
