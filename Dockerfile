FROM python:3.13-slim

LABEL org.opencontainers.image.source="https://github.com/dugnadctf/fiskebot"

ENV NAME bot
ENV APP_HOME /home/bot

RUN groupadd -g 1000 -r ${NAME} && useradd -r -g ${NAME} -u 1000 ${NAME}

COPY requirements/base.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

WORKDIR ${APP_HOME}

RUN mkdir ${APP_HOME}/backups && chown -R ${NAME}:${NAME} ${APP_HOME}

USER ${NAME}

COPY --chown=${NAME}:${NAME} ./bot/ ${APP_HOME}/

CMD ["python", "-u", "bot.py"]
