import os
import subprocess

from settings import SUBMIT_FOLDER_PATH, WORK_PATH, TESTCASE_IN_FILE

SRC = SUBMIT_FOLDER_PATH
CLS = os.path.join(WORK_PATH, "class")


def compile_java():
    if not os.path.exists(CLS):
        os.mkdir(CLS)
    main_class = os.path.join(SRC, "Compiler.java")
    cmd = f"javac -encoding UTF-8 -d {CLS} -sourcepath {SRC} {main_class}"
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, encoding="utf-8")


def run_java(tc):
    cwd = tc.work_path
    in_path = os.path.join(tc.data_path, TESTCASE_IN_FILE) 
    cmd = f"java -cp {CLS} Compiler"
    print(in_path)
    with open(in_path, "r") as in_file: 
        return subprocess.Popen(cmd, stdin=in_file, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, encoding="utf-8")
