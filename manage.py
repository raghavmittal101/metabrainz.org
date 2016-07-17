from __future__ import print_function
from metabrainz import create_app
from metabrainz.model.access_log import AccessLog
from metabrainz.model.utils import init_postgres, create_tables as db_create_tables
from werkzeug.serving import run_simple
import click


application = create_app()

cli = click.Group()


@cli.command()
@click.option("--host", "-h", default="0.0.0.0", show_default=True)
@click.option("--port", "-p", default=8080, show_default=True)
@click.option("--debug", "-d", is_flag=True,
              help="Turns debugging mode on or off. If specified, overrides "
                   "'DEBUG' value in the config file.")
def runserver(host, port, debug=False):
    run_simple(
        hostname=host,
        port=port,
        application=application,
        use_debugger=debug,
        use_reloader=debug,
    )


@cli.command()
def create_db():
    """Create and configure the database."""
    with application.app_context():
        init_postgres(application.config['SQLALCHEMY_DATABASE_URI'])


@cli.command()
def create_tables():
    with application.app_context():
        db_create_tables(application.config['SQLALCHEMY_DATABASE_URI'])


@cli.command()
def cleanup_logs():
    with create_app().app_context():
        AccessLog.remove_old_ip_addr_records()


if __name__ == '__main__':
    cli()
