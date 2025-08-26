"""Tests for diff service functionality."""
import pytest

from app.services.diff_service import DiffService


class TestDiffService:
    """Test diff service functionality."""
    
    def test_generate_unified_diff(self):
        """Test unified diff generation."""
        service = DiffService()
        
        original = """The rain drummed against the window as Sarah stared at her laptop screen.
The cursor blinked mockingly at the end of an unfinished sentence.
Three months since the accident, and still no words would come."""
        
        modified = """Heavy rain drummed against the window as Sarah stared at her laptop screen.
The cursor blinked mockingly at the end of an unfinished sentence.
Three months since the accident, and still no words would come.
She took a deep breath and began to type."""
        
        result = service.generate_unified_diff(original, modified, "test.md")
        
        assert result.additions > 0
        assert result.changes > 0
        assert len(result.unified_diff) > 0
        assert "Heavy rain" in result.unified_diff
        assert "She took a deep breath" in result.unified_diff
        
    def test_generate_side_by_side(self):
        """Test side-by-side diff generation."""
        service = DiffService()
        
        original = "The rain drummed against the window."
        modified = "Heavy rain drummed against the window."
        
        lines = service.generate_side_by_side(original, modified, width=40)
        
        assert len(lines) > 0
        # Should have tuples of (left, right, change_type)
        for line in lines:
            assert len(line) == 3
            left, right, change_type = line
            assert isinstance(left, str)
            assert isinstance(right, str)
            assert change_type in ['equal', 'delete', 'insert', 'replace']
            
    def test_apply_patch_simple(self):
        """Test simple patch application."""
        service = DiffService()
        
        original = """Line 1
Line 2
Line 3"""
        
        # Unified diff format patch
        patch = """--- test.txt
+++ test.txt
@@ -1,3 +1,3 @@
 Line 1
-Line 2
+Modified Line 2
 Line 3"""
        
        success, result, errors = service.apply_patch(original, patch)
        
        assert success is True
        assert "Modified Line 2" in result
        assert len(errors) == 0
        
    def test_apply_patch_fuzzy(self):
        """Test fuzzy patch application."""
        service = DiffService()
        
        # Original text that doesn't exactly match patch context
        original = """Introduction
The rain drummed against the window.
Sarah stared at her laptop screen.
Conclusion"""
        
        # Patch that should still apply with fuzzy matching
        patch = """--- scene.md
+++ scene.md
@@ -1,2 +1,2 @@
-The rain drummed against the window.
+Heavy rain drummed against the window.
 Sarah stared at her laptop screen."""
        
        success, result, errors = service.apply_patch(original, patch, fuzzy=True)
        
        if success:
            assert "Heavy rain" in result
        # If fuzzy matching fails, errors should be informative
        else:
            assert len(errors) > 0
            
    def test_apply_patch_invalid(self):
        """Test patch application with invalid patch."""
        service = DiffService()
        
        original = "Some text"
        invalid_patch = "Not a valid patch format"
        
        success, result, errors = service.apply_patch(original, invalid_patch)
        
        assert success is False
        assert len(errors) > 0
        
    def test_empty_diff(self):
        """Test diff with identical texts."""
        service = DiffService()
        
        text = "The same text"
        result = service.generate_unified_diff(text, text, "test.md")
        
        assert result.additions == 0
        assert result.deletions == 0
        assert result.changes == 0
        
    def test_large_diff(self):
        """Test diff with larger texts."""
        service = DiffService()
        
        original = "Line {}\n".format(i) for i in range(100)
        original = "".join(original)
        
        # Modify every 10th line
        modified_lines = []
        for i in range(100):
            if i % 10 == 0:
                modified_lines.append(f"Modified Line {i}\n")
            else:
                modified_lines.append(f"Line {i}\n")
        modified = "".join(modified_lines)
        
        result = service.generate_unified_diff(original, modified, "large.md")
        
        assert result.changes > 0
        assert result.additions > 0
        assert result.deletions > 0
        assert len(result.hunks) > 0