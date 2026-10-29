import os
import zipfile
import shutil

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_ZIP = os.path.join(PROJECT_ROOT, "ai_knowledge_base_project.zip")

EXCLUDE_DIRS = {
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".git",
    "venv",
    ".venv",
    "dist"
}

EXCLUDE_EXTS = {
    ".pyc",
    ".pyo",
    ".db",
    ".sqlite",
    ".log"
}


def package_project():
    print(f"Packaging project from {PROJECT_ROOT} into {OUTPUT_ZIP}...")

    if os.path.exists(OUTPUT_ZIP):
        os.remove(OUTPUT_ZIP)

    file_count = 0
    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zip_f:
        for root, dirs, files in os.walk(PROJECT_ROOT):
            # Modify dirs in-place to skip excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".")]

            for file in files:
                if file == "ai_knowledge_base_project.zip":
                    continue

                ext = os.path.splitext(file)[1].lower()
                if ext in EXCLUDE_EXTS:
                    continue

                abs_file = os.path.join(root, file)
                rel_path = os.path.relpath(abs_file, PROJECT_ROOT)

                zip_f.write(abs_file, rel_path)
                file_count += 1

    zip_size_mb = os.path.getsize(OUTPUT_ZIP) / (1024 * 1024)
    print(f"Successfully packaged {file_count} files into '{OUTPUT_ZIP}' ({zip_size_mb:.2f} MB)")
    return OUTPUT_ZIP


if __name__ == "__main__":
    package_project()
