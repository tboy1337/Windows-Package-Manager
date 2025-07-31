import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import json
from typing import Dict, List
from core.winget_manager import WingetManager
from core.app_database import AppDatabase
from core.installer import Installer

class MainWindow(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Winget Package Manager")
        self.geometry("800x600")
        self.apps: List[Dict[str, str]] = self.load_apps()
        self.categories: List[str] = self.load_categories()
        self.db = AppDatabase()
        self.installer = Installer()
        self.selected_packages = set()
        self.checkbuttons = {}
        self.create_ui()

    def load_apps(self) -> List[Dict[str, str]]:
        try:
            with open('data/app_catalog.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load app catalog: {e}")
            return []

    def load_categories(self) -> List[str]:
        try:
            with open('data/categories.json', 'r') as f:
                return json.load(f)['categories']
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load categories: {e}")
            return []

    def create_ui(self) -> None:
        # Search frame
        search_frame = ttk.Frame(self)
        search_frame.pack(fill='x', pady=5)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(fill='x', expand=True)
        search_entry.bind('<KeyRelease>', self.perform_search)

        # Notebook for categories
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True)
        self.category_frames = {}
        for cat in self.categories:
            outer_frame = ttk.Frame(self.notebook)
            scroll_canvas = tk.Canvas(outer_frame)
            scrollbar = ttk.Scrollbar(outer_frame, orient="vertical", command=scroll_canvas.yview)
            scroll_canvas.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side="right", fill="y")
            scroll_canvas.pack(side="left", fill="both", expand=True)
            inner_frame = ttk.Frame(scroll_canvas)
            scroll_canvas.create_window((0, 0), window=inner_frame, anchor="nw")
            inner_frame.bind("<Configure>", lambda e, c=scroll_canvas: c.configure(scrollregion=c.bbox("all")))
            scroll_canvas.bind("<MouseWheel>", lambda event, c=scroll_canvas: c.yview_scroll(int(-1 * (event.delta / 120)), "units"))
            self.category_frames[cat] = inner_frame
            self.notebook.add(outer_frame, text=cat)
            self.populate_category(cat)

        # Search results frame (hidden initially)
        self.search_results_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.search_results_frame, text="Search Results", state='hidden')

        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(fill='x', pady=5)
        install_btn = ttk.Button(button_frame, text="Install Selected", command=self.install_selected)
        install_btn.pack(side='left')
        select_all_btn = ttk.Button(button_frame, text="Select All", command=self.select_all)
        select_all_btn.pack(side='left')
        deselect_all_btn = ttk.Button(button_frame, text="Deselect All", command=self.deselect_all)
        deselect_all_btn.pack(side='left')
        save_btn = ttk.Button(button_frame, text="Save Profile", command=self.save_profile)
        save_btn.pack(side='left')
        load_btn = ttk.Button(button_frame, text="Load Profile", command=self.load_profile)
        load_btn.pack(side='left')
        export_btn = ttk.Button(button_frame, text="Export Script", command=self.export_script)
        export_btn.pack(side='left')

        # Log
        self.log_text = tk.Text(self, height=10)
        self.log_text.pack(fill='both', expand=True)

    def populate_category(self, cat: str) -> None:
        inner_frame = self.category_frames[cat]
        cat_apps = [app for app in self.apps if app['category'] == cat]
        left_frame = ttk.Frame(inner_frame)
        right_frame = ttk.Frame(inner_frame)
        left_frame.pack(side="left", fill="y", padx=10, pady=5)
        right_frame.pack(side="right", fill="y", padx=10, pady=5)
        half = len(cat_apps) // 2
        for i, app in enumerate(cat_apps):
            target = left_frame if i < half else right_frame
            var = tk.BooleanVar()
            chk = ttk.Checkbutton(target, text=app['name'], variable=var,
                                  command=lambda a=app['id'], v=var: self.toggle_select(a, v))
            chk.pack(anchor='w')
            self.checkbuttons[app['id']] = (chk, var)

    def toggle_select(self, pkg_id: str, var: tk.BooleanVar) -> None:
        if var.get():
            self.selected_packages.add(pkg_id)
        else:
            self.selected_packages.discard(pkg_id)

    def select_all(self) -> None:
        current_tab = self.notebook.tab(self.notebook.select(), "text")
        if current_tab in self.categories:
            cat_apps = [app for app in self.apps if app['category'] == current_tab]
            for app in cat_apps:
                self.checkbuttons[app['id']][1].set(True)
                self.selected_packages.add(app['id'])

    def deselect_all(self) -> None:
        current_tab = self.notebook.tab(self.notebook.select(), "text")
        if current_tab in self.categories:
            cat_apps = [app for app in self.apps if app['category'] == current_tab]
            for app in cat_apps:
                self.checkbuttons[app['id']][1].set(False)
                self.selected_packages.discard(app['id'])

    def perform_search(self, event=None) -> None:
        query = self.search_var.get().strip()
        if not query:
            self.notebook.tab(self.search_results_frame, state='hidden')
            return
        results = WingetManager.search_packages(query)
        # Clear previous results
        for widget in self.search_results_frame.winfo_children():
            widget.destroy()
        if not results:
            ttk.Label(self.search_results_frame, text="No results found").pack()
        else:
            for res in results:
                var = tk.BooleanVar()
                chk = ttk.Checkbutton(self.search_results_frame, text=f"{res['name']} ({res['id']})", variable=var,
                                      command=lambda i=res['id'], v=var: self.toggle_select(i, v))
                chk.pack(anchor='w')
                self.checkbuttons[res['id']] = (chk, var)  # Note: may overwrite if duplicate id
        self.notebook.tab(self.search_results_frame, state='normal')
        self.notebook.select(self.search_results_frame)

    def install_selected(self) -> None:
        if not self.selected_packages:
            messagebox.showinfo("Info", "No packages selected")
            return
        if not WingetManager.is_available():
            messagebox.showerror("Error", "Winget is not available. Please install it.")
            return
        def callback(pkg: str, result: Dict[str, any]) -> None:
            status = 'Success' if result['success'] else result.get('error', 'Failed')
            self.log_text.insert('end', f"{pkg}: {status}\n")
            self.log_text.see('end')
        self.installer.install_packages(list(self.selected_packages), callback)
        self.log_text.insert('end', "Installation started...\n")

    def save_profile(self) -> None:
        name = simpledialog.askstring("Save Profile", "Enter profile name:")
        if name:
            self.db.save_profile(name, list(self.selected_packages))
            messagebox.showinfo("Info", "Profile saved")

    def load_profile(self) -> None:
        profiles = self.db.get_all_profiles()
        if not profiles:
            messagebox.showinfo("Info", "No profiles saved")
            return
        name = simpledialog.askstring("Load Profile", "Enter profile name:")
        if name and name in profiles:
            selections = self.db.load_profile(name)
            self.selected_packages = set(selections)
            for pkg_id, (chk, var) in self.checkbuttons.items():
                var.set(pkg_id in self.selected_packages)
            messagebox.showinfo("Info", "Profile loaded")

    def export_script(self) -> None:
        if not self.selected_packages:
            messagebox.showinfo("Info", "No packages selected to export")
            return
        script = "# Winget install script\n"
        for pkg in self.selected_packages:
            script += f"winget install --id {pkg} --exact --silent --accept-package-agreements --accept-source-agreements\n"
        file_path = filedialog.asksaveasfilename(defaultextension=".ps1", filetypes=[("PowerShell Script", "*.ps1")])
        if file_path:
            with open(file_path, 'w') as f:
                f.write(script)
            messagebox.showinfo("Info", "Script exported successfully") 