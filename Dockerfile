###############################################
# Base Image
###############################################
FROM python:3.10-slim as python-base

ENV PROJECT_HOME="/app"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false

# prepend poetry to path
ENV PATH="$POETRY_HOME/bin:$PATH"

# create user account
RUN useradd -u 911 -U -d $PROJECT_HOME -s /bin/bash abc \
    && usermod -G users abc \
    && mkdir $PROJECT_HOME

###############################################
# Builder Image
###############################################
FROM python-base as builder-base
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    curl \
    build-essential \
    libpq-dev \
    libwebp-dev \
    libsasl2-dev libldap2-dev libssl-dev \
    gnupg gnupg2 gnupg1

# install poetry - respects $POETRY_VERSION & $POETRY_HOME
ENV POETRY_VERSION=1.3.1
RUN curl -sSL https://install.python-poetry.org | python3 -

###############################################
# Production Image
###############################################
FROM python-base as production
ENV PRODUCTION=true
ENV TESTING=false

ARG COMMIT
ENV GIT_COMMIT_HASH=$COMMIT

# copying poetry and venv into image
COPY --from=builder-base $POETRY_HOME $POETRY_HOME

# copy app
COPY ./steam_user_stats_bot $PROJECT_HOME/steam_user_stats_bot
COPY ./poetry.lock ./pyproject.toml ./run.py $PROJECT_HOME/

# Alembic
COPY ./alembic $PROJECT_HOME/alembic

# install runtime deps
WORKDIR $PROJECT_HOME
RUN poetry install --only main

VOLUME [ "$PROJECT_HOME/data/" ]
ENV APP_PORT=9000

EXPOSE ${APP_PORT}

RUN chmod +x run.py
CMD [ "sh", "-c", "python run.py ${DISCORDKEY}" ]
