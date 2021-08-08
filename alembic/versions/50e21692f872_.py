"""empty message

Revision ID: 50e21692f872
Revises: ad3283d42fd5
Create Date: 2021-08-08 22:07:21.507636

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy_utils import UUIDType, EmailType


# revision identifiers, used by Alembic.
revision = "50e21692f872"
down_revision = "ad3283d42fd5"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "admins",
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("id", UUIDType(binary=False), nullable=False),
        sa.Column("first_name", sa.String(), nullable=False),
        sa.Column("last_name", sa.String(), nullable=False),
        sa.Column("email", EmailType(length=255), nullable=False),
        sa.Column("hashed_password", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("admins")
    # ### end Alembic commands ###
