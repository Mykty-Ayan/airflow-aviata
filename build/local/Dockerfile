FROM python:3.13-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
	PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1

RUN apt-get update \
	&& apt-get install --yes --no-install-recommends build-essential libffi-dev libssl-dev \
	&& rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md ./

# Materialize requirements from pyproject to avoid maintaining a separate list.
RUN python - <<'PY'
import pathlib
import tomllib

pyproject_path = pathlib.Path('pyproject.toml')
project = tomllib.loads(pyproject_path.read_text()).get('project', {})
deps = project.get('dependencies', [])
pathlib.Path('requirements.txt').write_text('\n'.join(deps))
PY

RUN python -m venv /opt/venv \
	&& /opt/venv/bin/pip install --upgrade pip \
	&& /opt/venv/bin/pip install -r requirements.txt


FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1

RUN apt-get update \
	&& apt-get install --yes --no-install-recommends libffi-dev libssl-dev \
	&& rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv

ENV PATH=/opt/venv/bin:$PATH

COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]