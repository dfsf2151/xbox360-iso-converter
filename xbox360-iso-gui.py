#!/usr/bin/env python3
"""Simple window for converting Xbox 360 ISOs to GOD or an extracted XEX folder."""
import os, re, shutil, subprocess, sys, threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

BIN = os.environ.get("X360_BIN") or os.path.dirname(os.path.realpath(__file__))
TOOLS = {"god": os.path.join(BIN, "iso2god"), "xex": os.path.join(BIN, "extract-xiso")}


def usb_root():
    user = os.environ.get("USER", "")
    for base in (f"/run/media/{user}", f"/media/{user}"):
        if os.path.isdir(base):
            for d in sorted(os.listdir(base)):
                if os.path.ismount(os.path.join(base, d)):
                    return os.path.join(base, d)
    return None


def default_dest(mode):
    usb = usb_root()
    if not usb:
        return os.path.expanduser("~/Xbox360")
    return os.path.join(usb, "Content", "0000000000000000") if mode == "god" else os.path.join(usb, "Games")


def ask_file(title, directory=False, initial=None):
    """zenity looks native on most desktops; fall back to Tk's dialog."""
    if shutil.which("zenity"):
        cmd = ["zenity", "--file-selection", f"--title={title}"]
        if directory:
            cmd.append("--directory")
        else:
            cmd.append("--file-filter=Xbox 360 ISO | *.iso *.ISO")
        if initial:
            cmd.append(f"--filename={initial.rstrip('/')}/")
        r = subprocess.run(cmd, capture_output=True, text=True)
        return r.stdout.strip() or None
    if directory:
        return filedialog.askdirectory(title=title, initialdir=initial) or None
    return filedialog.askopenfilename(title=title, filetypes=[("Xbox 360 ISO", "*.iso *.ISO")]) or None


class App(tk.Tk):
    def __init__(self, iso=None):
        super().__init__()
        self.title("Xbox 360 ISO Converter for Linux")
        self.resizable(False, False)
        self.proc = None
        self.dest_custom = False

        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Big.TButton", font=("TkDefaultFont", 11, "bold"), padding=8)

        f = ttk.Frame(self, padding=16)
        f.grid(sticky="nsew")
        f.columnconfigure(1, weight=1)

        ttk.Label(f, text="ISO file:").grid(row=0, column=0, sticky="w", pady=4)
        self.iso = tk.StringVar(value=iso or "")
        ttk.Entry(f, textvariable=self.iso, width=52).grid(row=0, column=1, sticky="ew", padx=6)
        ttk.Button(f, text="Browse…", command=self.pick_iso).grid(row=0, column=2)

        ttk.Label(f, text="Convert to:").grid(row=1, column=0, sticky="w", pady=4)
        self.mode = tk.StringVar(value="god")
        modes = ttk.Frame(f)
        modes.grid(row=1, column=1, columnspan=2, sticky="w", padx=6)
        ttk.Radiobutton(modes, text="GOD  (recommended, USB / Aurora)", value="god",
                        variable=self.mode, command=self.mode_changed).pack(side="left")
        ttk.Radiobutton(modes, text="XEX folder", value="xex",
                        variable=self.mode, command=self.mode_changed).pack(side="left", padx=16)

        ttk.Label(f, text="Save to:").grid(row=2, column=0, sticky="w", pady=4)
        self.dest = tk.StringVar(value=default_dest("god"))
        ttk.Entry(f, textvariable=self.dest, width=52).grid(row=2, column=1, sticky="ew", padx=6)
        ttk.Button(f, text="Browse…", command=self.pick_dest).grid(row=2, column=2)

        self.bar = ttk.Progressbar(f, maximum=100)
        self.bar.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(14, 4))
        self.status = tk.StringVar(value="Choose an ISO file.")
        ttk.Label(f, textvariable=self.status).grid(row=4, column=0, columnspan=3, sticky="w")

        self.go = ttk.Button(f, text="Convert", style="Big.TButton", command=self.start)
        self.go.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(12, 0))

        if iso:
            self.status.set("Ready.")

    def pick_iso(self):
        p = ask_file("Choose ISO", initial=os.path.expanduser("~/Downloads"))
        if p:
            self.iso.set(p)
            self.status.set("Ready.")

    def pick_dest(self):
        p = ask_file("Save to", directory=True, initial=self.dest.get())
        if p:
            self.dest.set(p)
            self.dest_custom = True

    def mode_changed(self):
        if not self.dest_custom:
            self.dest.set(default_dest(self.mode.get()))

    def start(self):
        if self.proc:  # running -> cancel
            self.proc.terminate()
            return
        iso, dest, mode = self.iso.get().strip(), self.dest.get().strip(), self.mode.get()
        if not os.path.isfile(iso):
            messagebox.showerror("Error", "Choose a valid ISO file.")
            return
        os.makedirs(dest, exist_ok=True)
        name = os.path.splitext(os.path.basename(iso))[0]
        if mode == "god":
            cmd = [TOOLS["god"], iso, dest]
            self.out = dest
        else:
            self.out = os.path.join(dest, name)
            if os.path.exists(self.out):
                messagebox.showerror("Error", f"Already exists:\n{self.out}")
                return
            cmd = [TOOLS["xex"], "-x", "-d", self.out, iso]
            self.bar.configure(mode="indeterminate")
            self.bar.start(12)
        self.go.configure(text="Cancel")
        self.status.set(f"Converting {name} …")
        self.log = []
        threading.Thread(target=self.work, args=(cmd,), daemon=True).start()

    def work(self, cmd):
        self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in self.proc.stdout:
            self.log.append(line.rstrip())
            m = re.search(r"writing part files:\s*(\d+)/(\d+)", line)
            if m:
                done, total = int(m[1]), int(m[2])
                self.after(0, self.progress, done * 100 / total, f"Writing part {done}/{total}")
        rc = self.proc.wait()
        subprocess.run(["sync"])
        self.after(0, self.finished, rc)

    def progress(self, pct, text):
        self.bar.configure(mode="determinate", value=pct)
        self.status.set(text)

    def finished(self, rc):
        self.proc = None
        self.bar.stop()
        self.bar.configure(mode="determinate", value=100 if rc == 0 else 0)
        self.go.configure(text="Convert")
        if rc == 0:
            self.status.set("Done ✓")
            messagebox.showinfo("Done", f"Game saved to:\n{self.out}")
        elif rc < 0:
            self.status.set("Cancelled.")
        else:
            self.status.set("Failed.")
            messagebox.showerror("Failed", "\n".join(self.log[-6:]) or "Unknown error")


if __name__ == "__main__":
    App(sys.argv[1] if len(sys.argv) > 1 else None).mainloop()
