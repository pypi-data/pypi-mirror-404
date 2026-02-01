import tomllib
from dataclasses import dataclass
from pathlib import Path

import adaptix


@dataclass
class AssetsConfig:
    src: list[str]
    res: list[str]
    manifest: str


@dataclass
class BuildConfig:
    output_dir: str
    bootclasspath: list[str]
    build_cmd: list[str] | None = None
    preverify_cmd: list[str] | None = None
    package_cmd: list[str] | None = None


@dataclass
class LibConfig:
    glob: str
    include: bool


@dataclass
class ProjectConfig:
    name: str
    assets: AssetsConfig
    build: BuildConfig
    libs: dict[str, LibConfig]


def load_config(config_path: Path) -> ProjectConfig:
    dict_conf = tomllib.loads(config_path.read_text())
    return adaptix.load(dict_conf, ProjectConfig)
