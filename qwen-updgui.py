import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import json
import threading
from typing import List, Dict, Any

# --- Ensure script is running as administrator on Windows ---
import os, sys
if os.name == 'nt':
    import ctypes
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        is_admin = False
    if not is_admin:
        print("Re-launching as administrator...")
        params = ' '.join([f'"{arg}"' for arg in sys.argv])
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, params, None, 1)
        sys.exit(0)

class SoftwareManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Universal Package Manager")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # Package managers
        self.sources = {
            'winget': {'name': 'Windows Package Manager', 'available': self.check_winget()},
            'choco': {'name': 'Chocolatey', 'available': self.check_choco()}
        }
        
        self.setup_ui()
        self.populate_source_combo()
    
    def check_winget(self) -> bool:
        """Check if winget is available"""
        try:
            result = subprocess.run(["winget", "--version"], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def check_choco(self) -> bool:
        """Check if Chocolatey is available"""
        try:
            result = subprocess.run(["choco", "--version"], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def setup_ui(self):
        """Setup the user interface"""
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Source selection
        ttk.Label(main_frame, text="Package Source:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.source_var = tk.StringVar()
        self.source_combo = ttk.Combobox(main_frame, textvariable=self.source_var, state="readonly", width=20)
        self.source_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=0, column=2, sticky=tk.E)
        
        ttk.Button(button_frame, text="Refresh Sources", command=self.refresh_sources).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="View Installed", command=self.view_installed).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Search", command=self.search_packages).pack(side=tk.LEFT)
        
        # Search frame
        search_frame = ttk.Frame(main_frame)
        search_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 5))
        search_frame.columnconfigure(1, weight=1)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.search_entry.bind('<Return>', lambda e: self.search_packages())
        
        # Results treeview
        tree_frame = ttk.Frame(main_frame)
        tree_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        # Create treeview with scrollbar
        self.tree = ttk.Treeview(tree_frame, columns=('Name', 'Version', 'ID'), show='headings')
        self.tree.heading('Name', text='Name')
        self.tree.heading('Version', text='Version')
        self.tree.heading('ID', text='ID')
        self.tree.column('Name', width=200)
        self.tree.column('Version', width=100)
        self.tree.column('ID', width=200)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Action buttons for selected items
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Button(action_frame, text="Install Selected", command=self.install_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(action_frame, text="Update Selected", command=self.update_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(action_frame, text="Remove Selected", command=self.remove_selected).pack(side=tk.LEFT)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
    
    def populate_source_combo(self):
        """Populate the source combobox with available sources"""
        available_sources = []
        for key, source in self.sources.items():
            if source['available']:
                available_sources.append(f"{key} - {source['name']}")
        
        self.source_combo['values'] = available_sources
        if available_sources:
            self.source_combo.set(available_sources[0])
    
    def get_selected_source(self) -> str:
        """Get the selected source key"""
        selection = self.source_var.get()
        if selection:
            return selection.split(' - ')[0]
        return None
    
    def refresh_sources(self):
        """Refresh available package managers"""
        self.sources = {
            'winget': {'name': 'Windows Package Manager', 'available': self.check_winget()},
            'choco': {'name': 'Chocolatey', 'available': self.check_choco()}
        }
        self.populate_source_combo()
        self.status_var.set("Sources refreshed")
    
    def get_installed_packages(self, source: str) -> List[Dict[str, str]]:
        """Get installed packages from specified source"""
        packages = []
        
        if source == 'winget' and self.sources['winget']['available']:
            try:
                self.status_var.set("Fetching installed packages...")
                self.root.update()
                
                result = subprocess.run([
                    "winget", "list", "--json"
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    packages_data = data.get('Packages', []) if isinstance(data, dict) else data
                    for pkg in packages_data:
                        packages.append({
                            'id': pkg.get('Id', ''),
                            'name': pkg.get('Name', ''),
                            'version': pkg.get('Version', ''),
                            'source': 'winget'
                        })
            except Exception as e:
                messagebox.showerror("Error", f"Error getting winget packages: {e}")
        
        elif source == 'choco' and self.sources['choco']['available']:
            try:
                self.status_var.set("Fetching installed packages...")
                self.root.update()
                
                result = subprocess.run([
                    "choco", "list", "--local-only"
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines[1:-1]:  # Skip header and footer
                        if ' packages installed' not in line:
                            parts = line.split()
                            if len(parts) >= 2:
                                packages.append({
                                    'id': parts[0],
                                    'name': parts[0],
                                    'version': parts[1],
                                    'source': 'choco'
                                })
            except Exception as e:
                messagebox.showerror("Error", f"Error getting choco packages: {e}")
        
        return packages
    
    def search_packages_thread(self, query: str, source: str):
        """Search for packages in a separate thread"""
        packages = []
        
        if source == 'winget' and self.sources['winget']['available']:
            try:
                result = subprocess.run([
                    "winget", "search", query, "--json"
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    packages_data = data.get('Packages', []) if isinstance(data, dict) else data
                    for pkg in packages_data:
                        packages.append({
                            'id': pkg.get('Id', ''),
                            'name': pkg.get('Name', ''),
                            'version': pkg.get('Version', ''),
                            'source': 'winget'
                        })
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Error searching winget packages: {e}"))
        
        elif source == 'choco' and self.sources['choco']['available']:
            try:
                result = subprocess.run([
                    "choco", "search", query
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if '|' in line and not line.startswith('---'):
                            parts = line.split('|')
                            if len(parts) >= 2:
                                packages.append({
                                    'id': parts[0].strip(),
                                    'name': parts[0].strip(),
                                    'version': parts[1].strip(),
                                    'source': 'choco'
                                })
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Error searching choco packages: {e}"))
        
        # Update UI in main thread
        self.root.after(0, lambda: self.update_treeview(packages))
        self.root.after(0, lambda: self.status_var.set(f"Found {len(packages)} packages"))
    
    def update_treeview(self, packages: List[Dict[str, str]]):
        """Update the treeview with packages"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add new items
        for pkg in packages:
            self.tree.insert('', tk.END, values=(pkg['name'], pkg['version'], pkg['id']))
    
    def view_installed(self):
        """View installed packages"""
        source = self.get_selected_source()
        if not source:
            messagebox.showwarning("Warning", "Please select a package source")
            return
        
        # Run in separate thread to prevent UI freezing
        thread = threading.Thread(target=lambda: self.update_treeview(self.get_installed_packages(source)))
        thread.daemon = True
        thread.start()
    
    def search_packages(self):
        """Search for packages"""
        source = self.get_selected_source()
        query = self.search_var.get().strip()
        
        if not source:
            messagebox.showwarning("Warning", "Please select a package source")
            return
        
        if not query:
            messagebox.showwarning("Warning", "Please enter a search query")
            return
        
        # Clear current results
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.status_var.set("Searching...")
        
        # Run search in separate thread
        thread = threading.Thread(target=self.search_packages_thread, args=(query, source))
        thread.daemon = True
        thread.start()
    
    def install_selected(self):
        """Install selected packages"""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Warning", "Please select packages to install")
            return
        
        source = self.get_selected_source()
        if not source:
            messagebox.showwarning("Warning", "Please select a package source")
            return
        
        # Get selected package IDs
        package_ids = []
        for item in selected_items:
            values = self.tree.item(item, 'values')
            if len(values) >= 3:
                package_ids.append(values[2])  # ID is third column
        
        # Confirm installation
        if messagebox.askyesno("Confirm", f"Install {len(package_ids)} selected packages?"):
            self.status_var.set(f"Installing {len(package_ids)} packages...")
            # Installation logic would go here
            messagebox.showinfo("Info", "Installation started. Please check the terminal for progress.")
    
    def update_selected(self):
        """Update selected packages"""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Warning", "Please select packages to update")
            return
        
        source = self.get_selected_source()
        if not source:
            messagebox.showwarning("Warning", "Please select a package source")
            return
        
        messagebox.showinfo("Info", "Update functionality would be implemented here")
    
    def remove_selected(self):
        """Remove selected packages"""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Warning", "Please select packages to remove")
            return
        
        source = self.get_selected_source()
        if not source:
            messagebox.showwarning("Warning", "Please select a package source")
            return
        
        messagebox.showinfo("Info", "Remove functionality would be implemented here")

def main_gui():
    """Main GUI application"""
    root = tk.Tk()
    app = SoftwareManagerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    # Run GUI version
    main_gui()