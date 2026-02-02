from . import engine
from .templates.mysql import template_engine


def is_exist(conn, database):
    sql = template_engine.render('mysql_check_database_exists')
    result = engine.select_one(conn, sql, {'database_name': database})
    return result is not None


def create(conn, database, charset='utf8mb4', collation='utf8mb4_unicode_ci', dryrun=False):
    sql = template_engine.render(
        'mysql_create_database',
        database_name=database,
        charset=charset,
        collation=collation)
    engine.execute(conn, sql, dryrun=dryrun)


def drop(conn, database, dryrun=False):
    sql = template_engine.render('mysql_drop_database', database_name=database)
    engine.execute(conn, sql, dryrun=dryrun)


# def grant(conn, database, user, host, privileges='ALL PRIVILEGES'):
#     sql = f'GRANT {privileges} ON {database}.* TO :user'
#     print(sql)
#     engine.execute(conn, sql, {'user': f'{user}@{host}'})


# def create_user(conn, user, host, password):
#     sql = f"CREATE USER IF NOT EXISTS '{user}'@'{host}' IDENTIFIED BY '{password}'"
#     engine.execute(conn, sql)
