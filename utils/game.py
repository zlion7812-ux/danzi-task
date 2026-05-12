import random
from datetime import datetime
from utils.data import get_loot_table, get_bonus_quests_pool, get_today_jump_total

TASK_RANKS = {
    'easy': {'range': (1, 4), 'tasks': ['起床', '物品归位', '晨间勇者']},
    'medium': {'range': (2, 6), 'tasks': ['阅读', '复习', '阅读冒险', '知识复习']},
    'hard': {'range': (3, 8), 'tasks': ['作业', '作业讨伐', '每日背诵']}
}


def get_random_points_with_crit(base_min, base_max, crit_chance=0.2):
    points = random.randint(base_min, base_max)
    is_crit = random.random() < crit_chance
    if is_crit:
        points = points * 2
    return points, is_crit


def get_task_rank(task_name):
    for rank, info in TASK_RANKS.items():
        for keyword in info['tasks']:
            if keyword in task_name:
                return rank
    return 'medium'


def get_random_loot():
    loot_table = get_loot_table()
    if not loot_table:
        return {'name': '🍬 小糖果', 'add_points': 1, 'effect': '+1积分'}
    pool = []
    for item in loot_table:
        for _ in range(item['weight']):
            pool.append((item['name'], item['add_points'], item['effect']))
    chosen = random.choice(pool)
    return {'name': chosen[0], 'add_points': chosen[1], 'effect': chosen[2]}


def generate_bonus_quests():
    bonus_pool = get_bonus_quests_pool()
    if not bonus_pool:
        return []
    count = random.randint(2, 4)
    selected = random.sample(bonus_pool, min(count, len(bonus_pool)))
    return [{
        'name': q['name'], 'desc': q['desc'],
        'points_range': q['points_range'], 'completed': False, 'id': q['id']
    } for q in selected]


def is_weekend():
    return datetime.today().weekday() >= 5


def check_time_limit(task_name):
    now = datetime.now()
    current_time = now.hour * 60 + now.minute
    if "起床" in task_name:
        if current_time > 435:
            return False, "⏰ 起床任务需要在7:15前完成！明天请早点起～"
    elif "作业" in task_name:
        if current_time > 1200:
            return False, "⏰ 作业需要在20:00前完成！明天记得早点写作业～"
    return True, ""


def calculate_reading_reward(minutes):
    if minutes < 15:
        return 0, 0, 0, "时长不足15分钟，无法完成"
    base_points = random.randint(3, 6)
    extra_points = 0
    if minutes > 30:
        extra_blocks = (minutes - 30) // 20
        extra_points = extra_blocks * 3
    total = base_points + extra_points
    reward_desc = f"学习了{minutes}分钟"
    if extra_points > 0:
        reward_desc += f"，基础{base_points}分 + 超额{extra_points}分"
    return base_points, extra_points, total, reward_desc


def calculate_sport_reward(minutes):
    if minutes < 10:
        return 0, f"运动时长不足10分钟（{minutes}分钟），无法完成"
    if minutes > 30:
        minutes = 30
        extra_note = "（超过30分钟按30分钟计算）"
    else:
        extra_note = ""
    if minutes >= 30:
        total = 7
    elif minutes >= 20:
        total = 5
    else:
        total = 3
    return total, f"运动{minutes}分钟{extra_note}，获得{total}积分"


def can_start_sport():
    now = datetime.now()
    deadline = now.replace(hour=20, minute=50, second=0, microsecond=0)
    if now > deadline:
        return False, "⚠️ 运动时间已过（20:50后），明天早点来锻炼吧！"
    return True, ""


def can_start_jump_rope():
    return can_start_sport()


def calculate_jump_rope_reward(count, child_id, is_first_today):
    """计算跳绳奖励
    返回: {
        'success': bool,
        'message': str,
        'total_points': int,
        'is_crit': bool,
        'loot': dict
    }
    """
    if count <= 0:
        return {'success': False, 'message': '请输入有效的跳绳个数', 'total_points': 0, 'is_crit': False,
                'loot': {'add_points': 0, 'name': ''}}

    if count > 1000:
        return {'success': False, 'message': '每次跳绳不能超过1000个！', 'total_points': 0, 'is_crit': False,
                'loot': {'add_points': 0, 'name': ''}}

    today_total = get_today_jump_total(child_id)
    if today_total + count > 1000:
        remaining = 1000 - today_total
        return {'success': False, 'message': f'今日跳绳已达上限1000个，今日已跳{today_total}个，最多还能跳{remaining}个！',
                'total_points': 0, 'is_crit': False, 'loot': {'add_points': 0, 'name': ''}}

    if is_first_today:
        if count < 300:
            remaining = 300 - count
            return {'success': False, 'message': f'首次跳绳不足300个（当前{count}个），还差{remaining}个，要继续努力哦！',
                    'total_points': 0, 'is_crit': False, 'loot': {'add_points': 0, 'name': ''}}

        base_points = random.randint(5, 8)
        extra = 0
        if count > 300:
            extra_blocks = (count - 300) // 100
            extra = extra_blocks * 2
        total_points = base_points + extra
        reward_desc = f"首次跳绳{count}个，基础{base_points}分 + 超额{extra}分"

        is_crit = random.random() < 0.2
        if is_crit:
            total_points = total_points * 2
            reward_desc += " 💥暴击！💥"

        loot = get_random_loot() if random.random() < 0.3 else {'add_points': 0, 'name': '', 'effect': ''}

        return {
            'success': True,
            'message': reward_desc,
            'total_points': total_points,
            'is_crit': is_crit,
            'loot': loot
        }
    else:
        if count < 100:
            remaining = 100 - count
            return {'success': False, 'message': f'跳绳不足100个（当前{count}个），还差{remaining}个才能获得积分哦！',
                    'total_points': 0, 'is_crit': False, 'loot': {'add_points': 0, 'name': ''}}

        blocks = count // 100
        total_points = blocks * 2
        reward_desc = f"跳绳{count}个，获得{total_points}分（每100个得2分）"

        return {
            'success': True,
            'message': reward_desc,
            'total_points': total_points,
            'is_crit': False,
            'loot': {'add_points': 0, 'name': '', 'effect': ''}
        }