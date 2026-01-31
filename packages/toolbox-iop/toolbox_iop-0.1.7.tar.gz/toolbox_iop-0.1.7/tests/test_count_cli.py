import os
import tempfile
from pathlib import Path

import pytest
from unittest.mock import patch

from toolbox_iop.cli.count_cli import (
    detect_and_count_jsonl,
    count_jsonl_lines_fast,
    parse_args,
    main,
)


@pytest.fixture
def fixtures_path():
    return Path(__file__).parent / "fixtures"


def test_detect_and_count_jsonl_with_jsonl_file(fixtures_path):
    jsonl_file = fixtures_path / "test_jsonl_10lines.jsonl"
    is_jsonl, count = detect_and_count_jsonl(str(jsonl_file))
    assert is_jsonl is True
    assert count == 10


def test_detect_and_count_jsonl_with_large_jsonl_file(fixtures_path):
    jsonl_file = fixtures_path / "test_jsonl_100lines.jsonl"
    is_jsonl, count = detect_and_count_jsonl(str(jsonl_file))
    assert is_jsonl is True
    assert count == 100


def test_detect_and_count_jsonl_with_json_list_file(fixtures_path):
    json_file = fixtures_path / "test_json_list.json"
    is_jsonl, count = detect_and_count_jsonl(str(json_file))
    assert is_jsonl is False
    assert count == 1


def test_detect_and_count_jsonl_with_json_dict_file(fixtures_path):
    json_file = fixtures_path / "test_json_dict.json"
    is_jsonl, count = detect_and_count_jsonl(str(json_file))
    assert is_jsonl is False
    assert count == 1


def test_detect_and_count_jsonl_with_empty_file(fixtures_path):
    empty_file = fixtures_path / "test_empty.json"
    is_jsonl, count = detect_and_count_jsonl(str(empty_file))
    assert is_jsonl is False
    assert count == 0


def test_detect_and_count_jsonl_with_single_line(fixtures_path):
    single_file = fixtures_path / "test_single_line.json"
    is_jsonl, count = detect_and_count_jsonl(str(single_file))
    assert is_jsonl is False
    assert count == 1


def test_count_jsonl_lines_fast(fixtures_path):
    jsonl_file = fixtures_path / "test_jsonl_10lines.jsonl"
    count = count_jsonl_lines_fast(str(jsonl_file))
    assert count == 10


def test_count_jsonl_lines_fast_large_file(fixtures_path):
    jsonl_file = fixtures_path / "test_jsonl_100lines.jsonl"
    count = count_jsonl_lines_fast(str(jsonl_file))
    assert count == 100


def test_parse_args_with_file_path():
    with patch("sys.argv", ["toolbox-iop-count", "test.json"]):
        args = parse_args()
        assert args.file_path == "test.json"
        assert args.json is False
        assert args.jsonl is False


def test_parse_args_with_json_flag():
    with patch("sys.argv", ["toolbox-iop-count", "test.json", "--json"]):
        args = parse_args()
        assert args.file_path == "test.json"
        assert args.json is True
        assert args.jsonl is False


def test_parse_args_with_json_short_flag():
    with patch("sys.argv", ["toolbox-iop-count", "test.json", "-j"]):
        args = parse_args()
        assert args.file_path == "test.json"
        assert args.json is True
        assert args.jsonl is False


def test_parse_args_with_jsonl_flag():
    with patch("sys.argv", ["toolbox-iop-count", "test.jsonl", "--jsonl"]):
        args = parse_args()
        assert args.file_path == "test.jsonl"
        assert args.json is False
        assert args.jsonl is True


def test_parse_args_with_jsonl_short_flag():
    with patch("sys.argv", ["toolbox-iop-count", "test.jsonl", "-l"]):
        args = parse_args()
        assert args.file_path == "test.jsonl"
        assert args.json is False
        assert args.jsonl is True


@patch("sys.argv", ["toolbox-iop-count", "test.json", "--json"])
def test_main_with_json_flag_and_list_file(fixtures_path, capsys):
    json_file = fixtures_path / "test_json_list.json"
    
    with patch("toolbox_iop.cli.count_cli.parse_args") as mock_parse:
        mock_parse.return_value = type("Args", (), {
            "file_path": str(json_file),
            "json": True,
            "jsonl": False
        })()
        
        main()
        captured = capsys.readouterr()
        assert "✅JSON 是 list 类型，长度为: 5" in captured.out


@patch("sys.argv", ["toolbox-iop-count", "test.json", "--json"])
def test_main_with_json_flag_and_dict_file(fixtures_path, capsys):
    json_file = fixtures_path / "test_json_dict.json"
    
    with patch("toolbox_iop.cli.count_cli.parse_args") as mock_parse:
        mock_parse.return_value = type("Args", (), {
            "file_path": str(json_file),
            "json": True,
            "jsonl": False
        })()
        
        main()
        captured = capsys.readouterr()
        assert "❌JSON 不是 list 类型" in captured.out


@patch("sys.argv", ["toolbox-iop-count", "test.jsonl", "--jsonl"])
def test_main_with_jsonl_flag(fixtures_path, capsys):
    jsonl_file = fixtures_path / "test_jsonl_10lines.jsonl"
    
    with patch("toolbox_iop.cli.count_cli.parse_args") as mock_parse:
        mock_parse.return_value = type("Args", (), {
            "file_path": str(jsonl_file),
            "json": False,
            "jsonl": True
        })()
        
        main()
        captured = capsys.readouterr()
        assert "✅JSONL 文件，行数为: 10" in captured.out


@patch("sys.argv", ["toolbox-iop-count", "test.jsonl"])
def test_main_auto_detect_jsonl(fixtures_path, capsys):
    jsonl_file = fixtures_path / "test_jsonl_10lines.jsonl"
    
    with patch("toolbox_iop.cli.count_cli.parse_args") as mock_parse:
        mock_parse.return_value = type("Args", (), {
            "file_path": str(jsonl_file),
            "json": False,
            "jsonl": False
        })()
        
        main()
        captured = capsys.readouterr()
        assert "✅JSONL 文件，行数为: 10" in captured.out


@patch("sys.argv", ["toolbox-iop-count", "test.json"])
def test_main_auto_detect_json_list(fixtures_path, capsys):
    json_file = fixtures_path / "test_json_list.json"
    
    with patch("toolbox_iop.cli.count_cli.parse_args") as mock_parse:
        mock_parse.return_value = type("Args", (), {
            "file_path": str(json_file),
            "json": False,
            "jsonl": False
        })()
        
        main()
        captured = capsys.readouterr()
        assert "✅JSON 是 list 类型，长度为: 5" in captured.out


@patch("sys.argv", ["toolbox-iop-count", "test.json"])
def test_main_auto_detect_json_dict(fixtures_path, capsys):
    json_file = fixtures_path / "test_json_dict.json"
    
    with patch("toolbox_iop.cli.count_cli.parse_args") as mock_parse:
        mock_parse.return_value = type("Args", (), {
            "file_path": str(json_file),
            "json": False,
            "jsonl": False
        })()
        
        main()
        captured = capsys.readouterr()
        assert "❌JSON 不是 list 类型" in captured.out
