FROM python:3-alpine
COPY . /dirsearch/
ENTRYPOINT ["/dirsearch/dirsearch.py"]

