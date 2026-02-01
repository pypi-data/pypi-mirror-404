# coding: utf-8

import os
import click
from codebrick.brick import Brick
from codebrick.rich_console import rich_console

current_dir = os.path.dirname(os.path.abspath(__file__))
bricks_dir = os.path.join(current_dir, 'bricks')


@click.group()
def cli():
    """Codebrick CLI."""
    pass


@cli.command()
@click.argument('brick_name')
@click.argument('output', required=False)
def create(brick_name, output):
    """运行指定名称的 brick。"""
    brick = Brick.from_name(brick_name)
    brick.create_file(output)
    click.echo(f"Brick {brick_name} created successfully!")


@cli.command()
def ls():
    """列出所有可用的 brick。"""
    bricks = [[f, os.path.join(bricks_dir, f)] for f in os.listdir(bricks_dir) if not f.startswith('.') and not f.startswith('__')]
    rich_console.table.print_green(bricks, title="Bricks List", columns=["Name", "Path"])


if __name__ == "__main__":
    cli()
