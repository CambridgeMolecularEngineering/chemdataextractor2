FROM python:3.8-buster


RUN pip install --no-cache-dir chemdataextractor2
RUN pip install --no-cache-dir "numpy<1.24.0"

RUN cde

CMD ["/bin/bash", "-c", "bash"]
