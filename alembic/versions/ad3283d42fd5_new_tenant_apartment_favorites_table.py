"""new tenant apartment favorites table

Revision ID: ad3283d42fd5
Revises: 8f52c492d908
Create Date: 2021-06-19 07:27:31.731648

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy_utils import UUIDType

# revision identifiers, used by Alembic.
revision = "ad3283d42fd5"
down_revision = "8f52c492d908"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "favorite_apartments",
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column(
            "user_id",
            UUIDType(binary=False),
            nullable=False,
        ),
        sa.Column(
            "apartment_id",
            UUIDType(binary=False),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["apartment_id"], ["apartments.id"], onupdate="CASCADE", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], onupdate="CASCADE", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("user_id", "apartment_id"),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("favorite_apartments")
    # ### end Alembic commands ###