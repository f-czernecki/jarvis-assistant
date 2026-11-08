import os
import subprocess
from pathlib import Path
from functools import lru_cache
from jarvis.config import (
    PROJECTS_DIR,
    PROJECT_FOLDERS,
    APPS_DIR,
    VSCODE_EXE,
)
IGNORED_FOLDERS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
}
@lru_cache(maxsize=8)
def discover_files(
    root: Path,
    extension: str,
    allowed_folders: tuple[str, ...] | None = None,
) -> list[str]:
    """Find files, optionally scanning only selected top-level folders."""
    results = []

    allowed_names = (
        {name.casefold() for name in allowed_folders}
        if allowed_folders is not None
        else None
    )

    for current_folder, folders, files in os.walk(root):
        folders[:] = [
            name
            for name in folders
            if name.lower() not in IGNORED_FOLDERS
        ]

        if Path(current_folder) == root and allowed_names is not None:
            folders[:] = [
                name
                for name in folders
                if name.casefold() in allowed_names
            ]

            # Pomijamy pliki leżące bezpośrednio w E:\Github.
            continue

        for name in files:
            if name.lower().endswith(extension):
                path = Path(current_folder) / name
                results.append(str(path.relative_to(root)))

    return sorted(results)


def checked_path(root: Path, relative_path: str, extension: str) -> Path:
    """Validate that a file exists inside the permitted folder."""
    root = root.resolve()
    path = (root / relative_path).resolve()

    if not path.is_relative_to(root):
        raise ValueError("The file must be inside the configured folder.")

    if path.suffix.lower() != extension:
        raise ValueError(f"Expected a {extension} file.")

    if not path.is_file():
        raise FileNotFoundError(f"File not found: {relative_path}")

    return path


def list_scripts() -> str:
    """List available Python scripts from enabled project folders."""
    scripts = discover_files(
        PROJECTS_DIR,
        ".py",
        PROJECT_FOLDERS,
    )

    return "\n".join(scripts) if scripts else "No Python scripts found."

def open_script(relative_path: str) -> str:
    """Open a Python script in VS Code for editing without executing it.

    Args:
        relative_path: Exact relative path returned by list_scripts.
    """
    try:
        path = checked_path(PROJECTS_DIR, relative_path, ".py")
        relative = path.relative_to(PROJECTS_DIR.resolve())

        allowed_names = {
            name.casefold()
            for name in PROJECT_FOLDERS
        }

        if (
            len(relative.parts) < 2
            or relative.parts[0].casefold() not in allowed_names
        ):
            raise ValueError(
                "This project is not enabled in PROJECT_FOLDERS."
            )
        if not VSCODE_EXE.is_file():
            return f"VS Code executable not found: {VSCODE_EXE}"

        subprocess.Popen([
            str(VSCODE_EXE),
            "--reuse-window",
            str(path),
        ])

        return f"Sent VS Code a request to open: {relative_path}"

    except (OSError, ValueError) as error:
        return f"Could not open script: {error}"


def list_apps() -> str:
    """List application shortcuts available to launch."""
    if not APPS_DIR.is_dir():
        return f"Application shortcuts folder not found: {APPS_DIR}"

    shortcuts = discover_files(APPS_DIR, ".lnk")
    return "\n".join(shortcuts) if shortcuts else "No .lnk shortcuts found."


def open_app(shortcut_name: str) -> str:

    """Open or launch a desktop application using its catalog shortcut.
    
        Use for requests such as "open Spotify", "open up Spotify",
        "launch Spotify", or "open VS Code".
        Opening Spotify does not start or resume music playback.
    
        Args:
            shortcut_name: Exact shortcut path from the application catalog,
                including the .lnk extension.
        """
    try:
        path = checked_path(APPS_DIR, shortcut_name, ".lnk")
        os.startfile(str(path))

        return f"Sent Windows a request to launch: {shortcut_name}"

    except (OSError, ValueError) as error:
        return f"Could not launch application: {error}"
    
def refresh_catalogs() -> str:
    """Refresh the lists of available Python scripts and application shortcuts."""
    discover_files.cache_clear()

    script_count = len(discover_files(
        PROJECTS_DIR,
        ".py",
        PROJECT_FOLDERS,
    ))
    app_count = len(discover_files(APPS_DIR, ".lnk"))

    return (
        f"Catalogs refreshed: {script_count} scripts "
        f"and {app_count} application shortcuts."
    )





