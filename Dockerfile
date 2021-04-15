FROM python:latest

ENV NAME bot
ENV APP_HOME /home/bot

RUN groupadd -g 1000 -r ${NAME} && useradd -r -g ${NAME} -u 1000 ${NAME}

COPY requirements/base.txt requirements.txt

RUN pip install -r requirements.txt

WORKDIR ${APP_HOME}

RUN mkdir ${APP_HOME}/backups && chown ${NAME}:${NAME} ${APP_HOME}

USER ${NAME}

COPY --chown=${NAME}:${NAME} ./bot/* ${APP_HOME}/

CMD ["python", "-u", "bot.py"]