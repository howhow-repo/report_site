FROM python:3.8
# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV LANG=zh_CN.UTF-8

# pdf render tool
RUN wget https://s3.amazonaws.com/shopify-managemant-app/wkhtmltopdf-0.9.9-static-amd64.tar.bz2
RUN tar xvjf wkhtmltopdf-0.9.9-static-amd64.tar.bz2
RUN mv wkhtmltopdf-amd64 /usr/local/bin/wkhtmltopdf
RUN chmod +x /usr/local/bin/wkhtmltopdf

# add chinese font
RUN apt-get -qqy update \
  && apt-get -qqy --no-install-recommends install \
    fonts-wqy-microhei \
  && rm -rf /var/lib/apt/lists/* \
  && apt-get -qyy clean

# project src
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code/


# setup djngo
RUN python manage.py makemigrations
RUN python manage.py migrate
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
