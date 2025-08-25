import difflib
from typing import List, Dict, Any
import re

class DiffService:
    def generate_unified_diff(self, original: str, modified: str, filename: str = "scene.md") -> str:
        """Generate unified diff between original and modified text"""
        original_lines = original.splitlines(keepends=True)
        modified_lines = modified.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
            lineterm=""
        )
        
        return ''.join(diff)
    
    def apply_suggestions(self, original_text: str, suggestions: List[Dict[str, Any]]) -> str:
        """Apply line editing suggestions to create modified text"""
        lines = original_text.split('\n')
        
        # Sort suggestions by line number in reverse order to avoid index shifting
        sorted_suggestions = sorted(suggestions, key=lambda x: x.get('line_number', 0), reverse=True)
        
        for suggestion in sorted_suggestions:
            line_num = suggestion.get('line_number', 0)
            original = suggestion.get('original', '')
            suggested = suggestion.get('suggested', '')
            
            # Find the line with the original text (fuzzy matching)
            target_line = self._find_matching_line(lines, original, line_num)
            
            if target_line is not None:
                lines[target_line] = lines[target_line].replace(original, suggested)
        
        return '\n'.join(lines)
    
    def _find_matching_line(self, lines: List[str], target_text: str, suggested_line: int) -> int | None:
        """Find the line containing the target text, starting near the suggested line"""
        if not target_text:
            return None
        
        # Start search from suggested line
        search_range = range(max(0, suggested_line - 2), min(len(lines), suggested_line + 3))
        
        for i in search_range:
            if target_text in lines[i]:
                return i
        
        # Fallback: search entire text
        for i, line in enumerate(lines):
            if target_text in line:
                return i
        
        return None
    
    def extract_changes_summary(self, diff_content: str) -> Dict[str, Any]:
        """Extract summary information from a unified diff"""
        lines = diff_content.split('\n')
        
        additions = []
        deletions = []
        changes = 0
        
        for line in lines:
            if line.startswith('+') and not line.startswith('+++'):
                additions.append(line[1:].strip())
                changes += 1
            elif line.startswith('-') and not line.startswith('---'):
                deletions.append(line[1:].strip())
                changes += 1
        
        return {
            "total_changes": changes,
            "additions": len(additions),
            "deletions": len(deletions),
            "added_lines": additions[:5],  # First 5 for preview
            "deleted_lines": deletions[:5]  # First 5 for preview
        }

diff_service = DiffService()
