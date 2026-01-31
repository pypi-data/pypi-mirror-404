import json
import os
from pathlib import Path


def generate_test_data():
    fixtures_dir = Path(__file__).parent / "fixtures"
    fixtures_dir.mkdir(exist_ok=True)
    
    test_json_list = [
        {"id": 1, "name": "item1"},
        {"id": 2, "name": "item2"},
        {"id": 3, "name": "item3"},
        {"id": 4, "name": "item4"},
        {"id": 5, "name": "item5"}
    ]
    
    test_json_dict = {"id": 1, "name": "item1", "description": "This is a test item"}
    
    test_single_line = [{"id": 1, "name": "item1"}]
    
    test_jsonl_10lines = [{"id": i + 1, "name": f"item{i + 1}"} for i in range(10)]
    
    test_jsonl_100lines = [{"id": i + 1, "name": f"item{i + 1}"} for i in range(100)]
    
    with open(fixtures_dir / "test_json_list.json", "w", encoding="utf-8") as f:
        json.dump(test_json_list, f, ensure_ascii=False)
    
    with open(fixtures_dir / "test_json_dict.json", "w", encoding="utf-8") as f:
        json.dump(test_json_dict, f, ensure_ascii=False)
    
    with open(fixtures_dir / "test_single_line.json", "w", encoding="utf-8") as f:
        json.dump(test_single_line, f, ensure_ascii=False)
    
    with open(fixtures_dir / "test_empty.json", "w", encoding="utf-8") as f:
        f.write("")
    
    with open(fixtures_dir / "test_jsonl_10lines.jsonl", "w", encoding="utf-8") as f:
        for item in test_jsonl_10lines:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    
    with open(fixtures_dir / "test_jsonl_100lines.jsonl", "w", encoding="utf-8") as f:
        for item in test_jsonl_100lines:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    
    print(f"测试数据文件已生成到: {fixtures_dir}")
    print("生成的文件:")
    for file in fixtures_dir.glob("test_*"):
        print(f"  - {file.name}")


if __name__ == "__main__":
    generate_test_data()
