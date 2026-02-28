import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from src.tools.repo_tools import clone_repository, list_files, read_file, run_git_log, grep_search, cleanup_temp_dirs, _active_temp_dirs

def test_clone_repository_success():
    with patch("subprocess.run") as mock_run:
        # Avoid creating actual temp dirs that linger if not cleaned up properly in test, but the tool creates them
        # We can just let it create one and we will clean it up
        repo_url = "https://github.com/example/repo.git"
        result = clone_repository.invoke({"repo_url": repo_url})
        
        mock_run.assert_called_once()
        assert not result.startswith("Error")
        cleanup_temp_dirs()
        assert len(_active_temp_dirs) == 0

def test_clone_repository_failure():
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = Exception("Git not found")
        result = clone_repository.invoke({"repo_url": "test"})
        
        assert result.startswith("Error cloning repository")
        cleanup_temp_dirs()

def test_list_files(tmp_path):
    # Create some mock files
    (tmp_path / "file1.txt").touch()
    (tmp_path / "dir1").mkdir()
    (tmp_path / "dir1" / "file2.py").touch()
    
    result = list_files.invoke({"repo_path": str(tmp_path)})
    
    assert "file1.txt" in result
    assert "dir1/file2.py" in result

def test_read_file(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, Courtroom!")
    
    result = read_file.invoke({"repo_path": str(tmp_path), "file_path": "test.txt"})
    
    assert result == "Hello, Courtroom!"

def test_read_file_not_found(tmp_path):
    result = read_file.invoke({"repo_path": str(tmp_path), "file_path": "missing.txt"})
    assert result.startswith("Error: File")

def test_run_git_log_success():
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.stdout = "a1b2c3d Initial commit\n"
        mock_run.return_value = mock_result
        
        result = run_git_log.invoke({"repo_path": "/fake/path"})
        assert result == "a1b2c3d Initial commit\n"

def test_grep_search_success():
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.stdout = "file.py: def test():\n"
        mock_run.return_value = mock_result
        
        result = grep_search.invoke({"repo_path": "/fake/path", "pattern": "def"})
        assert result == "file.py: def test():\n"
