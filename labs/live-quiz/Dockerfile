FROM python:3.12-slim
# BUILD CONTEXT IS `labs/`, not `labs/live-quiz/` — the image needs the course
# worksheets as well as the app, and a context rooted at the app cannot reach
# its siblings. The first production deploy shipped without this and every
# /learn page 404'd: the app sits at /app, so content.py's default root resolved
# to `/`, where no weekNN-* directory exists.
#   docker buildx build --platform linux/amd64 -f live-quiz/Dockerfile labs/
WORKDIR /app
COPY live-quiz/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY live-quiz/ .
# The course content plane serves these read-only. content.py's PUBLIC_FILES
# allowlist means only worksheet.md and README.md are ever reachable; the lab
# solutions copied alongside them are already public in the repo, and the real
# answer keys live in git-ignored instructor/, outside this context entirely.
COPY . /content/
ENV CONTENT_ROOT=/content
# Run as a non-root user. Week 13 grades students on exactly this defect, so the
# course's own platform should practise it. /data is the sqlite volume mount point;
# create it and hand it over before dropping privileges (a fresh named volume
# inherits this ownership).
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /data \
    && chown -R appuser:appuser /data /app /content
USER appuser
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:5000/',timeout=2)"
CMD ["python", "app.py"]
