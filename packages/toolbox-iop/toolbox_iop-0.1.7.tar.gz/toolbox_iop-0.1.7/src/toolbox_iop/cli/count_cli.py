import argparse

from toolbox_iop.json_check_tools import count_json_list_length
from toolbox_iop.json_tools import load_json, load_json_file, load_json_line


def detect_and_count_jsonl(file_path, sample_lines=10):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = []
        line_count = 0
        total_lines_read = 0
        
        for line in f:
            total_lines_read += 1
            stripped = line.strip()
            if stripped:
                lines.append(stripped)
                line_count += 1
                if line_count >= sample_lines:
                    break
        
        if line_count == 0:
            return False, 0
        
        if line_count == 1:
            return False, 1
        
        try:
            load_json_line(lines[0])
            if line_count >= sample_lines:
                f.seek(0)
                total_lines = sum(1 for line in f if line.strip())
                return True, total_lines
            return True, line_count
        except:
            return False, line_count


def count_jsonl_lines_fast(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def parse_args():
    parser = argparse.ArgumentParser(description="统计JSON/JSONL文件中list的长度")
    parser.add_argument("file_path", help="要检查的JSON/JSONL文件路径")
    parser.add_argument(
        "--json", "-j", help="强制解析为json文件 【list(dict)格式】", action="store_true"
    )
    parser.add_argument(
        "--jsonl", "-l", help="强制解析为jsonl文件", action="store_true"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if args.json:
        json_obj = load_json_file(args.file_path)
        length = count_json_list_length(json_obj)

        if length is not None:
            print(f"✅JSON 是 list 类型，长度为: {length}")
        else:
            print("❌JSON 不是 list 类型")
    elif args.jsonl:
        count = count_jsonl_lines_fast(args.file_path)
        print(f"✅JSONL 文件，行数为: {count}")
    else:
        is_jsonl, count = detect_and_count_jsonl(args.file_path)
        
        if is_jsonl:
            print(f"✅JSONL 文件，行数为: {count}")
        else:
            if count == 1:
                json_obj = load_json_file(args.file_path)
                length = count_json_list_length(json_obj)

                if length is not None:
                    print(f"✅JSON 是 list 类型，长度为: {length}")
                else:
                    print("❌JSON 不是 list 类型")
            else:
                print(f"❌无法识别文件格式，非空行数: {count}")


if __name__ == "__main__":
    main()
