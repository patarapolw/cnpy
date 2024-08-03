from pathlib import Path
import shutil
import platform

import PyInstaller.__main__

APP_NAME = "cjpy"
VERSION = ""

pyi_args = ["app.py"]

pyi_args.append("--noconfirm")
# pyi_args.append("--noconsole")

pyi_args.extend(("--name", APP_NAME))

pyi_args.extend(("--add-data", "web/*:web"))

pyi_args.extend(("--collect-data", "wordfreq"))
pyi_args.extend(("--collect-data", "jieba"))


if __name__ == "__main__":
    dist_path = Path("dist") / APP_NAME
    keep_folders = ("assets", "user")

    for f in keep_folders:
        if (dist_path / f).exists():
            shutil.move(dist_path / f, dist_path.parent / f)

    PyInstaller.__main__.run(pyi_args)

    for f in Path().glob("*.md"):
        shutil.copy(f, dist_path)

        d = f.with_suffix("")
        if d.is_dir():
            shutil.copytree(d, dist_path / d.name)

    zip_name = APP_NAME
    if VERSION:
        zip_name += "-" + VERSION

    zip_name += "-" + platform.system()

    shutil.make_archive(str(dist_path.parent / zip_name), "zip", dist_path)

    for f in keep_folders:
        if (dist_path.parent / f).exists():
            shutil.move(dist_path.parent / f, dist_path / f)
