FROM ubuntu:20.04

RUN apt update && \
    apt install -y clang-10 python3 python3-pip git

RUN pip3 install gcovr
RUN pip3 install git+https://github.com/Suresoft-GLaDOS/SBFL.git

WORKDIR /home/compilify-runner

COPY ./ ./

ENV PATH="${PATH}:/opt/jdk-17/bin"
ENV PATH="${PATH}:/bin"

ENTRYPOINT ["python3", "main.py"]
