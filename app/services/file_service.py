import os
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
import aiofiles

class FileService:
    def __init__(self, base_path: str = "./data"):
        self.base_path = Path(base_path)
        self.manuscript_path = self.base_path / "manuscript"
        self.codex_path = self.base_path / "codex"
    
    async def discover_files(self, paths: List[str]) -> List[Path]:
        """Discover all markdown files in specified paths"""
        files = []
        for path_str in paths:
            path = Path(path_str)
            if path.exists():
                files.extend(path.rglob("*.md"))
        return files
    
    async def parse_scene(self, file_path: Path) -> Tuple[Dict[str, Any], str]:
        """Parse a scene file and extract metadata and content"""
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            content = await f.read()
        
        # Extract scene ID from path (e.g., ch02/ch02_s03.md -> ch02_s03)
        scene_id = self._extract_scene_id(file_path)
        
        # Extract chapter and order from scene ID
        chapter_match = re.search(r'ch(\d+)', scene_id)
        scene_match = re.search(r's(\d+)', scene_id)
        
        chapter = int(chapter_match.group(1)) if chapter_match else 1
        order = int(scene_match.group(1)) if scene_match else 1
        
        # Basic metadata extraction (could be enhanced with YAML frontmatter)
        metadata = {
            "id": scene_id,
            "chapter": chapter,
            "order_in_chapter": order,
            "text_path": str(file_path),
            "pov": self._extract_pov(content),
            "location": self._extract_location(content),
            "beats_json": self._extract_beats(content),
            "links_json": self._extract_links(content)
        }
        
        return metadata, content
    
    async def read_codex_files(self) -> List[str]:
        """Read all codex files and return their content"""
        codex_files = await self.discover_files([str(self.codex_path)])
        content_list = []
        
        for file_path in codex_files:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                content_list.append(f"# {file_path.name}\n{content}")
        
        return content_list
    
    async def write_scene(self, scene_id: str, content: str) -> bool:
        """Write scene content to file"""
        try:
            # Reconstruct file path from scene ID
            chapter_match = re.search(r'ch(\d+)', scene_id)
            if not chapter_match:
                return False
            
            chapter = chapter_match.group(0)
            file_path = self.manuscript_path / chapter / f"{scene_id}.md"
            
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            
            return True
        except Exception as e:
            print(f"Error writing scene {scene_id}: {e}")
            return False
    
    def _extract_scene_id(self, file_path: Path) -> str:
        """Extract scene ID from file path"""
        # Extract from path like: manuscript/ch02/ch02_s03.md
        parts = file_path.parts
        if len(parts) >= 2:
            chapter_dir = parts[-2]  # ch02
            filename = file_path.stem  # ch02_s03
            if filename.startswith(chapter_dir):
                return filename
        
        # Fallback: use filename without extension
        return file_path.stem
    
    def _extract_pov(self, content: str) -> str:
        """Extract point of view from content (basic heuristic)"""
        lines = content.split('\n')[:5]  # Check first few lines
        text = ' '.join(lines).lower()
        
        if ' i ' in text or text.startswith('i '):
            return "first_person"
        elif ' you ' in text:
            return "second_person"
        else:
            return "third_person"
    
    def _extract_location(self, content: str) -> str:
        """Extract location from content (basic heuristic)"""
        # Look for common location indicators
        lines = content.split('\n')[:10]
        for line in lines:
            if any(word in line.lower() for word in ['undercity', 'sector', 'district', 'station']):
                return line.strip()[:50]  # First location reference
        return "unknown"
    
    def _extract_beats(self, content: str) -> List[str]:
        """Extract story beats from content"""
        # Simple paragraph-based beat extraction
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        return [p[:100] + "..." if len(p) > 100 else p for p in paragraphs[:5]]
    
    def _extract_links(self, content: str) -> List[str]:
        """Extract character and location links from content"""
        links = []
        
        # Look for character mentions (basic pattern matching)
        char_patterns = [r'\b[A-Z][a-z]+\b']  # Capitalized words
        for pattern in char_patterns:
            matches = re.findall(pattern, content)
            for match in set(matches[:5]):  # Limit and deduplicate
                if len(match) > 2:  # Filter out short words
                    links.append(f"char:{match}")
        
        return links

file_service = FileService()
