FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 8080

ENTRYPOINT ["python", "-m", "src.server"]
CMD ["8080", "boards/ab.txt"]
