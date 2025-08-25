from typing import List, Dict, Any
import re

class LoreService:
    def __init__(self):
        self.character_registry = {}
        self.location_registry = {}
        self.terminology_registry = {}
    
    def build_registries(self, codex_content: List[str]):
        """Build registries from codex content"""
        self.character_registry = {}
        self.location_registry = {}
        self.terminology_registry = {}
        
        for content in codex_content:
            self._extract_entities(content)
    
    def _extract_entities(self, content: str):
        """Extract characters, locations, and terminology from codex content"""
        lines = content.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            # Detect section headers
            if line.startswith('# '):
                current_section = line[2:].lower()
            elif line.startswith('## '):
                subsection = line[3:].strip()
                
                # Extract character information
                if (current_section and 'character' in current_section) or 'char' in subsection.lower():
                    self._extract_character_info(line, content)
                
                # Extract location information
                elif (current_section and 'location' in current_section) or 'place' in subsection.lower():
                    self._extract_location_info(line, content)
                
                # Extract terminology
                elif (current_section and 'system' in current_section) or 'tech' in subsection.lower():
                    self._extract_terminology(line, content)
    
    def _extract_character_info(self, header: str, content: str):
        """Extract character information"""
        name = header.replace('##', '').strip()
        if name and len(name) < 50:  # Reasonable name length
            self.character_registry[name.lower()] = {
                "name": name,
                "source_content": content[:200]  # First 200 chars as context
            }
    
    def _extract_location_info(self, header: str, content: str):
        """Extract location information"""
        location = header.replace('##', '').strip()
        if location and len(location) < 50:
            self.location_registry[location.lower()] = {
                "name": location,
                "source_content": content[:200]
            }
    
    def _extract_terminology(self, header: str, content: str):
        """Extract terminology"""
        term = header.replace('##', '').strip()
        if term and len(term) < 50:
            self.terminology_registry[term.lower()] = {
                "term": term,
                "source_content": content[:200]
            }
    
    def validate_scene_lore(self, scene_text: str) -> Dict[str, Any]:
        """Validate scene against lore registries"""
        results = {
            "character_references": [],
            "location_references": [],
            "terminology_references": [],
            "potential_issues": []
        }
        
        scene_lower = scene_text.lower()
        
        # Check character references
        for char_key, char_info in self.character_registry.items():
            if char_key in scene_lower:
                results["character_references"].append({
                    "name": char_info["name"],
                    "context": char_info["source_content"]
                })
        
        # Check location references
        for loc_key, loc_info in self.location_registry.items():
            if loc_key in scene_lower:
                results["location_references"].append({
                    "name": loc_info["name"],
                    "context": loc_info["source_content"]
                })
        
        # Check terminology
        for term_key, term_info in self.terminology_registry.items():
            if term_key in scene_lower:
                results["terminology_references"].append({
                    "term": term_info["term"],
                    "context": term_info["source_content"]
                })
        
        return results
    
    def get_canon_receipts(self, scene_text: str) -> List[Dict[str, Any]]:
        """Generate canon receipts for lore elements in scene"""
        receipts = []
        validation = self.validate_scene_lore(scene_text)
        
        # Add receipts for each reference found
        for char_ref in validation["character_references"]:
            receipts.append({
                "type": "character",
                "element": char_ref["name"],
                "source": "codex/characters.md",
                "context": char_ref["context"]
            })
        
        for loc_ref in validation["location_references"]:
            receipts.append({
                "type": "location",
                "element": loc_ref["name"],
                "source": "codex/locations.md",
                "context": loc_ref["context"]
            })
        
        for term_ref in validation["terminology_references"]:
            receipts.append({
                "type": "terminology",
                "element": term_ref["term"],
                "source": "codex/systems.md",
                "context": term_ref["context"]
            })
        
        return receipts

lore_service = LoreService()
