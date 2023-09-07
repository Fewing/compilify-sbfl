import difflib
import json
import multiprocessing
import shutil
import subprocess
import tempfile

from settings import *
from srclang.cpp import gcc_compile


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


def run_testcase(
    language: str,
    testcase_input_file: str,
    testcase_output_file: str,
    output_file_name: str,
    working_dir: str,
):
    # 设置gcov输出的环境变量
    os.environ["GCOV_PREFIX"] = working_dir
    os.environ["GCOV_PREFIX_STRIP"] = "3"
    # 拷贝测试用例输入
    shutil.copy(testcase_input_file, os.path.join(working_dir, "testfile.txt"))
    if language == "C" or language == "cpp":
        command = f"timeout {60} ./main.run"
        try:
            res = subprocess.run(
                args=command,
                capture_output=True,
                shell=True,
                cwd=working_dir,
            )  # 运行程序
            if res.returncode == 124:
                return False, "Time Limit Exceeded", None, None
            if res.returncode != 0:
                print(res.stderr.decode("utf-8", errors="ignore"))
            res = subprocess.run(
                args='gcovr --gcov-executable "llvm-cov-10 gcov" --json',
                capture_output=True,
                shell=True,
                cwd=working_dir,
            )  # 运行gcovr
            if res.returncode == 0:
                coverage_data = json.loads(res.stdout)
                line_coverage, _ = process_gcovr_data(coverage_data, working_dir)
            else:
                print(res.stderr.decode("utf-8", errors="ignore"))
                return False, "Run gcovr failed", None, None
        except Exception as e:
            print(e)
            return False, str(e), None, None
        if not os.path.exists(os.path.join(working_dir, output_file_name)):
            return True, "No output file", False, line_coverage
        else:
            with open(os.path.join(working_dir, output_file_name), errors="ignore") as f:
                output = f.read()
            with open(testcase_output_file) as f:
                answer = f.read()
            diff = difflib.Differ().compare(output.splitlines(), answer.splitlines())
            for line in diff:
                if line.startswith("-") or line.startswith("+"):
                    return True, "Wrong Answer", False, line_coverage
            return True, "Accepted", True, line_coverage
    else:
        return False, "Language not supported", None, None


def run_testcase_wrapper(args):
    language, testcase_input_file, testcase_output_file, output_file_name, working_dir = args
    return run_testcase(
        language, testcase_input_file, testcase_output_file, output_file_name, working_dir
    )


# 计算各文件对应的代码行数
def generate_file_line_map(language: str, working_dir: str):
    file_line_map = {}
    # 设置gcov输出的环境变量
    os.environ["GCOV_PREFIX"] = working_dir
    os.environ["GCOV_PREFIX_STRIP"] = "3"
    if language == "C" or language == "cpp":
        command = f"timeout {TLE_LIMIT} ./main.run"
        try:
            res = subprocess.run(
                args=command,
                capture_output=True,
                shell=True,
                cwd=working_dir,
            )  # 运行程序
            if res.returncode == 124:
                return False, file_line_map
            res = subprocess.run(
                args='gcovr --gcov-executable "llvm-cov-10 gcov" --json',
                capture_output=True,
                shell=True,
                cwd=working_dir,
            )  # 运行gcovr
            if res.returncode == 0:
                coverage_data = json.loads(res.stdout)
                _, file_line_map = process_gcovr_data(coverage_data, working_dir)
            else:
                print(res.stderr.decode("utf-8", errors="ignore"))
                return False, file_line_map
        except Exception as e:
            print(e)
            return False, file_line_map
        return True, file_line_map
    else:
        return False, file_line_map


def generate_coverage_matrix(language: str):
    with tempfile.TemporaryDirectory() as temp_dir:
        # 测试用途
        # temp_dir = os.path.join("/home", "temp_dir")
        # os.mkdir(temp_dir)
        # 拷贝源代码并编译
        compile_dir = os.path.join(temp_dir, "compile_dir")
        shutil.copytree(SUBMIT_FOLDER_PATH, compile_dir)
        success, message = gcc_compile(compile_dir, language)
        if not success:
            print("Compile failed")
            print(message)
            return [], [], {}
        # 测试并生成文件行数映射
        shutil.copytree(compile_dir, os.path.join(temp_dir, "test_dir"))
        success, file_line_map = generate_file_line_map(
            language, os.path.join(temp_dir, "test_dir")
        )
        if not success:
            print("Generate file line map failed")
            return [], [], {}
        # 初始化
        coverage_matrix = []
        result_vector = []
        input_file_list = []
        output_file_list = []
        # 测试点
        for testcase in sorted(os.listdir(TESTCASES_DATA_PATH), key=int):
            input_file_list.append(
                os.path.join(TESTCASES_DATA_PATH, testcase, TESTCASE_TESTFILE_FILE)
            )
            output_file_list.append(
                os.path.join(TESTCASES_DATA_PATH, testcase, TESTCASE_EXPECT_OUTPUT_FILE)
            )
        # 运行测试点
        # 输入参数
        working_dirs = []
        for i in range(len(input_file_list)):
            working_dir = os.path.join(temp_dir, f"working_dir_{i}")
            shutil.copytree(compile_dir, working_dir)
            working_dirs.append(working_dir)
        args = zip(
            [language] * len(input_file_list),
            input_file_list,
            output_file_list,
            [PARSE_OUT_FILE] * len(input_file_list),
            working_dirs,
        )
        # 多进程运行
        pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
        results = pool.map(run_testcase_wrapper, args)
        for result in results:
            success, message, passed, line_coverage = result
            if success:
                result_vector.append(passed)
                coverage_matrix.append(line_coverage)
            else:
                if message != "Time Limit Exceeded":
                    print(f"Run failed: {message}")
    return result_vector, coverage_matrix, file_line_map
