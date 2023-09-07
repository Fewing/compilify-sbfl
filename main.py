import json

from generate_matrix import generate_coverage_matrix
from fault_location import start_fl
from settings import *

if __name__ == "__main__":
    result_vector, coverage_matrix, file_line_map = generate_coverage_matrix(SRC_LANG)
    with open(os.path.join(TESTCASES_RESULT_PATH, "coverage_matrix.txt"), "w") as f:
        for line in coverage_matrix:
            f.write(str(line) + "\n")
    with open(os.path.join(TESTCASES_RESULT_PATH, "result_vector.txt"), "w") as f:
        for line in result_vector:
            f.write(str(line) + "\n")
    with open(os.path.join(TESTCASES_RESULT_PATH, "file_line_map.json"), "w") as f:
        json.dump(file_line_map, f, indent=4)
    start_fl(result_vector, coverage_matrix, file_line_map)
