"""
数据层核心模块
统一使用 SQLite 存储所有数据
"""

import sqlite3
import json
import os
from datetime import date, datetime
from typing import List, Dict, Any, Optional

DB_FILE = 'danzi_data.db'


def get_connection():
    return sqlite3.connect(DB_FILE)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # 用户表
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

    # 每日完成任务表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_completed (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            child_id TEXT,
            task_id TEXT,
            date TEXT,
            UNIQUE(child_id, task_id, date)
        )
    ''')

    # 积分历史表
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

    # 兑换历史表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exchange_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            child_id TEXT,
            time TEXT,
            item_name TEXT,
            price INTEGER
        )
    ''')

    # 周限购记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weekly_exchanges (
            child_id TEXT,
            key TEXT,
            count INTEGER,
            PRIMARY KEY (child_id, key)
        )
    ''')

    # 彩蛋任务表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bonus_quests (
            child_id TEXT,
            date TEXT,
            quest_data TEXT,
            PRIMARY KEY (child_id, date)
        )
    ''')

    # 活跃计时器表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS active_timer (
            child_id TEXT PRIMARY KEY,
            task_id TEXT,
            task_name TEXT,
            start_time TEXT
        )
    ''')

    # 跳绳每日记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jump_rope_daily (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            child_id TEXT,
            date TEXT,
            total_count INTEGER,
            UNIQUE(child_id, date)
        )
    ''')

    # 任务配置表
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

    # 怪物配置表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS monsters_config (
            id TEXT PRIMARY KEY,
            name TEXT,
            icon TEXT,
            default_points INTEGER,
            description TEXT
        )
    ''')

    # 商品配置表
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

    # 掉落物品配置表
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

    # 彩蛋任务配置表
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

    # 系统配置表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_config (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')

    conn.commit()
    conn.close()

    import_from_json_seeds()


def import_from_json_seeds():
    conn = get_connection()
    cursor = conn.cursor()

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

    # 默认系统配置
    cursor.execute('INSERT OR REPLACE INTO system_config (key, value) VALUES (?, ?)', ('admin_password', 'admin123'))
    cursor.execute('INSERT OR REPLACE INTO system_config (key, value) VALUES (?, ?)', ('streak_rule', 'login'))
    cursor.execute('INSERT OR REPLACE INTO system_config (key, value) VALUES (?, ?)', ('version', '2.0'))

    conn.commit()
    conn.close()
    print("✅ 已从JSON文件导入初始配置数据")


# ========== 配置数据操作 ==========

def get_tasks() -> List[Dict]:
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
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM tasks_config')
    for task in tasks:
        cursor.execute('''
            INSERT INTO tasks_config (id, name, monster_id, description, default_points, enabled, "order")
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (task['id'], task['name'], task['monster_id'], task.get('description', ''),
              task.get('points', 3), 1 if task.get('enabled', True) else 0, task.get('order', 999)))
    conn.commit()
    conn.close()


def get_monsters() -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, icon, default_points, description FROM monsters_config')
    rows = cursor.fetchall()
    conn.close()
    return [{
        'id': r[0], 'name': r[1], 'icon': r[2], 'default_points': r[3], 'description': r[4]
    } for r in rows]


def save_monsters(monsters: List[Dict]):
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
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, price, icon, type, weekly_limit, description FROM shop_items_config ORDER BY id')
    rows = cursor.fetchall()
    conn.close()
    return [{
        'id': r[0], 'name': r[1], 'price': r[2], 'icon': r[3],
        'type': r[4], 'weekly_limit': r[5], 'description': r[6]
    } for r in rows]


def save_shop_items(items: List[Dict]):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM shop_items_config')
    for item in items:
        cursor.execute('''
            INSERT INTO shop_items_config (id, name, price, icon, type, weekly_limit, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (item['id'], item['name'], item['price'], item.get('icon', '🎁'),
              item.get('type', 'normal'), item.get('weekly_limit'), item.get('description', '')))
    conn.commit()
    conn.close()


def add_shop_item(item: Dict) -> Dict:
    items = get_shop_items()
    max_id = max([i['id'] for i in items]) if items else 0
    new_id = max_id + 1
    new_item = {
        'id': new_id,
        'name': item.get('name', '新商品'),
        'price': item.get('price', 10),
        'icon': item.get('icon', '🎁'),
        'type': item.get('type', 'normal'),
        'weekly_limit': item.get('weekly_limit'),
        'description': item.get('description', '')
    }
    items.append(new_item)
    save_shop_items(items)
    return new_item


def update_shop_item(item_id: int, data: Dict):
    items = get_shop_items()
    for item in items:
        if item['id'] == item_id:
            item['name'] = data.get('name', item['name'])
            item['price'] = data.get('price', item['price'])
            item['icon'] = data.get('icon', item['icon'])
            item['type'] = data.get('type', item['type'])
            item['weekly_limit'] = data.get('weekly_limit')
            item['description'] = data.get('description', item['description'])
            break
    save_shop_items(items)


def delete_shop_item(item_id: int) -> bool:
    items = get_shop_items()
    new_items = [i for i in items if i['id'] != item_id]
    if len(new_items) == len(items):
        return False
    save_shop_items(new_items)
    return True


def get_loot_table() -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT name, add_points, weight, effect, description FROM loot_items_config')
    rows = cursor.fetchall()
    conn.close()
    return [{'name': r[0], 'add_points': r[1], 'weight': r[2], 'effect': r[3], 'description': r[4]} for r in rows]


def get_bonus_quests_pool() -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, desc, points_min, points_max, description FROM bonus_quests_config')
    rows = cursor.fetchall()
    conn.close()
    return [{
        'id': r[0], 'name': r[1], 'desc': r[2], 'points_range': [r[3], r[4]], 'description': r[5]
    } for r in rows]


def get_config() -> Dict:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT key, value FROM system_config')
    rows = cursor.fetchall()
    conn.close()
    config = {'admin_password': 'admin123', 'streak_rule': 'login', 'version': '2.0'}
    for key, value in rows:
        config[key] = value
    return config


def save_config(config: Dict):
    conn = get_connection()
    cursor = conn.cursor()
    if 'streak_rule' in config:
        cursor.execute('INSERT OR REPLACE INTO system_config (key, value) VALUES (?, ?)', ('streak_rule', config['streak_rule']))
    if 'admin_password' in config:
        cursor.execute('INSERT OR REPLACE INTO system_config (key, value) VALUES (?, ?)', ('admin_password', config['admin_password']))
    conn.commit()
    conn.close()


# ========== 用户状态操作 ==========

def get_or_create_user(child_id: str) -> Dict:
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
        return {'points': 0, 'streak': 1, 'last_date': today, 'portal_used': False, 'treasure_taken_today': False}
    return {
        'points': row[1], 'streak': row[2], 'last_date': row[3],
        'portal_used': bool(row[4]), 'treasure_taken_today': bool(row[5])
    }


def update_user(child_id: str, data: Dict):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users SET points = ?, streak = ?, last_date = ?, portal_used = ?, treasure_taken_today = ?
        WHERE child_id = ?
    ''', (data['points'], data['streak'], data['last_date'],
          int(data.get('portal_used', False)), int(data.get('treasure_taken_today', False)), child_id))
    conn.commit()
    conn.close()


def add_defeated_monster(child_id: str, task_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    today = str(date.today())
    try:
        cursor.execute('INSERT INTO daily_completed (child_id, task_id, date) VALUES (?, ?, ?)', (child_id, task_id, today))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()


def get_defeated_monsters(child_id: str) -> List[str]:
    conn = get_connection()
    cursor = conn.cursor()
    today = str(date.today())
    cursor.execute('SELECT task_id FROM daily_completed WHERE child_id = ? AND date = ?', (child_id, today))
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]


def clear_defeated_monsters(child_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    today = str(date.today())
    cursor.execute('DELETE FROM daily_completed WHERE child_id = ? AND date = ?', (child_id, today))
    conn.commit()
    conn.close()


def add_points_record(child_id: str, source: str, change: int, description: str, total: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO points_history (child_id, time, source, change, description, total)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (child_id, datetime.now().strftime('%m-%d %H:%M'), source, change, description, total))
    conn.commit()
    conn.close()


def get_points_history(child_id: str, limit: int = 50) -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT time, source, change, description, total FROM points_history
        WHERE child_id = ? ORDER BY id DESC LIMIT ?
    ''', (child_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [{'time': r[0], 'source': r[1], 'change': r[2], 'description': r[3], 'total': r[4]} for r in rows]


def add_exchange_record(child_id: str, item_name: str, price: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO exchange_history (child_id, time, item_name, price) VALUES (?, ?, ?, ?)',
                   (child_id, datetime.now().strftime('%H:%M'), item_name, price))
    conn.commit()
    conn.close()


def get_exchange_history(child_id: str, limit: int = 20) -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT time, item_name, price FROM exchange_history WHERE child_id = ? ORDER BY id DESC LIMIT ?',
                   (child_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [{'time': r[0], 'item_name': r[1], 'price': r[2]} for r in rows]


def get_weekly_exchange_count(child_id: str, key: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT count FROM weekly_exchanges WHERE child_id = ? AND key = ?', (child_id, key))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0


def increment_weekly_exchange(child_id: str, key: str):
    conn = get_connection()
    cursor = conn.cursor()
    current = get_weekly_exchange_count(child_id, key)
    if current == 0:
        cursor.execute('INSERT INTO weekly_exchanges (child_id, key, count) VALUES (?, ?, ?)', (child_id, key, 1))
    else:
        cursor.execute('UPDATE weekly_exchanges SET count = ? WHERE child_id = ? AND key = ?', (current + 1, child_id, key))
    conn.commit()
    conn.close()


def save_bonus_quests(child_id: str, quests: List[Dict]):
    conn = get_connection()
    cursor = conn.cursor()
    today = str(date.today())
    cursor.execute('INSERT OR REPLACE INTO bonus_quests (child_id, date, quest_data) VALUES (?, ?, ?)',
                   (child_id, today, json.dumps(quests, ensure_ascii=False)))
    conn.commit()
    conn.close()


def get_bonus_quests(child_id: str) -> Optional[List[Dict]]:
    conn = get_connection()
    cursor = conn.cursor()
    today = str(date.today())
    cursor.execute('SELECT quest_data FROM bonus_quests WHERE child_id = ? AND date = ?', (child_id, today))
    row = cursor.fetchone()
    conn.close()
    return json.loads(row[0]) if row else None


def clear_bonus_quests(child_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    today = str(date.today())
    cursor.execute('DELETE FROM bonus_quests WHERE child_id = ? AND date = ?', (child_id, today))
    conn.commit()
    conn.close()


def save_active_timer(child_id: str, task_id: str, task_name: str, start_time: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO active_timer (child_id, task_id, task_name, start_time) VALUES (?, ?, ?, ?)',
                   (child_id, task_id, task_name, start_time))
    conn.commit()
    conn.close()


def get_active_timer(child_id: str) -> Optional[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT task_id, task_name, start_time FROM active_timer WHERE child_id = ?', (child_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {'task_id': row[0], 'task_name': row[1], 'start_time': row[2]}
    return None


def clear_active_timer(child_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM active_timer WHERE child_id = ?', (child_id,))
    conn.commit()
    conn.close()


# ========== 跳绳记录 ==========

def add_jump_rope_record(child_id: str, count: int):
    conn = get_connection()
    cursor = conn.cursor()
    today = str(date.today())
    cursor.execute('''
        INSERT INTO jump_rope_daily (child_id, date, total_count)
        VALUES (?, ?, ?)
        ON CONFLICT(child_id, date) DO UPDATE SET total_count = total_count + ?
    ''', (child_id, today, count, count))
    conn.commit()
    conn.close()


def get_today_jump_total(child_id: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    today = str(date.today())
    cursor.execute('SELECT total_count FROM jump_rope_daily WHERE child_id = ? AND date = ?', (child_id, today))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0


def clear_jump_rope_record(child_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    today = str(date.today())
    cursor.execute('DELETE FROM jump_rope_daily WHERE child_id = ? AND date = ?', (child_id, today))
    conn.commit()
    conn.close()


# ========== 连胜更新 ==========

def update_streak(child_id: str, new_streak: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET streak = ? WHERE child_id = ?', (new_streak, child_id))
    conn.commit()
    conn.close()


def check_and_update_streak(child_id: str):
    config = get_config()
    streak_rule = config.get('streak_rule', 'login')
    state = get_child_state(child_id)
    tasks = get_tasks()
    enabled_tasks = [t for t in tasks if t.get('enabled', True)]

    if streak_rule == 'clear_all':
        if len(state.get('defeated_monsters', [])) == len(enabled_tasks) and len(enabled_tasks) > 0:
            new_streak = state['streak'] + 1
            update_streak(child_id, new_streak)
            return new_streak
    else:
        new_streak = state['streak'] + 1
        update_streak(child_id, new_streak)
        return new_streak
    return state['streak']


# ========== 重置每日任务 ==========

def reset_daily_tasks(child_id: str):
    """手动重置每日任务（不自动增加连胜）"""
    clear_defeated_monsters(child_id)
    clear_bonus_quests(child_id)
    clear_active_timer(child_id)
    clear_jump_rope_record(child_id)

    user = get_or_create_user(child_id)
    user['portal_used'] = False
    user['treasure_taken_today'] = False
    user['last_date'] = str(date.today())
    update_user(child_id, user)

    # 注意：手动重置时不自动增加连胜，连胜由 get_child_state 中的每日切换处理


# ========== 获取完整状态 ==========

def get_child_state(child_id: str) -> Dict:
    user = get_or_create_user(child_id)
    today = str(date.today())

    if user['last_date'] != today:
        # 直接执行重置逻辑，避免递归调用 get_child_state
        clear_defeated_monsters(child_id)
        clear_bonus_quests(child_id)
        clear_active_timer(child_id)
        clear_jump_rope_record(child_id)

        # 更新用户每日重置状态
        user['portal_used'] = False
        user['treasure_taken_today'] = False
        user['last_date'] = today
        update_user(child_id, user)

        # 单独更新连胜（不通过 get_child_state）
        config = get_config()
        streak_rule = config.get('streak_rule', 'login')
        tasks = get_tasks()
        enabled_tasks = [t for t in tasks if t.get('enabled', True)]

        # 获取今日已完成的任务（此时已清空，因为跨天了）
        if streak_rule == 'clear_all':
            # 严格模式：昨天必须全清才涨连胜
            # 注意：昨天的情况已经在昨天的记录中处理了
            # 跨天后不需要额外操作，连胜保持不变
            pass
        else:
            # 宽松模式：跨天登录即涨连胜
            new_streak = user['streak'] + 1
            update_streak(child_id, new_streak)
            user['streak'] = new_streak

        # 重新获取用户数据
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


init_db()