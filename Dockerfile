# RunPod Serverless Infinity Embedding Server
FROM michaelf34/infinity:latest

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY entrypoint.sh .
COPY test_input.json .
RUN chmod +x entrypoint.sh

ENV MODEL_NAME="patrickjohncyh/fashion-clip"
ENV INFINITY_HOST="0.0.0.0"
ENV INFINITY_PORT="7997"
ENV DO_NOT_TRACK=1
ENV HF_HOME="/runpod-volume/cache"
ENV TRANSFORMERS_CACHE="/runpod-volume/cache"

RUN mkdir -p /runpod-volume/cache

# Add src files
ADD src .

# Add test input
COPY test_input.json /test_input.json

# start the handler
CMD ["python", "-u", "/handler.py"]
