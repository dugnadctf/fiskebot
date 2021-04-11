FROM python:3.7

ENV NAME eptbot
ENV APP_HOME /eptbot

RUN groupadd -r ${NAME} && useradd -r -g ${NAME} ${NAME}

COPY requirements/base.txt requirements.txt

RUN pip install -r requirements.txt

WORKDIR ${APP_HOME}

RUN chown ${NAME}:${NAME} ${APP_HOME}


COPY --chown=eptbot:eptbot ./bot/* ${APP_HOME}/

CMD ["python", "-u", "eptbot.py"]
