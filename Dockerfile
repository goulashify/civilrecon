FROM python:3.10-alpine
MAINTAINER Daniel Gulyas "dani@jazzware.io"

# Add deps.
WORKDIR /usr/lib/civilrecon
ADD poetry.lock pyproject.toml ./

# Install deps.
RUN apk add build-base libffi-dev openssl-dev libev libev-dev
RUN pip install --no-warn-script-location --user poetry=="1.1.11" gunicorn[gevent]
RUN python -m poetry config virtualenvs.create false
RUN python -m poetry install --no-dev
RUN apk del build-base libffi-dev openssl-dev libev-dev

# Add source.
ADD app.py wsgi.py ./
ADD templates ./templates
ADD static ./static

# Run the script, give it the config.
EXPOSE 5000
CMD /root/.local/bin/gunicorn --worker-class gevent --workers 8 --bind 0.0.0.0:5000 wsgi:app --max-requests 10000 --timeout 5 --keep-alive 5 --log-level info