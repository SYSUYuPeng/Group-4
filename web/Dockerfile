FROM python:3.6
COPY ./run.sh ./run.sh
COPY ./wait-for-it.sh ./wait-for-it.sh
COPY ./requirements.txt ./requirements.txt
RUN pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple
COPY . .
