# Базовый образ Ubuntu
FROM ubuntu:22.04

# Установка Python, Git и утилит для виртуального экрана
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y python3 python3-pip git xvfb scrot && rm -rf /var/lib/apt/lists/*

# Создание рабочей директории
WORKDIR /app

# Клонирование кода
RUN git clone https://github.com/nikitayashin20019-ai/SmartCalorie_KP.git .

# Установка зависимостей Python
RUN pip3 install -r requirements.txt

# Магия: Запускаем виртуальный экран, запускаем программу, ждем 3 сек, делаем скриншот
CMD ["bash", "-c", "Xvfb :99 -screen 0 1024x768x24 & export DISPLAY=:99 && timeout 3 python3 main.py; scrot /app/gui_proof.png && echo '--- GUI успешно отрисовалась в контейнере! Скриншот сохранен. ---' && ls -la /app/gui_proof.png"]