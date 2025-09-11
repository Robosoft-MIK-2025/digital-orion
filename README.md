# Цифровой Орион — Руководство по запуску и использованию

## 1) Сборка образа
```bash
cd /home/romix38/digital_oreon
# Рекомендуемый образ
docker build -t digital-oreon:humble -f docker/Dockerfile .
```

## 2) Запуск контейнера (терминал)
```bash
cd docker
docker compose up -d terminal
```

## 3) Вход в контейнер
```bash
docker compose exec terminal bash
```

## 4) Проверка GUI (внутри контейнера)
```bash
xeyes | cat
rviz2 | cat
```

## 5) Демонстрация ROS 2 (два терминала)
```bash
# Терминал A (внутри контейнера)
ros2 run demo_nodes_cpp talker | cat
# Терминал B (внутри контейнера)
ros2 run demo_nodes_cpp listener | cat
```

## Быстрая запись данных (rosbag2)
```bash
# внутри контейнера, после `source /opt/ros/humble/setup.bash`
ros2 bag record -a -o sample
# остановка через 30–60с (Ctrl+C), затем воспроизведение:
ros2 bag play sample
```

## Структура проекта
```
./
├─ docker/
│  ├─ Dockerfile
│  └─ compose.yaml
├─ ros2_ws/
│  └─ src/
└─ docs/
```

## Примечания
- В WSLg поддерживается GUI; если RViz падает из‑за OpenGL, попробуйте: `export LIBGL_ALWAYS_SOFTWARE=1`.
- Исходники рабочей области монтируются в контейнер по пути `/root/ros2_ws/src`.

## Следующие шаги
- PX4 SITL (iris/x500) с Gazebo и мостом ROS 2.
- Определить список топиков для записи; перейти от `ros2 bag record -a` к целевому набору.
- Добавить простой ноутбук для парсинга `.db3` в Parquet.

## PX4 + Gazebo Garden + ROS 2 (в контейнере)

### Сборка и запуск
```bash
cd /home/romix38/digital_oreon
docker build -t digital-oreon:humble -f docker/Dockerfile .
cd docker
docker compose up -d terminal
docker compose exec terminal bash
```

Внутри контейнера:
```bash
source /opt/ros/humble/setup.bash
# Проверка GUI
xeyes | cat
rviz2 | cat
```

### Запуск Gazebo Garden и мост камер
Первая оболочка (внутри контейнера):
```bash
gz sim -r shapes.sdf | cat
# либо загрузите свой мир/модель
```

Вторая оболочка (внутри контейнера), мост изображений (пакеты уже в образе):
```bash
source /opt/ros/humble/setup.bash
ros2 run ros_gz_bridge parameter_bridge \
  /camera@sensor_msgs/msg/Image@ignition.msgs.Image \
  /camera_info@sensor_msgs/msg/CameraInfo@ignition.msgs.CameraInfo \
  /depth_camera/points@sensor_msgs/msg/PointCloud2@gz.msgs.PointCloudPacked \
  /depth_camera@sensor_msgs/msg/Image@ignition.msgs.Image

# Альтернатива: специализированный мост изображений
ros2 run ros_gz_image image_bridge /camera
```

### PX4 SITL (опционально, зависимости уже подготовлены)
Образ включает зависимости для сборки PX4. Для быстрого SITL с Gazebo‑classic или Gazebo Garden — следуйте официальной документации PX4. Пример для Gazebo‑classic:
```bash
cd ~/ros2_ws
git clone https://github.com/PX4/PX4-Autopilot.git
cd PX4-Autopilot
git submodule update --init --recursive
make px4_sitl gazebo
```

### Диагностика
Если PX4 показывает:
- `ERROR [gz_bridge] timed out waiting for clock message`
- `ERROR [gz_bridge] Task start failed (-1)`
- `ERROR [init] gz_bridge failed to start`
- `ERROR [px4] Startup script returned with return value: 256`

Запустите внутри контейнера перед стартом:
```bash
pkill -9 ruby || true
unset GZ_IP
unset GZ_PARTITION
```

В WSLg, если RViz или Gazebo не запускаются из‑за OpenGL:
```bash
export LIBGL_ALWAYS_SOFTWARE=1
```

Если в ROS 2 не видно топики камеры — убедитесь, что запущен bridge и имена топиков совпадают с миром/моделью.

## Runbook (SITL, MAVROS, логгер, планировщик, метрики)

### Запуск контейнера
```bash
cd /home/romix38/digital_oreon
docker build -t digital-oreon:humble -f docker/Dockerfile .
cd docker && docker compose up -d terminal && docker compose exec terminal bash
```

Внутри контейнера задайте окружение ROS и RMW:
```bash
source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export RMW_CYCLONEDDS_USE_SHM=0
```

### A) PX4 SITL + Gazebo
GUI:
```bash
~/ros2_ws/../scripts/run_sitl_gui.sh
```
Headless:
```bash
~/ros2_ws/../scripts/run_sitl_headless.sh
```

### B) MAVROS
```bash
~/ros2_ws/../scripts/run_mavros.sh
```

### C) Логгер (Parquet/CSV)
```bash
~/ros2_ws/../scripts/ros2_logger.py
```
Выводы сохраняются в `~/ros2_ws/runs/<timestamp>/` (+ `manifest.json`).

### D) Онлайн‑обработчик событий
```bash
~/ros2_ws/../scripts/event_processor.py
```
Пишет `events.jsonl` в ту же папку запуска (ARM/DISARM, режимы, OFFBOARD, взлёт/посадка, отклонения).

### E) Offboard‑помощники / планировщик маршрутов
Зависание в точке:
```bash
~/ros2_ws/../scripts/offboard_hover.sh
```
Квадрат:
```bash
~/ros2_ws/../scripts/offboard_square.sh
```
Планировщик (читает WAYPOINTS_FILE или летит квадрат):
```bash
~/ros2_ws/../scripts/route_planner_offboard.py
```

### F) Метрики
```bash
~/ros2_ws/../scripts/compute_metrics.py
```
Печатает статистику отклонений, долю времени в ARM, счётчики событий за последние запуски.

### G) Остановка всего
```bash
~/ros2_ws/../scripts/stop_all.sh
```

## План тестирования (кратко)
1. Bring‑up: запустить SITL (GUI или headless) и MAVROS — проверить `/mavros/state` → `connected: true`.
2. OFFBOARD hover: выполнить `offboard_hover.sh`, затем перевести в OFFBOARD + ARM (или через планировщик) — проверить z≈2 м.
3. Маршрут: `route_planner_offboard.py` — БПЛА проходит 4 точки, без выпадения из режима.
4. Логирование: `ros2_logger.py` во время полёта — убедиться в наличии Parquet: `local_pose.parquet`, `setpoint_local.parquet`, `mavros_state.parquet`, `clock.parquet`.
5. События: `event_processor.py` — `events.jsonl` содержит ARM/DISARM, взлёт/посадку, смены режимов.
6. Метрики: `compute_metrics.py` — непустой JSON со сводной статистикой.
7. Повтор (опц.): воспроизведение записей или анализ Parquet `scripts/analyze_px4_data.py`.

Примечания:
- В обоих терминалах используйте `RMW_IMPLEMENTATION=rmw_cyclonedds_cpp` и `RMW_CYCLONEDDS_USE_SHM=0`.
- Если проблемы с GUI в WSLg — используйте headless + QGroundControl.

---

## Quickstart (Конвертация данных из QGC)
Используйте лаунчер для подготовки окружения и конвертации логов QGC `.ulg` в CSV.

```bash
# 1) Подготовка изолированного Python‑окружения (один раз)
./scripts/doron.sh setup-data-env

# 2) Конвертация последнего лога QGC (автоопределение или укажите путь)
./scripts/doron.sh ulog-latest
# либо
./scripts/doron.sh ulog-latest ~/QGroundControl/Logs
# либо
./scripts/doron.sh ulog-latest /path/to/log.ulg

# 3) Результат
# runs/<timestamp>/flight_data.csv и папка csv_raw/
```

Документация как сайт:
```bash
./scripts/doron.sh docs && ./scripts/doron.sh open-docs
```
