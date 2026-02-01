import click


def err_echo(text: str) -> None:
    click.echo(
        click.style(text, fg="red"),
        err=True,
        color=True
    )


def ok_echo(text: str) -> None:
    click.echo(
        click.style(text, fg="green"),
        color=True
    )
