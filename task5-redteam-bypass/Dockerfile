FROM python:latest
WORKDIR /app
COPY . .
RUN chmod 777 /app
RUN pip install --no-cache-dir flask
USER 1000
CMD ["python", "app.py"]
