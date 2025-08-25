"""Initial migration

Revision ID: 49190b0134b5
Revises: 
Create Date: 2025-08-25 17:45:38.296166

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '49190b0134b5'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create vector extension if using PostgreSQL (will be skipped for SQLite)
    try:
        op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    except:
        pass  # SQLite doesn't support extensions
    
    # Create scenes table
    op.create_table('scenes',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('chapter', sa.Integer(), nullable=False),
        sa.Column('order_in_chapter', sa.Integer(), nullable=False),
        sa.Column('pov', sa.Text(), nullable=True),
        sa.Column('location', sa.Text(), nullable=True),
        sa.Column('text_path', sa.Text(), nullable=True),
        sa.Column('beats_json', sa.JSON(), nullable=True),
        sa.Column('links_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scenes_chapter'), 'scenes', ['chapter'], unique=False)
    
    # Create characters table
    op.create_table('characters',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('voice_tags_json', sa.JSON(), nullable=True),
        sa.Column('preferred_words_json', sa.JSON(), nullable=True),
        sa.Column('banned_words_json', sa.JSON(), nullable=True),
        sa.Column('arc_flags_json', sa.JSON(), nullable=True),
        sa.Column('canon_quotes_json', sa.JSON(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create jobs table
    op.create_table('jobs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('scene_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('agents_json', sa.JSON(), nullable=True),
        sa.Column('result_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['scene_id'], ['scenes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_jobs_scene_id'), 'jobs', ['scene_id'], unique=False)
    
    # Create artifacts table
    op.create_table('artifacts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('scene_id', sa.String(), nullable=False),
        sa.Column('variant', sa.String(), nullable=False),
        sa.Column('diff_key', sa.Text(), nullable=True),
        sa.Column('metrics_before', sa.JSON(), nullable=True),
        sa.Column('metrics_after', sa.JSON(), nullable=True),
        sa.Column('receipts_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['scene_id'], ['scenes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_artifacts_scene_id'), 'artifacts', ['scene_id'], unique=False)
    
    # Create scene_embeddings table
    op.create_table('scene_embeddings',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('scene_id', sa.String(), nullable=False),
        sa.Column('chunk_no', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('embedding', sa.JSON(), nullable=True),  # JSON for SQLite, Vector for PostgreSQL
        sa.Column('meta', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['scene_id'], ['scenes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scene_embeddings_scene_id'), 'scene_embeddings', ['scene_id'], unique=False)
    op.create_index('ix_scene_embeddings_scene_chunk', 'scene_embeddings', ['scene_id', 'chunk_no'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index('ix_scene_embeddings_scene_chunk', table_name='scene_embeddings')
    op.drop_index(op.f('ix_scene_embeddings_scene_id'), table_name='scene_embeddings')
    op.drop_table('scene_embeddings')
    op.drop_index(op.f('ix_artifacts_scene_id'), table_name='artifacts')
    op.drop_table('artifacts')
    op.drop_index(op.f('ix_jobs_scene_id'), table_name='jobs')
    op.drop_table('jobs')
    op.drop_table('characters')
    op.drop_index(op.f('ix_scenes_chapter'), table_name='scenes')
    op.drop_table('scenes')