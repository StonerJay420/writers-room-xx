"""Diff utility functions as specified in Prompt 10."""
import difflib
from typing import List, Optional
from pathlib import Path
from rapidfuzz import fuzz
import logging

logger = logging.getLogger(__name__)


def make_unified_diff(
    original: str, 
    revised: str, 
    filename: str = "file.txt",
    n: int = 3
) -> str:
    """
    Create unified diff between original and revised text.
    
    Args:
        original: Original text content
        revised: Revised text content 
        filename: Name to use in diff header
        n: Number of context lines
        
    Returns:
        Unified diff as string
    """
    original_lines = original.splitlines(keepends=True)
    revised_lines = revised.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        original_lines,
        revised_lines,
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
        n=n
    )
    
    return ''.join(diff)


def apply_patch_to_file(file_path: str, unified_diff: str) -> bool:
    """
    Apply a unified diff patch to a file with fuzzy matching fallback.
    
    Args:
        file_path: Path to file to patch
        unified_diff: Unified diff content
        
    Returns:
        True if patch applied successfully, False otherwise
    """
    try:
        path = Path(file_path)
        
        if not path.exists():
            logger.error(f"File not found: {file_path}")
            return False
        
        original_content = path.read_text(encoding='utf-8')
        
        # Try to apply patch
        patched_content = apply_patch(original_content, unified_diff)
        
        if patched_content is None:
            # Try fuzzy matching as fallback
            logger.warning(f"Exact patch failed, attempting fuzzy match for {file_path}")
            patched_content = apply_patch_fuzzy(original_content, unified_diff)
            
            if patched_content is None:
                logger.error(f"Failed to apply patch to {file_path} even with fuzzy matching")
                return False
        
        # Write patched content
        path.write_text(patched_content, encoding='utf-8')
        logger.info(f"Successfully applied patch to {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error applying patch to {file_path}: {str(e)}")
        return False


def apply_patch(original: str, patch: str) -> Optional[str]:
    """
    Apply a unified diff patch to text.
    
    Args:
        original: Original text
        patch: Unified diff patch
        
    Returns:
        Patched text or None if failed
    """
    original_lines = original.splitlines(keepends=True)
    patch_lines = patch.splitlines(keepends=True)
    
    # Parse patch
    hunks = parse_unified_diff(patch_lines)
    
    if not hunks:
        return None
    
    # Apply hunks
    result_lines = original_lines.copy()
    offset = 0
    
    for hunk in hunks:
        # Adjust line numbers for offset from previous hunks
        start_line = hunk['start_line'] - 1 + offset
        
        # Verify context matches
        if not verify_context(result_lines, start_line, hunk['context_before']):
            return None
        
        # Apply changes
        end_line = start_line + len(hunk['removed_lines'])
        result_lines[start_line:end_line] = hunk['added_lines']
        
        # Update offset for next hunk
        offset += len(hunk['added_lines']) - len(hunk['removed_lines'])
    
    return ''.join(result_lines)


def apply_patch_fuzzy(original: str, patch: str, threshold: int = 80) -> Optional[str]:
    """
    Apply patch with fuzzy matching for slightly drifted content.
    
    Args:
        original: Original text  
        patch: Unified diff patch
        threshold: Minimum similarity score (0-100) for fuzzy matching
        
    Returns:
        Patched text or None if failed
    """
    original_lines = original.splitlines(keepends=True)
    patch_lines = patch.splitlines(keepends=True)
    
    # Parse patch
    hunks = parse_unified_diff(patch_lines)
    
    if not hunks:
        return None
    
    result_lines = original_lines.copy()
    offset = 0
    
    for hunk in hunks:
        # Find best matching position using fuzzy search
        best_pos = find_fuzzy_position(
            result_lines, 
            hunk['context_before'] + hunk['removed_lines'],
            hunk['start_line'] - 1 + offset,
            threshold
        )
        
        if best_pos is None:
            logger.warning(f"Could not find fuzzy match for hunk starting at line {hunk['start_line']}")
            return None
        
        # Apply changes at fuzzy matched position
        end_pos = best_pos + len(hunk['removed_lines'])
        result_lines[best_pos:end_pos] = hunk['added_lines']
        
        # Update offset
        actual_offset = best_pos - (hunk['start_line'] - 1)
        offset = actual_offset + len(hunk['added_lines']) - len(hunk['removed_lines'])
    
    return ''.join(result_lines)


def parse_unified_diff(patch_lines: List[str]) -> List[dict]:
    """Parse unified diff into hunks."""
    hunks = []
    current_hunk = None
    
    for line in patch_lines:
        if line.startswith('@@'):
            # Parse hunk header
            parts = line.split()
            if len(parts) >= 3:
                # Extract line numbers
                old_range = parts[1][1:]  # Remove '-' prefix
                new_range = parts[2][1:]  # Remove '+' prefix
                
                old_start = int(old_range.split(',')[0])
                
                current_hunk = {
                    'start_line': old_start,
                    'context_before': [],
                    'removed_lines': [],
                    'added_lines': [],
                    'context_after': []
                }
                hunks.append(current_hunk)
                
        elif current_hunk:
            if line.startswith('-'):
                current_hunk['removed_lines'].append(line[1:])
            elif line.startswith('+'):
                current_hunk['added_lines'].append(line[1:])
            elif line.startswith(' '):
                # Context line
                if not current_hunk['removed_lines'] and not current_hunk['added_lines']:
                    current_hunk['context_before'].append(line[1:])
                else:
                    current_hunk['context_after'].append(line[1:])
    
    return hunks


def verify_context(lines: List[str], start_line: int, context: List[str]) -> bool:
    """Verify that context lines match at the given position."""
    for i, context_line in enumerate(context):
        line_idx = start_line + i
        if line_idx >= len(lines):
            return False
        if lines[line_idx] != context_line:
            return False
    return True


def find_fuzzy_position(
    lines: List[str], 
    search_lines: List[str], 
    hint_pos: int,
    threshold: int = 80
) -> Optional[int]:
    """
    Find position in lines that fuzzy matches search_lines.
    
    Args:
        lines: Haystack lines to search in
        search_lines: Needle lines to find
        hint_pos: Suggested starting position
        threshold: Minimum similarity score
        
    Returns:
        Best matching position or None
    """
    if not search_lines:
        return hint_pos
    
    search_text = ''.join(search_lines)
    search_len = len(search_lines)
    
    # Search window around hint position
    search_range = 20
    start = max(0, hint_pos - search_range)
    end = min(len(lines), hint_pos + search_range + search_len)
    
    best_score = 0
    best_pos = None
    
    for pos in range(start, end - search_len + 1):
        candidate_text = ''.join(lines[pos:pos + search_len])
        score = fuzz.ratio(search_text, candidate_text)
        
        if score > best_score:
            best_score = score
            best_pos = pos
    
    if best_score >= threshold:
        return best_pos
    
    return None


def create_line_mapping(original: str, revised: str) -> dict:
    """
    Create mapping between line numbers in original and revised text.
    
    Returns:
        Dict mapping original line numbers to revised line numbers
    """
    original_lines = original.splitlines()
    revised_lines = revised.splitlines()
    
    matcher = difflib.SequenceMatcher(None, original_lines, revised_lines)
    mapping = {}
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            for i in range(i2 - i1):
                mapping[i1 + i] = j1 + i
        elif tag == 'replace':
            # Map to closest revised line
            for i in range(i2 - i1):
                if j2 > j1:
                    mapping[i1 + i] = j1 + min(i, j2 - j1 - 1)
    
    return mapping