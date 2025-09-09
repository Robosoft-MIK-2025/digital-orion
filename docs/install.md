# Установка и запуск

## Вариант A: Через Docker (рекомендуется)

Требуется Docker и Docker Compose.

```bash
# 1) Собрать образ
cd /home/romix38/digital_oreon
docker build -t digital-oreon:base -f docker/Dockerfile .

# 2) Поднять контейнер и войти внутрь
cd docker
docker compose up -d terminal
docker compose exec terminal bash

# 3) Быстрая проверка GUI (необязательно)
xeyes | cat || true
```

## Вариант B: Лаунчер одной командой

```bash
# подсказка по командам
./scripts/doron.sh

# типовые действия
./scripts/doron.sh build       # собрать образ
./scripts/doron.sh up          # запустить контейнер
./scripts/doron.sh shell       # войти в контейнер
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

## Проблемы c GUI в WSLg

Если GUI-приложения не стартуют из‑за OpenGL:
```bash
export LIBGL_ALWAYS_SOFTWARE=1
```
