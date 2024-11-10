from pathlib import Path
import shutil
import platform
import sys

import PyInstaller.__main__

APP_NAME = "cnpy"
VERSION = sys.argv[1] if len(sys.argv) > 1 else ""

pyi_args = ["app.py"]

pyi_args.append("--noconfirm")
# pyi_args.append("--noconsole")

pyi_args.extend(("--name", APP_NAME))
pyi_args.extend(("--collect-data", "jieba"))


if __name__ == "__main__":
    dist_path = Path("dist") / APP_NAME
    keep_folders = ("user", "tmp")

    for f in keep_folders:
        if (dist_path / f).exists():
            shutil.move(dist_path / f, dist_path.parent / f)

    PyInstaller.__main__.run(pyi_args)
    # PyInstaller.building.build_main.main(None, "cnpy.spec")  # type: ignore

    for f in Path().glob("*.md"):
        shutil.copy(f, dist_path)

        d = f.with_suffix("")
        d = d.with_name("_" + d.name)
        if d.is_dir():
            shutil.copytree(d, dist_path / d.name)

    shutil.copy("LICENSE", dist_path)

    shutil.copytree("assets", dist_path / "assets")
    shutil.copytree("web", dist_path / "web")

    zip_name = APP_NAME
    if VERSION:
        zip_name += "-" + VERSION

    zip_name += "-" + platform.system()

    (dist_path / "VERSION.txt").write_text(zip_name)

    shutil.make_archive(str(dist_path.parent / zip_name), "zip", dist_path)

    for f in keep_folders:
        if (dist_path.parent / f).exists():
            shutil.move(dist_path.parent / f, dist_path / f)
