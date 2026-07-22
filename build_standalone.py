import os
import sys
import shutil

def build_executable():
    """Build standalone executable using PyInstaller."""
    print("=" * 60)
    print("Building AI CI/CD Pipeline Generator Standalone Executable")
    print("=" * 60)

    try:
        import PyInstaller.__main__
    except ImportError:
        print("PyInstaller not installed. Install via: pip install pyinstaller")
        sys.exit(1)

    project_root = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(project_root, "main.py")
    templates_dir = os.path.join(project_root, "templates")

    # PyInstaller arguments
    args = [
        main_script,
        "--name=AI-CICD-Pipeline-Generator",
        "--onedir",
        "--windowed",
        "--noconfirm",
        "--clean",
        f"--add-data={templates_dir}{os.path.pathsep}templates",
        "--hidden-import=sqlalchemy.sql.default_comparator",
        "--hidden-import=sqlalchemy.ext.baked",
        "--hidden-import=sqlalchemy.dialects.sqlite",
        "--hidden-import=yaml",
        "--hidden-import=jinja2",
        "--hidden-import=cryptography",
        "--hidden-import=dotenv",
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=PySide6.QtGui",
        "--hidden-import=PySide6.QtWidgets",
    ]

    print(f"Executing PyInstaller build with options: {args}")
    PyInstaller.__main__.run(args)
    print("=" * 60)
    print("Build process completed successfully! Output in 'dist/AI-CICD-Pipeline-Generator'")
    print("=" * 60)

if __name__ == "__main__":
    build_executable()
