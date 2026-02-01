"""Exception and error handling tests for ProjectScanner.

Tests error scenarios including:
- File I/O errors (OSError, PermissionError)
- Syntax errors in Python AST parsing
- Unicode decode errors
- Missing/invalid paths
- Empty/corrupt files

Copyright 2025 Smart AI Memory, LLC
Licensed under Fair Source 0.9
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

from empathy_os.project_index.models import FileCategory
from empathy_os.project_index.scanner import ProjectScanner


class TestProjectScannerFileIOErrors:
    """Test file I/O error handling."""

    def test_analyze_file_handles_stat_error(self):
        """Test _analyze_file handles OSError when getting file stats."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = ProjectScanner(tmpdir)
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("def foo(): pass")

            # Mock stat to raise OSError
            with patch.object(Path, "stat", side_effect=OSError("Permission denied")):
                record = scanner._analyze_file(test_file)

                # Should still create record with None last_modified
                assert record is not None
                assert record.last_modified is None

    def test_analyze_code_metrics_handles_read_error(self):
        """Test _analyze_code_metrics handles OSError when reading file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = ProjectScanner(tmpdir)
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("def foo(): pass")

            # Mock read_text to raise OSError
            with patch.object(Path, "read_text", side_effect=OSError("Cannot read file")):
                metrics = scanner._analyze_code_metrics(test_file, "python")

                # Should return empty metrics
                assert metrics["lines_of_code"] == 0
                assert metrics["complexity"] == 0.0

    def test_analyze_code_metrics_handles_unicode_error(self):
        """Test _analyze_code_metrics handles Unicode decode errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = ProjectScanner(tmpdir)
            test_file = Path(tmpdir) / "binary.py"
            # Write binary content
            test_file.write_bytes(b"\x80\x81\x82\x83")

            # Should handle encoding errors gracefully (errors="ignore")
            metrics = scanner._analyze_code_metrics(test_file, "python")

            # Should return metrics without crashing
            assert isinstance(metrics, dict)
            assert "lines_of_code" in metrics

    def test_analyze_file_handles_test_file_stat_error(self):
        """Test _analyze_file handles OSError when getting test file stats."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = ProjectScanner(tmpdir)
            src_file = Path(tmpdir) / "core.py"
            test_file = Path(tmpdir) / "test_core.py"
            src_file.write_text("def core(): pass")
            test_file.write_text("def test_core(): pass")

            # Build test mapping
            files = scanner._discover_files()
            scanner._build_test_mapping(files)

            # Delete test file to cause stat error
            test_file.unlink()

            record = scanner._analyze_file(src_file)

            # Should have test file path but None last_modified
            # (test file exists in mapping but not on disk)
            assert record.test_file_path is not None
            assert record.tests_last_modified is None

    def test_determine_test_requirement_handles_read_error(self):
        """Test _determine_test_requirement handles read errors for __init__.py."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = ProjectScanner(tmpdir)
            init_file = Path(tmpdir) / "src" / "__init__.py"
            init_file.parent.mkdir()
            init_file.write_text("# init")

            # Mock read_text to raise OSError
            with patch.object(Path, "read_text", side_effect=OSError("Read error")):
                result = scanner._determine_test_requirement(init_file, FileCategory.SOURCE)

                # Should return REQUIRED (doesn't crash)
                assert result is not None

    def test_scan_handles_permission_errors(self):
        """Test scan handles permission errors gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = ProjectScanner(tmpdir)
            test_file = Path(tmpdir) / "restricted.py"
            test_file.write_text("def secret(): pass")

            # Mock file operations to raise PermissionError
            original_stat = Path.stat

            def stat_mock(self):
                if "restricted" in str(self):
                    raise PermissionError("Access denied")
                return original_stat(self)

            with patch.object(Path, "stat", side_effect=stat_mock, autospec=True):
                records, summary = scanner.scan()

                # Should complete without crashing
                assert isinstance(records, list)
                assert isinstance(summary, object)


class TestProjectScannerPythonASTErrors:
    """Test Python AST parsing error handling."""

    def test_analyze_code_metrics_handles_syntax_error(self):
        """Test _analyze_code_metrics handles SyntaxError in Python parsing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = ProjectScanner(tmpdir)
            bad_file = Path(tmpdir) / "syntax_error.py"
            # Write invalid Python syntax
            bad_file.write_text("def foo(\n    incomplete function")

            metrics = scanner._analyze_code_metrics(bad_file, "python")

            # Should return metrics without docstrings/type hints
            assert metrics["lines_of_code"] > 0  # Still counts lines
            assert metrics["has_docstrings"] is False
            assert metrics["has_type_hints"] is False
            assert metrics["complexity"] == 0.0

    def test_analyze_file_with_malformed_python(self):
        """Test full file analysis with malformed Python code."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = ProjectScanner(tmpdir)
            bad_file = Path(tmpdir) / "broken.py"
            bad_file.write_text("class Incomplete:")  # Missing body

            records, summary = scanner.scan()

            # Should create record for the file
            broken_record = next((r for r in records if "broken.py" in r.path), None)
            assert broken_record is not None
            assert broken_record.language == "python"

    def test_analyze_python_ast_empty_file(self):
        """Test analyzing AST of empty Python file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = ProjectScanner(tmpdir)
            empty_file = Path(tmpdir) / "empty.py"
            empty_file.write_text("")

            metrics = scanner._analyze_code_metrics(empty_file, "python")

            # Should handle empty file gracefully
            assert metrics["lines_of_code"] == 0
            assert metrics["has_docstrings"] is False


class TestProjectScannerInvalidPaths:
    """Test handling of invalid or missing paths."""

    def test_scanner_with_nonexistent_project_root(self):
        """Test scanner initialization with non-existent project root."""
        scanner = ProjectScanner("/nonexistent/path/12345")

        # Scanner should initialize (validation happens on scan)
        assert scanner.project_root == Path("/nonexistent/path/12345")

    def test_scan_nonexistent_directory(self):
        """Test scanning non-existent directory."""
        scanner = ProjectScanner("/nonexistent/directory")

        # os.walk doesn't fail on non-existent paths, it returns empty
        # But other operations might fail
        records, summary = scanner.scan()

        # Should return empty results
        assert records == []
        assert summary.total_files == 0

    def test_discover_files_with_broken_symlinks(self):
        """Test _discover_files handles broken symlinks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = ProjectScanner(tmpdir)
            # Create broken symlink
            link_path = Path(tmpdir) / "broken_link"
            link_path.symlink_to("/nonexistent/target")

            # Should handle broken symlinks without crashing
            files = scanner._discover_files()

            # Symlink might be included or excluded, but shouldn't crash
            assert isinstance(files, list)

    def test_analyze_file_with_deleted_file(self):
        """Test _analyze_file when file is deleted during scan."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = ProjectScanner(tmpdir)
            temp_file = Path(tmpdir) / "deleted.py"
            temp_file.write_text("def temp(): pass")

            # Delete file before analyzing
            temp_file.unlink()

            # Mock relative_to to not fail
            with patch.object(Path, "relative_to", return_value=Path("deleted.py")):
                # Should handle missing file gracefully
                record = scanner._analyze_file(temp_file)

                # Record should be created but with minimal data
                assert record.last_modified is None


class TestProjectScannerEmptyAndCorruptFiles:
    """Test handling of empty and corrupt files."""

    def test_analyze_empty_python_file(self):
        """Test analyzing completely empty Python file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = ProjectScanner(tmpdir)
            empty = Path(tmpdir) / "empty.py"
            empty.write_text("")

            records, summary = scanner.scan()

            empty_record = next((r for r in records if "empty.py" in r.path), None)
            assert empty_record is not None
            assert empty_record.lines_of_code == 0

    def test_analyze_whitespace_only_file(self):
        """Test analyzing file with only whitespace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = ProjectScanner(tmpdir)
            whitespace = Path(tmpdir) / "whitespace.py"
            whitespace.write_text("   \n\n\t\t\n   ")

            metrics = scanner._analyze_code_metrics(whitespace, "python")

            # Should count as 0 lines (comments/whitespace filtered)
            assert metrics["lines_of_code"] == 0

    def test_analyze_binary_file_as_python(self):
        """Test analyzing binary file misidentified as Python."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = ProjectScanner(tmpdir)
            binary = Path(tmpdir) / "binary.py"
            binary.write_bytes(b"\x00\x01\x02\x03\x04")

            # ast.parse will raise ValueError on null bytes
            # The scanner should handle this gracefully
            metrics = scanner._analyze_code_metrics(binary, "python")

            # Should return basic metrics (lines counted, but AST parsing failed)
            assert isinstance(metrics, dict)
            assert metrics["has_docstrings"] is False
            assert metrics["complexity"] == 0.0

    def test_analyze_file_with_null_bytes(self):
        """Test analyzing file containing null bytes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = ProjectScanner(tmpdir)
            null_bytes = Path(tmpdir) / "null.py"
            null_bytes.write_text("def foo():\x00 pass")

            # ast.parse raises ValueError on null bytes
            # Scanner handles this in try/except
            metrics = scanner._analyze_code_metrics(null_bytes, "python")

            # Should return basic metrics without AST analysis
            assert isinstance(metrics, dict)
            assert metrics["complexity"] == 0.0


class TestProjectScannerEdgeCases:
    """Test edge cases in scanner logic."""

    def test_build_test_mapping_with_circular_references(self):
        """Test _build_test_mapping with unusual file patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = ProjectScanner(tmpdir)
            # Create confusing names
            (Path(tmpdir) / "test_test.py").write_text("# test of test")
            (Path(tmpdir) / "test.py").write_text("# main")

            files = scanner._discover_files()
            scanner._build_test_mapping(files)

            # Should handle without crashing
            assert isinstance(scanner._test_file_map, dict)

    def test_scan_with_deeply_nested_directories(self):
        """Test scan with very deep directory nesting."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = ProjectScanner(tmpdir)
            # Create deep nesting
            deep_path = Path(tmpdir)
            for i in range(50):  # 50 levels deep
                deep_path = deep_path / f"level{i}"
            deep_path.mkdir(parents=True)
            (deep_path / "deep.py").write_text("# deep file")

            records, summary = scanner.scan()

            # Should handle deep nesting
            assert len(records) > 0

    def test_analyze_file_with_very_long_lines(self):
        """Test analyzing file with very long lines (>2000 chars)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = ProjectScanner(tmpdir)
            long_line = Path(tmpdir) / "long.py"
            long_line.write_text("x = '" + "a" * 5000 + "'")

            metrics = scanner._analyze_code_metrics(long_line, "python")

            # Should handle without crashing
            assert metrics["lines_of_code"] > 0

    def test_matches_glob_pattern_with_special_characters(self):
        """Test _matches_glob_pattern with special characters in path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = ProjectScanner(tmpdir)
            # Test various edge cases
            assert scanner._matches_glob_pattern(Path("test.py"), "*.py")
            assert scanner._matches_glob_pattern(Path("a/b/c.py"), "**/*.py")
            assert not scanner._matches_glob_pattern(Path("test.py"), "*.js")

    def test_scan_with_maximum_file_count(self):
        """Test scan with many files (stress test)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = ProjectScanner(tmpdir)
            # Create many files
            for i in range(100):
                (Path(tmpdir) / f"file{i}.py").write_text(f"# File {i}")

            records, summary = scanner.scan()

            # Should handle many files
            assert summary.total_files == 100

    def test_analyze_dependencies_with_no_imports(self):
        """Test _analyze_dependencies when no files have imports."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = ProjectScanner(tmpdir)
            (Path(tmpdir) / "standalone.py").write_text("x = 1")

            records, summary = scanner.scan()

            # Should complete without errors
            assert all(r.imported_by_count == 0 for r in records)

    def test_calculate_impact_scores_with_zero_values(self):
        """Test _calculate_impact_scores with all-zero metrics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = ProjectScanner(tmpdir)
            (Path(tmpdir) / "minimal.py").write_text("")

            records, summary = scanner.scan()

            # Should calculate scores without division errors
            for record in records:
                assert record.impact_score >= 0.0
