import os
import json
from sbfl.base import SBFL
import numpy as np

from settings import TESTCASES_RESULT_PATH, THRESHOLD_LINE_NUM, MAX_OUTPUT_LINE, RESULT_FILE


def start_fl(result_vector, coverage_matrix, file_line_map):
    if result_vector.count(True) == 0:  # 全部测试点WA
        message = "所有测试点均WA，无法定位错误位置"
        with open(os.path.join(TESTCASES_RESULT_PATH, RESULT_FILE), "w") as f:
            json.dump({"message": message}, f, indent=4, ensure_ascii=False)
        return
    elif result_vector.count(False) == 0:  # 全部测试点通过(其他的TLE了)
        message = "除了超时和运行时错误的测试点，其他测试点均AC，无法定位错误位置"
        with open(os.path.join(TESTCASES_RESULT_PATH, RESULT_FILE), "w") as f:
            json.dump({"message": message}, f, indent=4, ensure_ascii=False)
        return
    else:
        X = np.array(coverage_matrix, dtype=bool)
        y = np.array(result_vector, dtype=bool)
        sbfl = SBFL(formula="Ochiai")
        scores = sbfl.fit_predict(X, y)
        with open(os.path.join(TESTCASES_RESULT_PATH, "scores.txt"), "w") as f:
            for line in scores:
                f.write(str(line) + "\n")
        line_rank = sbfl.ranks(method="max")
        with open(os.path.join(TESTCASES_RESULT_PATH, "line_rank.txt"), "w") as f:
            for line in line_rank:
                f.write(str(line) + "\n")
        if min(line_rank) > THRESHOLD_LINE_NUM:
            message = "错误位置定位失败，可能是因为错误在出现在主干代码，而不是分支代码中"
            with open(os.path.join(TESTCASES_RESULT_PATH, RESULT_FILE), "w") as f:
                json.dump({"message": message}, f, indent=4, ensure_ascii=False)
            return
        # 按照得分排序
        scores_dict = {}
        for i in range(len(scores)):
            scores_dict[i] = scores[i]
        scores_dict = dict(sorted(scores_dict.items(), key=lambda item: item[1], reverse=True))
        # 取排序靠前的行（包含并列）并分组
        grouped_top_line = []
        cnt = 0
        current_score = None
        for line_num in scores_dict:
            if cnt < MAX_OUTPUT_LINE:
                if current_score == None:
                    grouped_top_line.append([line_num])
                    current_score = scores_dict[line_num]
                elif current_score == scores_dict[line_num]:
                    grouped_top_line[-1].append(line_num)
                else:
                    grouped_top_line.append([line_num])
                    current_score = scores_dict[line_num]
                cnt += 1
            elif current_score == scores_dict[line_num]:
                grouped_top_line[-1].append(line_num)
            else:
                break
        # 映射到文件
        location_result = []
        for group in grouped_top_line:
            location_result.append({})
            for line in group:
                for file in file_line_map:
                    if line <= file_line_map[file]["end"]:
                        if file not in location_result[-1]:
                            location_result[-1][file] = [line - file_line_map[file]["start"] + 1]
                        else:
                            location_result[-1][file].append(
                                line - file_line_map[file]["start"] + 1
                            )
                        break
        with open(os.path.join(TESTCASES_RESULT_PATH, RESULT_FILE), "w") as f:
            json.dump(location_result, f, indent=4, ensure_ascii=False)
