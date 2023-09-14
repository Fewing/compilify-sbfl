import os
import subprocess
import json

from settings import TLE_LIMIT


def find_all_files(path: str, suffix: str = "cpp"):
    """
    Find all files in the given path with the given suffix.
    """
    if not os.path.isdir(path):
        return []
    files = []
    for file in os.listdir(path):
        file_path = os.path.join(path, file)
        if os.path.isfile(file_path):
            if suffix is None or file_path.endswith(suffix):
                files.append(file_path)
        else:
            files += find_all_files(file_path, suffix)
    return files


def find_all_include_paths(path: str):
    """
    Find all include paths in the given path.
    """
    if not os.path.isdir(path):
        return []
    include_paths = []
    for file in os.listdir(path):
        file_path = os.path.join(path, file)
        if os.path.isfile(file_path):
            if (
                file_path.endswith(".h") or file_path.endswith(".hpp")
            ) and path not in include_paths:
                include_paths.append('"' + path + '"')
        else:
            include_paths += find_all_include_paths(file_path)
    return include_paths


def compile_cpp(src_dir: str, language: str):
    origin_cwd = os.getcwd()
    os.chdir(src_dir)  # change working directory to src_dir
    if language == "cpp":
        command = "clang++-10 -std=c++17 --coverage -g -O0 -lm "
        src_file_list = find_all_files(".", "cpp")
    if language == "c":
        command = "clang-10 -std=c11 --coverage -g -O0 -lm "
        src_file_list = find_all_files(".", "c")
    dir_list = find_all_include_paths(".")
    if len(dir_list) == 0:
        command = command + " ".join(src_file_list) + " -o " + "main.run"
    else:
        command = (
            command + " ".join(src_file_list) + " -o " + "main.run" + " -I " + " -I ".join(dir_list)
        )
    res = subprocess.run(args=command, capture_output=True, shell=True)
    os.chdir(origin_cwd)  # change working directory back
    if res.returncode != 0:
        return False, res.stderr.decode("utf-8", errors="ignore")
    else:
        return True, res.stderr.decode("utf-8", errors="ignore")


def run_cpp(working_dir: str):
    line_coverage = []
    file_line_map = {}
    command = f"timeout {TLE_LIMIT} ./main.run"
    # 设置gcov输出的环境变量
    os.environ["GCOV_PREFIX"] = working_dir
    os.environ["GCOV_PREFIX_STRIP"] = "3"
    try:
        res = subprocess.run(
            args=command,
            capture_output=True,
            shell=True,
            cwd=working_dir,
        )  # 运行程序
        if res.returncode == 124:
            return False, line_coverage, file_line_map
        res = subprocess.run(
            args='gcovr --gcov-executable "llvm-cov-10 gcov" --json',
            capture_output=True,
            shell=True,
            cwd=working_dir,
        )  # 运行gcovr
        if res.returncode == 0:
            coverage_data = json.loads(res.stdout)
            line_coverage, file_line_map = process_gcovr_data(coverage_data, working_dir)
            return True, line_coverage, file_line_map
        else:
            print(res.stderr.decode("utf-8", errors="ignore"))
            return False, line_coverage, file_line_map
    except Exception as e:
        print(e)
        return False, line_coverage, file_line_map


def process_gcovr_data(coverage_data: dict, src_dir: str):
    """
    Process the coverage data from gcovr.
    """
    line_coverage = []
    file_line_map = {}
    for file in coverage_data["files"]:
        # 计算file的总代码行
        with open(os.path.join(src_dir, file["file"]), "r", errors="ignore") as f:
            total_line_count = len(f.readlines())
        current_line_coverage = [0] * total_line_count
        for line in file["lines"]:
            if line["count"] > 0:
                current_line_coverage[line["line_number"] - 1] = 1
        line_coverage.extend(current_line_coverage)
        if file["file"] not in file_line_map:
            file_line_map[file["file"]] = {
                "start": len(line_coverage) - total_line_count,
                "end": len(line_coverage) - 1,
            }
    return line_coverage, file_line_map
