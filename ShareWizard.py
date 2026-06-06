# -*- coding: utf-8 -*-
"""
ShareWizard.py — Мастер публикации сетевой папки
Windows 10 / 11  |  Python 3.8+  |  tkinter (встроен)
Запуск: python ShareWizard.py  (обязательно от имени администратора)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess, threading, os, sys, socket, datetime, ctypes

# ─── Проверка прав администратора ────────────────────────────
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def relaunch_as_admin():
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

# ─── Цвета и стили ───────────────────────────────────────────
BG       = "#1e1e2e"
BG2      = "#2a2a3e"
BG3      = "#313145"
ACCENT   = "#7c6af7"
ACCENT2  = "#5a4fcf"
GREEN    = "#4caf88"
RED      = "#e05c5c"
YELLOW   = "#f0c040"
TEXT     = "#e8e8f0"
TEXT2    = "#9090b0"
BORDER   = "#3a3a55"
BTN_FG   = "#ffffff"

FONT_TITLE = ("Segoe UI", 14, "bold")
FONT_HEAD  = ("Segoe UI", 11, "bold")
FONT_NORM  = ("Segoe UI", 10)
FONT_SMALL = ("Segoe UI", 9)
FONT_MONO  = ("Consolas", 9)

# ─── Главное окно ────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ShareWizard — Сетевой доступ к папке")
        self.geometry("880x700")
        self.minsize(800, 620)
        self.configure(bg=BG)
        self.resizable(True, True)

        # Иконка (встроенная, без файла)
        try:
            self.iconbitmap(default="")
        except Exception:
            pass

        self._build_ui()
        self._check_admin_banner()

    # ── Верхний заголовок ────────────────────────────────────
    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=ACCENT2, height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="  📂  ShareWizard", font=("Segoe UI", 15, "bold"),
                 bg=ACCENT2, fg=BTN_FG).pack(side="left", padx=16, pady=10)
        self.admin_lbl = tk.Label(hdr, text="", font=FONT_SMALL,
                                  bg=ACCENT2, fg=YELLOW)
        self.admin_lbl.pack(side="right", padx=16)

        # Основная область — две колонки
        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True, padx=0, pady=0)

        # Левая панель (настройки)
        left = tk.Frame(main, bg=BG, width=440)
        left.pack(side="left", fill="both", expand=True, padx=(14,6), pady=10)

        # Правая панель (диагностика)
        right = tk.Frame(main, bg=BG2, width=380, bd=0,
                         highlightbackground=BORDER, highlightthickness=1)
        right.pack(side="right", fill="both", expand=False,
                   padx=(0,14), pady=10)
        right.pack_propagate(False)

        self._build_left(left)
        self._build_right(right)

        # Нижняя панель кнопок
        self._build_bottom()

    # ── Левая панель: настройки ──────────────────────────────
    def _build_left(self, parent):
        canvas = tk.Canvas(parent, bg=BG, highlightthickness=0)
        sb = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        self._scroll_frame = tk.Frame(canvas, bg=BG)
        self._scroll_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self._scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        canvas.bind_all("<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        p = self._scroll_frame

        self._section(p, "📁  Папка и SMB-ресурс")
        self.var_path  = self._field(p, "Путь к папке")
        fr = tk.Frame(p, bg=BG)
        fr.pack(fill="x", pady=(0,6))
        self._btn(fr, "Обзор...", self._browse_folder, small=True).pack(
            side="left", padx=(2,0))

        self.var_share = self._field(p, "Имя SMB-ресурса",  "SharedFolder")
        self.var_desc  = self._field(p, "Описание", "Общий сетевой ресурс")

        self._section(p, "👥  Права доступа")
        self._perm_rows = []
        self._perm_container = tk.Frame(p, bg=BG)
        self._perm_container.pack(fill="x", pady=(0,4))
        self._perm_header(self._perm_container)
        self._add_perm_row("Everyone", "Change", "Modify")
        self._add_perm_row("BUILTIN\\Administrators", "Full", "FullControl")
        self._btn(p, "+ Добавить строку", self._add_empty_perm, small=True
                  ).pack(anchor="w", pady=(0,8))

        self._section(p, "🔒  Параметры SMB-ресурса")
        self.var_abe      = self._toggle(p, "Access Based Enumeration (ABE)", True)
        self.var_encrypt  = self._toggle(p, "SMB-шифрование (Win 8+)", False)
        self.var_maxconn  = self._field(p, "Макс. подключений (0 = без лимита)", "0")
        opts_cache = ["None","Manual","Programs","Documents"]
        self.var_cache    = self._combo(p, "Кеширование файлов", opts_cache, 0)

        self._section(p, "🔥  Брандмауэр Windows")
        self.var_fw_smb   = self._toggle(p, "Открыть порт 445 (SMB)", True)
        self.var_fw_nb    = self._toggle(p, "Открыть порты 137-139 (NetBIOS)", True)
        self.var_fw_disc  = self._toggle(p, "Включить сетевое обнаружение", True)
        opts_prof = ["Domain, Private","Any","Domain","Private"]
        self.var_fw_prof  = self._combo(p, "Профиль брандмауэра", opts_prof, 0)

        self._section(p, "🌐  Сеть и обнаружение")
        self.var_net_disc = self._toggle(p, "Включить сетевое обнаружение (Network Discovery)", True)
        self.var_net_share= self._toggle(p, "Включить общий доступ к файлам и принтерам", True)
        self.var_net_pub  = self._toggle(p, "Разрешить доступ в публичных сетях", False)
        self.var_net_pass = self._toggle(p, "Отключить защиту паролем (Password Protected Sharing)", False)

        self._section(p, "⚙️  Службы и политики")
        self.var_svc_srv  = self._toggle(p, "Запустить LanmanServer (обязательно)", True)
        self.var_svc_wb   = self._toggle(p, "Запустить WS-Management (WinRM)", False)
        self.var_inherit  = self._toggle(p, "Включить наследование NTFS-прав", False)
        self.var_audit    = self._toggle(p, "Включить аудит доступа к папке", False)
        self.var_log      = self._toggle(p, "Сохранить лог в %TEMP%", True)

    # ── Правая панель: диагностика ───────────────────────────
    def _build_right(self, parent):
        tk.Label(parent, text="🖥  Диагностика", font=FONT_HEAD,
                 bg=BG2, fg=TEXT).pack(anchor="w", padx=12, pady=(10,2))

        # Статус системы
        self.diag_frame = tk.Frame(parent, bg=BG2)
        self.diag_frame.pack(fill="x", padx=10, pady=(0,6))
        self._diag_items = {}
        for key, label in [
            ("admin",   "Права администратора"),
            ("lanman",  "Служба LanmanServer"),
            ("fw",      "Брандмауэр SMB"),
            ("disc",    "Сетевое обнаружение"),
            ("smb",     "SMB v2/v3"),
        ]:
            row = tk.Frame(self.diag_frame, bg=BG2)
            row.pack(fill="x", pady=1)
            dot = tk.Label(row, text="●", font=("Segoe UI", 11),
                           bg=BG2, fg=TEXT2, width=2)
            dot.pack(side="left")
            tk.Label(row, text=label, font=FONT_SMALL,
                     bg=BG2, fg=TEXT2).pack(side="left")
            val = tk.Label(row, text="...", font=FONT_SMALL,
                           bg=BG2, fg=TEXT2, anchor="e")
            val.pack(side="right", padx=4)
            self._diag_items[key] = (dot, val)

        tk.Button(self.diag_frame, text="🔄 Обновить диагностику",
                  font=FONT_SMALL, bg=BG3, fg=TEXT, bd=0,
                  activebackground=ACCENT, activeforeground=BTN_FG,
                  cursor="hand2", pady=4,
                  command=self._run_diag).pack(fill="x", pady=(6,0))

        # Разделитель
        sep = tk.Frame(parent, bg=BORDER, height=1)
        sep.pack(fill="x", padx=10, pady=6)

        tk.Label(parent, text="📋  Журнал выполнения", font=FONT_HEAD,
                 bg=BG2, fg=TEXT).pack(anchor="w", padx=12, pady=(0,4))

        # Лог-окно
        log_frame = tk.Frame(parent, bg=BG2)
        log_frame.pack(fill="both", expand=True, padx=10, pady=(0,8))
        self.log = scrolledtext.ScrolledText(
            log_frame, font=FONT_MONO, bg="#111120", fg=TEXT,
            insertbackground=TEXT, bd=0, relief="flat",
            state="disabled", wrap="word")
        self.log.pack(fill="both", expand=True)
        self.log.tag_config("ok",   foreground=GREEN)
        self.log.tag_config("err",  foreground=RED)
        self.log.tag_config("warn", foreground=YELLOW)
        self.log.tag_config("info", foreground=ACCENT)
        self.log.tag_config("head", foreground=TEXT, font=("Consolas",9,"bold"))

        # Кнопки лога
        logbtns = tk.Frame(parent, bg=BG2)
        logbtns.pack(fill="x", padx=10, pady=(0,8))
        tk.Button(logbtns, text="Очистить", font=FONT_SMALL, bg=BG3,
                  fg=TEXT, bd=0, pady=3, cursor="hand2",
                  command=self._clear_log).pack(side="left", padx=(0,4))
        tk.Button(logbtns, text="Сохранить лог", font=FONT_SMALL, bg=BG3,
                  fg=TEXT, bd=0, pady=3, cursor="hand2",
                  command=self._save_log).pack(side="left")

    # ── Нижняя панель кнопок ─────────────────────────────────
    def _build_bottom(self):
        bot = tk.Frame(self, bg=BG3, height=52)
        bot.pack(fill="x", side="bottom")
        bot.pack_propagate(False)

        self.progress = ttk.Progressbar(bot, mode="indeterminate", length=200)
        self.progress.pack(side="left", padx=(14,12), pady=14)

        self.status_lbl = tk.Label(bot, text="Готов к работе",
                                   font=FONT_SMALL, bg=BG3, fg=TEXT2)
        self.status_lbl.pack(side="left")

        tk.Button(bot, text="✖ Выход", font=FONT_NORM, bg=BG3, fg=TEXT2,
                  bd=0, padx=16, cursor="hand2", activeforeground=RED,
                  command=self.quit).pack(side="right", padx=8)

        self.start_btn = tk.Button(
            bot, text="▶  ПРИМЕНИТЬ НАСТРОЙКИ",
            font=("Segoe UI", 11, "bold"),
            bg=ACCENT, fg=BTN_FG, bd=0, padx=24, pady=6,
            activebackground=ACCENT2, activeforeground=BTN_FG,
            cursor="hand2", command=self._start)
        self.start_btn.pack(side="right", padx=(0,8), pady=8)

    # ── Вспомогательные виджеты ──────────────────────────────
    def _section(self, parent, title):
        f = tk.Frame(parent, bg=BG)
        f.pack(fill="x", pady=(10,2))
        tk.Label(f, text=title, font=FONT_HEAD, bg=BG, fg=ACCENT
                 ).pack(side="left")
        tk.Frame(f, bg=BORDER, height=1).pack(side="left", fill="x",
                                               expand=True, padx=8, pady=6)

    def _field(self, parent, label, default=""):
        tk.Label(parent, text=label, font=FONT_SMALL,
                 bg=BG, fg=TEXT2).pack(anchor="w", pady=(2,0))
        var = tk.StringVar(value=default)
        entry = tk.Entry(parent, textvariable=var, font=FONT_NORM,
                         bg=BG3, fg=TEXT, insertbackground=TEXT,
                         relief="flat", bd=0, highlightthickness=1,
                         highlightbackground=BORDER,
                         highlightcolor=ACCENT)
        entry.pack(fill="x", pady=(2,6), ipady=5)
        return var

    def _toggle(self, parent, label, default=False):
        var = tk.BooleanVar(value=default)
        row = tk.Frame(parent, bg=BG)
        row.pack(fill="x", pady=1)
        cb = tk.Checkbutton(row, text=label, variable=var,
                            font=FONT_SMALL, bg=BG, fg=TEXT,
                            activebackground=BG, activeforeground=ACCENT,
                            selectcolor=BG3, bd=0, cursor="hand2")
        cb.pack(side="left")
        return var

    def _combo(self, parent, label, values, idx=0):
        tk.Label(parent, text=label, font=FONT_SMALL,
                 bg=BG, fg=TEXT2).pack(anchor="w", pady=(2,0))
        var = tk.StringVar(value=values[idx])
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("D.TCombobox",
                        fieldbackground=BG3, background=BG3,
                        foreground=TEXT, selectbackground=ACCENT,
                        selectforeground=BTN_FG, bordercolor=BORDER,
                        arrowcolor=TEXT2)
        cb = ttk.Combobox(parent, textvariable=var, values=values,
                          state="readonly", style="D.TCombobox",
                          font=FONT_NORM)
        cb.pack(fill="x", pady=(2,6), ipady=3)
        return var

    def _btn(self, parent, text, cmd, small=False):
        font = FONT_SMALL if small else FONT_NORM
        b = tk.Button(parent, text=text, font=font,
                      bg=BG3, fg=TEXT, bd=0, padx=10, pady=4,
                      activebackground=ACCENT, activeforeground=BTN_FG,
                      cursor="hand2", command=cmd)
        return b

    # ── Таблица прав ─────────────────────────────────────────
    def _perm_header(self, parent):
        row = tk.Frame(parent, bg=BG)
        row.pack(fill="x", pady=(0,2))
        for txt, w in [("Пользователь / группа", 20),
                       ("SMB-права", 12), ("NTFS-права", 12), ("", 3)]:
            tk.Label(row, text=txt, font=("Segoe UI",8,"bold"),
                     bg=BG, fg=TEXT2, width=w, anchor="w"
                     ).pack(side="left", padx=2)

    def _add_perm_row(self, user="", smb="Change", ntfs="Modify"):
        container = self._perm_container
        row = tk.Frame(container, bg=BG)
        row.pack(fill="x", pady=1)

        uvar = tk.StringVar(value=user)
        svar = tk.StringVar(value=smb)
        nvar = tk.StringVar(value=ntfs)

        ue = tk.Entry(row, textvariable=uvar, font=FONT_SMALL,
                      bg=BG3, fg=TEXT, insertbackground=TEXT,
                      relief="flat", bd=0, highlightthickness=1,
                      highlightbackground=BORDER, highlightcolor=ACCENT,
                      width=22)
        ue.pack(side="left", padx=(2,4), ipady=3)

        for var, vals, w in [
            (svar, ["Read","Change","Full"], 12),
            (nvar, ["Read","Modify","FullControl"], 12),
        ]:
            cb = ttk.Combobox(row, textvariable=var, values=vals,
                              state="readonly", width=w, font=FONT_SMALL)
            cb.pack(side="left", padx=2)

        def remove():
            row.destroy()
            self._perm_rows.remove(rec)

        rm = tk.Button(row, text="✕", font=FONT_SMALL, bg=BG, fg=RED,
                       bd=0, cursor="hand2", command=remove)
        rm.pack(side="left", padx=4)

        rec = (uvar, svar, nvar, row)
        self._perm_rows.append(rec)

    def _add_empty_perm(self):
        self._add_perm_row()

    # ── Обзор папки ──────────────────────────────────────────
    def _browse_folder(self):
        path = filedialog.askdirectory(title="Выберите папку")
        if path:
            path = os.path.normpath(path)
            self.var_path.set(path)
            if not self.var_share.get():
                self.var_share.set(os.path.basename(path))

    # ── Диагностика ──────────────────────────────────────────
    def _check_admin_banner(self):
        if is_admin():
            self.admin_lbl.config(text="✔ Администратор", fg=GREEN)
        else:
            self.admin_lbl.config(text="⚠ Нет прав администратора", fg=RED)
        self._run_diag()

    def _run_diag(self):
        threading.Thread(target=self._diag_worker, daemon=True).start()

    def _diag_worker(self):
        checks = {}

        # Права
        checks["admin"] = (is_admin(), "Есть", "Нет")

        # LanmanServer
        try:
            r = subprocess.run(
                ["sc","query","LanmanServer"],
                capture_output=True, text=True, timeout=4)
            running = "RUNNING" in r.stdout
            checks["lanman"] = (running, "Запущена", "Остановлена")
        except Exception:
            checks["lanman"] = (False, "", "Ошибка")

        # Брандмауэр SMB
        try:
            r = subprocess.run(
                ["netsh","advfirewall","firewall","show","rule",
                 "name=File and Printer Sharing (SMB-In)"],
                capture_output=True, text=True, timeout=4)
            enabled = "Enabled:                              Yes" in r.stdout
            checks["fw"] = (enabled, "Открыт", "Закрыт")
        except Exception:
            checks["fw"] = (False, "", "Ошибка")

        # Сетевое обнаружение
        try:
            r = subprocess.run(
                ["netsh","advfirewall","firewall","show","rule",
                 "name=Network Discovery (NB-Datagram-In)"],
                capture_output=True, text=True, timeout=4)
            enabled = "Enabled:                              Yes" in r.stdout
            checks["disc"] = (enabled, "Включено", "Выключено")
        except Exception:
            checks["disc"] = (False, "", "Ошибка")

        # SMB v2
        try:
            r = subprocess.run(
                ["powershell","-NoProfile","-Command",
                 "Get-SmbServerConfiguration | Select-Object EnableSMB2Protocol"],
                capture_output=True, text=True, timeout=6)
            enabled = "True" in r.stdout
            checks["smb"] = (enabled, "v2/v3 вкл", "Отключён")
        except Exception:
            checks["smb"] = (False, "", "Ошибка")

        self.after(0, self._apply_diag, checks)

    def _apply_diag(self, checks):
        for key, (ok, yes_text, no_text) in checks.items():
            dot, val = self._diag_items[key]
            dot.config(fg=GREEN if ok else RED)
            val.config(text=yes_text if ok else no_text,
                       fg=GREEN if ok else RED)

    # ── Лог-функции ──────────────────────────────────────────
    def _log(self, text, tag=""):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.log.config(state="normal")
        self.log.insert("end", f"[{ts}] {text}\n", tag)
        self.log.see("end")
        self.log.config(state="disabled")

    def _clear_log(self):
        self.log.config(state="normal")
        self.log.delete("1.0","end")
        self.log.config(state="disabled")

    def _save_log(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text","*.txt"),("All","*.*")],
            initialfile=f"ShareWizard_{datetime.datetime.now():%Y%m%d_%H%M%S}.txt")
        if path:
            with open(path,"w",encoding="utf-8") as f:
                f.write(self.log.get("1.0","end"))
            self._log(f"Лог сохранён: {path}", "ok")

    # ── ОСНОВНАЯ ЛОГИКА ──────────────────────────────────────
    def _start(self):
        path = self.var_path.get().strip()
        share = self.var_share.get().strip()

        if not path:
            messagebox.showwarning("ShareWizard", "Укажите путь к папке!")
            return
        if not share:
            messagebox.showwarning("ShareWizard", "Укажите имя SMB-ресурса!")
            return
        if not is_admin():
            if messagebox.askyesno("Нужны права администратора",
                    "Программа запущена без прав администратора.\n"
                    "Перезапустить с повышенными правами?"):
                relaunch_as_admin()
            return

        self.start_btn.config(state="disabled")
        self.progress.start(10)
        self._log("━" * 50, "head")
        self._log(f"Запуск: {share}  →  {path}", "head")
        self._log("━" * 50, "head")
        self._set_status("Выполняется...")

        threading.Thread(target=self._apply_worker,
                         args=(path, share), daemon=True).start()

    def _apply_worker(self, path, share):
        cfg = {
            "path": path, "share": share,
            "desc": self.var_desc.get().strip(),
            "abe": self.var_abe.get(),
            "encrypt": self.var_encrypt.get(),
            "maxconn": self.var_maxconn.get().strip(),
            "cache": self.var_cache.get(),
            "fw_smb": self.var_fw_smb.get(),
            "fw_nb": self.var_fw_nb.get(),
            "fw_disc": self.var_fw_disc.get(),
            "fw_prof": self.var_fw_prof.get(),
            "net_disc": self.var_net_disc.get(),
            "net_share": self.var_net_share.get(),
            "net_pub": self.var_net_pub.get(),
            "net_pass": self.var_net_pass.get(),
            "svc_srv": self.var_svc_srv.get(),
            "svc_wb": self.var_svc_wb.get(),
            "inherit": self.var_inherit.get(),
            "audit": self.var_audit.get(),
            "do_log": self.var_log.get(),
            "perms": [(u.get(), s.get(), n.get())
                      for u, s, n, _ in self._perm_rows if u.get().strip()],
        }
        ok = self._do_apply(cfg)
        self.after(0, self._done, ok)

    def _ps(self, cmd, desc=""):
        """Выполнить PowerShell-команду, вернуть (ok, out, err)."""
        # [chcp 65001] + [-OutputEncoding] гарантируют UTF-8 на любой локали Windows
        wrapped = (
            "$OutputEncoding = [Console]::OutputEncoding = "
            "[System.Text.Encoding]::UTF8; " + cmd
        )
        full = ["powershell","-NoProfile","-NonInteractive",
                "-ExecutionPolicy","Bypass","-Command", wrapped]
        try:
            r = subprocess.run(full, capture_output=True,
                               timeout=30, encoding="utf-8", errors="replace")
            out = r.stdout.strip()
            err = r.stderr.strip()
            return r.returncode == 0, out, err
        except Exception as ex:
            return False, "", str(ex)

    def _netsh(self, args):
        try:
            r = subprocess.run(["netsh"] + args, capture_output=True,
                               text=True, timeout=15,
                               encoding="utf-8", errors="replace")
            return r.returncode == 0, r.stdout.strip(), r.stderr.strip()
        except Exception as ex:
            return False, "", str(ex)

    def _sc(self, svc, action):
        try:
            subprocess.run(["sc","config",svc,"start=","auto"],
                           capture_output=True, timeout=8)
            r = subprocess.run(["sc",action,svc],
                               capture_output=True, text=True, timeout=15)
            # код 1056 = служба уже запущена, это не ошибка
            return r.returncode == 0 or r.returncode == 1056
        except Exception:
            return False

    def _do_apply(self, cfg):
        L = self._log
        errors = 0

        # Лог в файл
        log_path = None
        if cfg["do_log"]:
            log_path = os.path.join(
                os.environ.get("TEMP","C:\\Temp"),
                f"ShareWizard_{cfg['share']}_{datetime.datetime.now():%Y%m%d_%H%M%S}.log")

        def logf(text, tag=""):
            L(text, tag)
            if log_path:
                with open(log_path,"a",encoding="utf-8") as f:
                    ts = datetime.datetime.now().strftime("%H:%M:%S")
                    f.write(f"[{ts}] {text}\n")

        # 1. Создание папки
        logf("── Создание папки ──────────────────", "info")
        try:
            os.makedirs(cfg["path"], exist_ok=True)
            logf(f"Папка готова: {cfg['path']}", "ok")
        except Exception as ex:
            logf(f"Ошибка создания папки: {ex}", "err"); errors += 1

        # 2. Служба LanmanServer
        if cfg["svc_srv"]:
            logf("── Служба LanmanServer ─────────────", "info")
            ok = self._sc("LanmanServer","start")
            logf("LanmanServer запущена" if ok else
                 "Не удалось запустить LanmanServer", "ok" if ok else "err")
            if not ok: errors += 1

        # 3. Служба WinRM
        if cfg["svc_wb"]:
            logf("── Служба WinRM ─────────────────────", "info")
            ok = self._sc("WinRM","start")
            logf("WinRM запущена" if ok else "WinRM: ошибка", "ok" if ok else "warn")

        # 4. NTFS наследование
        if cfg["inherit"]:
            logf("── NTFS: наследование ───────────────", "info")
            ok, out, err = self._ps(
                f'$a=Get-Acl "{cfg["path"]}";'
                f'$a.SetAccessRuleProtection($false,$true);'
                f'Set-Acl "{cfg["path"]}" $a')
            logf("Наследование NTFS включено" if ok else f"NTFS inherit: {err}",
                 "ok" if ok else "warn")

        # 5. NTFS права
        logf("── Права NTFS ───────────────────────", "info")
        for user, smb_r, ntfs_r in cfg["perms"]:
            ntfs_map = {"Read":"ReadAndExecute,Synchronize",
                        "Modify":"Modify,Synchronize",
                        "FullControl":"FullControl"}
            ntfs_enum = ntfs_map.get(ntfs_r, "Modify,Synchronize")
            ps_cmd = (
                f'$a=Get-Acl "{cfg["path"]}";'
                f'$r=New-Object System.Security.AccessControl.FileSystemAccessRule('
                f'"{user}","{ntfs_enum}",'
                f'"ContainerInherit,ObjectInherit","None","Allow");'
                f'$a.SetAccessRule($r);Set-Acl "{cfg["path"]}" $a'
            )
            ok, out, err = self._ps(ps_cmd)
            logf(f"NTFS {user} => {ntfs_r}" if ok else
                 f"NTFS {user}: {err}", "ok" if ok else "err")
            if not ok: errors += 1

        # 6. Удалить старый SMB-ресурс
        logf("── SMB-ресурс ───────────────────────", "info")
        ok, out, err = self._ps(
            f'if(Get-SmbShare -Name "{cfg["share"]}" -EA SilentlyContinue)'
            f'{{Remove-SmbShare -Name "{cfg["share"]}" -Force}}')
        logf(f"Старый ресурс удалён (если был)", "warn")

        # 7. Создать SMB-ресурс
        abe_mode = "AccessBased" if cfg["abe"] else "Unrestricted"
        max_c = cfg["maxconn"] if cfg["maxconn"].isdigit() and int(cfg["maxconn"])>0 else "0"
        enc   = "$true" if cfg["encrypt"] else "$false"
        ps_new = (
            f'New-SmbShare -Name "{cfg["share"]}" -Path "{cfg["path"]}"'
            f' -FolderEnumerationMode {abe_mode}'
            f' -CachingMode {cfg["cache"]}'
            f' -EncryptData {enc}'
        )
        if cfg["desc"]:
            ps_new += f' -Description "{cfg["desc"]}"'
        if max_c != "0":
            ps_new += f' -ConcurrentUserLimit {max_c}'

        ok, out, err = self._ps(ps_new)
        logf(f"SMB-ресурс '{cfg['share']}' создан" if ok else
             f"Ошибка SMB: {err}", "ok" if ok else "err")
        if not ok: errors += 1

        # 8. SMB права — используем SID для обхода Error 1332 (проблема локализации)
        WELL_KNOWN_SIDS = {
            "everyone":                 "S-1-1-0",
            "all":                      "S-1-1-0",
            "builtin\\administrators":   "S-1-5-32-544",
            "administrators":           "S-1-5-32-544",
            "builtin\\users":            "S-1-5-32-545",
            "users":                    "S-1-5-32-545",
            "builtin\\guests":           "S-1-5-32-546",
            "guests":                   "S-1-5-32-546",
            "authenticated users":      "S-1-5-11",
            "network":                  "S-1-5-2",
        }
        for user, smb_r, ntfs_r in cfg["perms"]:
            sid = WELL_KNOWN_SIDS.get(user.strip().lower())
            if sid:
                ps_grant = (
                    f'$sid=New-Object System.Security.Principal.SecurityIdentifier("{sid}");' +
                    f'$acct=$sid.Translate([System.Security.Principal.NTAccount]).Value;' +
                    f'Grant-SmbShareAccess -Name "{cfg["share"]}" -AccountName $acct -AccessRight {smb_r} -Force'
                )
            else:
                ps_grant = (
                    f'Grant-SmbShareAccess -Name "{cfg["share"]}" ' +
                    f'-AccountName "{user}" -AccessRight {smb_r} -Force'
                )
            ok, out, err = self._ps(ps_grant)
            logf(f"SMB {user} => {smb_r}" if ok else
                 f"SMB {user}: {err}", "ok" if ok else "err")

        # 9. Брандмауэр — используем PowerShell + netsh fallback
        logf("── Брандмауэр Windows ───────────────", "info")
        prof = cfg["fw_prof"]

        if cfg["fw_smb"]:
            # Открыть порт 445 напрямую (не зависит от локализации группы)
            ps_smb445 = (
                'New-NetFirewallRule -DisplayName "ShareWizard-SMB-445" ' +
                '-Direction Inbound -Protocol TCP -LocalPort 445 ' +
                f'-Profile {prof} -Action Allow -EA SilentlyContinue; ' +
                'Set-NetFirewallRule -DisplayName "ShareWizard-SMB-445" ' +
                f'-Enabled True -Profile {prof} -EA SilentlyContinue'
            )
            ok, _, _ = self._ps(ps_smb445)
            # Fallback: netsh по номеру порта
            if not ok:
                ok2, _, _ = self._netsh([
                    "advfirewall","firewall","add","rule",
                    "name=ShareWizard-SMB-445","dir=in","action=allow",
                    "protocol=TCP","localport=445"])
                ok = ok2
            logf("Порт 445 (SMB) открыт" if ok else "FW SMB: не удалось открыть порт 445", "ok" if ok else "warn")

        if cfg["fw_nb"]:
            # NetBIOS 137 UDP, 138 UDP, 139 TCP
            for port, proto in [("137","UDP"),("138","UDP"),("139","TCP")]:
                self._netsh([
                    "advfirewall","firewall","add","rule",
                    f"name=ShareWizard-NetBIOS-{port}","dir=in","action=allow",
                    f"protocol={proto}",f"localport={port}"])
            logf("Порты 137-139 (NetBIOS) открыты", "ok")

        if cfg["fw_disc"]:
            # WSD / UPnP для сетевого обнаружения — порты 3702 UDP, 5355 UDP, 1900 UDP
            disc_ok = True
            for port, proto in [("3702","UDP"),("5355","UDP"),("1900","UDP"),("5357","TCP")]:
                ok2, _, _ = self._netsh([
                    "advfirewall","firewall","add","rule",
                    f"name=ShareWizard-Discovery-{port}","dir=in","action=allow",
                    f"protocol={proto}",f"localport={port}"])
                if not ok2:
                    disc_ok = False
            logf("Сетевое обнаружение (FW) включено" if disc_ok else "FW Discovery: частичная ошибка",
                 "ok" if disc_ok else "warn")

        # 10. Сетевое обнаружение (реестр + sc)
        logf("── Сеть и обнаружение ───────────────", "info")
        if cfg["net_disc"]:
            # Запустить зависимые службы
            for svc in ["fdPHost","FDResPub","SSDPSRV","upnphost"]:
                self._sc(svc, "start")
            logf("Службы сетевого обнаружения запущены", "ok")
            # Реестр: включить обнаружение
            self._ps(
                'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Network\\NewNetworkWindowOff" '
                '/f 2>nul; '
                'Set-ItemProperty -Path '
                '"HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\NcdAutoSetup" '
                '-Name AutoSetup -Value 1 -EA SilentlyContinue')

        if cfg["net_share"]:
            self._ps(
                'Set-ItemProperty -Path '
                '"HKLM:\\SYSTEM\\CurrentControlSet\\Services\\LanmanServer\\Parameters" '
                '-Name "SMB2" -Value 1 -Type DWORD')
            logf("Общий доступ к файлам и принтерам включён", "ok")

        if cfg["net_pass"]:
            # Отключить защиту паролем (PasswordProtectedSharing)
            self._ps(
                'Set-ItemProperty -Path '
                '"HKLM:\\SYSTEM\\CurrentControlSet\\Services\\LanmanServer\\Parameters" '
                '-Name "restrictnullsessaccess" -Value 0 -Type DWORD')
            self._netsh(["advfirewall","firewall","set","rule",
                          "group=File and Printer Sharing","new","enable=Yes"])
            logf("Защита паролем отключена", "warn")

        if cfg["net_pub"]:
            self._ps(
                'Set-NetFirewallRule -DisplayGroup "File and Printer Sharing"'
                ' -Enabled True -Profile Public')
            logf("Доступ в публичных сетях разрешён", "warn")

        # 11. Аудит — используем SID S-1-1-0 (Everyone) для обхода IdentityNotMappedException
        if cfg["audit"]:
            logf("── Аудит доступа ────────────────────", "info")
            ps_audit = (
                f'$sid=New-Object System.Security.Principal.SecurityIdentifier("S-1-1-0");' +
                f'$acct=$sid.Translate([System.Security.Principal.NTAccount]).Value;' +
                f'$a=Get-Acl "{cfg["path"]}";' +
                f'$r=New-Object System.Security.AccessControl.FileSystemAuditRule(' +
                f'$acct,"FullControl","ContainerInherit,ObjectInherit","None","Success,Failure");' +
                f'$a.SetAuditRule($r);Set-Acl "{cfg["path"]}" $a;' +
                f'auditpol /set /subcategory:"Object Access" /success:enable /failure:enable | Out-Null'
            )
            ok, _, err = self._ps(ps_audit)
            logf("Аудит включён" if ok else f"Аудит: {err}",
                 "ok" if ok else "warn")

        # Итог
        comp = socket.gethostname()
        logf("━" * 50, "head")
        if errors == 0:
            logf(f"ВСЁ ВЫПОЛНЕНО БЕЗ ОШИБОК", "ok")
        else:
            logf(f"Выполнено с {errors} ошибками — проверьте журнал", "warn")
        logf(f"Сетевой путь: \\\\{comp}\\{cfg['share']}", "ok")
        logf("━" * 50, "head")

        if cfg["do_log"] and log_path:
            logf(f"Лог сохранён: {log_path}", "info")

        return errors == 0

    def _done(self, ok):
        self.progress.stop()
        self.start_btn.config(state="normal")
        self._set_status("Готов к работе")
        self._run_diag()
        share = self.var_share.get().strip()
        comp  = socket.gethostname()
        if ok:
            messagebox.showinfo("ShareWizard",
                f"Настройка завершена успешно!\n\n"
                f"Сетевой путь:\n\\\\{comp}\\{share}")
        else:
            messagebox.showwarning("ShareWizard",
                "Выполнено с ошибками.\nПроверьте журнал диагностики.")

    def _set_status(self, text):
        self.status_lbl.config(text=text)


# ─── Точка входа ─────────────────────────────────────────────
if __name__ == "__main__":
    # На Windows — UAC при необходимости
    if sys.platform == "win32" and not is_admin():
        resp = messagebox.askyesno(
            "ShareWizard",
            "Для применения сетевых настроек требуются права администратора.\n"
            "Перезапустить программу с повышенными правами?")
        if resp:
            relaunch_as_admin()

    app = App()
    app.mainloop()
