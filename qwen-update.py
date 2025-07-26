import subprocess
import json
import os
import sys
from typing import List, Dict, Any

# --- Ensure script is running as administrator on Windows ---
if os.name == 'nt':
    import ctypes
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        is_admin = False
    if not is_admin:
        print("Re-launching as administrator...")
        params = ' '.join([f'"{arg}"' for arg in sys.argv])
        # Use ShellExecuteEx to relaunch as admin
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, params, None, 1)
        sys.exit(0)

class SoftwareManager:
    def __init__(self):
        self.sources = {
            'winget': {'name': 'Windows Package Manager', 'available': self.check_winget()},
            'choco': {'name': 'Chocolatey', 'available': self.check_choco()},
            'scoop': {'name': 'Scoop', 'available': self.check_scoop()}
        }
        self.installed_packages = []
        self.available_packages = []
    
    def check_winget(self) -> bool:
        """Check if winget is available"""
        try:
            result = subprocess.run(["winget", "--version"], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except:
            return False
    
    def check_choco(self) -> bool:
        """Check if Chocolatey is available"""
        try:
            result = subprocess.run(["choco", "--version"], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except:
            return False
    
    def check_scoop(self) -> bool:
        """Check if Scoop is available"""
        try:
            result = subprocess.run(["scoop", "--version"], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except:
            return False
    
    def get_installed_packages(self, source: str) -> List[Dict[str, str]]:
        """Get installed packages from specified source"""
        packages = []
        
        if source == 'winget' and self.sources['winget']['available']:
            try:
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
                print(f"Error getting winget packages: {e}")
        
        elif source == 'choco' and self.sources['choco']['available']:
            try:
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
                print(f"Error getting choco packages: {e}")
        
        return packages
    
    def search_packages(self, query: str, source: str) -> List[Dict[str, str]]:
        """Search for packages from specified source"""
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
                print(f"Error searching winget packages: {e}")
        
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
                print(f"Error searching choco packages: {e}")
        
        return packages
    
    def install_package(self, package_id: str, source: str, silent: bool = True) -> bool:
        """Install package from specified source"""
        try:
            if source == 'winget':
                cmd = ["winget", "install", "--id", package_id]
                if silent:
                    cmd.extend(["--silent", "--accept-package-agreements", "--accept-source-agreements"])
                result = subprocess.run(cmd, capture_output=True, text=True)
                return result.returncode == 0
                
            elif source == 'choco':
                cmd = ["choco", "install", package_id, "-y"]
                if silent:
                    cmd.append("--no-progress")
                result = subprocess.run(cmd, capture_output=True, text=True)
                return result.returncode == 0
                
        except Exception as e:
            print(f"Error installing {package_id}: {e}")
            return False
        
        return False
    
    def update_package(self, package_id: str, source: str, silent: bool = True) -> bool:
        """Update package from specified source"""
        try:
            if source == 'winget':
                cmd = ["winget", "upgrade", "--id", package_id]
                if silent:
                    cmd.append("--silent")
                result = subprocess.run(cmd, capture_output=True, text=True)
                return result.returncode == 0
                
            elif source == 'choco':
                cmd = ["choco", "upgrade", package_id, "-y"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                return result.returncode == 0
                
        except Exception as e:
            print(f"Error updating {package_id}: {e}")
            return False
        
        return False

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_menu():
    """Display main menu"""
    clear_screen()
    print("=" * 50)
    print("           Universal Package Manager")
    print("=" * 50)
    print("1. View installed packages")
    print("2. Search for packages")
    print("3. Install package")
    print("4. Update packages")
    print("5. Check available sources")
    print("0. Exit")
    print("=" * 50)

def display_sources(sources: Dict[str, Dict[str, Any]]):
    """Display available package sources"""
    print("\nAvailable Package Sources:")
    print("-" * 30)
    for key, source in sources.items():
        status = "✓ Available" if source['available'] else "✗ Not Available"
        print(f"{key}: {source['name']} - {status}")

def select_source(sources: Dict[str, Dict[str, Any]]) -> str:
    """Let user select a package source"""
    available_sources = [key for key, source in sources.items() if source['available']]
    
    if not available_sources:
        print("No package managers available!")
        return None
    
    print("\nSelect package source:")
    for i, source in enumerate(available_sources, 1):
        print(f"{i}. {source} - {sources[source]['name']}")
    
    try:
        choice = int(input(f"\nEnter choice (1-{len(available_sources)}): ")) - 1
        if 0 <= choice < len(available_sources):
            return available_sources[choice]
        else:
            print("Invalid choice!")
            return None
    except ValueError:
        print("Invalid input!")
        return None

def main_cli():
    """Main CLI interface"""
    manager = SoftwareManager()
    
    while True:
        display_menu()
        try:
            choice = input("\nEnter your choice: ").strip()
            
            if choice == '0':
                print("Goodbye!")
                break
            elif choice == '1':
                # View installed packages
                source = select_source(manager.sources)
                if source:
                    packages = manager.get_installed_packages(source)
                    if packages:
                        print(f"\nInstalled packages from {source}:")
                        print("-" * 60)
                        for i, pkg in enumerate(packages[:20], 1):  # Show first 20
                            print(f"{i:2d}. {pkg['name']} ({pkg['version']}) - ID: {pkg['id']}")
                        if len(packages) > 20:
                            print(f"... and {len(packages) - 20} more packages")
                    else:
                        print("No packages found or error occurred.")
                    input("\nPress Enter to continue...")
            
            elif choice == '2':
                # Search for packages
                source = select_source(manager.sources)
                if source:
                    query = input("Enter search query: ").strip()
                    if query:
                        packages = manager.search_packages(query, source)
                        if packages:
                            print(f"\nSearch results from {source}:")
                            print("-" * 60)
                            for i, pkg in enumerate(packages[:20], 1):  # Show first 20
                                print(f"{i:2d}. {pkg['name']} ({pkg['version']}) - ID: {pkg['id']}")
                            
                            # Option to install
                            try:
                                install_choice = input("\nInstall a package? (number or 0 to skip): ").strip()
                                if install_choice != '0':
                                    idx = int(install_choice) - 1
                                    if 0 <= idx < len(packages):
                                        selected_pkg = packages[idx]
                                        confirm = input(f"Install {selected_pkg['name']}? (y/N): ").strip().lower()
                                        if confirm in ['y', 'yes']:
                                            print(f"Installing {selected_pkg['name']}...")
                                            if manager.install_package(selected_pkg['id'], source):
                                                print("✓ Installation successful!")
                                            else:
                                                print("✗ Installation failed!")
                                    else:
                                        print("Invalid selection!")
                            except ValueError:
                                pass
                        else:
                            print("No packages found.")
                        input("\nPress Enter to continue...")
            
            elif choice == '3':
                # Install package
                source = select_source(manager.sources)
                if source:
                    package_id = input("Enter package ID to install: ").strip()
                    if package_id:
                        print(f"Installing {package_id} from {source}...")
                        if manager.install_package(package_id, source):
                            print("✓ Installation successful!")
                        else:
                            print("✗ Installation failed!")
                        input("\nPress Enter to continue...")
            
            elif choice == '4':
                # Update packages
                source = select_source(manager.sources)
                if source:
                    packages = manager.get_installed_packages(source)
                    if packages:
                        print(f"\nInstalled packages from {source}:")
                        print("-" * 60)
                        for i, pkg in enumerate(packages[:10], 1):
                            print(f"{i:2d}. {pkg['name']} ({pkg['version']}) - ID: {pkg['id']}")
                        
                        try:
                            update_choice = input("\nUpdate packages? (numbers separated by commas, 'all' for all, or 0 to skip): ").strip()
                            if update_choice != '0':
                                if update_choice.lower() == 'all':
                                    # Update all (simplified)
                                    print("Update functionality would go here...")
                                else:
                                    # Update selected packages
                                    indices = [int(x.strip()) - 1 for x in update_choice.split(',')]
                                    for idx in indices:
                                        if 0 <= idx < len(packages):
                                            pkg = packages[idx]
                                            print(f"Updating {pkg['name']}...")
                                            if manager.update_package(pkg['id'], source):
                                                print(f"✓ {pkg['name']} updated!")
                                            else:
                                                print(f"✗ Failed to update {pkg['name']}")
                        except ValueError:
                            print("Invalid input!")
                    else:
                        print("No packages found.")
                    input("\nPress Enter to continue...")
            
            elif choice == '5':
                # Check available sources
                display_sources(manager.sources)
                input("\nPress Enter to continue...")
            
            else:
                print("Invalid choice! Please try again.")
                input("\nPress Enter to continue...")
                
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    main_cli()