from __future__ import annotations

import argparse
import os
import queue
import subprocess
import sys
import threading
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from scan2doc_core import JobConfig, default_output_dir, prepare_offline_models, run_job

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:
    DND_FILES = None
    TkinterDnD = None


class Scan2DocApp:
    def __init__(self, root: tk.Tk, initial_pdf: str | None = None):
        self.root = root
        self.root.title("Scan2Doc - private PDF OCR")
        self.root.geometry("780x650")
        self.root.minsize(700, 580)
        self.events: queue.Queue[tuple] = queue.Queue()
        self.cancel = threading.Event()
        self.worker: threading.Thread | None = None

        self.pdf_var = tk.StringVar(value=initial_pdf or "")
        self.output_var = tk.StringVar()
        self.language_var = tk.StringVar(value="en")
        self.device_var = tk.StringVar(value="cpu")
        self.profile_var = tk.StringVar(value="quality")
        self.markdown_var = tk.BooleanVar(value=True)
        self.docx_var = tk.BooleanVar(value=True)
        self.offline_var = tk.BooleanVar(value=False)
        self.orientation_var = tk.BooleanVar(value=True)
        self.textline_var = tk.BooleanVar(value=True)
        self.unwarp_var = tk.BooleanVar(value=False)
        self.tables_var = tk.BooleanVar(value=True)
        self.formulas_var = tk.BooleanVar(value=False)
        self.charts_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="Ready")

        self._build()
        if initial_pdf:
            self._select_pdf(Path(initial_pdf))
        self.root.after(100, self._poll_events)

    def _build(self) -> None:
        outer = ttk.Frame(self.root, padding=18)
        outer.pack(fill="both", expand=True)

        ttk.Label(outer, text="Scan2Doc", font=("Segoe UI", 20, "bold")).pack(anchor="w")
        ttk.Label(
            outer,
            text="Local OCR for large scanned PDFs - Markdown and editable Word output",
        ).pack(anchor="w", pady=(0, 14))

        self.drop = ttk.Label(
            outer,
            text="Drop a PDF here\n(or click Choose PDF)",
            anchor="center",
            relief="groove",
            padding=22,
        )
        self.drop.pack(fill="x")
        if DND_FILES and hasattr(self.drop, "drop_target_register"):
            self.drop.drop_target_register(DND_FILES)
            self.drop.dnd_bind("<<Drop>>", self._on_drop)
        else:
            self.drop.configure(text="Choose a PDF below\n(you can also drag a PDF onto Start Scan2Doc.bat)")

        files = ttk.Frame(outer)
        files.pack(fill="x", pady=10)
        ttk.Label(files, text="PDF").grid(row=0, column=0, sticky="w", padx=(0, 8))
        ttk.Entry(files, textvariable=self.pdf_var).grid(row=0, column=1, sticky="ew")
        ttk.Button(files, text="Choose PDF", command=self._browse_pdf).grid(row=0, column=2, padx=(8, 0))
        ttk.Label(files, text="Output").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
        ttk.Entry(files, textvariable=self.output_var).grid(row=1, column=1, sticky="ew", pady=(8, 0))
        ttk.Button(files, text="Choose folder", command=self._browse_output).grid(row=1, column=2, padx=(8, 0), pady=(8, 0))
        files.columnconfigure(1, weight=1)

        settings = ttk.LabelFrame(outer, text="Recognition settings", padding=10)
        settings.pack(fill="x")
        ttk.Label(settings, text="Language code").grid(row=0, column=0, sticky="w")
        ttk.Combobox(
            settings,
            textvariable=self.language_var,
            values=("en", "ch", "fr", "de", "es", "it", "pt", "ar", "ru", "ja", "ko"),
            width=12,
        ).grid(row=0, column=1, sticky="w", padx=(8, 22))
        ttk.Label(settings, text="Device").grid(row=0, column=2, sticky="w")
        ttk.Combobox(
            settings,
            textvariable=self.device_var,
            values=("cpu", "gpu:0"),
            state="readonly",
            width=10,
        ).grid(row=0, column=3, sticky="w", padx=8)
        ttk.Label(settings, text="Profile").grid(row=0, column=4, sticky="w", padx=(18, 0))
        ttk.Combobox(
            settings,
            textvariable=self.profile_var,
            values=("quality", "fast_cpu"),
            state="readonly",
            width=12,
        ).grid(row=0, column=5, sticky="w", padx=8)
        ttk.Checkbutton(settings, text="Markdown (.md)", variable=self.markdown_var).grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Checkbutton(settings, text="Word (.docx)", variable=self.docx_var).grid(row=1, column=1, sticky="w", pady=(8, 0))
        ttk.Checkbutton(settings, text="Offline (models cached)", variable=self.offline_var).grid(row=1, column=2, columnspan=2, sticky="w", pady=(8, 0))
        ttk.Checkbutton(settings, text="Correct page rotation", variable=self.orientation_var).grid(row=2, column=0, sticky="w", pady=(8, 0))
        ttk.Checkbutton(settings, text="Correct rotated text", variable=self.textline_var).grid(row=2, column=1, sticky="w", pady=(8, 0))
        ttk.Checkbutton(settings, text="Unwarp curved pages", variable=self.unwarp_var).grid(row=2, column=2, columnspan=2, sticky="w", pady=(8, 0))
        ttk.Checkbutton(settings, text="Recognize tables", variable=self.tables_var).grid(row=3, column=0, sticky="w", pady=(8, 0))
        ttk.Checkbutton(settings, text="Recognize formulas (slower)", variable=self.formulas_var).grid(row=3, column=1, sticky="w", pady=(8, 0))
        ttk.Checkbutton(settings, text="Recognize charts (slower)", variable=self.charts_var).grid(row=3, column=2, columnspan=2, sticky="w", pady=(8, 0))

        actions = ttk.Frame(outer)
        actions.pack(fill="x", pady=12)
        self.start_button = ttk.Button(actions, text="Start / Resume", command=self._start)
        self.start_button.pack(side="left")
        self.stop_button = ttk.Button(actions, text="Stop after current page", command=self._stop, state="disabled")
        self.stop_button.pack(side="left", padx=8)
        ttk.Button(actions, text="Prepare offline models", command=self._prepare_models).pack(side="left")
        ttk.Button(actions, text="Open output folder", command=self._open_output).pack(side="right")

        self.progress = ttk.Progressbar(outer, mode="determinate")
        self.progress.pack(fill="x")
        ttk.Label(outer, textvariable=self.status_var).pack(anchor="w", pady=(5, 5))
        self.log = tk.Text(outer, height=12, wrap="word", state="disabled")
        self.log.pack(fill="both", expand=True)

    def _on_drop(self, event) -> None:
        paths = self.root.tk.splitlist(event.data)
        if paths:
            self._select_pdf(Path(paths[0]))

    def _select_pdf(self, path: Path) -> None:
        self.pdf_var.set(str(path))
        self.output_var.set(str(default_output_dir(path)))
        self.drop.configure(text=f"Selected:\n{path.name}")

    def _browse_pdf(self) -> None:
        value = filedialog.askopenfilename(filetypes=[("PDF documents", "*.pdf")])
        if value:
            self._select_pdf(Path(value))

    def _browse_output(self) -> None:
        value = filedialog.askdirectory()
        if value:
            self.output_var.set(value)

    def _config(self) -> JobConfig:
        return JobConfig(
            input_pdf=Path(self.pdf_var.get().strip()),
            output_dir=Path(self.output_var.get().strip()),
            language=self.language_var.get(),
            device=self.device_var.get(),
            profile=self.profile_var.get(),
            make_markdown=self.markdown_var.get(),
            make_docx=self.docx_var.get(),
            offline=self.offline_var.get(),
            retries=1,
            orientation=self.orientation_var.get(),
            textline_orientation=self.textline_var.get(),
            unwarp=self.unwarp_var.get(),
            tables=self.tables_var.get(),
            formulas=self.formulas_var.get(),
            charts=self.charts_var.get(),
        )

    def _append(self, text: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", text.rstrip() + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _set_busy(self, busy: bool) -> None:
        self.start_button.configure(state="disabled" if busy else "normal")
        self.stop_button.configure(state="normal" if busy else "disabled")

    def _start(self) -> None:
        if self.worker and self.worker.is_alive():
            return
        try:
            config = self._config()
            if not str(config.input_pdf):
                raise ValueError("Choose a PDF first.")
            if not str(config.output_dir):
                raise ValueError("Choose an output folder.")
        except Exception as exc:
            messagebox.showerror("Scan2Doc", str(exc))
            return
        self.cancel.clear()
        self._set_busy(True)
        self.progress["value"] = 0
        self._append(f"Starting: {config.input_pdf}")
        self.worker = threading.Thread(target=self._run_worker, args=(config,), daemon=True)
        self.worker.start()

    def _run_worker(self, config: JobConfig) -> None:
        try:
            summary = run_job(
                config,
                progress=lambda message, done, total: self.events.put(("progress", message, done, total)),
                cancel_event=self.cancel,
            )
            self.events.put(("done", summary))
        except Exception as exc:
            self.events.put(("error", f"{type(exc).__name__}: {exc}"))

    def _prepare_models(self) -> None:
        if self.worker and self.worker.is_alive():
            return
        try:
            config = self._config()
        except Exception as exc:
            messagebox.showerror("Scan2Doc", str(exc))
            return
        self._set_busy(True)
        self._append("Downloading and initializing the selected models. This is a one-time online step...")
        self.worker = threading.Thread(target=self._prepare_worker, args=(config,), daemon=True)
        self.worker.start()

    def _prepare_worker(self, config: JobConfig) -> None:
        try:
            prepare_offline_models(config)
            self.events.put(("prepared",))
        except Exception as exc:
            self.events.put(("error", f"{type(exc).__name__}: {exc}"))

    def _stop(self) -> None:
        self.cancel.set()
        self.status_var.set("Stop requested; finishing the current page safely...")

    def _open_output(self) -> None:
        path = Path(self.output_var.get())
        if path.is_dir():
            os.startfile(str(path))
        else:
            messagebox.showinfo("Scan2Doc", "The output folder does not exist yet.")

    def _poll_events(self) -> None:
        try:
            while True:
                event = self.events.get_nowait()
                if event[0] == "progress":
                    _, message, done, total = event
                    self.status_var.set(message)
                    self._append(message)
                    self.progress["maximum"] = max(total, 1)
                    self.progress["value"] = done
                elif event[0] == "done":
                    summary = event[1]
                    self._set_busy(False)
                    if summary.cancelled:
                        message = "Paused safely. Click Start / Resume when ready."
                    else:
                        message = f"Finished {summary.completed_pages}/{summary.total_pages} pages."
                        if summary.failed_pages:
                            message += f" Failed pages: {summary.failed_pages}. See scan2doc.log."
                    self.status_var.set(message)
                    self._append(message)
                    messagebox.showinfo("Scan2Doc", message)
                elif event[0] == "prepared":
                    self._set_busy(False)
                    self.status_var.set("Models are cached. Offline mode is ready.")
                    self._append("Models are cached. You can now select Offline mode.")
                elif event[0] == "error":
                    self._set_busy(False)
                    self.status_var.set("Stopped with an error")
                    self._append(event[1])
                    messagebox.showerror("Scan2Doc", event[1])
        except queue.Empty:
            pass
        self.root.after(100, self._poll_events)


def run_cli(args: argparse.Namespace) -> int:
    input_pdf = Path(args.pdf)
    output = Path(args.output) if args.output else default_output_dir(input_pdf)
    config = JobConfig(
        input_pdf=input_pdf,
        output_dir=output,
        language=args.language,
        device=args.device,
        profile=args.profile,
        make_markdown=not args.docx_only,
        make_docx=not args.markdown_only,
        offline=args.offline,
        formulas=args.formulas,
        charts=args.charts,
        unwarp=args.unwarp,
    )
    summary = run_job(config, progress=lambda msg, done, total: print(f"[{done}/{total}] {msg}", flush=True))
    print(f"Completed {summary.completed_pages}/{summary.total_pages}; failed={summary.failed_pages}")
    return 2 if summary.failed_pages else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Local large-PDF OCR to DOCX and Markdown")
    parser.add_argument("pdf", nargs="?", help="PDF to preselect in the desktop app")
    parser.add_argument("--cli", action="store_true", help="Run without the desktop window")
    parser.add_argument("--output")
    parser.add_argument("--language", default="en")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--profile", choices=("quality", "fast_cpu"), default="quality")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--markdown-only", action="store_true")
    parser.add_argument("--docx-only", action="store_true")
    parser.add_argument("--formulas", action="store_true")
    parser.add_argument("--charts", action="store_true")
    parser.add_argument("--unwarp", action="store_true")
    args = parser.parse_args()
    if args.cli:
        if not args.pdf:
            parser.error("a PDF path is required with --cli")
        return run_cli(args)

    root = TkinterDnD.Tk() if TkinterDnD else tk.Tk()
    Scan2DocApp(root, args.pdf)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
