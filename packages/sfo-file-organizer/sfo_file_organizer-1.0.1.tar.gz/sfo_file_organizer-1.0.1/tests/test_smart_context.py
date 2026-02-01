
import pytest
from pathlib import Path
import shutil
import time
from app_config import DETAILED_CATEGORIES, FILE_CATEGORIES
from organizer import detect_folder_context, get_detailed_category, organize_files

@pytest.fixture
def smart_test_env(tmp_path):
    # Setup directories
    src = tmp_path / "src"
    dest = tmp_path / "dest"
    src.mkdir()
    dest.mkdir()
    return src, dest

def test_detect_documents_context(smart_test_env):
    src, _ = smart_test_env
    # Create mostly docs
    (src / "doc1.pdf").touch()
    (src / "doc2.docx").touch()
    (src / "doc3.txt").touch()
    (src / "img1.jpg").touch()
    
    assert detect_folder_context(src) == "Documents"

def test_detect_images_context(smart_test_env):
    src, _ = smart_test_env
    # Create mostly images
    (src / "img1.jpg").touch()
    (src / "img2.png").touch()
    (src / "img3.gif").touch()
    (src / "doc1.pdf").touch()
    
    assert detect_folder_context(src) == "Images"

def test_organize_documents_smart(smart_test_env):
    src, dest = smart_test_env
    # Create docs
    (src / "report.pdf").touch()
    (src / "notes.txt").touch()
    
    # Run smart organization
    stats = organize_files(str(src), str(dest), smart_context=True)
    
    # Verify subfolders
    assert (dest / "PDFs" / "report.pdf").exists()
    assert (dest / "Text Files" / "notes.txt").exists()
    # Should NOT be in generic "Documents"
    assert not (dest / "Documents" / "report.pdf").exists()

def test_organize_images_smart(smart_test_env):
    src, dest = smart_test_env
    # Create images
    img = src / "photo.jpg"
    img.touch()
    # Set time to 2023
    # (timestamp for 2023-01-01)
    os.utime(img, (1672531200, 1672531200))
    
    # Run smart organization
    organize_files(str(src), str(dest), smart_context=True)
    
    # Verify year folder
    assert (dest / "2023" / "photo.jpg").exists()

import os
