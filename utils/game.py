import random
from datetime import datetime
from utils.data import get_loot_table, get_bonus_quests_pool

# 任务等级配置
TASK_RANKS = {
    'easy': {'range': (1, 4), 'tasks': ['起床', '物品归位', '晨间勇者']},
    'medium': {'range': (2, 6), 'tasks': ['阅读', '复习', '阅读冒险', '知识复习']},
    'hard': {'range': (3, 8), 'tasks': ['作业', '作业讨伐']}
}


def get_random_points_with_crit(base_min, base_max, crit_chance=0.2):
    """获取随机积分，20%概率暴击翻倍"""
    points = random.randint(base_min, base_max)
    is_crit = random.random() < crit_chance
    if is_crit:
        points = points * 2
    return points, is_crit


def get_task_rank(task_name):
    """根据任务名称判断难度等级"""
    for rank, info in TASK_RANKS.items():
        for keyword in info['tasks']:
            if keyword in task_name:
                return rank
    return 'medium'


def get_random_loot():
    """获取随机掉落道具"""
    loot_table = get_loot_table()
    if not loot_table:
        return {'name': '🍬 小糖果', 'add_points': 1, 'effect': '+1积分'}

    pool = []
    for item in loot_table:
        name = item['name']
        add_points = item['add_points']
        weight = item['weight']
        effect = item['effect']
        for _ in range(weight):
            pool.append((name, add_points, effect))
    chosen = random.choice(pool)
    return {'name': chosen[0], 'add_points': chosen[1], 'effect': chosen[2]}


def generate_bonus_quests():
    """生成随机彩蛋任务"""
    bonus_pool = get_bonus_quests_pool()
    if not bonus_pool:
        return []

    count = random.randint(2, 4)
    selected = random.sample(bonus_pool, min(count, len(bonus_pool)))
    return [{
        'name': q['name'],
        'desc': q['desc'],
        'points_range': q['points_range'],
        'completed': False,
        'id': q['id']
    } for q in selected]


def is_weekend():
    """判断今天是否是周末"""
    today = datetime.today().weekday()
    return today >= 5  # 5=周六, 6=周日


def check_time_limit(task_name):
    """
    检查任务的时间限制
    返回: (是否允许完成, 提示信息)
    """
    now = datetime.now()
    current_hour = now.hour
    current_minute = now.minute
    current_time = current_hour * 60 + current_minute

    # 起床：7:15前（7*60+15 = 435）
    if "起床" in task_name:
        if current_time > 435:
            return False, "⏰ 起床任务需要在7:15前完成！明天请早点起～"
        return True, ""

    # 作业：19:30前（19*60+30 = 1170）
    elif "作业" in task_name:
        if current_time > 1170:
            return False, "⏰ 作业需要在19:30前完成！明天记得早点写作业～"
        return True, ""

    # 其他任务无时间限制
    else:
        return True, ""


# ========== 计时任务相关 ==========

def calculate_reading_reward(minutes):
    """
    计算阅读/复习的积分奖励
    返回: (基础分, 奖励分, 总积分, 奖励描述)
    """
    if minutes < 15:
        return 0, 0, 0, "时长不足15分钟，无法完成"

    # 基础积分 3-6分随机（中难度）
    base_points = random.randint(3, 6)

    # 超额奖励：超过30分钟后，每20分钟+3分
    extra_points = 0
    if minutes > 30:
        extra_blocks = (minutes - 30) // 20
        extra_points = extra_blocks * 3

    total = base_points + extra_points

    reward_desc = f"学习了{minutes}分钟"
    if extra_points > 0:
        reward_desc += f"，基础{base_points}分 + 超额{extra_points}分"

    return base_points, extra_points, total, reward_desc


# ========== 运动任务相关 ==========

def calculate_sport_reward(minutes):
    """
    计算运动的积分奖励
    参数: minutes - 运动分钟数
    返回: (总积分, 积分描述)
    """
    if minutes < 10:
        return 0, f"运动时长不足10分钟（{minutes}分钟），无法完成"

    # 限制最多30分钟
    if minutes > 30:
        minutes = 30
        extra_note = "（超过30分钟按30分钟计算）"
    else:
        extra_note = ""

    # 计算积分：基础10分钟3分，之后每10分钟+2分
    if minutes >= 30:
        total = 7  # 3+2+2
    elif minutes >= 20:
        total = 5  # 3+2
    else:
        total = 3  # 3

    return total, f"运动{minutes}分钟{extra_note}，获得{total}积分"


def can_start_sport():
    """
    检查当前时间是否在 20:50 之前
    返回: (是否允许开始, 提示信息)
    """
    now = datetime.now()
    deadline = now.replace(hour=20, minute=50, second=0, microsecond=0)
    if now > deadline:
        return False, "⚠️ 运动时间已过（20:50后），明天早点来锻炼吧！"
    return True, ""


# ========== 跳绳任务相关 ==========

def calculate_jump_rope_reward(count):
    """
    计算跳绳任务的积分奖励
    参数: count - 跳绳个数
    返回: (总积分, 积分描述, 是否达标)
    """
    # 最低门槛 300 个
    if count < 300:
        return 0, f"跳绳不足300个（当前{count}个），还需继续努力！", False

    # 限制最多 1000 个
    original_count = count
    if count > 1000:
        count = 1000
        limit_note = "（超过1000个按1000个计算）"
    else:
        limit_note = ""

    # 基础积分 5-7 随机
    import random
    base_points = random.randint(5, 7)

    # 超额奖励：超过300后，每多100个 +2 分
    extra = 0
    if count > 300:
        extra_blocks = (count - 300) // 100
        extra = extra_blocks * 2

    total = base_points + extra

    reward_desc = f"跳绳{original_count}个{limit_note}，基础{base_points}分 + 超额{extra}分"

    return total, reward_desc, True


def can_start_jump_rope():
    """
    检查当前时间是否在 20:50 之前
    返回: (是否允许开始, 提示信息)
    跳绳任务复用运动任务的时间限制
    """
    from datetime import datetime
    now = datetime.now()
    deadline = now.replace(hour=20, minute=50, second=0, microsecond=0)
    if now > deadline:
        return False, "⚠️ 运动时间已过（20:50后），明天早点来锻炼吧！"
    return True, ""


# ========== 跳绳任务相关 ==========

# 用于存储每天的跳绳记录（内存缓存，实际应该存数据库）
jump_rope_daily_record = {}


def calculate_jump_rope_reward(count, child_id, is_first_of_day):
    """
    计算跳绳任务的积分奖励
    参数: count - 跳绳个数
          child_id - 孩子ID
          is_first_of_day - 是否是当天第一次跳绳
    返回: (总积分, 积分描述, 是否达标)
    """
    # 每日上限检查
    daily_total = jump_rope_daily_record.get(child_id, 0)
    if daily_total + count > 1000:
        remaining = 1000 - daily_total
        return 0, f"今日跳绳已达上限1000个，今日已跳{daily_total}个，最多还能跳{remaining}个！", False

    if is_first_of_day:
        # 首次跳绳：最低 300 个
        if count < 300:
            remaining = 300 - count
            return 0, f"跳绳不足300个（当前{count}个），还差{remaining}个，要继续努力哦！", False

        # 基础积分 5-8 随机
        import random
        base_points = random.randint(5, 8)

        # 超额奖励：超过300后，每多100个 +2 分
        extra = 0
        if count > 300:
            extra_blocks = (count - 300) // 100
            extra = extra_blocks * 2

        total = base_points + extra
        reward_desc = f"首次跳绳{count}个，基础{base_points}分 + 超额{extra}分"

        # 更新当日累计
        jump_rope_daily_record[child_id] = daily_total + count

        return total, reward_desc, True, True  # 最后一个是 is_first 标志

    else:
        # 后续跳绳：最低 100 个
        if count < 100:
            remaining = 100 - count
            return 0, f"跳绳不足100个（当前{count}个），还差{remaining}个才能获得积分哦！", False

        # 每满100个给2分
        blocks = count // 100
        total = blocks * 2
        reward_desc = f"跳绳{count}个，获得{total}分（每100个得2分）"

        # 更新当日累计
        jump_rope_daily_record[child_id] = daily_total + count

        return total, reward_desc, True, False


def can_start_jump_rope():
    """检查当前时间是否在 20:50 之前"""
    from datetime import datetime
    now = datetime.now()
    deadline = now.replace(hour=20, minute=50, second=0, microsecond=0)
    if now > deadline:
        return False, "⚠️ 运动时间已过（20:50后），明天早点来锻炼吧！"
    return True, ""


def reset_jump_rope_daily_record():
    """每天重置跳绳记录（应该在每日重置时调用）"""
    global jump_rope_daily_record
    jump_rope_daily_record = {}