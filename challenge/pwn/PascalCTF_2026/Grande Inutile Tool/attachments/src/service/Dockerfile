FROM python:3.13-alpine

WORKDIR /app

RUN apk add --no-cache openssh-client sshpass

RUN pip install flask paramiko requests

COPY templates /app/templates
COPY app.py /app/app.py

EXPOSE 8080

CMD ["python", "app.py"]
