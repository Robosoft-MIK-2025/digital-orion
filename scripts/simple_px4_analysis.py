#!/usr/bin/env python3
"""
Простой анализ данных PX4 из rosbag2 
Базовая статистика без pandas/matplotlib
"""

import sqlite3
import sys
from pathlib import Path
import json

def get_topics_info(db_path):
    """Получить информацию о топиках"""
    conn = sqlite3.connect(db_path)
    
    # Получить список топиков
    topics_query = "SELECT id, name, type FROM topics"
    topics = conn.execute(topics_query).fetchall()
    
    print("📋 Доступные топики:")
    for topic_id, name, topic_type in topics:
        # Подсчитать количество сообщений
        count_query = "SELECT COUNT(*) FROM messages WHERE topic_id = ?"
        count = conn.execute(count_query, (topic_id,)).fetchone()[0]
        print(f"   {name}: {count} сообщений ({topic_type})")
    
    conn.close()
    return topics

def analyze_timestamps(db_path, topic_name):
    """Анализ временных меток для топика"""
    conn = sqlite3.connect(db_path)
    
    query = """
    SELECT timestamp 
    FROM messages 
    WHERE topic_id = (
        SELECT id FROM topics 
        WHERE name = ?
    )
    ORDER BY timestamp
    """
    
    rows = conn.execute(query, (topic_name,)).fetchall()
    conn.close()
    
    if not rows:
        return None
    
    timestamps = [row[0] / 1e9 for row in rows]  # nanoseconds to seconds
    
    if len(timestamps) < 2:
        return {
            'count': len(timestamps),
            'duration': 0,
            'frequency': 0
        }
    
    duration = timestamps[-1] - timestamps[0]
    frequency = len(timestamps) / duration if duration > 0 else 0
    
    # Вычислить интервалы
    intervals = []
    for i in range(1, len(timestamps)):
        intervals.append(timestamps[i] - timestamps[i-1])
    
    avg_interval = sum(intervals) / len(intervals) if intervals else 0
    min_interval = min(intervals) if intervals else 0
    max_interval = max(intervals) if intervals else 0
    
    return {
        'count': len(timestamps),
        'duration': duration,
        'frequency': frequency,
        'avg_interval': avg_interval,
        'min_interval': min_interval,
        'max_interval': max_interval,
        'start_time': timestamps[0],
        'end_time': timestamps[-1]
    }

def analyze_bag(bag_dir):
    """Анализ rosbag данных"""
    bag_path = Path(bag_dir)
    db_file = None
    
    # Найти .db3 файл
    for file in bag_path.glob("*.db3"):
        db_file = file
        break
    
    if not db_file:
        print(f"❌ Не найден .db3 файл в {bag_dir}")
        return
    
    print(f"📊 Анализируем: {db_file}")
    print(f"   Размер файла: {db_file.stat().st_size / 1024:.1f} KB")
    print()
    
    # Получить информацию о топиках
    topics = get_topics_info(str(db_file))
    print()
    
    # Анализ ключевых топиков PX4
    key_topics = [
        '/fmu/out/vehicle_attitude',
        '/fmu/out/vehicle_status_v1',
        '/fmu/out/sensor_combined',
        '/fmu/out/vehicle_local_position_v1'
    ]
    
    print("📈 Детальный анализ ключевых топиков:")
    results = {}
    
    for topic in key_topics:
        stats = analyze_timestamps(str(db_file), topic)
        if stats:
            results[topic] = stats
            print(f"\n🔹 {topic}:")
            print(f"   Сообщений: {stats['count']}")
            print(f"   Длительность: {stats['duration']:.2f} сек")
            print(f"   Частота: {stats['frequency']:.1f} Hz")
            print(f"   Средний интервал: {stats['avg_interval']*1000:.1f} мс")
            print(f"   Мин. интервал: {stats['min_interval']*1000:.1f} мс")
            print(f"   Макс. интервал: {stats['max_interval']*1000:.1f} мс")
    
    # Сохранить результаты в JSON
    results_file = bag_path.parent / f"analysis_{bag_path.name}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Результаты сохранены: {results_file}")
    
    # Общая статистика
    total_messages = sum(stats['count'] for stats in results.values())
    if results:
        overall_duration = max(stats['end_time'] for stats in results.values()) - \
                          min(stats['start_time'] for stats in results.values())
        
        print(f"\n📊 Общая статистика:")
        print(f"   Всего сообщений: {total_messages}")
        print(f"   Общая длительность: {overall_duration:.2f} сек")
        print(f"   Средняя частота: {total_messages/overall_duration:.1f} msg/sec")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Использование: python3 simple_px4_analysis.py <путь_к_rosbag>")
        sys.exit(1)
    
    bag_directory = sys.argv[1]
    analyze_bag(bag_directory)
