FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && \
    apt install -y clang-10 python3 python3-pip git openjdk-17-jdk-headless

RUN pip3 install gcovr
RUN pip3 install git+https://github.com/Suresoft-GLaDOS/SBFL.git

WORKDIR /home/compilify-runner

COPY ./ ./

ENTRYPOINT ["python3", "main.py"]
