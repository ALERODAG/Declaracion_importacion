import os
import sys
import json
import threading
import subprocess
import queue
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

APP_TITLE = "Lanzador de Scripts"
CONFIG_FILE = "launcher_config.json"
SUPPORTED_EXT = {".py", ".bat", ".ps1"}

# Detectar si estamos ejecutando desde un EXE empaquetado
RUNNING_AS_EXE = getattr(sys, 'frozen', False)

def find_system_python():
    """Encuentra la ruta al intérprete de Python del sistema."""
    try:
        # Intenta encontrar python en PATH
        if os.name == 'nt':  # Windows
            for cmd in ['python.exe', 'python3.exe']:
                try:
                    result = subprocess.run(['where', cmd], 
                                         capture_output=True, 
                                         text=True, 
                                         creationflags=subprocess.CREATE_NO_WINDOW)
                    if result.returncode == 0:
                        # Toma la primera línea (primera coincidencia)
                        return result.stdout.strip().split('\n')[0]
                except:
                    continue
        else:  # Unix-like
            for cmd in ['python3', 'python']:
                try:
                    result = subprocess.run(['which', cmd], 
                                         capture_output=True, 
                                         text=True)
                    if result.returncode == 0:
                        return result.stdout.strip()
                except:
                    continue
    except:
        pass
    
    # Fallback: buscar en ubicaciones comunes
    common_paths = []
    if os.name == 'nt':
        program_files = os.environ.get('PROGRAMFILES', r'C:\Program Files')
        common_paths = [
            os.path.join(program_files, 'Python3*', 'python.exe'),
            os.path.join(program_files, 'Python', 'Python3*', 'python.exe'),
            r'C:\Python3*\python.exe',
            os.path.expandvars(r'%LOCALAPPDATA%\Programs\Python\Python3*\python.exe'),
        ]
    else:
        common_paths = [
            '/usr/bin/python3',
            '/usr/local/bin/python3',
        ]

    for pattern in common_paths:
        if '*' in pattern:
            import glob
            matches = sorted(glob.glob(pattern), reverse=True)
            if matches:
                return matches[0]
        elif os.path.isfile(pattern):
            return pattern

    return None

class ScriptLauncher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.minsize(960, 640)
        self._proc = None
        self._log_queue = queue.Queue()
        self._stop_event = threading.Event()
        self._config = self._load_config()

        # UI
        self._build_toolbar()
        self._build_main()
        self._build_log()

        # State
        # Por defecto abrir la carpeta del proyecto donde están los scripts
        default_folder = r"D:\DESARROLLO DE SOFTWARE\Declaracion-de-importacion_V_29"
        self.folder_var.set(self._config.get("folder", default_folder))
        # Si estamos ejecutando desde un EXE empaquetado, intentar encontrar Python del sistema
        if RUNNING_AS_EXE:
            default_python = find_system_python() or sys.executable
        else:
            default_python = sys.executable
        self.python_var.set(self._config.get("python", default_python))
        self.args_var.set(self._config.get("args", ""))

        # Data
        self.refresh_list()
        self.after(100, self._drain_log_queue)

    # ---------------------------- UI ----------------------------
    def _build_toolbar(self):
        bar = ttk.Frame(self, padding=(10,8))
        bar.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(bar, text="Carpeta de scripts:").pack(side=tk.LEFT)
        self.folder_var = tk.StringVar()
        self.folder_entry = ttk.Entry(bar, textvariable=self.folder_var, width=60)
        self.folder_entry.pack(side=tk.LEFT, padx=(6,6))
        ttk.Button(bar, text="Examinar…", command=self.choose_folder).pack(side=tk.LEFT)
        ttk.Button(bar, text="Refrescar", command=self.refresh_list).pack(side=tk.LEFT, padx=(6,0))

        bar2 = ttk.Frame(self, padding=(10,0))
        bar2.pack(side=tk.TOP, fill=tk.X)
        ttk.Label(bar2, text="Intérprete Python:").pack(side=tk.LEFT)
        self.python_var = tk.StringVar()
        self.python_entry = ttk.Entry(bar2, textvariable=self.python_var, width=50)
        self.python_entry.pack(side=tk.LEFT, padx=(6,6))
        ttk.Button(bar2, text="Elegir…", command=self.choose_python).pack(side=tk.LEFT)

        bar3 = ttk.Frame(self, padding=(10,8))
        bar3.pack(side=tk.TOP, fill=tk.X)
        ttk.Label(bar3, text="Args del script (opcional):").pack(side=tk.LEFT)
        self.args_var = tk.StringVar()
        self.args_entry = ttk.Entry(bar3, textvariable=self.args_var, width=80)
        self.args_entry.pack(side=tk.LEFT, padx=(6,6))

    def _build_main(self):
        paned = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(paned, padding=10)
        right = ttk.Frame(paned, padding=10)
        paned.add(left, weight=1)
        paned.add(right, weight=3)

        # Lista de scripts (mostrar solo la ruta completa)
        self.tree = ttk.Treeview(left, columns=("path",), show="headings", height=20)
        self.tree.heading("path", text="Ruta")
        # Dar todo el ancho a la columna de ruta para que se vea completa
        self.tree.column("path", width=700, anchor=tk.W)
        self.tree.pack(fill=tk.BOTH, expand=True)

        btns = ttk.Frame(left)
        btns.pack(fill=tk.X, pady=(8,0))
        ttk.Button(btns, text="Ejecutar seleccionado", command=self.run_selected).pack(side=tk.LEFT)
        ttk.Button(btns, text="Ejecutar lote (selección múltiple)", command=self.run_batch).pack(side=tk.LEFT, padx=(8,0))
        ttk.Button(btns, text="Detener", command=self.stop_process).pack(side=tk.RIGHT)

        # Detalles/ayuda
        self.info = tk.Text(right, height=6, wrap=tk.WORD)
        self.info.pack(fill=tk.BOTH, expand=False)
        self._set_info()

    def _build_log(self):
        log_frame = ttk.LabelFrame(self, text="Salida del proceso")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,10))

        # Crear Text para la salida; algunos backends de Tk/Ttk empaquetados
        # pueden no aceptar opciones de color en ciertos widgets, por eso
        # intentamos crear el widget con los colores y caemos a una
        # variante por defecto si el intérprete de Tcl/Tk lanza un error.
        try:
            self.log = tk.Text(log_frame, wrap=tk.NONE, height=12, bg="#0e0e0e", fg="#e5e5e5", insertbackground="#e5e5e5")
        except tk.TclError:
            # Fallback: crear con opciones por defecto (evita crash por opciones no soportadas)
            self.log = tk.Text(log_frame, wrap=tk.NONE, height=12)
        self.log.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        scroll_y = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log.yview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.log.configure(yscrollcommand=scroll_y.set)

    def _set_info(self):
        text = (
            "Instrucciones:\n"
            "1) Coloca tus scripts (.py, .bat, .ps1) en la carpeta indicada.\n"
            "2) Selecciona el intérprete de Python (tu venv) si ejecutarás .py.\n"
            "3) Opcional: escribe argumentos para el script (se aplican al que ejecutes).\n"
            "4) Selecciona un script en la lista y pulsa 'Ejecutar', o selecciona varios para un lote.\n"
            "5) La salida/errores se muestran abajo en tiempo real.\n"
        )
        self.info.delete("1.0", tk.END)
        self.info.insert(tk.END, text)
        self.info.configure(state=tk.DISABLED)

    # ---------------------------- Actions ----------------------------
    def choose_folder(self):
        d = filedialog.askdirectory(initialdir=self.folder_var.get() or str(Path.cwd()))
        if d:
            self.folder_var.set(d)
            self.refresh_list()
            self._save_config()

    def choose_python(self):
        exe = filedialog.askopenfilename(title="Selecciona el intérprete de Python", filetypes=[("Python", "python.exe"), ("Todos", "*")])
        if exe:
            self.python_var.set(exe)
            self._save_config()

    def refresh_list(self):
        folder = Path(self.folder_var.get()).expanduser()
        for i in self.tree.get_children():
            self.tree.delete(i)
        # Mostrar solo archivos .py en la carpeta raíz (no recursivo)
        if folder.is_dir():
            for p in sorted(folder.iterdir()):
                if p.is_file() and p.suffix.lower() == ".py":
                    # Insertar solo la ruta como único valor
                    self.tree.insert("", tk.END, values=(str(p),))
        else:
            messagebox.showwarning(APP_TITLE, f"La carpeta no existe:\n{folder}")
        self._save_config()

    def run_selected(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo(APP_TITLE, "Selecciona un script de la lista.")
            return
        item = selection[0]
        path = self.tree.item(item, "values")[0]
        self._run_script(Path(path))

    def run_batch(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo(APP_TITLE, "Selecciona uno o más scripts.")
            return
        scripts = [Path(self.tree.item(i, "values")[0]) for i in selection]
        threading.Thread(target=self._run_batch_worker, args=(scripts,), daemon=True).start()

    def _run_batch_worker(self, scripts):
        for s in scripts:
            if self._stop_event.is_set():
                break
            self._run_script(s, block=True)

    def _run_script(self, script_path: Path, block=False):
        if self._proc and self._proc.poll() is None:
            messagebox.showwarning(APP_TITLE, "Ya hay un proceso ejecutándose. Deténlo antes de iniciar otro.")
            return
        if not script_path.exists():
            messagebox.showerror(APP_TITLE, f"No existe: {script_path}")
            return

        args_text = self.args_var.get().strip()
        extra_args = []
        if args_text:
            # División simple por espacios respetando comillas
            import shlex
            extra_args = shlex.split(args_text)

        cmd, env = self._build_command(script_path, extra_args)
        self._append_log(f"\n>>> Ejecutando: {' '.join(map(str, cmd))}\n")
        self._stop_event.clear()

        def worker():
            try:
                self._proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=1,
                    cwd=str(script_path.parent),
                    env=env,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                )
                for line in self._proc.stdout:
                    if self._stop_event.is_set():
                        break
                    self._log_queue.put(line.rstrip("\n"))
                self._proc.wait()
                code = self._proc.returncode
                self._log_queue.put(f"\n<<< Proceso finalizado con código {code}\n")
            except Exception as e:
                self._log_queue.put(f"[ERROR] {e}")
            finally:
                self._proc = None

        t = threading.Thread(target=worker, daemon=True)
        t.start()
        if block:
            t.join()

    def _build_command(self, script_path: Path, extra_args):
        ext = script_path.suffix.lower()
        env = os.environ.copy()

        if ext == ".py":
            # Si estamos ejecutando desde un EXE empaquetado, asegurarnos de usar un intérprete Python real
            if RUNNING_AS_EXE:
                py = self.python_var.get().strip()
                if not py or not Path(py).exists() or py == sys.executable:
                    # Si no hay un intérprete válido, buscar uno
                    py = find_system_python()
                    if not py:
                        raise RuntimeError("No se encontró un intérprete de Python válido. Por favor, selecciona uno usando 'Elegir...'")
                    self.python_var.set(py)
            else:
                py = self.python_var.get().strip() or sys.executable

            if not Path(py).exists():
                raise RuntimeError(f"No se encontró el intérprete de Python: {py}")
            cmd = [py, str(script_path), *extra_args]
        elif ext == ".bat":
            cmd = ["cmd.exe", "/c", str(script_path), *extra_args]
        elif ext == ".ps1":
            # Permitir ejecución; si hay políticas restrictivas, el usuario deberá ajustarlas
            cmd = ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", str(script_path), *extra_args]
        else:
            raise RuntimeError(f"Extensión no soportada: {ext}")

        return cmd, env

    def stop_process(self):
        if self._proc and self._proc.poll() is None:
            self._stop_event.set()
            self._proc.terminate()
            try:
                self._proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._proc.kill()
            self._append_log("\n<<< Proceso detenido por el usuario\n")
            self._proc = None

    def _append_log(self, text: str):
        self.log.insert(tk.END, text)
        self.log.see(tk.END)

    def _drain_log_queue(self):
        try:
            while True:
                line = self._log_queue.get_nowait()
                self._append_log(line + "\n")
        except queue.Empty:
            pass
        self.after(100, self._drain_log_queue)

    # ---------------------------- Config ----------------------------
    def _config_path(self):
        # En modo EXE, guarda config en AppData o similar
        if RUNNING_AS_EXE:
            if os.name == 'nt':
                return Path(os.environ['APPDATA']) / CONFIG_FILE
            else:
                return Path.home() / '.config' / CONFIG_FILE
        # En modo desarrollo, junto al script
        return Path(sys.argv[0]).parent / CONFIG_FILE

    def _load_config(self):
        p = self._config_path()
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def _save_config(self):
        data = {
            "folder": self.folder_var.get(),
            "python": self.python_var.get(),
            "args": self.args_var.get(),
        }
        try:
            config_path = self._config_path()
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            self._append_log(f"[WARN] No se pudo guardar la configuración: {e}")


def main():
    app = ScriptLauncher()
    app.mainloop()

if __name__ == "__main__":
    main()
