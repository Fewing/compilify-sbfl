import os
import subprocess


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


def gcc_compile(src_dir: str, language: str):
    origin_cwd = os.getcwd()
    os.chdir(src_dir)  # change working directory to src_dir
    if language == "cpp":
        command = "clang++-10 -std=c++17 --coverage -g -O0 -lm "
        src_file_list = find_all_files(".", "cpp")
    if language == "C":
        command = "clang -std=c11 --coverage -g -O0 -lm "
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
