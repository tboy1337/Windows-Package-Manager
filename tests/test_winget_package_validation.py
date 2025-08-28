"""Tests to validate that winget package IDs in the catalog are correct and exist."""

import json
import subprocess
import time
from pathlib import Path
from typing import Dict, List, NamedTuple
import pytest
from core.winget_manager import WingetManager
from core.exceptions import WingetNotAvailableError


class ValidationResult(NamedTuple):
    """Result of package ID validation."""
    package_id: str
    package_name: str
    is_valid: bool
    error_message: str = ""
    winget_name: str = ""


class TestWingetPackageValidation:
    """Test suite for validating winget package IDs."""

    @pytest.fixture(scope="class")
    def app_catalog(self) -> List[Dict[str, str]]:
        """Load the application catalog."""
        catalog_path = Path("data/app_catalog.json")
        if not catalog_path.exists():
            pytest.skip("App catalog file not found")
        
        with open(catalog_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @pytest.fixture(scope="class")
    def winget_available(self) -> bool:
        """Check if winget is available for testing."""
        try:
            return WingetManager.is_available()
        except Exception:
            return False

    def validate_package_id(self, package_id: str, timeout: int = 10) -> Dict[str, any]:
        """
        Validate a single package ID using winget show command.
        
        Args:
            package_id: The winget package ID to validate
            timeout: Timeout in seconds for the command
            
        Returns:
            Dictionary with validation results
        """
        try:
            # Use winget show to verify package exists
            result = subprocess.run(
                ["winget", "show", package_id, "--accept-source-agreements"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",  # Replace invalid characters instead of failing
                timeout=timeout,
                check=False
            )
            
            if result.returncode == 0:
                # Package exists, try to extract the name
                output_lines = result.stdout.strip().split('\n')
                winget_name = ""
                
                # Look for "Found" line which contains the actual name
                for line in output_lines:
                    if line.startswith("Found "):
                        # Extract name from "Found PackageName [PackageID]" format
                        name_part = line.replace("Found ", "").strip()
                        if "[" in name_part:
                            winget_name = name_part.split("[")[0].strip()
                        else:
                            winget_name = name_part
                        break
                
                return {
                    "is_valid": True,
                    "error_message": "",
                    "winget_name": winget_name,
                    "output": result.stdout
                }
            else:
                # Check if it's a "not found" error vs other error
                error_output = result.stderr.strip() or result.stdout.strip()
                if "No package found matching input criteria" in error_output:
                    return {
                        "is_valid": False,
                        "error_message": f"Package not found in winget repository",
                        "winget_name": "",
                        "output": error_output
                    }
                else:
                    return {
                        "is_valid": False,
                        "error_message": f"Winget command failed (exit code {result.returncode}): {error_output}",
                        "winget_name": "",
                        "output": error_output
                    }
                    
        except subprocess.TimeoutExpired:
            return {
                "is_valid": False,
                "error_message": f"Timeout after {timeout} seconds",
                "winget_name": "",
                "output": ""
            }
        except Exception as e:
            return {
                "is_valid": False,
                "error_message": f"Validation error: {str(e)}",
                "winget_name": "",
                "output": ""
            }

    @pytest.mark.timeout(900)  # 15 minute timeout for the entire test
    def test_all_package_ids_valid(self, app_catalog, winget_available):
        """Test that all package IDs in the catalog are valid winget packages."""
        if not winget_available:
            pytest.skip("Winget is not available on this system")
        
        results = []
        invalid_packages = []
        
        print(f"\n🔍 Validating {len(app_catalog)} winget package IDs...")
        
        for i, app in enumerate(app_catalog, 1):
            package_id = app["id"]
            package_name = app["name"]
            
            print(f"  [{i:3d}/{len(app_catalog)}] Validating: {package_name} ({package_id})")
            
            validation = self.validate_package_id(package_id)
            
            result = ValidationResult(
                package_id=package_id,
                package_name=package_name,
                is_valid=validation["is_valid"],
                error_message=validation["error_message"],
                winget_name=validation["winget_name"]
            )
            
            results.append(result)
            
            if not result.is_valid:
                invalid_packages.append(result)
                print(f"    ❌ INVALID: {result.error_message}")
            else:
                print(f"    ✅ VALID: {result.winget_name}")
            
            # Small delay to be nice to winget servers
            time.sleep(0.5)
        
        # Generate summary report
        valid_count = sum(1 for r in results if r.is_valid)
        invalid_count = len(invalid_packages)
        
        print(f"\n📊 VALIDATION SUMMARY:")
        print(f"    Total packages: {len(results)}")
        print(f"    Valid packages: {valid_count}")
        print(f"    Invalid packages: {invalid_count}")
        print(f"    Success rate: {(valid_count / len(results) * 100):.1f}%")
        
        if invalid_packages:
            print(f"\n❌ INVALID PACKAGES:")
            for pkg in invalid_packages:
                print(f"    • {pkg.package_name} ({pkg.package_id})")
                print(f"      Error: {pkg.error_message}")
        
        # Save detailed results to file for analysis
        self._save_validation_report(results)
        
        # Fail the test if any packages are invalid
        assert invalid_count == 0, f"Found {invalid_count} invalid package IDs out of {len(results)} total packages"

    def _save_validation_report(self, results: List[ValidationResult]) -> None:
        """Save detailed validation report to file."""
        report_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_packages": len(results),
            "valid_packages": sum(1 for r in results if r.is_valid),
            "invalid_packages": sum(1 for r in results if not r.is_valid),
            "results": [
                {
                    "package_name": r.package_name,
                    "package_id": r.package_id,
                    "is_valid": r.is_valid,
                    "error_message": r.error_message,
                    "winget_name": r.winget_name
                }
                for r in results
            ]
        }
        
        report_path = Path("logs/winget_package_validation_report.json")
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Detailed report saved to: {report_path}")

    @pytest.mark.timeout(60)
    def test_sample_package_ids(self, app_catalog, winget_available):
        """Quick test with a sample of package IDs for faster feedback."""
        if not winget_available:
            pytest.skip("Winget is not available on this system")
        
        # Test a representative sample of packages
        sample_packages = [
            # Popular applications that should definitely exist
            {"name": "Google Chrome", "id": "Google.Chrome"},
            {"name": "Microsoft Edge", "id": "Microsoft.Edge"}, 
            {"name": "Visual Studio Code", "id": "Microsoft.VisualStudioCode"},
            {"name": "Mozilla Firefox", "id": "Mozilla.Firefox"},
            {"name": "7-Zip", "id": "7zip.7zip"},
            {"name": "Git", "id": "Git.Git"},
            {"name": "Node.js", "id": "OpenJS.NodeJS"},
            {"name": "Python 3.13", "id": "Python.Python.3.13"},
            {"name": "VLC", "id": "VideoLAN.VLC"},
            {"name": "Steam", "id": "Valve.Steam"}
        ]
        
        print(f"\n🔍 Quick validation of {len(sample_packages)} sample packages...")
        
        failed_packages = []
        
        for app in sample_packages:
            package_id = app["id"]
            package_name = app["name"]
            
            print(f"  Validating: {package_name} ({package_id})")
            
            validation = self.validate_package_id(package_id, timeout=15)
            
            if not validation["is_valid"]:
                failed_packages.append({
                    "name": package_name,
                    "id": package_id,
                    "error": validation["error_message"]
                })
                print(f"    ❌ FAILED: {validation['error_message']}")
            else:
                print(f"    ✅ SUCCESS: {validation['winget_name']}")
        
        if failed_packages:
            error_msg = f"Sample validation failed for {len(failed_packages)} packages:\n"
            for pkg in failed_packages:
                error_msg += f"  • {pkg['name']} ({pkg['id']}): {pkg['error']}\n"
            
            pytest.fail(error_msg)

    def test_winget_availability(self):
        """Test that winget is available for package validation."""
        try:
            is_available = WingetManager.is_available()
            assert is_available, "Winget is not available on this system"
            print("✅ Winget is available and ready for package validation")
        except WingetNotAvailableError as e:
            pytest.fail(f"Winget not available: {e}")
        except Exception as e:
            pytest.fail(f"Error checking winget availability: {e}")

    def test_catalog_structure(self, app_catalog):
        """Test that the app catalog has the expected structure."""
        assert len(app_catalog) > 0, "App catalog should not be empty"
        
        required_fields = ["name", "id", "category", "description"]
        
        for i, app in enumerate(app_catalog):
            for field in required_fields:
                assert field in app, f"App at index {i} missing required field: {field}"
                assert app[field], f"App at index {i} has empty {field}"
            
            # Validate ID format (should not contain spaces or special chars that would break winget)
            package_id = app["id"]
            assert " " not in package_id, f"Package ID '{package_id}' contains spaces"
            assert not package_id.startswith(" ") and not package_id.endswith(" "), f"Package ID '{package_id}' has leading/trailing spaces"
        
        print(f"✅ App catalog structure is valid with {len(app_catalog)} packages")
