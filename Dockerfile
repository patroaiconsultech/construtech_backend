FROM python:3.12.14-slim@sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py config.py prompt.py provider.py quota.py ./
RUN python -m compileall -q .
USER 65532:65532
EXPOSE 8080
CMD ["sh","-c","exec uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080}"]
