import json
from logging import getLogger

from . import engine
from .templates.mysql import template_engine

from ..models.schema import Table
from ..models.column import Column

logger = getLogger(__name__)


def is_exist(conn, env: str, table: Table):
    sql = template_engine.render('mysql_check_table_exists')
    result = engine.select_one(conn, sql, {'env': env, 'table_name': table.table_name})
    return result is not None


def drop(conn, env: str, table: Table, dryrun=False):
    sql = template_engine.render('mysql_drop_table', env=env, table_name=table.table_name)
    engine.execute(conn, sql, dryrun=dryrun)


def create(conn, env: str, table: Table, dryrun=False):
    # Use template engine for CREATE TABLE
    sql = template_engine.render('mysql_create_table', env=env, table=table)
    engine.execute(conn, sql, dryrun=dryrun)

    # Create indexes using template engine
    for idx, index in enumerate(table.indexes):
        # Set loop context for template
        loop_context = type('LoopContext', (), {'index0': idx})()
        sql = template_engine.render(
            'mysql_create_index',
            env=env,
            table=table,
            index=index,
            loop=loop_context)
        engine.execute(conn, sql, dryrun=dryrun)


def _col_value(item: dict, column: Column):
    if column.column_name in item:
        if item[column.column_name] is not None and type(item[column.column_name]) is str:
            # 関数定義されている場合には、SQLに関数を埋め込む。
            if '(' in item[column.column_name]:
                return item[column.column_name]
        return f':{column.column_name}'
    # FIXME データ整備ミスとなるので、例外を投げるが、事前チェックが望ましいと思う。
    raise ValueError(f"Column '{column.column_name}' not found in item.")


def _col_conv(values: dict):
    return {
        k: v if not isinstance(v, dict) else json.dumps(v, ensure_ascii=True)
        for k, v in values.items()
    }


def insert(conn, env: str, table: Table, items: list[dict], dryrun=False):
    if len(items) == 0:
        logger.warning(f'No items to insert into {env}.{table.table_name}')
        return
    # Filter out generated columns (expression fields) from INSERT
    insertable_columns = [c for c in table.columns if c.expression is None]

    # Prepare column names and value placeholders
    column_names = [c.column_name for c in insertable_columns]
    value_placeholders = [_col_value(items[0], c) for c in insertable_columns]
    params = [_col_conv(item) for item in items]

    sql = template_engine.render(
        'mysql_insert_into',
        env=env,
        table_name=table.table_name,
        column_names=column_names,
        value_placeholders=value_placeholders
    )
    engine.execute(conn, sql, params, dryrun=dryrun)
    if not dryrun:
        conn.commit()


def backup(conn, env: str, table: Table, ymd: str, dryrun=False):
    sql = template_engine.render(
        'mysql_backup_table',
        env=env,
        table_name=table.table_name,
        ymd=ymd
    )
    engine.execute(conn, sql, dryrun=dryrun)


def restore(conn, env: str, table: Table, ymd: str, dryrun=False):
    sql = template_engine.render(
        'mysql_restore_table',
        env=env,
        table_name=table.table_name,
        ymd=ymd
    )
    engine.execute(conn, sql, dryrun=dryrun)


def restore_update(conn, env: str, table: Table, ymd: str, dryrun=False):
    """Restore data from backup table with REPLACE INTO (update existing records)."""
    sql = template_engine.render(
        'mysql_restore_table_update',
        env=env,
        table_name=table.table_name,
        ymd=ymd
    )
    engine.execute(conn, sql, dryrun=dryrun)


def is_exist_backup(conn, env: str, table: Table, ymd: str):
    sql = template_engine.render('mysql_check_backup_exists')
    backup_table_name = f'bak_{table.table_name}_{ymd}'
    result = engine.select_one(conn, sql, {'env': env, 'backup_table_name': backup_table_name})
    return result is not None


def drop_indexes(conn, env: str, table: Table, dryrun=False):
    """Drop all secondary indexes on a table (excluding primary key)."""
    for idx, index in enumerate(table.indexes):
        index_name = index.index_name or f'{table.table_name}_IX{idx}'

        # Check if index exists
        sql_check = template_engine.render('mysql_check_index_exists')
        result = engine.select_one(conn, sql_check, {
            'env': env,
            'table_name': table.table_name,
            'index_name': index_name
        })

        if result is not None:
            # Drop the index
            sql_drop = template_engine.render(
                'mysql_drop_index',
                env=env,
                table_name=table.table_name,
                index_name=index_name
            )
            engine.execute(conn, sql_drop, dryrun=dryrun)
            logger.info(f'Dropped index {index_name} on {env}.{table.table_name}')


def create_indexes(conn, env: str, table: Table, dryrun=False):
    """Create all secondary indexes on a table."""
    for idx, index in enumerate(table.indexes):
        # Set loop context for template
        loop_context = type('LoopContext', (), {'index0': idx})()
        sql = template_engine.render(
            'mysql_create_index',
            env=env,
            table=table,
            index=index,
            loop=loop_context
        )
        engine.execute(conn, sql, dryrun=dryrun)
        index_name = index.index_name or f'{table.table_name}_IX{idx}'
        logger.info(f'Created index {index_name} on {env}.{table.table_name}')


def recreate_indexes(conn, env: str, table: Table, dryrun=False):
    """Drop and recreate all secondary indexes on a table."""
    logger.info(f'Recreating indexes for {env}.{table.table_name}')
    drop_indexes(conn, env, table, dryrun)
    create_indexes(conn, env, table, dryrun)
