import json
import os
from datetime import date, datetime

# 配置文件路径
DATA_FILE = 'danzi_data.json'
CONFIG_FILE = 'config.json'
MONSTERS_FILE = 'monsters.json'
TASKS_FILE = 'tasks.json'
SHOP_ITEMS_FILE = 'shop_items.json'
LOOT_TABLE_FILE = 'loot_table.json'
BONUS_QUESTS_FILE = 'bonus_quests.json'


def load_json(file_path, default=None):
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return default if default is not None else []
    return default if default is not None else []


def save_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_monsters():
    return load_json(MONSTERS_FILE, [])


def get_tasks():
    tasks = load_json(TASKS_FILE, [])
    for task in tasks:
        if 'enabled' not in task:
            task['enabled'] = True
        if 'order' not in task:
            task['order'] = 999
    return sorted(tasks, key=lambda x: x.get('order', 999))


def save_tasks(tasks):
    save_json(TASKS_FILE, tasks)


def save_monsters(monsters):
    save_json(MONSTERS_FILE, monsters)


def get_config():
    default = {'admin_password': 'admin123', 'streak_rule': 'login', 'version': '1.0'}
    config = load_json(CONFIG_FILE, default)
    if 'streak_rule' not in config:
        config['streak_rule'] = 'login'
    return config


def save_config(config):
    save_json(CONFIG_FILE, config)


def get_shop_items():
    return load_json(SHOP_ITEMS_FILE, [])


def get_loot_table():
    return load_json(LOOT_TABLE_FILE, [])


def get_bonus_quests_pool():
    return load_json(BONUS_QUESTS_FILE, [])


def get_task_details():
    return load_json('task_details.json', {})


def load_child_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    return None


def save_child_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_child_state(session_child_id):
    child_id = session_child_id
    today = str(date.today())

    saved = load_child_data()
    if saved and saved.get('child_id') == child_id:
        state = saved['state']
        # 跨日重置
        if state.get('last_date') != today:
            print(f"跨日重置: 上次日期={state.get('last_date')}, 今天={today}")  # 调试日志

            config = get_config()
            streak_rule = config.get('streak_rule', 'login')

            # 计算昨天的任务完成情况（用于严格模式）
            yesterday_completed_all = False
            if streak_rule == 'clear_all' and state.get('last_date'):
                tasks = get_tasks()
                enabled_tasks = [t for t in tasks if t.get('enabled', True)]
                defeated_yesterday = state.get('defeated_monsters', [])
                yesterday_completed_all = len(defeated_yesterday) == len(enabled_tasks) and len(enabled_tasks) > 0

            # 重置每周兑换记录（周一重置）
            last_date = datetime.strptime(state['last_date'], '%Y-%m-%d') if state.get('last_date') else None
            today_dt = datetime.strptime(today, '%Y-%m-%d')
            if last_date and last_date.weekday() > today_dt.weekday():
                state['weekly_exchanges'] = {}

            # ========== 重置当日任务进度 ==========
            state['defeated_monsters'] = []
            state['portal_used'] = False
            state['bonus_quests'] = []
            state['treasure_taken_today'] = False
            # ====================================

            # 计算连胜
            if state.get('last_date'):
                last = datetime.strptime(state['last_date'], '%Y-%m-%d').date()
                today_dt_obj = datetime.strptime(today, '%Y-%m-%d').date()
                if (today_dt_obj - last).days == 1:
                    if streak_rule == 'login':
                        state['streak'] = state.get('streak', 0) + 1
                    else:
                        if yesterday_completed_all:
                            state['streak'] = state.get('streak', 0) + 1
                        else:
                            state['streak'] = 1
                else:
                    state['streak'] = 1
            else:
                state['streak'] = 1

            state['last_date'] = today
            save_child_data({'child_id': child_id, 'state': state})
        return state
    else:
        # 新用户
        state = {
            'points': 0,
            'last_date': today,
            'streak': 1,
            'defeated_monsters': [],
            'portal_used': False,
            'bonus_quests': [],
            'exchange_history': [],
            'points_history': [],
            'weekly_exchanges': {},
        }
        save_child_data({'child_id': child_id, 'state': state})
        return state


def update_child_state(session_child_id, state):
    save_child_data({'child_id': session_child_id, 'state': state})


def add_points_record(session_child_id, state, source, change, desc):
    record = {
        'time': datetime.now().strftime('%m-%d %H:%M'),
        'source': source,
        'change': change,
        'description': desc,
        'total': state['points']
    }
    state['points_history'].insert(0, record)
    if len(state['points_history']) > 50:
        state['points_history'] = state['points_history'][:50]
    update_child_state(session_child_id, state)