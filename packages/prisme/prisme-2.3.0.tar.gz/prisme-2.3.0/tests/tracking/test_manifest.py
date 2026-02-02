"""Tests for the file manifest system."""

from __future__ import annotations

from pathlib import Path

from prisme.spec.stack import FileStrategy
from prisme.tracking.manifest import (
    FileManifest,
    ManifestManager,
    TrackedFile,
    hash_content,
)


def test_hash_content():
    """Test content hashing."""
    content1 = "print('hello world')"
    content2 = "print('hello world')"
    content3 = "print('goodbye world')"

    hash1 = hash_content(content1)
    hash2 = hash_content(content2)
    hash3 = hash_content(content3)

    # Same content = same hash
    assert hash1 == hash2

    # Different content = different hash
    assert hash1 != hash3

    # Hash is hex string of expected length (SHA-256 = 64 chars)
    assert len(hash1) == 64
    assert all(c in "0123456789abcdef" for c in hash1)


def test_tracked_file_creation():
    """Test creating a TrackedFile."""
    tracked = TrackedFile(
        path="backend/services/user.py",
        strategy=FileStrategy.GENERATE_ONCE.value,
        content_hash="abc123",
        generated_at="2026-01-23T10:00:00",
        has_hooks=True,
        extends="backend/services/_base/user_base.py",
    )

    assert tracked.path == "backend/services/user.py"
    assert tracked.strategy == FileStrategy.GENERATE_ONCE.value
    assert tracked.content_hash == "abc123"
    assert tracked.has_hooks is True
    assert tracked.extends == "backend/services/_base/user_base.py"


def test_tracked_file_to_dict():
    """Test converting TrackedFile to dictionary."""
    tracked = TrackedFile(
        path="backend/models/user.py",
        strategy=FileStrategy.ALWAYS_OVERWRITE.value,
        content_hash="def456",
        generated_at="2026-01-23T10:00:00",
        has_hooks=False,
    )

    data = tracked.to_dict()

    assert data["strategy"] == FileStrategy.ALWAYS_OVERWRITE.value
    assert data["content_hash"] == "def456"
    assert data["generated_at"] == "2026-01-23T10:00:00"
    assert data["has_hooks"] is False
    assert data["extends"] is None


def test_tracked_file_from_dict():
    """Test creating TrackedFile from dictionary."""
    data = {
        "strategy": FileStrategy.ALWAYS_OVERWRITE.value,
        "content_hash": "ghi789",
        "generated_at": "2026-01-23T10:00:00",
        "has_hooks": True,
        "extends": "base.py",
    }

    tracked = TrackedFile.from_dict("services/user.py", data)

    assert tracked.path == "services/user.py"
    assert tracked.strategy == FileStrategy.ALWAYS_OVERWRITE.value
    assert tracked.content_hash == "ghi789"
    assert tracked.has_hooks is True
    assert tracked.extends == "base.py"


def test_file_manifest_track_file():
    """Test tracking a file in the manifest."""
    manifest = FileManifest()

    tracked = TrackedFile(
        path="backend/models/user.py",
        strategy=FileStrategy.ALWAYS_OVERWRITE.value,
        content_hash="abc123",
        generated_at="2026-01-23T10:00:00",
    )

    manifest.track_file(tracked)

    assert len(manifest.files) == 1
    assert "backend/models/user.py" in manifest.files
    assert manifest.files["backend/models/user.py"] == tracked


def test_file_manifest_get_file():
    """Test retrieving a tracked file."""
    manifest = FileManifest()

    tracked = TrackedFile(
        path="backend/services/user.py",
        strategy=FileStrategy.GENERATE_ONCE.value,
        content_hash="def456",
        generated_at="2026-01-23T10:00:00",
    )

    manifest.track_file(tracked)

    # Get by string path
    result = manifest.get_file("backend/services/user.py")
    assert result == tracked

    # Get by Path object
    result = manifest.get_file(Path("backend/services/user.py"))
    assert result == tracked

    # Get non-existent file
    result = manifest.get_file("nonexistent.py")
    assert result is None


def test_file_manifest_is_modified():
    """Test detecting file modifications."""
    manifest = FileManifest()

    original_content = "print('hello')"
    tracked = TrackedFile(
        path="test.py",
        strategy=FileStrategy.GENERATE_ONCE.value,
        content_hash=hash_content(original_content),
        generated_at="2026-01-23T10:00:00",
    )

    manifest.track_file(tracked)

    # Same content = not modified
    assert not manifest.is_modified("test.py", original_content)

    # Different content = modified
    modified_content = "print('goodbye')"
    assert manifest.is_modified("test.py", modified_content)

    # File not in manifest = not modified
    assert not manifest.is_modified("unknown.py", "any content")


def test_file_manifest_remove_file():
    """Test removing a file from tracking."""
    manifest = FileManifest()

    tracked = TrackedFile(
        path="to_remove.py",
        strategy=FileStrategy.ALWAYS_OVERWRITE.value,
        content_hash="abc",
        generated_at="2026-01-23T10:00:00",
    )

    manifest.track_file(tracked)
    assert len(manifest.files) == 1

    manifest.remove_file("to_remove.py")
    assert len(manifest.files) == 0
    assert manifest.get_file("to_remove.py") is None


def test_file_manifest_to_dict():
    """Test converting manifest to dictionary."""
    manifest = FileManifest(
        version="1.0",
        prisme_version="0.4.0",
        spec_hash="spec123",
    )

    tracked1 = TrackedFile(
        path="file1.py",
        strategy=FileStrategy.ALWAYS_OVERWRITE.value,
        content_hash="hash1",
        generated_at="2026-01-23T10:00:00",
    )

    tracked2 = TrackedFile(
        path="file2.py",
        strategy=FileStrategy.GENERATE_ONCE.value,
        content_hash="hash2",
        generated_at="2026-01-23T10:00:00",
        has_hooks=True,
    )

    manifest.track_file(tracked1)
    manifest.track_file(tracked2)

    data = manifest.to_dict()

    assert data["version"] == "1.0"
    assert data["prisme_version"] == "0.4.0"
    assert data["spec_hash"] == "spec123"
    assert "generated_at" in data
    assert len(data["files"]) == 2
    assert "file1.py" in data["files"]
    assert "file2.py" in data["files"]


def test_file_manifest_from_dict():
    """Test creating manifest from dictionary."""
    data = {
        "version": "1.0",
        "generated_at": "2026-01-23T10:00:00",
        "prisme_version": "0.4.0",
        "spec_hash": "spec456",
        "files": {
            "file1.py": {
                "strategy": FileStrategy.ALWAYS_OVERWRITE.value,
                "content_hash": "hash1",
                "generated_at": "2026-01-23T10:00:00",
                "has_hooks": False,
                "extends": None,
            },
            "file2.py": {
                "strategy": FileStrategy.GENERATE_ONCE.value,
                "content_hash": "hash2",
                "generated_at": "2026-01-23T10:00:00",
                "has_hooks": True,
                "extends": "base.py",
            },
        },
    }

    manifest = FileManifest.from_dict(data)

    assert manifest.version == "1.0"
    assert manifest.prisme_version == "0.4.0"
    assert manifest.spec_hash == "spec456"
    assert len(manifest.files) == 2

    file1 = manifest.get_file("file1.py")
    assert file1 is not None
    assert file1.strategy == FileStrategy.ALWAYS_OVERWRITE.value
    assert file1.has_hooks is False

    file2 = manifest.get_file("file2.py")
    assert file2 is not None
    assert file2.strategy == FileStrategy.GENERATE_ONCE.value
    assert file2.has_hooks is True
    assert file2.extends == "base.py"


def test_manifest_manager_save_and_load(tmp_path: Path):
    """Test saving and loading manifest."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    # Create manifest
    manifest = FileManifest(prisme_version="0.4.0", spec_hash="test123")

    tracked = TrackedFile(
        path="backend/models/user.py",
        strategy=FileStrategy.ALWAYS_OVERWRITE.value,
        content_hash="abc123",
        generated_at="2026-01-23T10:00:00",
    )

    manifest.track_file(tracked)

    # Save manifest
    ManifestManager.save(manifest, project_dir)

    # Check file was created
    manifest_path = project_dir / ".prisme" / "manifest.json"
    assert manifest_path.exists()

    # Load manifest
    loaded = ManifestManager.load(project_dir)

    assert loaded.prisme_version == "0.4.0"
    assert loaded.spec_hash == "test123"
    assert len(loaded.files) == 1

    loaded_file = loaded.get_file("backend/models/user.py")
    assert loaded_file is not None
    assert loaded_file.content_hash == "abc123"


def test_manifest_manager_load_nonexistent(tmp_path: Path):
    """Test loading manifest when file doesn't exist."""
    project_dir = tmp_path / "empty_project"
    project_dir.mkdir()

    # Should return empty manifest without error
    manifest = ManifestManager.load(project_dir)

    assert isinstance(manifest, FileManifest)
    assert len(manifest.files) == 0


def test_manifest_manager_load_corrupted(tmp_path: Path):
    """Test loading corrupted manifest file."""
    project_dir = tmp_path / "project"
    manifest_dir = project_dir / ".prisme"
    manifest_dir.mkdir(parents=True)

    # Write corrupted JSON
    manifest_path = manifest_dir / "manifest.json"
    manifest_path.write_text("{ invalid json }")

    # Should return empty manifest without crashing
    manifest = ManifestManager.load(project_dir)

    assert isinstance(manifest, FileManifest)
    assert len(manifest.files) == 0


def test_file_manifest_list_modified_files(tmp_path: Path):
    """Test listing modified files."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    # Create some test files
    file1_path = project_dir / "file1.py"
    file1_content = "print('original')"
    file1_path.write_text(file1_content)

    file2_path = project_dir / "file2.py"
    file2_content = "print('unchanged')"
    file2_path.write_text(file2_content)

    # Create manifest tracking both files
    manifest = FileManifest()

    manifest.track_file(
        TrackedFile(
            path="file1.py",
            strategy=FileStrategy.GENERATE_ONCE.value,
            content_hash=hash_content(file1_content),
            generated_at="2026-01-23T10:00:00",
        )
    )

    manifest.track_file(
        TrackedFile(
            path="file2.py",
            strategy=FileStrategy.GENERATE_ONCE.value,
            content_hash=hash_content(file2_content),
            generated_at="2026-01-23T10:00:00",
        )
    )

    # Modify file1
    file1_path.write_text("print('modified')")

    # Get modified files list
    modified = manifest.list_modified_files(project_dir)

    assert len(modified) == 1
    assert "file1.py" in modified
    assert "file2.py" not in modified


def test_manifest_roundtrip_serialization():
    """Test that manifest can be serialized and deserialized without loss."""
    original = FileManifest(
        version="1.0",
        prisme_version="0.4.0",
        spec_hash="roundtrip_test",
    )

    original.track_file(
        TrackedFile(
            path="file1.py",
            strategy=FileStrategy.ALWAYS_OVERWRITE.value,
            content_hash="hash1",
            generated_at="2026-01-23T10:00:00",
            has_hooks=False,
        )
    )

    original.track_file(
        TrackedFile(
            path="file2.py",
            strategy=FileStrategy.ALWAYS_OVERWRITE.value,
            content_hash="hash2",
            generated_at="2026-01-23T11:00:00",
            has_hooks=True,
            extends="base.py",
        )
    )

    # Serialize to dict
    data = original.to_dict()

    # Deserialize from dict
    restored = FileManifest.from_dict(data)

    # Verify everything matches
    assert restored.version == original.version
    assert restored.prisme_version == original.prisme_version
    assert restored.spec_hash == original.spec_hash
    assert len(restored.files) == len(original.files)

    for path, original_file in original.files.items():
        restored_file = restored.get_file(path)
        assert restored_file is not None
        assert restored_file.path == original_file.path
        assert restored_file.strategy == original_file.strategy
        assert restored_file.content_hash == original_file.content_hash
        assert restored_file.has_hooks == original_file.has_hooks
        assert restored_file.extends == original_file.extends
