import os
import subprocess
import xml.etree.ElementTree as ET

from settings import TLE_LIMIT


def compile_java(src_dir: str):
    origin_cwd = os.getcwd()
    os.chdir(src_dir)  # change working directory to src_dir
    command = "javac -encoding UTF-8 -g -sourcepath . Compiler.java"
    res = subprocess.run(args=command, capture_output=True, shell=True)
    os.chdir(origin_cwd)  # change working directory back
    if res.returncode != 0:
        return False, res.stderr.decode("utf-8", errors="ignore")
    else:
        return True, res.stderr.decode("utf-8", errors="ignore")


def run_java(working_dir: str):
    line_coverage = []
    file_line_map = {}
    jacocoagent_path = os.path.join(working_dir, "..", "jacoco_lib", "jacocoagent.jar")
    jacococli_path = os.path.join(working_dir, "..", "jacoco_lib", "jacococli.jar")
    try:
        command = f"timeout {TLE_LIMIT} java  -javaagent:{jacocoagent_path} Compiler"
        res = subprocess.run(
            args=command,
            capture_output=True,
            shell=True,
            cwd=working_dir,
        )  # 运行程序
        if res.returncode == 124:
            return False, line_coverage, file_line_map
        res = subprocess.run(
            args=f"java -jar {jacococli_path} report --classfiles . --sourcefiles . --xml jacoco-report.xml jacoco.exec",
            capture_output=True,
            shell=True,
            cwd=working_dir,
        )  # 运行jacococli
        if res.returncode == 0:
            coverage_file = os.path.join(working_dir, "jacoco-report.xml")
            line_coverage, file_line_map = process_jacoco_xml_file(working_dir, coverage_file)
        else:
            return False, line_coverage, file_line_map
    except Exception as e:
        return False, line_coverage, file_line_map
    return True, line_coverage, file_line_map


def process_jacoco_xml_file(src_dir: str, coverage_file: str):
    """
    Process the coverage data from jacoco.
    """
    line_coverage = []
    file_line_map = {}
    tree = ET.parse(coverage_file)
    root = tree.getroot()
    for package in root.findall("package"):
        package_name = package.attrib["name"]
        sourcefile_coverage_dict = {}
        for sourcefile in package.findall("sourcefile"):
            sourcefile_coverage_dict[sourcefile.attrib["name"]] = [
                i.attrib for i in sourcefile.findall("line")
            ]
        for java_class in package.findall("class"):
            if package_name == "":
                src_file = f"{java_class.attrib['sourcefilename']}"
            else:
                src_file = f"{package_name}/{java_class.attrib['sourcefilename']}"
            # 计算file的总代码行
            with open(os.path.join(src_dir, src_file), "r", errors="ignore") as f:
                total_line_count = len(f.readlines())
            current_line_coverage = [0] * total_line_count
            for line in sourcefile_coverage_dict[java_class.attrib["sourcefilename"]]:
                if int(line["ci"]) + int(line["cb"]) > 0:
                    current_line_coverage[int(line["nr"]) - 1] = 1
            line_coverage.extend(current_line_coverage)
            if src_file not in file_line_map:
                file_line_map[src_file] = {
                    "start": len(line_coverage) - total_line_count,
                    "end": len(line_coverage) - 1,
                }
    return line_coverage, file_line_map
