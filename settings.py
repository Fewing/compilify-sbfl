import os

# testcase
TESTCASE_TESTFILE_FILE = "testfile.txt"
TESTCASE_EXPECT_OUTPUT_FILE = "ans.txt"
TESTCASE_IN_FILE = "in.txt"
TESTCASE_CONFIG_FILE = "config.json"

# out file
PARSE_OUT_FILE = "output.txt"

# fault location result file
RESULT_FILE = "location_result.json"

# env var
SUBMIT_FOLDER_PATH = os.environ["SUBMIT_FOLDER_PATH"]
TESTCASES_DATA_PATH = os.environ["TESTCASES_DATA_PATH"]
TESTCASES_RESULT_PATH = os.environ["TESTCASES_RESULT_PATH"]
SRC_LANG = os.environ["SRC_LANG"]

# local dev var
# SUBMIT_FOLDER_PATH = "temp/submit"
# TESTCASES_DATA_PATH = "temp/testcases"
# TESTCASES_RESULT_PATH = "temp/result"
# SRC_LANG = "cpp"

# TLE Limit
TLE_LIMIT = 30

# 错误定位输出最大行数
MAX_OUTPUT_LINE = 30

# 错误定位失效阈值
THRESHOLD_LINE_NUM = 50
