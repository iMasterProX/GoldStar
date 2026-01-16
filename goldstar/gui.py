import json
import re
import shutil
from pathlib import Path
import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox, ttk

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except Exception:
    Image = None
    ImageTk = None
    PIL_AVAILABLE = False

from .config import EXPECTED_PACKS
from .pack_ops import check_missing_packs, create_missing_packs, expected_pack_names
from .paths import default_root, normalize_root
from .scanner import scan_packs

MAX_NAME_LEN = 20


class ListboxTooltip:
    def __init__(self, listbox: tk.Listbox, descriptions: dict[str, str]) -> None:
        self.listbox = listbox
        self.descriptions = descriptions
        self.tip = None
        self.last_index = None
        self.listbox.bind("<Motion>", self._on_motion)
        self.listbox.bind("<Leave>", self._on_leave)

    def _on_motion(self, event: tk.Event) -> None:
        index = self.listbox.nearest(event.y)
        if index < 0:
            return
        name = self.listbox.get(index)
        description = self.descriptions.get(name)
        if not description:
            self._hide()
            return
        if self.last_index == index and self.tip is not None:
            return
        self._show(event, description)
        self.last_index = index

    def _on_leave(self, _event: tk.Event) -> None:
        self._hide()

    def _show(self, event: tk.Event, text: str) -> None:
        self._hide()
        self.tip = tk.Toplevel(self.listbox)
        self.tip.wm_overrideredirect(True)
        x = event.x_root + 12
        y = event.y_root + 12
        self.tip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self.tip,
            text=text,
            justify="left",
            background="#fff9c4",
            relief="solid",
            borderwidth=1,
            padx=8,
            pady=6,
        )
        label.pack()

    def _hide(self) -> None:
        if self.tip is not None:
            self.tip.destroy()
            self.tip = None
            self.last_index = None


class MainWindow:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("GoldStar")
        self.root.minsize(860, 600)

        self.root_path_var = tk.StringVar(value=str(default_root()))
        self.status_var = tk.StringVar(value="")

        self.splash_frame = None
        self.progress = None
        self.loading_value = 0

        self.current_frame = None
        self.pack_list = None
        self.log_text = None
        self.select_button = None

        self.entity_name_var = None
        self.namespace_var = None
        self.anim_controller_var = None
        self.animation_var = None
        self.model_var = None
        self.texture_var = None
        self.icon_var = None
        self.entity_log_text = None

        self.logo_source = None
        self.logo_image = None
        self.logo_icon = None

        self.title_font = self._make_font(28, "bold")
        self.header_font = self._make_font(14, "bold")

        self._load_logo_assets()
        self._build_splash()
        self._start_loading()

    def _make_font(self, size: int, weight: str) -> tkfont.Font:
        base = tkfont.nametofont("TkDefaultFont")
        custom = base.copy()
        custom.configure(size=size, weight=weight)
        return custom

    def _build_splash(self) -> None:
        self.splash_frame = tk.Frame(self.root, bg="white")
        self.splash_frame.pack(fill="both", expand=True)

        if self.logo_image is not None:
            title = tk.Label(self.splash_frame, image=self.logo_image, bg="white")
        else:
            title = tk.Label(
                self.splash_frame,
                text="GoldStar",
                font=self.title_font,
                bg="white",
                fg="#222222",
            )
        title.pack(expand=True)

        self.progress = ttk.Progressbar(
            self.splash_frame,
            orient="horizontal",
            mode="determinate",
            length=320,
            maximum=100,
        )
        self.progress.pack(pady=(0, 80))

    def _start_loading(self) -> None:
        self.loading_value = 0
        self._step_loading()

    def _step_loading(self) -> None:
        self.loading_value += 10
        if self.progress is not None:
            self.progress["value"] = self.loading_value
        if self.loading_value >= 100:
            self._show_selector()
        else:
            self.root.after(80, self._step_loading)

    def _load_logo_assets(self) -> None:
        logo_path = self._resolve_logo_path()
        if logo_path is None:
            return

        if PIL_AVAILABLE:
            try:
                image = Image.open(logo_path)
                self.logo_image = self._scale_pil(image, 260)
                self.logo_icon = self._scale_pil(image, 32)
                if self.logo_icon is not None:
                    self.root.iconphoto(True, self.logo_icon)
                return
            except Exception:
                pass

        try:
            self.logo_source = tk.PhotoImage(file=str(logo_path))
        except tk.TclError:
            return

        self.logo_image = self._scale_logo(self.logo_source, 260)
        self.logo_icon = self._scale_logo(self.logo_source, 32)
        if self.logo_icon is not None:
            self.root.iconphoto(True, self.logo_icon)

    def _resolve_logo_path(self) -> Path | None:
        candidates = [
            Path(__file__).resolve().parent.parent / "logo.png",
            Path(__file__).resolve().parent / "logo.png",
            Path.cwd() / "logo.png",
        ]
        for path in candidates:
            if path.is_file():
                return path
        return None

    def _scale_pil(self, image, target_size: int):
        if ImageTk is None:
            return None
        width, height = image.size
        max_dim = max(width, height)
        if max_dim <= target_size:
            resized = image.copy()
        else:
            scale = target_size / max_dim
            new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
            resized = image.resize(new_size, Image.LANCZOS)
        return ImageTk.PhotoImage(resized)

    def _scale_logo(self, image: tk.PhotoImage, target_size: int) -> tk.PhotoImage:
        width = image.width()
        height = image.height()
        max_dim = max(width, height)
        if max_dim <= target_size:
            return image
        scale = target_size / max_dim
        new_w = max(1, int(width * scale))
        new_h = max(1, int(height * scale))
        new_image = tk.PhotoImage(width=new_w, height=new_h)
        step_x = width / new_w
        step_y = height / new_h

        for y in range(new_h):
            y0 = int(y * step_y)
            y1 = int((y + 1) * step_y)
            if y1 <= y0:
                y1 = y0 + 1
            row = []
            for x in range(new_w):
                x0 = int(x * step_x)
                x1 = int((x + 1) * step_x)
                if x1 <= x0:
                    x1 = x0 + 1
                r_sum = g_sum = b_sum = 0
                count = 0
                for sy in range(y0, y1):
                    for sx in range(x0, x1):
                        r, g, b = self._parse_color(image.get(sx, sy))
                        r_sum += r
                        g_sum += g
                        b_sum += b
                        count += 1
                if count == 0:
                    row.append("#000000")
                else:
                    row.append(
                        f"#{r_sum // count:02x}{g_sum // count:02x}{b_sum // count:02x}"
                    )
            new_image.put("{" + " ".join(row) + "}", to=(0, y))
        return new_image

    def _parse_color(self, value):
        if isinstance(value, tuple) and len(value) >= 3:
            return int(value[0]), int(value[1]), int(value[2])
        if isinstance(value, str):
            if value.startswith("#") and len(value) == 7:
                return (
                    int(value[1:3], 16),
                    int(value[3:5], 16),
                    int(value[5:7], 16),
                )
            parts = value.split()
            if len(parts) >= 3:
                return int(parts[0]), int(parts[1]), int(parts[2])
        return 0, 0, 0

    def _switch_view(self, frame: ttk.Frame) -> None:
        if self.current_frame is not None:
            self.current_frame.destroy()
        self.current_frame = frame
        self.current_frame.pack(fill="both", expand=True)

    def _show_selector(self) -> None:
        if self.splash_frame is not None:
            self.splash_frame.destroy()
        self._switch_view(self._build_selector())
        self._scan_required_packs()

    def _build_selector(self) -> ttk.Frame:
        wrapper = ttk.Frame(self.root, padding=12)

        ttk.Label(
            wrapper,
            text="작업할 리소스팩을 선택하세요",
            font=self.header_font,
        ).pack(anchor="w", pady=(0, 8))

        info = (
            "이 프로그램을 사용하려면 아래 경로에 BLF_ 리소스팩 11개가 모두 있어야 합니다."
        )
        ttk.Label(wrapper, text=info, foreground="#444444").pack(anchor="w")

        path_frame = ttk.Frame(wrapper)
        path_frame.pack(fill="x", pady=10)

        ttk.Label(path_frame, text="리소스팩 경로").pack(side="left")
        entry = ttk.Entry(path_frame, textvariable=self.root_path_var, width=80)
        entry.pack(side="left", padx=6, fill="x", expand=True)
        ttk.Button(path_frame, text="찾기", command=self._browse).pack(side="left")
        ttk.Button(path_frame, text="검사", command=self._scan_required_packs).pack(
            side="left", padx=6
        )

        list_frame = ttk.Frame(wrapper)
        list_frame.pack(fill="both", expand=True)

        self.pack_list = tk.Listbox(list_frame, height=11)
        self.pack_list.pack(side="left", fill="both", expand=True)
        list_scroll = ttk.Scrollbar(
            list_frame, orient="vertical", command=self.pack_list.yview
        )
        list_scroll.pack(side="right", fill="y")
        self.pack_list.config(yscrollcommand=list_scroll.set)
        self.pack_list.bind("<Double-Button-1>", self._on_pack_double_click)

        descriptions = {name: desc for name, desc in EXPECTED_PACKS}
        ListboxTooltip(self.pack_list, descriptions)

        action_frame = ttk.Frame(wrapper)
        action_frame.pack(fill="x", pady=(8, 4))

        self.select_button = ttk.Button(
            action_frame, text="선택", command=self._select_pack
        )
        self.select_button.pack(side="right")
        ttk.Label(action_frame, textvariable=self.status_var).pack(side="left")

        log_frame = ttk.Frame(wrapper)
        log_frame.pack(fill="both", expand=True, pady=(8, 0))

        ttk.Label(log_frame, text="로그").pack(anchor="w")
        self.log_text = tk.Text(log_frame, height=8, wrap="word")
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scroll = ttk.Scrollbar(
            log_frame, orient="vertical", command=self.log_text.yview
        )
        log_scroll.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=log_scroll.set)
        self.log_text.configure(state="disabled")

        self._populate_pack_list()
        return wrapper

    def _build_entity_creator(self) -> ttk.Frame:
        wrapper = ttk.Frame(self.root, padding=12)

        header_frame = ttk.Frame(wrapper)
        header_frame.pack(fill="x")

        ttk.Label(
            header_frame,
            text="CustomEntity - 새 엔티티 생성",
            font=self.header_font,
        ).pack(side="left")
        ttk.Button(header_frame, text="뒤로", command=self._show_selector).pack(
            side="right"
        )

        note = (
            "이름/모델/텍스처는 필수입니다. "
            "애니메이션 컨트롤러/애니메이션/아이콘은 선택 사항입니다."
        )
        ttk.Label(wrapper, text=note, foreground="#444444").pack(anchor="w", pady=6)

        form = ttk.Frame(wrapper)
        form.pack(fill="x", pady=(8, 4))
        form.columnconfigure(1, weight=1)

        self.entity_name_var = tk.StringVar()
        self.namespace_var = tk.StringVar(value="blf")
        self.anim_controller_var = tk.StringVar()
        self.animation_var = tk.StringVar()
        self.model_var = tk.StringVar()
        self.texture_var = tk.StringVar()
        self.icon_var = tk.StringVar()

        namespace_label = "아이덴티피어 prefix"
        ttk.Label(form, text=namespace_label).grid(row=0, column=0, sticky="w", pady=4)
        namespace_entry = ttk.Entry(
            form,
            textvariable=self.namespace_var,
            validate="key",
            validatecommand=(self.root.register(self._validate_namespace), "%P"),
        )
        namespace_entry.grid(row=0, column=1, sticky="ew", padx=6, pady=4)
        ttk.Label(
            form,
            text="비우면 기본값 blf",
            foreground="#666666",
        ).grid(row=0, column=2, sticky="w", padx=6)

        name_label = "엔티티 이름 *"
        ttk.Label(form, text=name_label).grid(row=1, column=0, sticky="w", pady=4)
        name_entry = ttk.Entry(
            form,
            textvariable=self.entity_name_var,
            validate="key",
            validatecommand=(self.root.register(self._validate_entity_name), "%P"),
        )
        name_entry.grid(row=1, column=1, sticky="ew", padx=6, pady=4)
        ttk.Label(
            form,
            text=f"영문 소문자/숫자/언더바만, 공백/대문자 불가, 최대 {MAX_NAME_LEN}자",
            foreground="#666666",
        ).grid(row=1, column=2, sticky="w", padx=6)

        self._add_file_row(
            form,
            row=2,
            label="애니메이션 컨트롤러",
            var=self.anim_controller_var,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        self._add_file_row(
            form,
            row=3,
            label="애니메이션",
            var=self.animation_var,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        self._add_file_row(
            form,
            row=4,
            label="모델링 *",
            var=self.model_var,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        self._add_file_row(
            form,
            row=5,
            label="텍스처 *",
            var=self.texture_var,
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
        )
        self._add_file_row(
            form,
            row=6,
            label="아이콘 텍스처",
            var=self.icon_var,
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
        )

        action_frame = ttk.Frame(wrapper)
        action_frame.pack(fill="x", pady=(10, 6))
        ttk.Button(action_frame, text="생성", command=self._create_entity).pack(
            side="right"
        )

        log_frame = ttk.Frame(wrapper)
        log_frame.pack(fill="both", expand=True, pady=(8, 0))

        ttk.Label(log_frame, text="로그").pack(anchor="w")
        self.entity_log_text = tk.Text(log_frame, height=10, wrap="word")
        self.entity_log_text.pack(side="left", fill="both", expand=True)
        log_scroll = ttk.Scrollbar(
            log_frame, orient="vertical", command=self.entity_log_text.yview
        )
        log_scroll.pack(side="right", fill="y")
        self.entity_log_text.config(yscrollcommand=log_scroll.set)
        self.entity_log_text.configure(state="disabled")

        return wrapper

    def _add_file_row(
        self,
        parent: ttk.Frame,
        row: int,
        label: str,
        var: tk.StringVar,
        filetypes: list[tuple[str, str]],
    ) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=4)
        entry = ttk.Entry(parent, textvariable=var)
        entry.grid(row=row, column=1, sticky="ew", padx=6, pady=4)
        ttk.Button(
            parent,
            text="찾기",
            command=lambda: self._choose_file(var, filetypes),
        ).grid(row=row, column=2, sticky="w", padx=6)

    def _choose_file(self, var: tk.StringVar, filetypes: list[tuple[str, str]]) -> None:
        initial_dir = self._pack_path("BLF_CustomEntity")
        path = filedialog.askopenfilename(
            initialdir=str(initial_dir) if initial_dir else None,
            filetypes=filetypes,
        )
        if path:
            var.set(path)

    def _validate_entity_name(self, value: str) -> bool:
        if len(value) > MAX_NAME_LEN:
            return False
        if value == "":
            return True
        return re.fullmatch(r"[a-z0-9_]+", value) is not None

    def _validate_namespace(self, value: str) -> bool:
        if value == "":
            return True
        if len(value) > MAX_NAME_LEN:
            return False
        return re.fullmatch(r"[a-z]+", value) is not None

    def _normalize_namespace(self) -> str:
        if self.namespace_var is None:
            return "blf"
        value = self.namespace_var.get().strip()
        return value if value else "blf"

    def _validate_entity_input(self) -> list[str]:
        errors = []
        name = (self.entity_name_var.get() if self.entity_name_var else "").strip()
        if not name:
            errors.append("엔티티 이름은 필수입니다.")
        elif len(name) > MAX_NAME_LEN:
            errors.append(f"엔티티 이름은 최대 {MAX_NAME_LEN}자까지 가능합니다.")
        elif re.fullmatch(r"[a-z0-9_]+", name) is None:
            errors.append("엔티티 이름은 영문 소문자/숫자/언더바만 사용할 수 있습니다.")

        namespace = (self.namespace_var.get() if self.namespace_var else "").strip()
        if namespace and re.fullmatch(r"[a-z]+", namespace) is None:
            errors.append("prefix는 영문 소문자만 사용할 수 있습니다.")
        elif namespace and len(namespace) > MAX_NAME_LEN:
            errors.append(f"prefix는 최대 {MAX_NAME_LEN}자까지 가능합니다.")

        model_path = (self.model_var.get() if self.model_var else "").strip()
        if not model_path:
            errors.append("모델링 파일은 필수입니다.")
        elif not Path(model_path).is_file():
            errors.append("모델링 파일 경로가 올바르지 않습니다.")

        texture_path = (self.texture_var.get() if self.texture_var else "").strip()
        if not texture_path:
            errors.append("텍스처 파일은 필수입니다.")
        elif not Path(texture_path).is_file():
            errors.append("텍스처 파일 경로가 올바르지 않습니다.")

        anim_controller = (
            self.anim_controller_var.get() if self.anim_controller_var else ""
        ).strip()
        if anim_controller and not Path(anim_controller).is_file():
            errors.append("애니메이션 컨트롤러 파일 경로가 올바르지 않습니다.")

        animation = (self.animation_var.get() if self.animation_var else "").strip()
        if animation and not Path(animation).is_file():
            errors.append("애니메이션 파일 경로가 올바르지 않습니다.")

        icon = (self.icon_var.get() if self.icon_var else "").strip()
        if icon and not Path(icon).is_file():
            errors.append("아이콘 텍스처 파일 경로가 올바르지 않습니다.")

        return errors

    def _create_entity(self) -> None:
        errors = self._validate_entity_input()
        if errors:
            messagebox.showerror("입력 오류", "\n".join(errors))
            return

        name = self.entity_name_var.get().strip()
        namespace = self._normalize_namespace()
        if self._entity_name_in_use(name):
            messagebox.showerror("이름 중복", "이미 쓰고 있는 이름입니다.")
            return

        pack_path = self._pack_path("BLF_CustomEntity")
        if pack_path is None:
            messagebox.showerror("경로 오류", "BLF_CustomEntity 경로를 찾을 수 없습니다.")
            return

        try:
            self._ensure_entity_dirs(pack_path)

            entity_path = pack_path / "entity" / f"{name}.entity.json"
            model_target = pack_path / "models" / "entity" / f"{name}.geo.json"
            texture_target = pack_path / "textures" / "entity" / f"{name}.png"
            anim_target = pack_path / "animations" / f"{name}.animation.json"
            controller_target = (
                pack_path / "animation_controllers" / f"{name}.ac.json"
            )
            icon_target = pack_path / "textures" / "items" / f"{name}.icon.png"

            defaults = self._default_entity_templates()

            model_path = Path(self.model_var.get().strip())
            texture_path = Path(self.texture_var.get().strip())
            anim_controller_path = self.anim_controller_var.get().strip()
            animation_path = self.animation_var.get().strip()
            icon_path = self.icon_var.get().strip()

            self._copy_json_with_replacements(model_path, model_target, name)
            shutil.copy2(texture_path, texture_target)

            if anim_controller_path:
                self._copy_json_with_replacements(
                    Path(anim_controller_path), controller_target, name
                )
            else:
                self._copy_json_with_replacements(
                    Path(defaults["anim_controller"]), controller_target, name
                )

            if animation_path:
                self._copy_json_with_replacements(
                    Path(animation_path), anim_target, name
                )
            else:
                self._copy_json_with_replacements(
                    Path(defaults["animation"]), anim_target, name
                )

            if icon_path:
                shutil.copy2(Path(icon_path), icon_target)
            else:
                shutil.copy2(Path(defaults["icon"]), icon_target)

            self._create_entity_json(
                Path(defaults["entity"]), entity_path, name, namespace
            )
            self._update_item_texture(pack_path, name)

            self._log_entity(f"생성 완료: {entity_path}")
            messagebox.showinfo("완료", "엔티티 파일이 생성되었습니다.")
            self._show_selector()
        except Exception as exc:
            messagebox.showerror("생성 실패", f"생성 중 오류가 발생했습니다.\n{exc}")

    def _default_entity_templates(self) -> dict[str, str]:
        pack_path = self._pack_path("BLF_CustomEntity")
        if pack_path is None:
            return {
                "entity": "entity/default_entity.entity.json",
                "anim_controller": "animation_controllers/default_entity.ac.json",
                "animation": "animations/default_entity.animation.json",
                "icon": "textures/items/default_entity.icon.png",
            }
        return {
            "entity": str(pack_path / "entity" / "default_entity.entity.json"),
            "anim_controller": str(
                pack_path / "animation_controllers" / "default_entity.ac.json"
            ),
            "animation": str(pack_path / "animations" / "default_entity.animation.json"),
            "icon": str(pack_path / "textures" / "items" / "default_entity.icon.png"),
        }

    def _ensure_entity_dirs(self, pack_path: Path) -> None:
        for rel in [
            "entity",
            "animations",
            "animation_controllers",
            "models/entity",
            "textures/entity",
            "textures/items",
            "textures",
        ]:
            (pack_path / rel).mkdir(parents=True, exist_ok=True)

    def _entity_name_in_use(self, name: str) -> bool:
        pack_path = self._pack_path("BLF_CustomEntity")
        if pack_path is None:
            return False
        if (pack_path / "entity" / f"{name}.entity.json").is_file():
            return True
        if (pack_path / "models" / "entity" / f"{name}.geo.json").is_file():
            return True
        if (pack_path / "textures" / "entity" / f"{name}.png").is_file():
            return True
        if (pack_path / "textures" / "items" / f"{name}.icon.png").is_file():
            return True
        item_texture = pack_path / "textures" / "item_texture.json"
        data = self._load_json(item_texture)
        if isinstance(data, dict):
            texture_data = data.get("texture_data")
            if isinstance(texture_data, dict) and name in texture_data:
                return True
        return False

    def _load_json(self, path: Path):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def _write_json(self, path: Path, data) -> None:
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def _replace_in_json(self, obj, old: str, new: str):
        if isinstance(obj, dict):
            updated = {}
            for key, value in obj.items():
                new_key = key.replace(old, new) if isinstance(key, str) else key
                updated[new_key] = self._replace_in_json(value, old, new)
            return updated
        if isinstance(obj, list):
            return [self._replace_in_json(item, old, new) for item in obj]
        if isinstance(obj, str):
            return obj.replace(old, new)
        return obj

    def _copy_json_with_replacements(self, src: Path, dest: Path, name: str) -> None:
        data = self._load_json(src)
        if data is None:
            shutil.copy2(src, dest)
            return
        replaced = self._replace_in_json(data, "default_entity", name)
        self._write_json(dest, replaced)

    def _create_entity_json(
        self, template_path: Path, dest: Path, name: str, namespace: str
    ) -> None:
        data = self._load_json(template_path)
        if data is None:
            raise ValueError("기본 엔티티 템플릿을 읽을 수 없습니다.")
        replaced = self._replace_in_json(data, "default_entity", name)

        entity = replaced.get("minecraft:client_entity")
        if isinstance(entity, dict):
            desc = entity.get("description")
            if isinstance(desc, dict):
                desc["identifier"] = f"{namespace}:{name}"
                spawn = desc.get("spawn_egg")
                if not isinstance(spawn, dict):
                    spawn = {}
                    desc["spawn_egg"] = spawn
                spawn["texture"] = name

        self._write_json(dest, replaced)

    def _update_item_texture(self, pack_path: Path, name: str) -> None:
        item_path = pack_path / "textures" / "item_texture.json"
        data = self._load_json(item_path)
        if not isinstance(data, dict):
            data = {
                "resource_pack_name": "vanilla",
                "texture_name": "atlas.items",
                "texture_data": {},
            }

        texture_data = data.get("texture_data")
        if not isinstance(texture_data, dict):
            texture_data = {}
            data["texture_data"] = texture_data

        texture_data[name] = {"textures": f"textures/items/{name}.icon"}
        self._write_json(item_path, data)

    def _pack_path(self, name: str) -> Path | None:
        root_path = normalize_root(self.root_path_var.get())
        if not root_path.is_dir():
            return None
        path = root_path / name
        if path.is_dir():
            return path
        return None

    def _browse(self) -> None:
        path = filedialog.askdirectory()
        if path:
            self.root_path_var.set(path)

    def _scan_required_packs(self) -> None:
        root_path = normalize_root(self.root_path_var.get())
        if not root_path.is_dir():
            messagebox.showerror("경로 오류", "리소스팩 경로가 존재하지 않습니다.")
            self._set_ready_state(False)
            return

        missing = check_missing_packs(root_path)
        expected = expected_pack_names()

        if missing:
            missing_list = ", ".join(missing)
            self._log(f"누락된 리소스팩: {missing_list}")
            if len(missing) == len(expected):
                if messagebox.askyesno(
                    "리소스팩 없음",
                    "BLF_ 리소스팩이 하나도 없습니다.\n"
                    "메타데이터 기반으로 최소 리소스팩을 생성할까요?",
                ):
                    created = create_missing_packs(root_path, missing)
                    created_names = ", ".join([p.name for p in created])
                    self._log(f"생성 완료: {created_names}")
                    missing = check_missing_packs(root_path)
            else:
                messagebox.showwarning("리소스팩 누락", f"누락된 팩: {missing_list}")

        is_ready = not missing
        self._set_ready_state(is_ready)

        if is_ready:
            self._log("BLF_ 팩 11개 확인 완료.")
            for pack in scan_packs(root_path):
                self._log(pack.summary_line())
        else:
            self._log("모든 BLF_ 팩이 준비되어야 선택할 수 있습니다.")

    def _set_ready_state(self, ready: bool) -> None:
        if self.pack_list is not None:
            state = "normal" if ready else "disabled"
            self.pack_list.configure(state=state)
        if self.select_button is not None:
            self.select_button.configure(state=("normal" if ready else "disabled"))
        self.status_var.set("모든 팩이 준비되었습니다." if ready else "팩이 누락되었습니다.")

    def _populate_pack_list(self) -> None:
        if self.pack_list is None:
            return
        self.pack_list.delete(0, tk.END)
        for name, _desc in EXPECTED_PACKS:
            self.pack_list.insert(tk.END, name)

    def _select_pack(self) -> None:
        if self.pack_list is None:
            return
        selection = self.pack_list.curselection()
        if not selection:
            messagebox.showinfo("선택 필요", "리소스팩을 하나 선택하세요.")
            return
        name = self.pack_list.get(selection[0])
        self._open_pack(name)

    def _on_pack_double_click(self, _event: tk.Event) -> None:
        if self.pack_list is None:
            return
        selection = self.pack_list.curselection()
        if not selection:
            return
        name = self.pack_list.get(selection[0])
        self._open_pack(name)

    def _open_pack(self, name: str) -> None:
        if name != "BLF_CustomEntity":
            messagebox.showinfo("준비중", "현재는 CustomEntity만 지원합니다.")
            self._log(f"선택됨: {name}")
            return
        self._switch_view(self._build_entity_creator())

    def _log(self, message: str) -> None:
        if self.log_text is None:
            return
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _log_entity(self, message: str) -> None:
        if self.entity_log_text is None:
            return
        self.entity_log_text.configure(state="normal")
        self.entity_log_text.insert("end", message + "\n")
        self.entity_log_text.see("end")
        self.entity_log_text.configure(state="disabled")

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    app = MainWindow()
    app.run()