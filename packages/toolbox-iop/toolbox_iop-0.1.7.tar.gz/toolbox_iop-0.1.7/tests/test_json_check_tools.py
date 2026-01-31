import pytest
import tempfile
import os

from toolbox_iop.json_check_tools import count_json_list_length, find_duplicate_ids


def test_count_json_list_length_with_list():
    test_list = [{"id": 1}, {"id": 2}, {"id": 3}]
    result = count_json_list_length(test_list)
    assert result == 3


def test_count_json_list_length_with_empty_list():
    test_list = []
    result = count_json_list_length(test_list)
    assert result == 0


def test_count_json_list_length_with_dict():
    test_dict = {"id": 1, "name": "test"}
    result = count_json_list_length(test_dict)
    assert result is None


def test_count_json_list_length_with_string():
    test_string = "test string"
    result = count_json_list_length(test_string)
    assert result is None


def test_count_json_list_length_with_number():
    test_number = 42
    result = count_json_list_length(test_number)
    assert result is None


def test_count_json_list_length_with_nested_list():
    test_list = [[1, 2], [3, 4], [5, 6]]
    result = count_json_list_length(test_list)
    assert result == 3


def test_find_duplicate_ids_with_duplicates():
    test_data = [
        {"id": 1, "name": "item1"},
        {"id": 2, "name": "item2"},
        {"id": 1, "name": "item1_dup"},
        {"id": 3, "name": "item3"},
        {"id": 2, "name": "item2_dup"},
    ]
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        for item in test_data:
            f.write(f"{item}\n")
        temp_file = f.name
    
    try:
        duplicates = find_duplicate_ids(temp_file, key="id", json_file=False)
        assert len(duplicates) == 2
        assert 1 in duplicates
        assert 2 in duplicates
        assert len(duplicates[1]) == 2
        assert len(duplicates[2]) == 2
    finally:
        os.unlink(temp_file)


def test_find_duplicate_ids_without_duplicates():
    test_data = [
        {"id": 1, "name": "item1"},
        {"id": 2, "name": "item2"},
        {"id": 3, "name": "item3"},
    ]
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        for item in test_data:
            f.write(f"{item}\n")
        temp_file = f.name
    
    try:
        duplicates = find_duplicate_ids(temp_file, key="id", json_file=False)
        assert len(duplicates) == 0
    finally:
        os.unlink(temp_file)


def test_find_duplicate_ids_with_custom_key():
    test_data = [
        {"name": "item1"},
        {"name": "item2"},
        {"name": "item1"},
    ]
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        for item in test_data:
            f.write(f"{item}\n")
        temp_file = f.name
    
    try:
        duplicates = find_duplicate_ids(temp_file, key="name", json_file=False)
        assert len(duplicates) == 1
        assert "item1" in duplicates
        assert len(duplicates["item1"]) == 2
    finally:
        os.unlink(temp_file)
