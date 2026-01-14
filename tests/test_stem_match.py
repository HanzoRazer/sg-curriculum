"""
Micro test harness for CHANGELOG stem-matching logic.

Validates:
- ✅ added-lines only (deleted lines don't count)
- ✅ token-safe matching (no partials)
- ✅ case sensitivity
"""
from __future__ import annotations

import re

import pytest


def stem_mentioned(text: str, stem: str) -> bool:
    """Check if stem appears as a whole token (not partial match)."""
    pat = re.compile(rf"(?<![A-Za-z0-9_]){re.escape(stem)}(?![A-Za-z0-9_])")
    return pat.search(text) is not None


def extract_added_lines(diff: str) -> str:
    """Extract only added lines from a unified diff (like the CI gate does)."""
    return "\n".join(
        ln[1:] for ln in diff.splitlines()
        if ln.startswith("+") and not ln.startswith("+++ ")
    )


# Simulated git diff of contracts/CHANGELOG.md
SAMPLE_DIFF = """
@@ -1,6 +1,9 @@
 ## Unreleased

-- cam_policy: legacy wording cleanup
+- cam_policy: tightened voltage range validation
+- viewer_pack_v1: clarified unit semantics
+- Notes: reviewed smart_guitar_toolbox_telemetry_v1

+Added documentation for qa_core

"""


class TestStemMatching:
    """Test token-safe stem matching."""

    @pytest.fixture
    def added_lines(self) -> str:
        return extract_added_lines(SAMPLE_DIFF)

    def test_exact_stem_matches(self, added_lines: str):
        """Exact stems in added lines should match."""
        assert stem_mentioned(added_lines, "cam_policy")
        assert stem_mentioned(added_lines, "viewer_pack_v1")
        assert stem_mentioned(added_lines, "smart_guitar_toolbox_telemetry_v1")
        assert stem_mentioned(added_lines, "qa_core")

    def test_extended_stem_no_match(self, added_lines: str):
        """Partial/extended stems should NOT match (token boundary)."""
        # cam_policy exists, but cam_policy_extended does not
        assert not stem_mentioned(added_lines, "cam_policy_extended")

    def test_case_sensitive(self, added_lines: str):
        """Case must match exactly."""
        assert stem_mentioned(added_lines, "viewer_pack_v1")
        assert not stem_mentioned(added_lines, "Viewer_Pack_v1")
        assert not stem_mentioned(added_lines, "VIEWER_PACK_V1")

    def test_deleted_lines_ignored(self):
        """Deleted lines (starting with -) should not satisfy governance."""
        # The diff has "- cam_policy: legacy wording cleanup" as deleted
        # If we only had the deleted line, stem should NOT be found
        diff_delete_only = """
@@ -1,3 +1,2 @@
 ## Unreleased

-- cam_policy: legacy wording cleanup
"""
        added = extract_added_lines(diff_delete_only)
        assert not stem_mentioned(added, "cam_policy")

    def test_stem_in_prose_works(self):
        """Stems embedded in markdown prose should match."""
        text = "Added documentation for `session_record_v1` schema."
        assert stem_mentioned(text, "session_record_v1")

        text2 = "- assignment_v1: new field added"
        assert stem_mentioned(text2, "assignment_v1")

    def test_stem_at_boundaries(self):
        """Stems at start/end of line should match."""
        assert stem_mentioned("session_record_v1: updated", "session_record_v1")
        assert stem_mentioned("updated session_record_v1", "session_record_v1")
        assert stem_mentioned("session_record_v1", "session_record_v1")

    def test_stem_with_punctuation(self):
        """Punctuation should not block matches."""
        assert stem_mentioned("(session_record_v1)", "session_record_v1")
        assert stem_mentioned("[session_record_v1]", "session_record_v1")
        assert stem_mentioned("session_record_v1.", "session_record_v1")
        assert stem_mentioned("session_record_v1,", "session_record_v1")


class TestExtractAddedLines:
    """Test diff parsing."""

    def test_extracts_plus_lines_only(self):
        diff = """\
@@ -1,2 +1,3 @@
 unchanged
-deleted
+added
"""
        added = extract_added_lines(diff)
        assert "added" in added
        assert "deleted" not in added
        assert "unchanged" not in added

    def test_skips_diff_header(self):
        diff = """\
--- a/file.txt
+++ b/file.txt
@@ -1 +1 @@
-old
+new
"""
        added = extract_added_lines(diff)
        assert "b/file.txt" not in added
        assert "new" in added
