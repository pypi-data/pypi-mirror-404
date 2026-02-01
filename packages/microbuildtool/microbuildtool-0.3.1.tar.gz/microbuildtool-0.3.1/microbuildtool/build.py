import os
import shutil
import subprocess
import zipfile
from pathlib import Path

import click

from microbuildtool.click_utils import err_echo, ok_echo
from microbuildtool.command_builder import build_cmd

DEFAULT_BUILD_CMD = [
    "$MBT_JAVAC",
    "-source", "1.3",
    "-target", "1.1",
    "-d", "$RAW_BUILD_DIR",
    "-bootclasspath", "$BOOTCLASSPATH",
    "-cp", "$CLASSPATH",
    "@$SOURCES_FILE"
]
DEFAULT_PREVERIFY_CMD = [
    "$MBT_JRE", "-jar", "$PROGUARD",
    "-microedition",
    "-injars", "$RAW_BUILD_DIR",
    "-outjars", "$PREVERIFIED_BUILD_DIR",
    "-dontshrink",
    "-dontobfuscate",
    "-dontoptimize",
    "-dontnote",
    "-dontwarn",
    "-forceprocessing"
]
DEFAULT_JAR_CMD = [
    "$MBT_JAR",
    "cvfm",
    "$OUTPUT_JAR",
    "$MANIFEST",
    "-C", "$PREVERIFIED_BUILD_DIR",
    "."
]


class BuildError(Exception): ...


def compile_classes(
    cmd: list[str],
    namespace: dict[str, str],
    sources: list[Path],
    libs: list[Path],
    bundled_libs: list[Path],
    boot_libs: list[Path],
    build_dir: Path,
):
    click.echo("Compiling classes")
    build_dir.mkdir(parents=True, exist_ok=True)

    if not sources:
        err_echo("No source files found.")
        return False

    classpath_str = os.pathsep.join(str(p.absolute()) for p in libs)
    bootclasspath_str = os.pathsep.join(str(p.absolute()) for p in boot_libs)

    (build_dir / "sources").write_text(
        "\n".join(
            str(src.absolute()) for src in sources
        )
    )
    (build_dir / "raw").mkdir(parents=True, exist_ok=True)

    cmd = build_cmd(
        cmd, namespace | {
            "RAW_BUILD_DIR": str(build_dir / "raw"),
            "BOOTCLASSPATH": bootclasspath_str,
            "CLASSPATH": classpath_str,
            "SOURCES_FILE": str((build_dir / "sources").absolute()),
        }
    )

    click.echo(f"Compiling {len(sources)} source files")
    click.echo(f"Full command: {'\n'.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
        ok_echo("Compilation successful.")
    except subprocess.CalledProcessError as e:
        raise BuildError(
            f"Compilation failed with exit code {e.returncode}"
        ) from e
    else:
        for lib_jar in bundled_libs:
            click.echo(f"Merging library: {os.path.basename(lib_jar)}")
            try:
                with zipfile.ZipFile(lib_jar, 'r') as zip_ref:
                    for member in zip_ref.namelist():
                        if member.startswith("META-INF"):
                            continue
                        zip_ref.extract(member, build_dir)
            except Exception as e:
                raise BuildError(
                    f"Error extracting {lib_jar}: {e}"
                ) from e
        ok_echo(f"Successfully merged {len(bundled_libs)} libraries.")


def preverify(
    cmd: list[str],
    namespace: dict[str, str],
    build_dir: Path,
    boot_libs: list[Path],
):
    click.echo("Preverifying classes")
    preverified_dir = build_dir / "preverified"
    if preverified_dir.exists():
        click.echo("Removing existing preverified classes")
        shutil.rmtree(preverified_dir)
    preverified_dir.mkdir(parents=True, exist_ok=True)
    bootclasspath_str = os.pathsep.join(str(p.absolute()) for p in boot_libs)
    cmd = build_cmd(
        cmd, {"PROGUARD": "proguard.jar"} | namespace | {
            "RAW_BUILD_DIR": str(build_dir / "raw"),
            "PREVERIFIED_BUILD_DIR": str(preverified_dir),
            "BOOTCLASSPATH": bootclasspath_str,
        }
    )
    try:
        subprocess.run(cmd, check=True)
        ok_echo("Preverification successful.")
    except subprocess.CalledProcessError as e:
        raise BuildError(
            f"Failed to preverify classes: exit code {e.returncode}"
        ) from e


def package_jar(
    cmd: list[str],
    namespace: dict[str, str],
    resources_map: dict[Path, Path],
    build_dir: Path,
    output_jar: Path,
    manifest_file: Path,
):
    preverified_dir = build_dir / "preverified"
    for res_src, res_dst in resources_map.items():
        if res_src.is_file():
            (preverified_dir / res_dst).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(res_src, preverified_dir / res_dst)

    output_jar.parent.mkdir(parents=True, exist_ok=True)

    cmd = build_cmd(
        cmd, namespace | {
            "PREVERIFIED_BUILD_DIR": str(preverified_dir),
            "OUTPUT_JAR": str(output_jar),
            "MANIFEST": str(manifest_file),
        }
    )

    click.echo("Crafting JAR")
    click.echo(f"Bundling {len(resources_map)} resources")
    click.echo(f"Full command: {'\n'.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
        ok_echo(f"JAR created successfully: {output_jar}")
    except subprocess.CalledProcessError as e:
        raise BuildError(
            f"Packaging failed with exit code {e.returncode}"
        ) from e
