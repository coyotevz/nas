# -*- coding: utf-8 -*-

"""
    nas.commands
    ~~~~~~~~~~~~

    :copyright: (c) 2017 by Augusto Roccasalva
    :license: MIT, see LICENSE for more details.
"""

import click

from nas.application import create_app
from nas.models import db

app = create_app()

@app.cli.command()
@click.option('--create-admin-user', is_flag=True)
def initdb(create_admin_user):
    """Creates database tables"""
    db.create_all()
    # from nas.models.product import create_primitive_units
    # create_primitive_units()
    # if create_admin_user:
    #     from nas.models.user import create_admin_user
    #     create_admin_user()


@app.cli.command()
def dropdb():
    """Drops all database tables"""
    if click.confirm("Are you sure ? You will lose all your data!"):
        db.drop_all()


@app.cli.command()
def migrate():
    """Migrate from a database for old application"""
    from nas.utils.migrate import migrate_suppliers, configure_session
    db.create_all()
    session = configure_session(app.config['MIGRATION_DB_URI'])
    migrate_suppliers(session)
