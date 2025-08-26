"""Diff generation and patch application service."""
import difflib
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import re


@dataclass
class DiffResult:
    """Result of a diff operation."""
    unified_diff: str
    additions: int
    deletions: int
    changes: int
    hunks: List[Dict[str, Any]]


class DiffService:
    """Service for generating diffs and applying patches."""
    
    def __init__(self):
        self.context_lines = 3
    
    def generate_unified_diff(
        self,
        original: str,
        modified: str,
        filename: str = "scene.txt",
        label_a: str = "original",
        label_b: str = "modified"
    ) -> DiffResult:
        """Generate a unified diff between two texts."""
        
        original_lines = original.splitlines(keepends=True)
        modified_lines = modified.splitlines(keepends=True)
        
        # Generate unified diff
        diff_lines = list(difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile=f"{label_a}/{filename}",
            tofile=f"{label_b}/{filename}",
            n=self.context_lines,
            lineterm=""
        ))
        
        # Parse diff to extract statistics
        additions = 0
        deletions = 0
        hunks = []
        current_hunk = None
        
        for line in diff_lines:
            if line.startswith("+++") or line.startswith("---"):
                continue
            elif line.startswith("@@"):
                # Parse hunk header
                match = re.match(r"@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@(.*)", line)
                if match:
                    current_hunk = {
                        "old_start": int(match.group(1)),
                        "old_lines": int(match.group(2)) if match.group(2) else 1,
                        "new_start": int(match.group(3)),
                        "new_lines": int(match.group(4)) if match.group(4) else 1,
                        "context": match.group(5).strip(),
                        "changes": []
                    }
                    hunks.append(current_hunk)
            elif line.startswith("+") and not line.startswith("+++"):
                additions += 1
                if current_hunk:
                    current_hunk["changes"].append({"type": "add", "line": line[1:]})
            elif line.startswith("-") and not line.startswith("---"):
                deletions += 1
                if current_hunk:
                    current_hunk["changes"].append({"type": "delete", "line": line[1:]})
            elif current_hunk and line.startswith(" "):
                current_hunk["changes"].append({"type": "context", "line": line[1:]})
        
        return DiffResult(
            unified_diff="".join(diff_lines),
            additions=additions,
            deletions=deletions,
            changes=additions + deletions,
            hunks=hunks
        )
    
    def apply_patch(
        self,
        original: str,
        patch: str,
        fuzzy: bool = True
    ) -> Tuple[bool, str, List[str]]:
        """Apply a patch to original text.
        
        Returns:
            Tuple of (success, patched_text, errors)
        """
        
        errors = []
        
        # Parse patch into hunks
        hunks = self._parse_patch(patch)
        
        if not hunks:
            errors.append("No valid hunks found in patch")
            return False, original, errors
        
        # Split original into lines
        original_lines = original.splitlines(keepends=True)
        
        # Apply hunks in reverse order to maintain line numbers
        for hunk in reversed(hunks):
            success, error = self._apply_hunk(original_lines, hunk, fuzzy)
            if not success:
                errors.append(error)
        
        # Join lines back
        result = "".join(original_lines)
        
        return len(errors) == 0, result, errors
    
    def _parse_patch(self, patch: str) -> List[Dict[str, Any]]:
        """Parse a unified diff patch into hunks."""
        
        hunks = []
        lines = patch.splitlines()
        current_hunk = None
        
        for i, line in enumerate(lines):
            if line.startswith("@@"):
                # Parse hunk header
                match = re.match(r"@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@", line)
                if match:
                    current_hunk = {
                        "old_start": int(match.group(1)) - 1,  # Convert to 0-based
                        "old_lines": int(match.group(2)) if match.group(2) else 1,
                        "new_start": int(match.group(3)) - 1,
                        "new_lines": int(match.group(4)) if match.group(4) else 1,
                        "lines": []
                    }
                    hunks.append(current_hunk)
            elif current_hunk is not None:
                if line.startswith("+"):
                    current_hunk["lines"].append(("add", line[1:]))
                elif line.startswith("-"):
                    current_hunk["lines"].append(("delete", line[1:]))
                elif line.startswith(" "):
                    current_hunk["lines"].append(("context", line[1:]))
        
        return hunks
    
    def _apply_hunk(
        self,
        lines: List[str],
        hunk: Dict[str, Any],
        fuzzy: bool
    ) -> Tuple[bool, Optional[str]]:
        """Apply a single hunk to lines."""
        
        start = hunk["old_start"]
        
        # If fuzzy matching, try to find the best position
        if fuzzy:
            best_pos = self._find_best_position(lines, hunk, start)
            if best_pos is not None:
                start = best_pos
            else:
                return False, f"Could not find matching context for hunk at line {start + 1}"
        
        # Apply the hunk
        new_lines = []
        old_pos = 0
        
        for action, content in hunk["lines"]:
            if action == "delete":
                # Skip the line in original
                old_pos += 1
            elif action == "add":
                # Add new line
                new_lines.append(content)
            else:  # context
                # Keep the line
                if start + old_pos < len(lines):
                    new_lines.append(lines[start + old_pos])
                old_pos += 1
        
        # Replace the lines
        del lines[start:start + hunk["old_lines"]]
        for i, line in enumerate(new_lines):
            lines.insert(start + i, line)
        
        return True, None
    
    def _find_best_position(
        self,
        lines: List[str],
        hunk: Dict[str, Any],
        hint: int
    ) -> Optional[int]:
        """Find the best position to apply a hunk using fuzzy matching."""
        
        # Extract context lines from hunk
        context_lines = []
        for action, content in hunk["lines"]:
            if action in ["context", "delete"]:
                context_lines.append(content.rstrip())
        
        if not context_lines:
            return hint
        
        # Search for best match within a window
        window = 10
        best_score = 0
        best_pos = None
        
        for pos in range(max(0, hint - window), min(len(lines), hint + window)):
            score = 0
            for i, context in enumerate(context_lines):
                if pos + i < len(lines):
                    if lines[pos + i].rstrip() == context:
                        score += 1
            
            if score > best_score:
                best_score = score
                best_pos = pos
        
        # Require at least 50% match
        if best_score >= len(context_lines) * 0.5:
            return best_pos
        
        return None
    
    def generate_side_by_side(
        self,
        original: str,
        modified: str,
        width: int = 80
    ) -> List[Tuple[str, str, str]]:
        """Generate side-by-side diff view.
        
        Returns list of tuples: (left_line, right_line, change_type)
        where change_type is 'add', 'delete', 'modify', or 'equal'
        """
        
        original_lines = original.splitlines()
        modified_lines = modified.splitlines()
        
        # Use SequenceMatcher for better diff
        matcher = difflib.SequenceMatcher(None, original_lines, modified_lines)
        
        result = []
        
        for opcode, a_start, a_end, b_start, b_end in matcher.get_opcodes():
            if opcode == 'equal':
                for i in range(a_end - a_start):
                    left = original_lines[a_start + i][:width]
                    right = modified_lines[b_start + i][:width]
                    result.append((left, right, 'equal'))
            
            elif opcode == 'delete':
                for i in range(a_start, a_end):
                    left = original_lines[i][:width]
                    result.append((left, '', 'delete'))
            
            elif opcode == 'insert':
                for i in range(b_start, b_end):
                    right = modified_lines[i][:width]
                    result.append(('', right, 'add'))
            
            elif opcode == 'replace':
                # Show as side-by-side modification
                for i in range(max(a_end - a_start, b_end - b_start)):
                    left = ''
                    right = ''
                    
                    if a_start + i < a_end:
                        left = original_lines[a_start + i][:width]
                    if b_start + i < b_end:
                        right = modified_lines[b_start + i][:width]
                    
                    result.append((left, right, 'modify'))
        
        return result


# Global diff service instance
diff_service = DiffService()