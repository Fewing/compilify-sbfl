import difflib
import json
import multiprocessing
import shutil
import tempfile

from settings import *
from srclang.cpp import compile_cpp, run_cpp
from srclang.java import compile_java, run_java


def run_testcase(
    language: str,
    testcase_input_file: str,
    testcase_output_file: str,
    output_file_name: str,
    working_dir: str,
):
    # 拷贝测试用例输入
    shutil.copy(testcase_input_file, os.path.join(working_dir, "testfile.txt"))
    if language == "cpp":
        success, line_coverage, file_line_map = run_cpp(working_dir)
        if not success:
            return False, "Run cpp failed", None, None
    elif language == "java":
        success, line_coverage, file_line_map = run_java(working_dir)
        if not success:
            return False, "Run java failed", None, None
    else:
        return False, "Language not supported", None, None
    # 比较输出
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


def run_testcase_wrapper(args):
    language, testcase_input_file, testcase_output_file, output_file_name, working_dir = args
    return run_testcase(
        language, testcase_input_file, testcase_output_file, output_file_name, working_dir
    )


# 计算各文件对应的代码行数
def generate_file_line_map(language: str, working_dir: str):
    if language == "cpp":
        success, line_coverage, file_line_map = run_cpp(working_dir)
        return success, file_line_map
    elif language == "java":
        success, line_coverage, file_line_map = run_java(working_dir)
        return success, file_line_map
    else:
        return False, file_line_map


def generate_coverage_matrix(language: str):
    with tempfile.TemporaryDirectory() as temp_dir:
        # 拷贝源代码并编译
        compile_dir = os.path.join(temp_dir, "compile_dir")
        shutil.copytree(SUBMIT_FOLDER_PATH, compile_dir)
        if language == "cpp":
            success, message = compile_cpp(compile_dir, language)
        elif language == "java":
            success, message = compile_java(compile_dir)
            shutil.copytree("jacoco_lib", os.path.join(temp_dir, "jacoco_lib"))
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
        # 测试输入
        input_file_list = []
        # 测试预期输出文件
        output_file_list = []
        # 测试实际输出文件
        compiler_output_file = []
        # 测试点
        for testcase in os.listdir(TESTCASES_DATA_PATH):
            input_file_list.append(
                os.path.join(TESTCASES_DATA_PATH, testcase, TESTCASE_TESTFILE_FILE)
            )
            output_file_list.append(
                os.path.join(TESTCASES_DATA_PATH, testcase, TESTCASE_EXPECT_OUTPUT_FILE)
            )
            config_file= os.path.join(TESTCASES_DATA_PATH, testcase, TESTCASE_CONFIG_FILE)
            with open(config_file) as f:
                config_dict = json.load(f)
            compiler_output_file.append(f"{config_dict.get("type", "ans")}.txt")
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
            compiler_output_file,
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
