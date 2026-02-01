"""
sweepy - Sweep away unused imports from your codebase
Git repository URL 또는 로컬 경로를 받아서 미사용 import 탐지
"""

import ast
import subprocess
import tempfile
import shutil
from pathlib import Path
from dataclasses import dataclass, field


DEFAULT_EXCLUDE_DIRS = {
    '__pycache__', '.git', '.venv', 'venv', 'env',
    'node_modules', '.tox', '.eggs', 'build', 'dist',
    '.mypy_cache', '.pytest_cache', '.ruff_cache'
}

DEFAULT_EXCLUDE_FILES = {
    '__init__.py',
}


@dataclass
class UnusedImport:
    file: str
    line: int
    module: str


@dataclass
class AnalysisResult:
    repo_path: str
    unused_imports: list[UnusedImport] = field(default_factory=list)
    files_analyzed: int = 0
    files_skipped: int = 0
    parse_errors: list[tuple[str, str]] = field(default_factory=list)
    
    def by_file(self) -> dict[str, list[UnusedImport]]:
        result: dict[str, list[UnusedImport]] = {}
        for item in self.unused_imports:
            result.setdefault(item.file, []).append(item)
        return result
    
    def summary(self) -> str:
        lines = [
            f"Repository: {self.repo_path}",
            f"Files analyzed: {self.files_analyzed}",
            f"Files skipped: {self.files_skipped}",
            f"Unused imports: {len(self.unused_imports)}",
        ]
        return "\n".join(lines)


class UnusedImportDetector(ast.NodeVisitor):
    def __init__(self):
        self.imports: dict[str, int] = {}
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
        repo_path: str,
        exclude_dirs: set[str] | None = None,
        exclude_files: set[str] | None = None
    ):
        self.original_path = repo_path
        self.is_github = 'github.com' in repo_path
        self.is_remote = self._is_git_url(repo_path)
        self.temp_dir: str | None = None
        self.exclude_dirs = exclude_dirs or DEFAULT_EXCLUDE_DIRS
        self.exclude_files = exclude_files or DEFAULT_EXCLUDE_FILES
        self.root: Path | None = None
    
    def _is_git_url(self, path: str) -> bool:
        return (
            path.startswith('https://') or 
            path.startswith('git@') or
            path.startswith('http://') or
            'github.com' in path or
            'gitlab.com' in path or
            'bitbucket.org' in path
        )
    
    def _parse_github_url(self, url: str) -> tuple[str, str, str | None]:
        """GitHub URL에서 owner, repo, branch 추출"""
        url = url.replace('.git', '')
        parts = url.split('github.com/')[-1].split('/')
        owner = parts[0]
        repo = parts[1]
        branch = None
        
        if len(parts) > 3 and parts[2] == 'tree':
            branch = '/'.join(parts[3:])
        
        return owner, repo, branch
    
    def _clone_repo(self, url: str) -> Path:
        self.temp_dir = tempfile.mkdtemp()
        
        if 'github.com' in url:
            owner, repo, branch = self._parse_github_url(url)
            clone_url = f"https://github.com/{owner}/{repo}.git"
            
            cmd = ['git', 'clone', '--depth', '1']
            if branch:
                cmd.extend(['-b', branch])
            cmd.extend([clone_url, self.temp_dir])
        
        elif 'gitlab.com' in url:
            parts = url.split('gitlab.com/')[-1].split('/')
            user, repo = parts[0], parts[1].replace('.git', '')
            clone_url = f"https://gitlab.com/{user}/{repo}.git"
            cmd = ['git', 'clone', '--depth', '1', clone_url, self.temp_dir]
        
        elif 'bitbucket.org' in url:
            parts = url.split('bitbucket.org/')[-1].split('/')
            user, repo = parts[0], parts[1].replace('.git', '')
            clone_url = f"https://bitbucket.org/{user}/{repo}.git"
            cmd = ['git', 'clone', '--depth', '1', clone_url, self.temp_dir]
        
        else:
            cmd = ['git', 'clone', '--depth', '1', url, self.temp_dir]
        
        subprocess.run(cmd, check=True, capture_output=True)
        return Path(self.temp_dir)
    
    def _cleanup(self):
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def analyze(self) -> AnalysisResult:
        result = AnalysisResult(repo_path=self.original_path)
        
        if self.is_remote:
            self.root = self._clone_repo(self.original_path)
        else:
            self.root = Path(self.original_path).resolve()
        
        return self._analyze_local(result)
    
    def _analyze_local(self, result: AnalysisResult) -> AnalysisResult:
        """로컬 파일 시스템에서 분석"""
        for py_file in self.root.rglob('*.py'):
            if self._should_skip(py_file):
                result.files_skipped += 1
                continue
            
            rel_path = str(py_file.relative_to(self.root))
            source = py_file.read_text(encoding='utf-8')
            
            compile(source, rel_path, 'exec', ast.PyCF_ONLY_AST)
            
            tree = ast.parse(source)
            detector = UnusedImportDetector()
            detector.visit(tree)
            
            for name, line in detector.get_unused():
                result.unused_imports.append(
                    UnusedImport(file=rel_path, line=line, module=name)
                )
            
            result.files_analyzed += 1
        
        if self.is_remote:
            self._cleanup()
        
        return result
    
    def _should_skip(self, path: Path) -> bool:
        for part in path.relative_to(self.root).parts:
            if part in self.exclude_dirs:
                return True
        
        if path.name in self.exclude_files:
            return True
        
        return False


def print_report(result: AnalysisResult):
    print(f"\n{'='*60}")
    print("SWEEPY ANALYSIS REPORT")
    print(f"{'='*60}")
    print(result.summary())
    
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


def analyze(repo: str) -> AnalysisResult:
    """
    메인 API 함수
    
    Args:
        repo: Git URL 또는 로컬 경로
              - https://github.com/user/repo.git
              - git@github.com:user/repo.git
              - /path/to/local/repo
    
    Returns:
        AnalysisResult 객체
    """
    analyzer = RepoAnalyzer(repo)
    return analyzer.analyze()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="sweepy - Sweep away unused imports"
    )
    parser.add_argument(
        "repo",
        help="Git repository URL or local path"
    )
    parser.add_argument(
        "--exclude-dir",
        action="append",
        default=[],
        help="Additional directories to exclude"
    )
    parser.add_argument(
        "--exclude-file",
        action="append",
        default=[],
        help="Additional files to exclude"
    )
    
    args = parser.parse_args()
    
    exclude_dirs = DEFAULT_EXCLUDE_DIRS | set(args.exclude_dir)
    exclude_files = DEFAULT_EXCLUDE_FILES | set(args.exclude_file)
    
    analyzer = RepoAnalyzer(args.repo, exclude_dirs, exclude_files)
    result = analyzer.analyze()
    
    print_report(result)
    
    exit(1 if result.unused_imports else 0)


if __name__ == "__main__":
    main()