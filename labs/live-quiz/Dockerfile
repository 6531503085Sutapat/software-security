FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Run as a non-root user. Week 13 grades students on exactly this defect, so the
# course's own platform should practise it. /data is the sqlite volume mount point;
# create it and hand it over before dropping privileges (a fresh named volume
# inherits this ownership).
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /data \
    && chown -R appuser:appuser /data /app
USER appuser
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:5000/',timeout=2)"
CMD ["python", "app.py"]
