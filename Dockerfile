FROM python:3.7

ENV NAME fiskebot
ENV APP_HOME /fiskebot

RUN groupadd -r ${NAME} && useradd -r -g ${NAME} ${NAME}

COPY requirements/base.txt requirements.txt

RUN pip install -r requirements.txt

WORKDIR ${APP_HOME}

RUN chown ${NAME}:${NAME} ${APP_HOME}


COPY --chown=fiskebot:fiskebot ./bot/* ${APP_HOME}/

CMD ["python", "-u", "fiskebot.py"]
