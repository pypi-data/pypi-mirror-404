"""
Unused Import Detector Agent (Repository-level)
레포지토리 전체를 brute force로 스캔하여 미사용 import 탐지
"""

import ast
from pathlib import Path
from dataclasses import dataclass, field


DEFAULT_EXCLUDE_DIRS = {
    '__pycache__', '.git', '.venv', 'venv', 'env',
    'node_modules', '.tox', '.eggs', 'build', 'dist',
    '.mypy_cache', '.pytest_cache', '.ruff_cache'
}

DEFAULT_EXCLUDE_FILES = {
    '__init__.py',  # re-export 용도로 import만 하는 경우 많음
}


@dataclass
class UnusedImport:
    file: str
    line: int
    module: str


@dataclass
class AnalysisResult:
    unused_imports: list[UnusedImport] = field(default_factory=list)
    files_analyzed: int = 0
    files_skipped: int = 0
    parse_errors: list[tuple[str, str]] = field(default_factory=list)
    
    def by_file(self) -> dict[str, list[UnusedImport]]:
        result: dict[str, list[UnusedImport]] = {}
        for item in self.unused_imports:
            result.setdefault(item.file, []).append(item)
        return result


class UnusedImportDetector(ast.NodeVisitor):
    def __init__(self):
        self.imports: dict[str, int] = {}  # name -> line
        self.used_names: set[str] = set()
    
    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            name = alias.asname or alias.name.split('.')[0]
            self.imports[name] = node.lineno
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        for alias in node.names:
            if alias.name == '*':
                continue
            name = alias.asname or alias.name
            self.imports[name] = node.lineno
        self.generic_visit(node)
    
    def visit_Name(self, node: ast.Name):
        self.used_names.add(node.id)
        self.generic_visit(node)
    
    def visit_Attribute(self, node: ast.Attribute):
        if isinstance(node.value, ast.Name):
            self.used_names.add(node.value.id)
        self.generic_visit(node)
    
    def get_unused(self) -> list[tuple[str, int]]:
        unused = []
        for name, line in self.imports.items():
            if name not in self.used_names:
                unused.append((name, line))
        return sorted(unused, key=lambda x: x[1])


class RepoAnalyzer:
    def __init__(
        self,
        repo_path: str | Path,
        exclude_dirs: set[str] | None = None,
        exclude_files: set[str] | None = None
    ):
        self.root = Path(repo_path).resolve()
        self.exclude_dirs = exclude_dirs or DEFAULT_EXCLUDE_DIRS
        self.exclude_files = exclude_files or DEFAULT_EXCLUDE_FILES
    
    def analyze(self) -> AnalysisResult:
        result = AnalysisResult()
        
        for py_file in self.root.rglob('*.py'):
            if self._should_skip(py_file):
                result.files_skipped += 1
                continue
            
            rel_path = str(py_file.relative_to(self.root))
            
            source = py_file.read_text(encoding='utf-8')
            
            # syntax 검증
            code = compile(source, rel_path, 'exec', ast.PyCF_ONLY_AST)
            if code is None:
                result.parse_errors.append((rel_path, "Failed to compile"))
                continue
            
            tree = ast.parse(source)
            detector = UnusedImportDetector()
            detector.visit(tree)
            
            for name, line in detector.get_unused():
                result.unused_imports.append(
                    UnusedImport(file=rel_path, line=line, module=name)
                )
            
            result.files_analyzed += 1
        
        return result
    
    def _should_skip(self, path: Path) -> bool:
        # 디렉토리 체크
        for part in path.relative_to(self.root).parts:
            if part in self.exclude_dirs:
                return True
        
        # 파일명 체크
        if path.name in self.exclude_files:
            return True
        
        return False


def print_report(result: AnalysisResult):
    print(f"\n{'='*60}")
    print("UNUSED IMPORT ANALYSIS REPORT")
    print(f"{'='*60}")
    print(f"Files analyzed: {result.files_analyzed}")
    print(f"Files skipped:  {result.files_skipped}")
    print(f"Unused imports: {len(result.unused_imports)}")
    
    if result.parse_errors:
        print(f"\nParse errors ({len(result.parse_errors)}):")
        for file, error in result.parse_errors:
            print(f"  {file}: {error}")
    
    if not result.unused_imports:
        print("\nNo unused imports found.")
        return
    
    print(f"\n{'-'*60}")
    for file, items in result.by_file().items():
        print(f"\n{file}")
        for item in items:
            print(f"   Line {item.line:3d}: {item.module}")
    
    print(f"\n{'-'*60}")
    print("To fix:")
    print("   autoflake --in-place --remove-all-unused-imports <file>")
    print("   ruff check --fix <file>")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Repository-level unused import detector"
    )
    parser.add_argument(
        "repo",
        nargs="?",
        default=".",
        help="Repository root path (default: current directory)"
    )
    parser.add_argument(
        "--exclude-dir",
        action="append",
        default=[],
        help="Additional directories to exclude (can be used multiple times)"
    )
    parser.add_argument(
        "--exclude-file",
        action="append",
        default=[],
        help="Additional files to exclude (can be used multiple times)"
    )
    
    args = parser.parse_args()
    
    repo_path = Path(args.repo)
    if not repo_path.is_dir():
        print(f"[ERROR] Not a directory: {repo_path}")
        exit(1)
    
    exclude_dirs = DEFAULT_EXCLUDE_DIRS | set(args.exclude_dir)
    exclude_files = DEFAULT_EXCLUDE_FILES | set(args.exclude_file)
    
    analyzer = RepoAnalyzer(repo_path, exclude_dirs, exclude_files)
    result = analyzer.analyze()
    
    print_report(result)
    
    exit(1 if result.unused_imports else 0)
