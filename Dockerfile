FROM python:3.11.8

WORKDIR /

COPY requirements.txt /
RUN pip3 install -r requirements.txt

COPY . .

CMD [ "python", "-m" , "flask", "run", "--host=0.0.0.0"]