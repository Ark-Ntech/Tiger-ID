"""Script to check all imports in the codebase and verify they exist"""

import ast
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Set
from collections import defaultdict

class ImportChecker:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.imports: Dict[str, List[Tuple[str, int, str]]] = defaultdict(list)
        self.missing_imports: Dict[str, List[Tuple[str, int, str]]] = defaultdict(list)
        self.file_cache: Set[Path] = set()
        
    def find_python_files(self) -> List[Path]:
        """Find all Python files in the codebase"""
        python_files = []
        for ext in ['**/*.py']:
            python_files.extend(self.root_dir.glob(ext))
        # Filter out common directories to ignore
        excluded = {'__pycache__', '.git', 'node_modules', 'venv', 'env', '.venv', 
                   'migrations/versions', 'data/models', 'data/datasets'}
        filtered = []
        for f in python_files:
            if not any(excluded_part in str(f) for excluded_part in excluded):
                filtered.append(f)
        return filtered
    
    def get_module_path(self, module_name: str, current_file: Path) -> Tuple[Path, bool]:
        """
        Resolve a module import to a file path.
        Returns (Path, exists) tuple.
        """
        # Handle relative imports
        if module_name.startswith('.'):
            parts = module_name.split('.')
            depth = len([p for p in parts if p == ''])
            module_parts = [p for p in parts if p]
            
            current_dir = current_file.parent
            for _ in range(depth - 1):
                current_dir = current_dir.parent
            
            # Build path from current directory
            module_path = current_dir / '/'.join(module_parts)
            # Try as file first, then as package
            for suffix in ['', '.py', '/__init__.py']:
                test_path = Path(str(module_path) + suffix)
                if test_path.exists():
                    return test_path, True
            
            return module_path, False
        
        # Handle absolute imports
        # Check if it's a local module (app.*, backend.*)
        if module_name.startswith(('app.', 'backend.', 'scripts.', 'tests.')):
            # Convert to file path
            parts = module_name.split('.')
            if parts[0] in ('app', 'backend', 'scripts', 'tests'):
                module_path = self.root_dir / '/'.join(parts)
                # Try as file first, then as package
                for suffix in ['.py', '/__init__.py', '']:
                    test_path = Path(str(module_path) + suffix)
                    if test_path.exists():
                        return test_path, True
                
                # Check if parent directory exists as package
                parent = module_path.parent
                if parent.exists() and (parent / '__init__.py').exists():
                    # Might be a missing __init__.py in the module itself
                    return module_path, False
        
        # Check standard library
        try:
            __import__(module_name)
            return Path(''), True  # Standard library
        except ImportError:
            pass
        
        # Check if it's a third-party package (skip)
        return Path(''), True  # Assume third-party exists
    
    def check_imports_in_file(self, file_path: Path):
        """Check all imports in a Python file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(file_path))
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name
                        line_no = node.lineno
                        self.imports[str(file_path)].append((module_name, line_no, 'import'))
                        module_path, exists = self.get_module_path(module_name, file_path)
                        if not exists and module_name.startswith(('app.', 'backend.', 'scripts.', 'tests.')):
                            self.missing_imports[str(file_path)].append((module_name, line_no, 'import'))
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:  # from x import y
                        module_name = node.module
                        line_no = node.lineno
                        self.imports[str(file_path)].append((module_name, line_no, f'from {module_name}'))
                        module_path, exists = self.get_module_path(module_name, file_path)
                        if not exists and module_name.startswith(('app.', 'backend.', 'scripts.', 'tests.')):
                            self.missing_imports[str(file_path)].append((module_name, line_no, f'from {module_name}'))
        
        except SyntaxError as e:
            print(f"Syntax error in {file_path}: {e}")
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    def check_all(self):
        """Check all Python files"""
        python_files = self.find_python_files()
        print(f"Found {len(python_files)} Python files to check...")
        
        for file_path in python_files:
            self.check_imports_in_file(file_path)
    
    def create_missing_file(self, module_name: str) -> bool:
        """Create a missing module file if it's a local import"""
        if not module_name.startswith(('app.', 'backend.', 'scripts.', 'tests.')):
            return False
        
        parts = module_name.split('.')
        if parts[0] not in ('app', 'backend', 'scripts', 'tests'):
            return False
        
        # Build file path
        module_path = self.root_dir / '/'.join(parts)
        
        # Check if parent exists
        parent = module_path.parent
        if not parent.exists():
            return False
        
        # Try .py file first
        py_file = Path(str(module_path) + '.py')
        if not py_file.exists():
            # Create the file with a basic structure
            try:
                py_file.parent.mkdir(parents=True, exist_ok=True)
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.write(f'"""{module_name} module"""\n\n')
                    print(f"Created missing file: {py_file}")
                return True
            except Exception as e:
                print(f"Failed to create {py_file}: {e}")
                return False
        
        # Try __init__.py
        init_file = module_path / '__init__.py'
        if module_path.is_dir() and not init_file.exists():
            try:
                with open(init_file, 'w', encoding='utf-8') as f:
                    f.write(f'"""{module_name} package"""\n\n')
                print(f"Created missing __init__.py: {init_file}")
                return True
            except Exception as e:
                print(f"Failed to create {init_file}: {e}")
                return False
        
        return False
    
    def report(self):
        """Print a report of missing imports"""
        print("\n" + "="*80)
        print("IMPORT CHECK REPORT")
        print("="*80)
        
        if not self.missing_imports:
            print("\n[OK] All imports found!")
            return
        
        print(f"\nFound {sum(len(v) for v in self.missing_imports.values())} missing imports:")
        
        for file_path, missing in sorted(self.missing_imports.items()):
            print(f"\n{file_path}:")
            for module_name, line_no, import_type in missing:
                print(f"  Line {line_no}: {import_type}")
        
        return self.missing_imports

def main():
    root_dir = Path(__file__).parent.parent
    print(f"Checking imports in: {root_dir}")
    
    checker = ImportChecker(root_dir)
    checker.check_all()
    missing = checker.report()
    
    if missing:
        print("\n" + "="*80)
        print("ATTEMPTING TO CREATE MISSING FILES")
        print("="*80)
        
        created = []
        for file_path, missing_list in missing.items():
            for module_name, line_no, import_type in missing_list:
                if checker.create_missing_file(module_name):
                    created.append(module_name)
        
        if created:
            print(f"\n[OK] Created {len(created)} missing files")
            print("\nRe-running import check...")
            checker.missing_imports.clear()
            checker.check_all()
            checker.report()

if __name__ == "__main__":
    main()
