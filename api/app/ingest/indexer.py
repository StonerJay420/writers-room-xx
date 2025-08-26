"""Document indexing and ingestion pipeline."""
import os
import re
import yaml
from pathlib import Path
from typing import List, Dict, Tuple, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import hashlib
import json

from ..models import Scene, SceneEmbedding
from ..db import get_write_session


def discover_files(paths: List[str]) -> List[Path]:
    """Discover markdown files in the given paths."""
    discovered_files = []
    
    for path_str in paths:
        path = Path(path_str)
        if not path.exists():
            continue
            
        if path.is_file() and path.suffix == '.md':
            discovered_files.append(path)
        elif path.is_dir():
            # Recursively find all .md files
            discovered_files.extend(path.glob('**/*.md'))
    
    return discovered_files


def parse_scene(path: Path) -> Tuple[Dict[str, Any], str]:
    """Parse a scene file and extract metadata and content."""
    content = path.read_text(encoding='utf-8')
    
    # Initialize metadata
    meta = {
        'text_path': str(path),
        'chapter': 1,
        'order_in_chapter': 1,
        'pov': None,
        'location': None,
        'beats_json': None,
        'links_json': None
    }
    
    # Try to extract chapter number from path
    # Pattern: ch01, ch02, chapter1, chapter_1, etc.
    path_str = str(path)
    chapter_match = re.search(r'ch(?:apter)?[_-]?(\d+)', path_str, re.IGNORECASE)
    if chapter_match:
        meta['chapter'] = int(chapter_match.group(1))
    
    # Try to extract scene number
    scene_match = re.search(r's(?:cene)?[_-]?(\d+)', path_str, re.IGNORECASE)
    if scene_match:
        meta['order_in_chapter'] = int(scene_match.group(1))
    
    # Check for YAML front matter
    if content.startswith('---'):
        try:
            # Split on the second '---'
            parts = content.split('---', 2)
            if len(parts) >= 3:
                yaml_content = parts[1]
                text_content = parts[2].strip()
                
                # Parse YAML
                front_matter = yaml.safe_load(yaml_content) or {}
                
                # Update metadata from front matter
                if 'chapter' in front_matter:
                    meta['chapter'] = int(front_matter['chapter'])
                if 'scene' in front_matter:
                    meta['order_in_chapter'] = int(front_matter['scene'])
                if 'pov' in front_matter:
                    meta['pov'] = str(front_matter['pov'])
                if 'location' in front_matter:
                    meta['location'] = str(front_matter['location'])
                if 'beats' in front_matter:
                    meta['beats_json'] = front_matter['beats']
                if 'links' in front_matter:
                    meta['links_json'] = front_matter['links']
                
                content = text_content
        except Exception as e:
            print(f"Error parsing front matter in {path}: {e}")
    
    # Generate scene ID
    scene_id = f"ch{meta['chapter']:02d}_s{meta['order_in_chapter']:02d}"
    meta['id'] = scene_id
    
    return meta, content


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Split text into overlapping chunks for embedding."""
    chunks = []
    words = text.split()
    
    if len(words) <= chunk_size:
        return [text]
    
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunks.append(' '.join(chunk_words))
        
        # Move start forward with overlap
        start += chunk_size - overlap
        
        # Break if we've processed all words
        if end >= len(words):
            break
    
    return chunks


def generate_embedding_stub(text: str) -> List[float]:
    """Generate a stub embedding (will be replaced with actual embeddings later)."""
    # For now, generate a deterministic fake embedding based on text hash
    text_hash = hashlib.md5(text.encode()).hexdigest()
    # Convert hash to 384 floats between -1 and 1
    embedding = []
    for i in range(0, len(text_hash), 2):
        hex_val = text_hash[i:i+2]
        # Convert hex to float in range [-1, 1]
        val = (int(hex_val, 16) - 128) / 128.0
        embedding.append(val)
    
    # Pad to 384 dimensions
    while len(embedding) < 384:
        embedding.append(0.0)
    
    return embedding[:384]


def upsert_scene_chunks(db: Session, scene_id: str, text: str) -> int:
    """Create or update scene embedding chunks."""
    # Delete existing chunks for this scene
    db.query(SceneEmbedding).filter(SceneEmbedding.scene_id == scene_id).delete()
    
    # Create new chunks
    chunks = chunk_text(text)
    chunk_count = 0
    
    for i, chunk in enumerate(chunks):
        embedding = SceneEmbedding(
            scene_id=scene_id,
            chunk_no=i,
            content=chunk,
            embedding=generate_embedding_stub(chunk),
            meta={'chunk_size': len(chunk.split())}
        )
        db.add(embedding)
        chunk_count += 1
    
    return chunk_count


def index_files(paths: List[str], reindex: bool = False) -> Dict[str, int]:
    """Index files into the database."""
    results = {
        'indexed_docs': 0,
        'scenes': 0,
        'chunks': 0,
        'errors': 0
    }
    
    # Discover files
    files = discover_files(paths)
    results['indexed_docs'] = len(files)
    print(f"Found {len(files)} files to index: {[str(f) for f in files]}")
    
    # Process each file
    with next(get_write_session()) as db:
        for file_path in files:
            try:
                # Parse scene
                meta, content = parse_scene(file_path)
                scene_id = meta['id']
                
                # Check if scene exists
                existing_scene = db.query(Scene).filter(Scene.id == scene_id).first()
                
                if existing_scene and not reindex:
                    print(f"Scene {scene_id} already indexed, skipping")
                    continue
                
                # Create or update scene
                if existing_scene:
                    # Update existing scene
                    for key, value in meta.items():
                        if key != 'id':
                            setattr(existing_scene, key, value)
                    existing_scene.updated_at = datetime.utcnow()
                else:
                    # Create new scene
                    scene = Scene(**meta)
                    db.add(scene)
                    results['scenes'] += 1
                
                # Create embedding chunks
                chunk_count = upsert_scene_chunks(db, scene_id, content)
                results['chunks'] += chunk_count
                
                print(f"Indexed scene {scene_id} with {chunk_count} chunks")
                
            except Exception as e:
                print(f"Error indexing {file_path}: {e}")
                results['errors'] += 1
                continue
        
        # Commit all changes
        db.commit()
    
    return results