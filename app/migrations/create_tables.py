import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Base, engine, init_db
from alembic import op
import sqlalchemy as sa
from datetime import datetime

def upgrade():
    """Create all tables."""
    init_db()
    print("Database tables created successfully!")

def downgrade():
    """Drop all tables."""
    Base.metadata.drop_all(bind=engine)
    print("Database tables dropped successfully!")

if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in ['upgrade', 'downgrade']:
        print("Usage: python create_tables.py [upgrade|downgrade]")
        sys.exit(1)
    
    if sys.argv[1] == 'upgrade':
        upgrade()
    else:
        downgrade() 