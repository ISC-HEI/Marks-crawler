#############################################################################
## Base setup
FROM python:3.9-slim
WORKDIR /app

#############################################################################
## Install tools

RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
#############################################################################

#############################################################################
## Install streamlit
COPY .streamlit pyproject.toml .
RUN \
  . $HOME/.local/bin/env && \
  uv python install && \
  uv add streamlit && \
  uv cache clean

#############################################################################
## Copy the rest of th project
COPY . /app
#############################################################################

#############################################################################
## Run the app
EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health
ENTRYPOINT ["./.venv/bin/streamlit", "run", "marks_overview.py", "--server.port=8501", "--server.address=0.0.0.0"]
#############################################################################
