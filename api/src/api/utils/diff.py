"""Diff utilities for patch creation and application."""
import difflib
from pathlib import Path
from typing import List
import re
import logging

try:
    from rapidfuzz import fuzz
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False
    fuzz = None

logger = logging.getLogger(__name__)


def make_unified_diff(original: str, revised: str, filename: str) -> str:
    """
    Create a unified diff between two text strings.
    
    Args:
        original: Original text
        revised: Revised text
        filename: Filename for diff header
        
    Returns:
        Unified diff string
    """
    original_lines = original.splitlines(keepends=True)
    revised_lines = revised.splitlines(keepends=True)
    
    # Ensure lines end with newlines for proper diff formatting
    if original_lines and not original_lines[-1].endswith('\n'):
        original_lines[-1] += '\n'
    if revised_lines and not revised_lines[-1].endswith('\n'):
        revised_lines[-1] += '\n'
    
    diff_lines = list(difflib.unified_diff(
        original_lines,
        revised_lines,
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
        lineterm=""
    ))
    
    return "\n".join(diff_lines) + ("\n" if diff_lines else "")


def apply_patch_to_file(file_path: str, unified_diff: str) -> bool:
    """
    Apply a unified diff patch to a file.
    
    Args:
        file_path: Path to the file to patch
        unified_diff: Unified diff string
        
    Returns:
        True if patch applied successfully, False otherwise
    """
    try:
        path = Path(file_path)
        
        if not path.exists():
            logger.error(f"File does not exist: {file_path}")
            return False
        
        # Read current file content
        with open(path, 'r', encoding='utf-8') as f:
            original_lines = f.readlines()
        
        # Parse the diff
        parsed_hunks = _parse_unified_diff(unified_diff)
        if not parsed_hunks:
            logger.warning("No valid hunks found in diff")
            return False
        
        # Apply hunks in reverse order to preserve line numbers
        modified_lines = original_lines[:]
        
        for hunk in reversed(parsed_hunks):
            if not _apply_hunk(modified_lines, hunk):
                logger.error(f"Failed to apply hunk at line {hunk['start_line']}")
                return False
        
        # Verify the result makes sense
        if len(modified_lines) < 0:
            logger.error("Patch resulted in negative line count")
            return False
        
        # Write the modified content back to file
        with open(path, 'w', encoding='utf-8') as f:
            f.writelines(modified_lines)
        
        logger.info(f"Successfully applied patch to {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error applying patch to {file_path}: {e}")
        return False


def _parse_unified_diff(unified_diff: str) -> List[dict]:
    """Parse unified diff into structured hunks."""
    lines = unified_diff.split('\n')
    hunks = []
    current_hunk = None
    
    for line in lines:
        if line.startswith('@@'):
            # Parse hunk header: @@ -start,count +start,count @@
            match = re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', line)
            if match:
                old_start = int(match.group(1))
                old_count = int(match.group(2)) if match.group(2) else 1
                new_start = int(match.group(3))
                new_count = int(match.group(4)) if match.group(4) else 1
                
                current_hunk = {
                    'start_line': old_start,
                    'old_count': old_count,
                    'new_start': new_start,
                    'new_count': new_count,
                    'changes': []
                }
                hunks.append(current_hunk)
        elif current_hunk and (line.startswith(' ') or line.startswith('-') or line.startswith('+')):
            current_hunk['changes'].append(line)
    
    return hunks


def _apply_hunk(lines: List[str], hunk: dict) -> bool:
    """Apply a single hunk to the lines."""
    try:
        start_idx = hunk['start_line'] - 1  # Convert to 0-indexed
        
        # Verify the context matches
        original_idx = start_idx
        changes = hunk['changes']
        
        # First pass: verify all context and deletion lines match
        temp_idx = original_idx
        for change in changes:
            if change.startswith(' ') or change.startswith('-'):
                expected_line = change[1:] + '\n'
                if temp_idx >= len(lines):
                    logger.error(f"Hunk extends beyond file end: {temp_idx} >= {len(lines)}")
                    return False
                
                actual_line = lines[temp_idx]
                if change.startswith(' ') and expected_line != actual_line:
                    # Try fuzzy matching for context lines with rapidfuzz
                    if not _lines_match_fuzzy(expected_line, actual_line):
                        logger.error(f"Context mismatch at line {temp_idx + 1}")
                        return False
                elif change.startswith('-') and expected_line != actual_line:
                    # Allow fuzzy matching for deletion lines too
                    if not _lines_match_fuzzy(expected_line, actual_line):
                        logger.error(f"Deletion line mismatch at line {temp_idx + 1}")
                        return False
                
                temp_idx += 1
        
        # Second pass: apply the changes
        new_lines = []
        change_idx = 0
        original_idx = start_idx
        
        for change in changes:
            if change.startswith(' '):
                # Context line - keep as is
                new_lines.append(lines[original_idx])
                original_idx += 1
            elif change.startswith('-'):
                # Deletion - skip the original line
                original_idx += 1
            elif change.startswith('+'):
                # Addition - add the new line
                new_lines.append(change[1:] + '\n')
        
        # Replace the section in the original lines
        end_idx = original_idx
        lines[start_idx:end_idx] = new_lines
        
        return True
        
    except Exception as e:
        logger.error(f"Error applying hunk: {e}")
        return False


def _lines_match_fuzzy(expected: str, actual: str, threshold: float = 0.85) -> bool:
    """
    Check if two lines match using fuzzy string matching.
    
    Args:
        expected: Expected line content
        actual: Actual line content  
        threshold: Similarity threshold (0.0 to 1.0)
        
    Returns:
        True if lines match closely enough
    """
    # First try exact match
    if expected == actual:
        return True
    
    # Try stripping whitespace
    if expected.strip() == actual.strip():
        return True
    
    # Use rapidfuzz if available for fuzzy matching
    if RAPIDFUZZ_AVAILABLE and fuzz:
        similarity = fuzz.ratio(expected.strip(), actual.strip()) / 100.0
        return similarity >= threshold
    
    # Fallback: simple character-based similarity
    expected_clean = expected.strip()
    actual_clean = actual.strip()
    
    if not expected_clean and not actual_clean:
        return True
    if not expected_clean or not actual_clean:
        return False
    
    # Simple Levenshtein-like comparison
    max_len = max(len(expected_clean), len(actual_clean))
    min_len = min(len(expected_clean), len(actual_clean))
    
    # If length difference is too large, not a match
    if max_len > min_len * 1.5:
        return False
    
    # Count matching characters in similar positions
    matches = sum(1 for i in range(min_len) if expected_clean[i] == actual_clean[i])
    similarity = matches / max_len
    
    return similarity >= threshold