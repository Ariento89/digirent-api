"""create first and last agg functions

Revision ID: e004cf216542
Revises: 1ffa3186eb5d
Create Date: 2021-01-10 07:37:14.974525

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "e004cf216542"
down_revision = "1ffa3186eb5d"
branch_labels = None
depends_on = None


def upgrade():
    create_first_func = """
        CREATE OR REPLACE FUNCTION public.first_func ( anyelement, anyelement )
        RETURNS anyelement LANGUAGE sql IMMUTABLE STRICT PARALLEL SAFE AS $$
        SELECT $1;
        $$;
    """

    create_last_func = """
        CREATE OR REPLACE FUNCTION public.last_func ( anyelement, anyelement )
        RETURNS anyelement LANGUAGE sql IMMUTABLE STRICT PARALLEL SAFE AS $$
        SELECT $2;
        $$;
    """

    create_first_agg = """
        CREATE AGGREGATE public.first (
            sfunc    = public.first_func,
            basetype = anyelement,
            stype    = anyelement,
            "parallel" = safe
        );
    """

    create_last_agg = """
        CREATE AGGREGATE public.last (
            sfunc    = public.last_func,
            basetype = anyelement,
            stype    = anyelement,
            "parallel" = safe
        );
    """

    conn = op.get_bind()
    conn.execute(create_first_func)
    conn.execute(create_first_agg)
    conn.execute(create_last_func)
    conn.execute(create_last_agg)


def downgrade():
    drop_first_func = "DROP FUNCTION public.first_func ( anyelement, anyelement );"
    drop_last_func = "DROP FUNCTION public.last_func ( anyelement, anyelement );"
    drop_first_agg = "DROP AGGREGATE public.first(anyelement);"
    drop_last_agg = "DROP AGGREGATE public.last(anyelement);"
    conn = op.get_bind()
    conn.execute(drop_first_agg)
    conn.execute(drop_last_agg)
    conn.execute(drop_first_func)
    conn.execute(drop_last_func)
