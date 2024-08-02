from pathlib import Path
import shutil
import platform

import PyInstaller.__main__

APP_NAME = "cjpy"

pyi_args = ["app.py"]

pyi_args.append("--noconfirm")

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

    shutil.make_archive(
        str(dist_path.parent / f"{APP_NAME}-{platform.system()}"), "zip", dist_path
    )

    for f in keep_folders:
        if (dist_path.parent / f).exists():
            shutil.move(dist_path.parent / f, dist_path / f)
