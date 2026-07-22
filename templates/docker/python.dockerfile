# Metadata: version=1.0.0, category=docker, language=Python
FROM python:{{ python_version|default('3.12') }}-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:{{ python_version|default('3.12') }}-slim AS runner
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
RUN useradd -u 8888 appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE {{ port|default(8000) }}
CMD ["gunicorn", "{{ app_name|default('app') }}.wsgi:application", "--bind", "0.0.0.0:{{ port|default(8000) }}"]
