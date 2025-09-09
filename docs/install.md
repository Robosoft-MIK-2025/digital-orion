# Установка и запуск

## Вариант A: Через Docker (рекомендуется)

Требуется Docker и Docker Compose.

```bash
# 1) Собрать образ
cd /home/romix38/digital_oreon
docker build -t digital-oreon:humble -f docker/Dockerfile .

# 2) Поднять контейнер и войти внутрь
cd docker
docker compose up -d terminal
docker compose exec terminal bash

# 3) Проверка GUI (внутри контейнера)
xeyes | cat
rviz2 | cat
```

ROS 2 окружение внутри контейнера:
```bash
source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export RMW_CYCLONEDDS_USE_SHM=0
```

## Вариант B: Лаунчер одной командой

```bash
# подсказка по командам
./scripts/doron.sh

# типовые действия
./scripts/doron.sh build       # собрать образ
./scripts/doron.sh up          # запустить контейнер
./scripts/doron.sh shell       # войти в контейнер
./scripts/doron.sh record 30   # записать все топики 30с
./scripts/doron.sh docs        # собрать сайт документации
./scripts/doron.sh open-docs   # открыть сайт локально
./scripts/doron.sh stop        # остановить контейнер
```

## Вариант C: Makefile шорткаты

```bash
make build   # собрать образ
make up      # поднять контейнер
make shell   # войти в контейнер
make docs    # собрать документацию
```

## Вариант D: Локально (только документация)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r docs/requirements-docs.txt
sphinx-build -b html docs docs/_build/html
xdg-open docs/_build/html/index.html
```

## Быстрые проверки (внутри контейнера)

Запись всех топиков в rosbag2 на 30–60 секунд:
```bash
source /opt/ros/humble/setup.bash
ros2 bag record -a -o sample
# остановите Ctrl+C и воспроизведите, если нужно:
ros2 bag play sample
```

## Проблемы c GUI в WSLg

Если RViz/Gazebo не стартуют из‑за OpenGL:
```bash
export LIBGL_ALWAYS_SOFTWARE=1
```
