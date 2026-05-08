"""
数据层核心模块
统一使用 SQLite 存储所有数据
"""

import sqlite3
import json
import os
from datetime import date, datetime
from typing import List, Dict, Any, Optional

# 数据库文件路径
DB_FILE = 'danzi_data.db'

# ========== 数据库初始化 ==========

def get_connection():
    """获取数据库连接"""
    return sqlite3.connect(DB_FILE)

def init_db():
    """初始化数据库：创建所有表"""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. 用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            child_id TEXT PRIMARY KEY,
            points INTEGER DEFAULT 0,
            streak INTEGER DEFAULT 1,
            last_date TEXT,
            portal_used INTEGER DEFAULT 0,
            treasure_taken_today INTEGER DEFAULT 0
        )
    ''')

    # 2. 每日完成任务表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_completed (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            child_id TEXT,
            task_id TEXT,
            date TEXT,
            UNIQUE(child_id, task_id, date)
        )
    ''')

    # 3. 积分历史表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS points_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            child_id TEXT,
            time TEXT,
            source TEXT,
            change INTEGER,
            description TEXT,
            total INTEGER
        )
    ''')

    # 4. 兑换历史表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exchange_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            child_id TEXT,
            time TEXT,
            item_name TEXT,
            price INTEGER
        )
    ''')

    # 5. 周限购记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weekly_exchanges (
            child_id TEXT,
            key TEXT,
            count INTEGER,
            PRIMARY KEY (child_id, key)
        )
    ''')

    # 6. 彩蛋任务表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bonus_quests (
            child_id TEXT,
            date TEXT,
            quest_data TEXT,
            PRIMARY KEY (child_id, date)
        )
    ''')

    # 7. 活跃计时器表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS active_timer (
            child_id TEXT PRIMARY KEY,
            task_id TEXT,
            task_name TEXT,
            start_time TEXT
        )
    ''')

    conn.commit()
    conn.close()

    # 导入初始配置数据
    import_from_json_seeds()

# ========== 从JSON文件导入初始数据 ==========

def import_from_json_seeds():
    """首次运行时从JSON文件导入配置数据到数据库"""
    conn = get_connection()
    cursor = conn.cursor()

    # 创建配置表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks_config (
            id TEXT PRIMARY KEY,
            name TEXT,
            monster_id TEXT,
            description TEXT,
            default_points INTEGER,
            enabled INTEGER,
            "order" INTEGER
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS monsters_config (
            id TEXT PRIMARY KEY,
            name TEXT,
            icon TEXT,
            default_points INTEGER,
            description TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shop_items_config (
            id INTEGER PRIMARY KEY,
            name TEXT,
            price INTEGER,
            icon TEXT,
            type TEXT,
            weekly_limit INTEGER,
            description TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS loot_items_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            add_points INTEGER,
            weight INTEGER,
            effect TEXT,
            description TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bonus_quests_config (
            id TEXT PRIMARY KEY,
            name TEXT,
            desc TEXT,
            points_min INTEGER,
            points_max INTEGER,
            description TEXT
        )
    ''')

    # 检查是否已经导入过
    cursor.execute("SELECT COUNT(*) FROM tasks_config")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    # 导入 tasks.json
    if os.path.exists('tasks.json'):
        with open('tasks.json', 'r', encoding='utf-8') as f:
            tasks = json.load(f)
        for task in tasks:
            cursor.execute('''
                INSERT OR REPLACE INTO tasks_config (id, name, monster_id, description, default_points, enabled, "order")
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (task['id'], task['name'], task['monster_id'], task.get('description', ''),
                  task.get('points', 3), 1 if task.get('enabled', True) else 0, task.get('order', 999)))

    # 导入 monsters.json
    if os.path.exists('monsters.json'):
        with open('monsters.json', 'r', encoding='utf-8') as f:
            monsters = json.load(f)
        for monster in monsters:
            cursor.execute('''
                INSERT OR REPLACE INTO monsters_config (id, name, icon, default_points, description)
                VALUES (?, ?, ?, ?, ?)
            ''', (monster['id'], monster['name'], monster.get('icon', '👾'),
                  monster.get('default_points', 1), monster.get('description', '')))

    # 导入 shop_items.json
    if os.path.exists('shop_items.json'):
        with open('shop_items.json', 'r', encoding='utf-8') as f:
            shop_items = json.load(f)
        for item in shop_items:
            cursor.execute('''
                INSERT OR REPLACE INTO shop_items_config (id, name, price, icon, type, weekly_limit, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (item['id'], item['name'], item['price'], item.get('icon', '🎁'),
                  item.get('type', 'normal'), item.get('weekly_limit'), item.get('description', '')))

    # 导入 loot_table.json
    if os.path.exists('loot_table.json'):
        with open('loot_table.json', 'r', encoding='utf-8') as f:
            loot_items = json.load(f)
        for idx, item in enumerate(loot_items):
            cursor.execute('''
                INSERT OR REPLACE INTO loot_items_config (id, name, add_points, weight, effect, description)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (idx + 1, item['name'], item.get('add_points', 0), item.get('weight', 1),
                  item.get('effect', ''), item.get('description', '')))

    # 导入 bonus_quests.json
    if os.path.exists('bonus_quests.json'):
        with open('bonus_quests.json', 'r', encoding='utf-8') as f:
            bonus_quests = json.load(f)
        for quest in bonus_quests:
            cursor.execute('''
                INSERT OR REPLACE INTO bonus_quests_config (id, name, desc, points_min, points_max, description)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (quest['id'], quest['name'], quest.get('desc', ''),
                  quest.get('points_range', [1, 4])[0], quest.get('points_range', [1, 4])[1],
                  quest.get('description', '')))

    conn.commit()
    conn.close()
    print("✅ 已从JSON文件导入初始配置数据")

# ========== 获取配置数据的函数 ==========

def get_tasks() -> List[Dict]:
    """从数据库获取任务列表"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, monster_id, description, default_points, enabled, "order" FROM tasks_config ORDER BY "order"')
    rows = cursor.fetchall()
    conn.close()
    return [{
        'id': r[0], 'name': r[1], 'monster_id': r[2], 'description': r[3],
        'points': r[4], 'enabled': bool(r[5]), 'order': r[6]
    } for r in rows]

def save_tasks(tasks: List[Dict]):
    """保存任务列表到数据库"""
    conn = get_connection()
    cursor = conn.cursor()

    # 清空现有数据
    cursor.execute('DELETE FROM tasks_config')

    # 插入新数据
    for task in tasks:
        cursor.execute('''
            INSERT INTO tasks_config (id, name, monster_id, description, default_points, enabled, "order")
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (task['id'], task['name'], task['monster_id'], task.get('description', ''),
              task.get('points', 3), 1 if task.get('enabled', True) else 0, task.get('order', 999)))

    conn.commit()
    conn.close()

def get_monsters() -> List[Dict]:
    """从数据库获取怪物列表"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, icon, default_points, description FROM monsters_config')
    rows = cursor.fetchall()
    conn.close()
    return [{
        'id': r[0], 'name': r[1], 'icon': r[2], 'default_points': r[3], 'description': r[4]
    } for r in rows]

def save_monsters(monsters: List[Dict]):
    """保存怪物列表到数据库"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM monsters_config')

    for monster in monsters:
        cursor.execute('''
            INSERT INTO monsters_config (id, name, icon, default_points, description)
            VALUES (?, ?, ?, ?, ?)
        ''', (monster['id'], monster['name'], monster.get('icon', '👾'),
              monster.get('default_points', 1), monster.get('description', '')))

    conn.commit()
    conn.close()

def get_shop_items() -> List[Dict]:
    """从数据库获取商品列表"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, price, icon, type, weekly_limit, description FROM shop_items_config')
    rows = cursor.fetchall()
    conn.close()
    return [{
        'id': r[0], 'name': r[1], 'price': r[2], 'icon': r[3],
        'type': r[4], 'weekly_limit': r[5], 'description': r[6]
    } for r in rows]

def get_loot_table() -> List[Dict]:
    """从数据库获取掉落物品列表"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT name, add_points, weight, effect, description FROM loot_items_config')
    rows = cursor.fetchall()
    conn.close()
    return [{
        'name': r[0], 'add_points': r[1], 'weight': r[2], 'effect': r[3], 'description': r[4]
    } for r in rows]

def get_bonus_quests_pool() -> List[Dict]:
    """从数据库获取彩蛋任务池"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, desc, points_min, points_max, description FROM bonus_quests_config')
    rows = cursor.fetchall()
    conn.close()
    return [{
        'id': r[0], 'name': r[1], 'desc': r[2], 'points_range': [r[3], r[4]], 'description': r[5]
    } for r in rows]

# ========== 系统配置操作 ==========

def get_config() -> Dict:
    """获取系统配置"""
    conn = get_connection()
    cursor = conn.cursor()

    # 创建配置表（如果不存在）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_config (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')

    # 读取配置
    cursor.execute('SELECT key, value FROM system_config')
    rows = cursor.fetchall()
    conn.close()

    # 默认配置
    config = {
        'admin_password': 'admin123',
        'streak_rule': 'login',
        'version': '2.0'
    }

    # 覆盖数据库中的配置
    for row in rows:
        key, value = row
        if key == 'streak_rule':
            config['streak_rule'] = value
        elif key == 'admin_password':
            config['admin_password'] = value
        elif key == 'version':
            config['version'] = value

    return config

def save_config(config: Dict):
    """保存系统配置"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_config (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')

    if 'streak_rule' in config:
        cursor.execute('INSERT OR REPLACE INTO system_config (key, value) VALUES (?, ?)',
                       ('streak_rule', config['streak_rule']))
    if 'admin_password' in config:
        cursor.execute('INSERT OR REPLACE INTO system_config (key, value) VALUES (?, ?)',
                       ('admin_password', config['admin_password']))
    if 'version' in config:
        cursor.execute('INSERT OR REPLACE INTO system_config (key, value) VALUES (?, ?)',
                       ('version', config['version']))

    conn.commit()
    conn.close()

# ========== 用户状态操作 ==========

def get_or_create_user(child_id: str) -> Dict:
    """获取或创建用户，返回用户状态"""
    conn = get_connection()
    cursor = conn.cursor()

    today = str(date.today())

    cursor.execute('SELECT * FROM users WHERE child_id = ?', (child_id,))
    row = cursor.fetchone()

    if row is None:
        cursor.execute('''
            INSERT INTO users (child_id, points, streak, last_date, portal_used, treasure_taken_today)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (child_id, 0, 1, today, 0, 0))
        conn.commit()
        user_data = {
            'points': 0,
            'streak': 1,
            'last_date': today,
            'portal_used': False,
            'treasure_taken_today': False
        }
    else:
        user_data = {
            'points': row[1],
            'streak': row[2],
            'last_date': row[3],
            'portal_used': bool(row[4]),
            'treasure_taken_today': bool(row[5])
        }

    conn.close()
    return user_data

def update_user(child_id: str, data: Dict):
    """更新用户状态"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users 
        SET points = ?, streak = ?, last_date = ?, portal_used = ?, treasure_taken_today = ?
        WHERE child_id = ?
    ''', (data['points'], data['streak'], data['last_date'],
          int(data.get('portal_used', False)),
          int(data.get('treasure_taken_today', False)), child_id))
    conn.commit()
    conn.close()

# ========== 任务完成记录 ==========

def add_defeated_monster(child_id: str, task_id: str):
    """记录完成的任务（今天）"""
    conn = get_connection()
    cursor = conn.cursor()
    today = str(date.today())
    try:
        cursor.execute('''
            INSERT INTO daily_completed (child_id, task_id, date)
            VALUES (?, ?, ?)
        ''', (child_id, task_id, today))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()

def get_defeated_monsters(child_id: str) -> List[str]:
    """获取今天已完成的任务ID列表"""
    conn = get_connection()
    cursor = conn.cursor()
    today = str(date.today())
    cursor.execute('''
        SELECT task_id FROM daily_completed 
        WHERE child_id = ? AND date = ?
    ''', (child_id, today))
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def clear_defeated_monsters(child_id: str):
    """清除今天的任务完成记录"""
    conn = get_connection()
    cursor = conn.cursor()
    today = str(date.today())
    cursor.execute('DELETE FROM daily_completed WHERE child_id = ? AND date = ?', (child_id, today))
    conn.commit()
    conn.close()

# ========== 积分历史 ==========

def add_points_record(child_id: str, source: str, change: int, description: str, total: int):
    """添加积分变动记录"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO points_history (child_id, time, source, change, description, total)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (child_id, datetime.now().strftime('%m-%d %H:%M'), source, change, description, total))
    conn.commit()
    conn.close()

def get_points_history(child_id: str, limit: int = 50) -> List[Dict]:
    """获取积分历史"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT time, source, change, description, total 
        FROM points_history 
        WHERE child_id = ? 
        ORDER BY id DESC 
        LIMIT ?
    ''', (child_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [{'time': r[0], 'source': r[1], 'change': r[2], 'description': r[3], 'total': r[4]} for r in rows]

# ========== 兑换历史 ==========

def add_exchange_record(child_id: str, item_name: str, price: int):
    """添加兑换记录"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO exchange_history (child_id, time, item_name, price)
        VALUES (?, ?, ?, ?)
    ''', (child_id, datetime.now().strftime('%H:%M'), item_name, price))
    conn.commit()
    conn.close()

def get_exchange_history(child_id: str, limit: int = 20) -> List[Dict]:
    """获取兑换历史"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT time, item_name, price 
        FROM exchange_history 
        WHERE child_id = ? 
        ORDER BY id DESC 
        LIMIT ?
    ''', (child_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [{'time': r[0], 'item_name': r[1], 'price': r[2]} for r in rows]

# ========== 周限购 ==========

def get_weekly_exchange_count(child_id: str, key: str) -> int:
    """获取周限购已兑换次数"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT count FROM weekly_exchanges WHERE child_id = ? AND key = ?', (child_id, key))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0

def increment_weekly_exchange(child_id: str, key: str):
    """增加周限购计数"""
    conn = get_connection()
    cursor = conn.cursor()
    current = get_weekly_exchange_count(child_id, key)
    if current == 0:
        cursor.execute('INSERT INTO weekly_exchanges (child_id, key, count) VALUES (?, ?, ?)', (child_id, key, 1))
    else:
        cursor.execute('UPDATE weekly_exchanges SET count = ? WHERE child_id = ? AND key = ?',
                       (current + 1, child_id, key))
    conn.commit()
    conn.close()

# ========== 彩蛋任务 ==========

def save_bonus_quests(child_id: str, quests: List[Dict]):
    """保存当天的彩蛋任务"""
    conn = get_connection()
    cursor = conn.cursor()
    today = str(date.today())
    cursor.execute('''
        INSERT OR REPLACE INTO bonus_quests (child_id, date, quest_data)
        VALUES (?, ?, ?)
    ''', (child_id, today, json.dumps(quests, ensure_ascii=False)))
    conn.commit()
    conn.close()

def get_bonus_quests(child_id: str) -> Optional[List[Dict]]:
    """获取当天的彩蛋任务"""
    conn = get_connection()
    cursor = conn.cursor()
    today = str(date.today())
    cursor.execute('SELECT quest_data FROM bonus_quests WHERE child_id = ? AND date = ?', (child_id, today))
    row = cursor.fetchone()
    conn.close()
    return json.loads(row[0]) if row else None

def clear_bonus_quests(child_id: str):
    """清除当天的彩蛋任务"""
    conn = get_connection()
    cursor = conn.cursor()
    today = str(date.today())
    cursor.execute('DELETE FROM bonus_quests WHERE child_id = ? AND date = ?', (child_id, today))
    conn.commit()
    conn.close()

# ========== 活跃计时器 ==========

def save_active_timer(child_id: str, task_id: str, task_name: str, start_time: str):
    """保存活跃计时器"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO active_timer (child_id, task_id, task_name, start_time)
        VALUES (?, ?, ?, ?)
    ''', (child_id, task_id, task_name, start_time))
    conn.commit()
    conn.close()

def get_active_timer(child_id: str) -> Optional[Dict]:
    """获取活跃计时器"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT task_id, task_name, start_time FROM active_timer WHERE child_id = ?', (child_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {'task_id': row[0], 'task_name': row[1], 'start_time': row[2]}
    return None

def clear_active_timer(child_id: str):
    """清除活跃计时器"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM active_timer WHERE child_id = ?', (child_id,))
    conn.commit()
    conn.close()

# ========== 统一获取/保存孩子状态 ==========

def get_child_state(child_id: str) -> Dict:
    """获取孩子的完整状态"""
    user = get_or_create_user(child_id)

    today = str(date.today())
    if user['last_date'] != today:
        user['last_date'] = today
        user['portal_used'] = False
        user['treasure_taken_today'] = False
        update_user(child_id, user)
        clear_defeated_monsters(child_id)
        clear_bonus_quests(child_id)
        clear_active_timer(child_id)

    user = get_or_create_user(child_id)

    state = {
        'points': user['points'],
        'streak': user['streak'],
        'last_date': user['last_date'],
        'portal_used': user['portal_used'],
        'treasure_taken_today': user['treasure_taken_today'],
        'defeated_monsters': get_defeated_monsters(child_id),
        'exchange_history': get_exchange_history(child_id),
        'points_history': get_points_history(child_id),
        'bonus_quests': get_bonus_quests(child_id) or [],
        'active_timer': get_active_timer(child_id),
        'weekly_exchanges': {}
    }
    return state

def update_child_state(child_id: str, state: Dict):
    """保存孩子的完整状态"""
    user_data = {
        'points': state['points'],
        'streak': state['streak'],
        'last_date': state['last_date'],
        'portal_used': state.get('portal_used', False),
        'treasure_taken_today': state.get('treasure_taken_today', False)
    }
    update_user(child_id, user_data)

    if state.get('bonus_quests'):
        save_bonus_quests(child_id, state['bonus_quests'])
    else:
        clear_bonus_quests(child_id)

    timer = state.get('active_timer')
    if timer:
        save_active_timer(child_id, timer['task_id'], timer['task_name'], timer['start_time'])
    else:
        clear_active_timer(child_id)

# ========== 连胜更新 ==========

def update_streak(child_id: str, new_streak: int):
    """单独更新连胜天数"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET streak = ? WHERE child_id = ?', (new_streak, child_id))
    conn.commit()
    conn.close()

# ========== 重置每日任务 ==========

def reset_daily_tasks(child_id: str):
    """重置每日任务"""
    clear_defeated_monsters(child_id)
    clear_bonus_quests(child_id)
    clear_active_timer(child_id)

    user = get_or_create_user(child_id)
    user['portal_used'] = False
    user['treasure_taken_today'] = False
    update_user(child_id, user)

# ========== 初始化数据库 ==========
init_db()