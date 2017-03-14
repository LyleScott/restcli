import argparse

from restcli.app import App
from restcli.icli import Cmd


def run():
    parser = argparse.ArgumentParser(prog='restcli')

    # Positional arguments
    parser.add_argument('group', nargs='?', default=None)
    parser.add_argument('request', nargs='?', default=None)
    parser.add_argument('attr', nargs='?', default=None)

    # Options
    parser.add_argument('-c', '--collection')
    parser.add_argument('-e', '--env')

    # Flags
    parser.add_argument('-i', '--interactive', action='store_true')
    parser.add_argument('-p', '--inspect', action='store_true')
    parser.add_argument('-s', '--save-env', action='store_true')

    args = parser.parse_args()

    app = App(args.collection, args.env)

    if args.interactive:
        cmd = Cmd(app)
        cmd.cmdloop()
    elif args.inspect:
        app.inspect(args.group, args.request, args.attr)
    else:
        app.run(args.group, args.request)
        if args.save_env:
            app.save_env()
