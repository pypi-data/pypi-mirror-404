"""
Unit tests for rule-based file classification.
"""

import pytest
from rules import classify_by_rules, classify_by_extension, classify_file


class TestClassifyByRules:
    """Tests for keyword-based classification."""
    
    def test_invoice_keyword(self):
        """Files with 'invoice' should be classified as Documents."""
        assert classify_by_rules("invoice_2024.pdf") == "Documents"
        assert classify_by_rules("INVOICE_001.xlsx") == "Documents"
        assert classify_by_rules("my_invoice.jpg") == "Documents"
    
    def test_screenshot_keyword(self):
        """Files with 'screenshot' should be classified as Images."""
        assert classify_by_rules("screenshot_2024.png") == "Images"
        assert classify_by_rules("Screenshot from Chrome.png") == "Images"
    
    def test_video_keyword(self):
        """Files with 'video' should be classified as Videos."""
        assert classify_by_rules("video_tutorial.mp4") == "Videos"
        assert classify_by_rules("my_video.avi") == "Videos"
    
    def test_music_keyword(self):
        """Files with 'music' or 'song' should be classified as Audio."""
        assert classify_by_rules("my_music.mp3") == "Audio"
        assert classify_by_rules("favorite_song.wav") == "Audio"
    
    def test_backup_keyword(self):
        """Files with 'backup' should be classified as Archives."""
        assert classify_by_rules("backup_2024.zip") == "Archives"
        assert classify_by_rules("system_backup.tar") == "Archives"
    
    def test_no_keyword_match(self):
        """Files without matching keywords should return None."""
        assert classify_by_rules("random_file.txt") is None
        assert classify_by_rules("document.pdf") is None
        assert classify_by_rules("vacation.jpg") is None  # 'photo' is a keyword, 'vacation' is not
    
    def test_case_insensitive(self):
        """Keyword matching should be case-insensitive."""
        assert classify_by_rules("INVOICE.pdf") == "Documents"
        assert classify_by_rules("Invoice.PDF") == "Documents"
        assert classify_by_rules("iNvOiCe.pdf") == "Documents"


class TestClassifyByExtension:
    """Tests for extension-based classification."""
    
    def test_image_extensions(self):
        """Image extensions should be classified correctly."""
        assert classify_by_extension(".jpg") == "Images"
        assert classify_by_extension(".PNG") == "Images"
        assert classify_by_extension(".gif") == "Images"
    
    def test_document_extensions(self):
        """Document extensions should be classified correctly."""
        assert classify_by_extension(".pdf") == "Documents"
        assert classify_by_extension(".docx") == "Documents"
        assert classify_by_extension(".txt") == "Documents"
    
    def test_video_extensions(self):
        """Video extensions should be classified correctly."""
        assert classify_by_extension(".mp4") == "Videos"
        assert classify_by_extension(".mkv") == "Videos"
    
    def test_audio_extensions(self):
        """Audio extensions should be classified correctly."""
        assert classify_by_extension(".mp3") == "Audio"
        assert classify_by_extension(".wav") == "Audio"
    
    def test_unknown_extension(self):
        """Unknown extensions should return 'Other'."""
        assert classify_by_extension(".xyz") == "Other"
        assert classify_by_extension(".unknown") == "Other"
        assert classify_by_extension("") == "Other"


class TestClassifyFile:
    """Tests for the main classification function."""
    
    def test_extension_priority(self):
        """Extension should take priority over keywords for known file types."""
        # video_clip.jpg should be Images (extension), not Videos (keyword "clip")
        assert classify_file("video_clip.jpg", ".jpg") == "Images"
        # audio_source.mp4 should be Videos (extension), not Code (keyword "source")
        assert classify_file("audio_source.mp4", ".mp4") == "Videos"
        # coverage_test.png should be Images (extension), not Images (keyword "cover")
        assert classify_file("coverage_test.png", ".png") == "Images"
    
    def test_keywords_for_ambiguous_files(self):
        """Keywords should refine classification for text/unknown files."""
        # invoice.txt should be Documents (keyword refines text file)
        assert classify_file("invoice.txt", ".txt") == "Documents"
        # Unknown extension with keyword should use keyword
        assert classify_file("system_backup.xyz", ".xyz") == "Archives"
    
    def test_fallback_to_extension(self):
        """When no keyword matches, use extension."""
        assert classify_file("vacation.jpg", ".jpg") == "Images"
        assert classify_file("report.pdf", ".pdf") == "Documents"
    
    def test_unknown_file(self):
        """Files with no keyword and unknown extension should be 'Other'."""
        assert classify_file("random.xyz", ".xyz") == "Other"
