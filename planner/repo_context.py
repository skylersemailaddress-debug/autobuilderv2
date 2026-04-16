from pathlib import Path
from typing import Dict, List


COMMON_CONFIG_FILES = {
    "pyproject.toml": "python",
    "requirements.txt": "python",
    "setup.py": "python",
    "package.json": "node",
    "package-lock.json": "node",
    "yarn.lock": "node",
    "pnpm-lock.yaml": "node",
    "go.mod": "go",
    "Cargo.toml": "rust",
    "Dockerfile": "docker",
    "docker-compose.yml": "docker",
    "tsconfig.json": "typescript",
    "webpack.config.js": "javascript",
    "vite.config.js": "javascript",
    "nx.json": "monorepo",
    "workspace.json": "monorepo",
    "angular.json": "angular",
    "next.config.js": "nextjs",
    "gatsby-config.js": "gatsby",
}

FRAMEWORK_HINTS = {
    "django": "django",
    "flask": "flask",
    "fastapi": "fastapi",
    "react": "react",
    "vue": "vue",
    "angular": "angular",
    "express": "express",
    "spring": "spring",
    "rails": "rails",
}

TEST_FOLDER_NAMES = {"tests", "test", "spec", "e2e", "integration"}


def inspect_repo_context(repo_root: Path) -> Dict:
    """Inspect repository structure and return metadata useful for planning."""
    repo_root = repo_root.resolve()
    top_level_folders = [p.name for p in repo_root.iterdir() if p.is_dir()]
    key_config_files = [p.name for p in repo_root.iterdir() if p.is_file() and p.name in COMMON_CONFIG_FILES]
    test_folders = [folder for folder in top_level_folders if folder.lower() in TEST_FOLDER_NAMES]

    framework_hints = []
    detected_frameworks = set()

    # Infer framework hints from config files
    for config_name in key_config_files:
        hint = COMMON_CONFIG_FILES.get(config_name)
        if hint:
            detected_frameworks.add(hint)

    # Inspect top-level folder names and file contents for additional hints
    for folder_name in top_level_folders:
        normalized = folder_name.lower()
        if normalized in {"src", "app", "backend", "frontend", "web"}:
            framework_hints.append(f"contains {folder_name} folder")
        if normalized in {"api", "service"}:
            framework_hints.append(f"contains {folder_name} service folder")

    # Look for common framework names in project files
    for config_path in repo_root.iterdir():
        if config_path.is_file() and config_path.suffix in {".json", ".toml", ".yml", ".yaml", ".py", ".txt"}:
            try:
                content = config_path.read_text(encoding="utf-8", errors="ignore").lower()
            except OSError:
                continue
            for key, hint in FRAMEWORK_HINTS.items():
                if key in content:
                    detected_frameworks.add(hint)

    if detected_frameworks:
        framework_hints.extend(sorted(detected_frameworks))

    # Deduplicate hints
    framework_hints = list(dict.fromkeys(framework_hints))

    return {
        "repo_mode": True,
        "repo_root": str(repo_root),
        "top_level_folders": sorted(top_level_folders),
        "config_files": sorted(key_config_files),
        "framework_hints": framework_hints,
        "test_folders": sorted(test_folders),
    }