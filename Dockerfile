FROM python:3.13.2-alpine3.21

# prevent alpine error with TkAgg but still allow GUI for my local dev...
ENV HEADLESS=true

# some meson build error, seems to be absent c compiler on alpine?
RUN apk add --no-cache \
        build-base \
        python3-dev \
        musl-dev \
        openblas-dev \
        lapack-dev

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# slimming the image
RUN apk del build-base python3-dev musl-dev

COPY . .
CMD ["sh"]