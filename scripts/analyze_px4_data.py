#!/usr/bin/env python3
"""
Анализ данных PX4 из rosbag2
Конвертация и построение графиков ориентации, статуса дрона
"""

import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys
import json
from datetime import datetime


def extract_vehicle_attitude(db_path):
    """Извлечь данные ориентации дрона из rosbag"""
    conn = sqlite3.connect(db_path)
    
    # Получить данные vehicle_attitude
    query = """
    SELECT timestamp, data 
    FROM messages 
    WHERE topic_id = (
        SELECT id FROM topics 
        WHERE name = '/fmu/out/vehicle_attitude'
    )
    ORDER BY timestamp
    """
    
    rows = conn.execute(query).fetchall()
    conn.close()
    
    if not rows:
        print("⚠️  Нет данных vehicle_attitude")
        return None
    
    # Простое извлечение временных меток (данные в CDR формате)
    timestamps = []
    for timestamp, data in rows:
        # Конвертируем nanoseconds в seconds
        timestamps.append(timestamp / 1e9)
    
    return pd.DataFrame({
        'timestamp': timestamps,
        'message_count': range(len(timestamps))
    })


def extract_vehicle_status(db_path):
    """Извлечь данные статуса дрона"""
    conn = sqlite3.connect(db_path)
    
    query = """
    SELECT timestamp, data 
    FROM messages 
    WHERE topic_id = (
        SELECT id FROM topics 
        WHERE name = '/fmu/out/vehicle_status_v1'
    )
    ORDER BY timestamp
    """
    
    rows = conn.execute(query).fetchall()
    conn.close()
    
    if not rows:
        print("⚠️  Нет данных vehicle_status")
        return None
    
    timestamps = []
    for timestamp, data in rows:
        timestamps.append(timestamp / 1e9)
    
    return pd.DataFrame({
        'timestamp': timestamps,
        'status_updates': range(len(timestamps))
    })


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
    
    # Извлечь данные
    attitude_df = extract_vehicle_attitude(str(db_file))
    status_df = extract_vehicle_status(str(db_file))
    
    # Создать графики
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Анализ данных полёта PX4 SITL', fontsize=16)
    
    if attitude_df is not None:
        # График частоты сообщений attitude
        time_diff = attitude_df['timestamp'].diff().dropna()
        frequency = 1.0 / time_diff.mean()
        
        axes[0, 0].plot(attitude_df['timestamp'], attitude_df['message_count'])
        axes[0, 0].set_title(f'Vehicle Attitude Messages\n(~{frequency:.1f} Hz)')
        axes[0, 0].set_xlabel('Время (с)')
        axes[0, 0].set_ylabel('Номер сообщения')
        axes[0, 0].grid(True)
        
        # Гистограмма интервалов между сообщениями
        axes[0, 1].hist(time_diff * 1000, bins=50, alpha=0.7)
        axes[0, 1].set_title('Интервалы между сообщениями attitude')
        axes[0, 1].set_xlabel('Интервал (мс)')
        axes[0, 1].set_ylabel('Количество')
        axes[0, 1].grid(True)
    
    if status_df is not None:
        # График обновлений статуса
        axes[1, 0].plot(status_df['timestamp'], status_df['status_updates'], 'r-')
        axes[1, 0].set_title('Vehicle Status Updates')
        axes[1, 0].set_xlabel('Время (с)')
        axes[1, 0].set_ylabel('Номер обновления')
        axes[1, 0].grid(True)
        
        # Частота обновлений статуса
        if len(status_df) > 1:
            status_time_diff = status_df['timestamp'].diff().dropna()
            status_freq = 1.0 / status_time_diff.mean()
            
            axes[1, 1].hist(status_time_diff, bins=20, alpha=0.7, color='red')
            axes[1, 1].set_title(f'Status Update Frequency\n(~{status_freq:.1f} Hz)')
            axes[1, 1].set_xlabel('Интервал (с)')
            axes[1, 1].set_ylabel('Количество')
            axes[1, 1].grid(True)
    
    plt.tight_layout()
    
    # Сохранить график
    output_file = bag_path.parent / f"analysis_{bag_path.name}.png"
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"📈 График сохранён: {output_file}")
    
    # Показать статистику
    print("\n📋 Статистика:")
    if attitude_df is not None:
        duration = attitude_df['timestamp'].max() - attitude_df['timestamp'].min()
        print(f"   Длительность записи: {duration:.1f} секунд")
        print(f"   Сообщений attitude: {len(attitude_df)}")
        print(f"   Частота attitude: {len(attitude_df)/duration:.1f} Hz")
    
    if status_df is not None:
        print(f"   Сообщений status: {len(status_df)}")
    
    return output_file


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Использование: python3 analyze_px4_data.py <путь_к_rosbag>")
        sys.exit(1)
    
    bag_directory = sys.argv[1]
    analyze_bag(bag_directory)
