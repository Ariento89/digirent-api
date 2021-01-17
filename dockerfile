FROM python:3.8.1

ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DEFAULT_TIMEOUT=300 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=1.0.5 \
    POETRY_VIRTUALENVS_CREATE=0

WORKDIR /src/digirent

COPY pyproject.toml poetry.lock ./

RUN pip install --upgrade pip "poetry==$POETRY_VERSION"

RUN poetry install

COPY . .

RUN poetry install

RUN useradd -m digirent_user && chown -R digirent_user /src

USER digirent_user

ENTRYPOINT [ "/bin/sh", "entrypoint.sh" ]