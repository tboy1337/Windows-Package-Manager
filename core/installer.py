import threading
from typing import List, Callable, Dict
from .winget_manager import WingetManager

class Installer:
    def __init__(self) -> None:
        self.winget = WingetManager()

    def install_packages(self, package_ids: List[str], callback: Callable[[str, Dict[str, any]], None] = None) -> threading.Thread:
        def install_thread() -> None:
            for pkg_id in package_ids:
                attempts = 0
                max_attempts = 3
                while attempts < max_attempts:
                    result = self.winget.install_package(pkg_id)
                    if result['success']:
                        break
                    attempts += 1
                    if 'error' in result and 'admin' in result['error'].lower():
                        break  # No retry for admin issues
                if callback:
                    callback(pkg_id, result)

        thread = threading.Thread(target=install_thread)
        thread.start()
        return thread 