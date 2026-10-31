FROM python:3.12-slim
WORKDIR /srv
# Install the wheel produced by the build job (no source copy, no rebuild)
COPY dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm /tmp/*.whl
RUN useradd --create-home appuser
USER appuser
EXPOSE 8000
CMD ["skillsforge-demo"]
