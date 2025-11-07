# RunPod Serverless Infinity Embedding Server

FROM michaelf34/infinity:latest

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY src/handler.py /app/handler.py

COPY test_input.json /app/test_input.json

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENV MODEL_NAME="patrickjohncyh/fashion-clip"
ENV INFINITY_HOST="0.0.0.0"
ENV INFINITY_PORT="7997"
ENV DO_NOT_TRACK=1
ENV HF_HOME="/runpod-volume/cache"
ENV TRANSFORMERS_CACHE="/runpod-volume/cache"

RUN mkdir -p /runpod-volume/cache

EXPOSE 7997

ENTRYPOINT ["/app/entrypoint.sh"]
