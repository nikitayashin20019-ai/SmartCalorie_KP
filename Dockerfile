FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y python3 python3-pip git && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN git clone https://github.com/nikitayashin20019-ai/calorie_tracker.git .

RUN pip3 install --break-system-packages -r requirements.txt

CMD ["bash", "-c", "ls -la && ls -la data/ && echo '--- Проект успешно собран в контейнере ---' && bash"]
