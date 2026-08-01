"""Create the owner-only alpha schema."""

from alembic import op
from bodyos_api.models import Base

revision = "0001_owner_alpha"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
