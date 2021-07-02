FROM python:3.8.2

ADD . /code

WORKDIR /code

RUN pip install -r requirements.txt -i https://pypi.douban.com/simple --trusted-host=pypi.douban.com

EXPOSE 8888
CMD ["python3", "app.py"]
