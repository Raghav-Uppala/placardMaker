FROM python:3.11.8

WORKDIR /

COPY requirements.txt /
RUN pip3 install -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["gunicorn", "--bind" , ":8000", "--workers", "2", "app:app"]
