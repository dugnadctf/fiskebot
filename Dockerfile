FROM python:3.7

ENV NAME eptbot
ENV APP_HOME /eptbot

RUN groupadd -r ${NAME} && useradd -r -g ${NAME} ${NAME}

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

WORKDIR ${APP_HOME}

RUN chown ${NAME}:${NAME} ${APP_HOME}


COPY --chown=eptbot:eptbot nullctf.py util.py ${APP_HOME}/
COPY --chown=eptbot:eptbot cogs ${APP_HOME}/cogs
COPY --chown=eptbot:eptbot vars ${APP_HOME}/vars
COPY --chown=eptbot:eptbot models ${APP_HOME}/models
COPY --chown=eptbot:eptbot controllers ${APP_HOME}/controllers

CMD ["python", "-u", "nullctf.py"]