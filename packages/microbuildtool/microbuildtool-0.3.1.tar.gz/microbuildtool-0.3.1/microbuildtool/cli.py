import os
import sys
from pathlib import Path

import click
import requests

from microbuildtool.build import (
    compile_classes, package_jar,
    DEFAULT_BUILD_CMD, preverify, DEFAULT_PREVERIFY_CMD, BuildError,
    DEFAULT_JAR_CMD,
)
from microbuildtool.click_utils import err_echo, ok_echo
from microbuildtool.collect import (
    collect_all_libs,
    collect_bundled_libs,
    collect_res,
    collect_sources, collect_bootclasspath,
)
from microbuildtool.config import load_config


@click.command()
def mbt():
    click.echo("MicroBuildTool v0.3.0")


@click.group()
def mbt_group():
    """MBT CLI."""


@mbt_group.command("build")
@click.option("-f", "--projectfile", type=click.STRING, default="mbt-project.toml")
def build_command(projectfile):
    cfg = load_config(Path(projectfile))
    base = Path(projectfile).resolve().parent
    click.echo("Collecting sources")
    sources = collect_sources(base, cfg.assets.src)
    click.echo(f"Collected {len(sources)} sources")
    click.echo("Collecting libraries")
    all_libs = collect_all_libs(cfg.libs, base)
    bundled_libs = collect_bundled_libs(cfg.libs, base)
    click.echo(
        f"Collected {len(all_libs)} libraries, "
        f"out of them {len(bundled_libs)} bundled"
    )
    boot_cp = collect_bootclasspath(cfg.build.bootclasspath, base)
    click.echo(f"Using {boot_cp} as boot classpath")
    try:
        compile_classes(
            cfg.build.build_cmd or DEFAULT_BUILD_CMD,
            {key: val for key, val in os.environ.items()},
            sources,
            all_libs,
            bundled_libs,
            boot_cp,
            (base / cfg.build.output_dir).resolve(),
        )
        preverify(
            cfg.build.preverify_cmd or DEFAULT_PREVERIFY_CMD,
            {key: val for key, val in os.environ.items()},
            (base / cfg.build.output_dir).resolve(),
            boot_cp,
        )
    except BuildError as e:
        err_echo(f"Failed: {e}")


@mbt_group.command("jar")
@click.argument(
    "output_jar",
    type=click.Path(),
)
@click.option("-f", "--projectfile", type=click.STRING, default="mbt-project.toml")
def jar_command(output_jar, projectfile):
    cfg = load_config(Path(projectfile))
    base = Path(projectfile).resolve().parent
    resources = collect_res(base, cfg.assets.res)
    package_jar(
        cfg.build.package_cmd or DEFAULT_JAR_CMD,
        {key: val for key, val in os.environ.items()},
        resources,
        (base / cfg.build.output_dir).resolve(),
        Path(output_jar),
        (base / cfg.assets.manifest).resolve()
    )


@mbt_group.command("get-proguard")
@click.argument("version", type=click.STRING, default="4.4")
def get_proguard_command(version):
    response = requests.get(
        f"https://repo1.maven.org/maven2/net/sf/proguard/proguard/"
        f"{version}/proguard-{version}.jar"
    )
    Path("proguard.jar").write_bytes(response.content)
    ok_echo(f"Successfully downloaded ProGuard v{version} to proguard.jar.")


def main():
    if len(sys.argv) > 1:
        mbt_group()
    else:
        mbt()


if __name__ == '__main__':
    main()
