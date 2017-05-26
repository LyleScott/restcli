import click
from click_repl import register_repl

from restcli.app import App
from restcli.exceptions import (
    CollectionError,
    EnvError,
    InputError,
    LibError,
    NotFoundError,
    expect
)

pass_app = click.make_pass_decorator(App)


@click.group()
@click.option('-c', '--collection', envvar='RESTCLI_COLLECTION', required=True,
              type=click.Path(exists=True, dir_okay=False),
              help='Collection file.')
@click.option('-e', '--env', envvar='RESTCLI_ENV',
              type=click.Path(exists=True, dir_okay=False),
              help='Environment file.')
@click.option('-s/-S', '--save/--no-save', envvar='RESTCLI_AUTOSAVE',
              default=False,
              help='Save Environment to disk after changes.')
@click.pass_context
def cli(ctx, collection, env, save):
    with expect(CollectionError, EnvError, LibError):
        ctx.obj = App(collection, env, autosave=save)


@cli.command(help='Run a Request.')
@click.argument('group')
@click.argument('request')
@click.option('-o', '--override', multiple=True,
              help='Add "key:val" pairs that shadow the Environment.')
@pass_app
def run(app, group, request, override):
    with expect(InputError, NotFoundError):
        output = app.run(group, request, *override)
    click.echo(output)


@cli.command(help='View a Group, Request, or Request Attribute.')
@click.argument('group')
@click.argument('request', required=False)
@click.argument('attr', required=False)
@pass_app
def view(app, group, request, attr):
    with expect(NotFoundError):
        output = app.view(group, request, attr)
    click.echo(output)


@cli.command(help='View or set Environment variables.'
                  ' If no args are given, print the current environment.'
                  ' Otherwise, change the Environment via the given args.')
@click.argument('args', nargs=-1)
@pass_app
def env(app, args):
    if args:
        app.autosave = True
        output = app.set_env(*args)
    else:
        output = app.show_env()
    click.echo(output)


register_repl(cli)
