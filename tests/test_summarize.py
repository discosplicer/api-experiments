from project_sunrise.summarize import is_text_file, get_text_files_from_path


def test_is_text_file_with_text(tmp_path):
    file = tmp_path / "test.txt"
    file.write_text("Hello, world!")
    assert is_text_file(str(file)) is True


def test_is_text_file_with_binary(tmp_path):
    file = tmp_path / "test.bin"
    file.write_bytes(b"\x00\x01\x02\x03")
    assert is_text_file(str(file)) is False


def test_get_text_files_from_path_file(tmp_path):
    file = tmp_path / "test.txt"
    file.write_text("Hello, world!")
    result = get_text_files_from_path(str(file))
    assert result == [str(file)]


def test_get_text_files_from_path_directory(tmp_path):
    text_file = tmp_path / "a.txt"
    bin_file = tmp_path / "b.bin"
    text_file.write_text("abc")
    bin_file.write_bytes(b"\x00\x01")
    result = get_text_files_from_path(str(tmp_path))
    assert str(text_file) in result
    assert str(bin_file) not in result
