import glob
from pathlib import Path
import os

from microbuildtool.config import LibConfig


def collect_sources(base: Path, source_globs: list[str]) -> list[Path]:
    sources = []
    for pattern in source_globs:
        sources.extend(
            base / path
            for path in glob.glob(pattern, recursive=True, root_dir=base)
        )
    return sources


def collect_res(base: Path, res_patterns) -> dict[Path, Path]:
    res = {}
    for pattern in res_patterns:
        src, target = pattern.rsplit(":", maxsplit=1)
        files = glob.glob(src, recursive=True, root_dir=base)
        if len(files) == 1 and "*" not in src and "?" not in src:
            res[base / src] = Path(target)
        else:
            pref = os.path.commonpath(files)
            for file in files:
                res[base / file] = Path(file).relative_to(pref)
    return res


def collect_all_libs(
    lib_confs: dict[str, LibConfig],
    base: Path,
) -> list[Path]:
    libs = []
    for conf in lib_confs.values():
        libs.extend(
            base / path
            for path in glob.glob(conf.glob, recursive=True, root_dir=base)
        )
    return libs


def collect_bundled_libs(
    lib_confs: dict[str, LibConfig],
    base: Path,
) -> list[Path]:
    libs = []
    for conf in lib_confs.values():
        if conf.include:
            libs.extend(
                base / path
                for path in glob.glob(conf.glob, recursive=True, root_dir=base)
            )
    return libs


def collect_bootclasspath(boot_cp: list[str], base: Path) -> list[Path]:
    libs = []
    for cp in boot_cp:
        libs.extend(
            base / path for path in glob.glob(cp, recursive=True, root_dir=base)
        )
    return libs
