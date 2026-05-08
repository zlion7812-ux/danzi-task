from flask import request, jsonify, session
from datetime import datetime
from utils.data import get_tasks, get_monsters, get_child_state, update_child_state, add_points_record
from utils.game import get_task_rank, TASK_RANKS, get_random_points_with_crit, get_random_loot, check_time_limit, \
    calculate_reading_reward


def register_fight_routes(app):
    # ========== 复习/阅读：开始计时 ==========
    @app.route('/start_timer', methods=['POST'])
    def start_timer():
        data = request.get_json()
        task_id = data.get('task_id')
        task_name = data.get('task_name')

        child_id = session.get('child_id', 'default_child')
        state = get_child_state(child_id)

        if state.get('active_timer'):
            return jsonify({'error': '已有进行中的任务，请先结束当前任务'})

        if task_id in state.get('defeated_monsters', []):
            return jsonify({'error': '这个任务今天已经完成过了'})

        can_complete, time_msg = check_time_limit(task_name)
        if not can_complete:
            return jsonify({'error': time_msg})

        state['active_timer'] = {
            'task_id': task_id,
            'task_name': task_name,
            'start_time': datetime.now().isoformat()
        }
        update_child_state(child_id, state)

        return jsonify({
            'status': 'ok',
            'message': f'⏰ 开始{task_name}！加油～'
        })

    # ========== 复习/阅读：结束计时 ==========
    @app.route('/end_timer', methods=['POST'])
    def end_timer():
        data = request.get_json()
        task_name = data.get('task_name')

        child_id = session.get('child_id', 'default_child')
        state = get_child_state(child_id)

        if not state.get('active_timer'):
            return jsonify({'error': '没有进行中的任务'})

        timer = state['active_timer']
        if timer['task_name'] != task_name:
            return jsonify({'error': '任务名称不匹配'})

        start_time = datetime.fromisoformat(timer['start_time'])
        end_time = datetime.now()
        minutes = int((end_time - start_time).total_seconds() / 60)

        if minutes < 15:
            return jsonify({'error': f'时长不足15分钟（当前{minutes}分钟），请继续学习！'})

        tasks = get_tasks()
        monsters = get_monsters()
        task = next((t for t in tasks if t['id'] == timer['task_id']), None)
        if not task:
            return jsonify({'error': '任务不存在'})

        if timer['task_id'] in state.get('defeated_monsters', []):
            state['active_timer'] = None
            update_child_state(child_id, state)
            return jsonify({'error': '这个任务已经完成过了'})

        base_points, extra_points, total_points, reward_desc = calculate_reading_reward(minutes)

        import random
        is_crit = random.random() < 0.2
        if is_crit:
            total_points = total_points * 2
            crit_text = " 💥暴击！💥"
        else:
            crit_text = ""

        state['points'] += total_points
        add_points_record(child_id, state, '讨伐', total_points, f'完成任务: {task["name"]} ({reward_desc}){crit_text}')

        loot = get_random_loot()
        loot_text = ""
        if loot['add_points'] > 0:
            state['points'] += loot['add_points']
            add_points_record(child_id, state, '魔法掉落', loot['add_points'], f'{loot["name"]}')
            loot_text = f" 额外掉落 +{loot['add_points']}({loot['name']})"

        state.setdefault('defeated_monsters', []).append(timer['task_id'])
        state['active_timer'] = None

        enabled_tasks = [t for t in tasks if t.get('enabled', True)]
        all_defeated = len(state['defeated_monsters']) == len(enabled_tasks)
        update_child_state(child_id, state)

        monster = next((m for m in monsters if m['id'] == task['monster_id']), None)
        monster_name = monster['name'] if monster else task['name']

        return jsonify({
            'status': 'ok',
            'message': f'🎉 {task["name"]}完成！学习了{minutes}分钟，获得{total_points}金币{crit_text}{loot_text}',
            'monster_name': monster_name,
            'points_earned': total_points,
            'minutes': minutes,
            'is_crit': is_crit,
            'loot_add': loot['add_points'],
            'loot_effect': loot['effect'],
            'all_defeated': all_defeated
        })

    # ========== 普通任务（起床、作业、物品归位）的原有逻辑 ==========
    @app.route('/fight', methods=['POST'])
    def fight():
        data = request.get_json()
        task_id = data.get('task_id')
        if not task_id:
            return jsonify({'error': '任务ID不能为空'})

        child_id = session.get('child_id', 'default_child')
        state = get_child_state(child_id)
        tasks = get_tasks()
        monsters = get_monsters()
        enabled_tasks = [t for t in tasks if t.get('enabled', True)]

        task = next((t for t in enabled_tasks if t['id'] == task_id), None)
        if not task:
            return jsonify({'error': f'任务不存在: {task_id}'})

        # 时间限制检查（作业、物品归位等）
        can_complete, time_msg = check_time_limit(task['name'])
        if not can_complete:
            return jsonify({'error': time_msg})

        if task_id in state.get('defeated_monsters', []):
            return jsonify({'error': '这只怪物已经讨伐过了！'})

        monster = next((m for m in monsters if m['id'] == task['monster_id']), None)
        monster_name = monster['name'] if monster else task['name']

        # ========== 起床任务特殊处理 ==========
        if "起床" in task['name']:
            now = datetime.now()
            morning_deadline = now.replace(hour=7, minute=15, second=0, microsecond=0)
            is_early = now <= morning_deadline

            if is_early:
                # 早起：随机 1-4 分 + 暴击
                rank = get_task_rank(task['name'])
                rank_range = TASK_RANKS[rank]['range']
                base_min, base_max = rank_range
                points_earned, is_crit = get_random_points_with_crit(base_min, base_max)
                crit_text = " 💥暴击！💥" if is_crit else ""
                message_suffix = f"获得 {points_earned} 金币{crit_text}"
                add_points_record(child_id, state, '讨伐', points_earned, f'完成任务: {task["name"]} (早起){crit_text}')
            else:
                # 迟到：固定 1 分，无暴击无掉落
                points_earned = 1
                is_crit = False
                crit_text = ""
                message_suffix = f"获得 {points_earned} 金币（迟到了，明天早点起哦）"
                add_points_record(child_id, state, '讨伐', points_earned, f'完成任务: {task["name"]} (迟到)')
                # 迟到不触发掉落
                state['points'] += points_earned
                state.setdefault('defeated_monsters', []).append(task_id)
                all_defeated = len(state['defeated_monsters']) == len(enabled_tasks)
                update_child_state(child_id, state)
                return jsonify({
                    'message': f'😴 起床晚了！{message_suffix}',
                    'monster_name': monster_name,
                    'base_points': points_earned,
                    'is_crit': False,
                    'loot_add': 0,
                    'loot_effect': '无掉落',
                    'loot_name': '',
                    'all_defeated': all_defeated
                })
        else:
            # 普通任务（作业、物品归位）
            rank = get_task_rank(task['name'])
            rank_range = TASK_RANKS[rank]['range']
            base_min, base_max = rank_range
            points_earned, is_crit = get_random_points_with_crit(base_min, base_max)
            crit_text = " 💥暴击！💥" if is_crit else ""
            message_suffix = f"获得 {points_earned} 金币{crit_text}"
            add_points_record(child_id, state, '讨伐', points_earned, f'完成任务: {task["name"]}{crit_text}')

        # 增加积分（早起或普通任务）
        if "起床" not in task['name'] or (
                "起床" in task['name'] and datetime.now() <= datetime.now().replace(hour=7, minute=15, second=0,
                                                                                    microsecond=0)):
            state['points'] += points_earned

        # 随机掉落（迟到不触发）
        loot = get_random_loot()
        loot_text = ""
        if loot['add_points'] > 0 and not (
                "起床" in task['name'] and datetime.now() > datetime.now().replace(hour=7, minute=15, second=0,
                                                                                   microsecond=0)):
            state['points'] += loot['add_points']
            add_points_record(child_id, state, '魔法掉落', loot['add_points'], f'{loot["name"]}')
            loot_text = f" 额外掉落 +{loot['add_points']}({loot['name']})"

        state.setdefault('defeated_monsters', []).append(task_id)
        all_defeated = len(state['defeated_monsters']) == len(enabled_tasks)
        update_child_state(child_id, state)

        return jsonify({
            'message': f'讨伐成功！{message_suffix}{loot_text}',
            'monster_name': monster_name,
            'base_points': points_earned,
            'is_crit': is_crit,
            'loot_add': loot['add_points'],
            'loot_effect': loot['effect'],
            'loot_name': loot['name'],
            'all_defeated': all_defeated
        })

    # ========== 传送门和彩蛋任务 ==========
    @app.route('/portal', methods=['POST'])
    def portal():
        child_id = session.get('child_id', 'default_child')
        state = get_child_state(child_id)
        tasks = get_tasks()
        enabled_tasks = [t for t in tasks if t.get('enabled', True)]
        if len(state.get('defeated_monsters', [])) != len(enabled_tasks):
            return jsonify({'error': '必须讨伐全部怪物才能开启传送门'})
        if state.get('portal_used', False):
            return jsonify({'error': '传送门今日已经开启过了'})
        state['portal_used'] = True
        from utils.game import generate_bonus_quests
        state['bonus_quests'] = generate_bonus_quests()
        update_child_state(child_id, state)
        return jsonify({'status': 'ok'})

    @app.route('/complete_bonus', methods=['POST'])
    def complete_bonus():
        data = request.get_json()
        idx = data['bonus_index']
        child_id = session.get('child_id', 'default_child')
        state = get_child_state(child_id)
        bonus_list = state.get('bonus_quests', [])
        if idx >= len(bonus_list):
            return jsonify({'error': '任务不存在'})
        quest = bonus_list[idx]
        if quest.get('completed', False):
            return jsonify({'error': '这个彩蛋任务已经完成过了'})

        points_earned, is_crit = get_random_points_with_crit(1, 4)
        state['points'] += points_earned
        crit_text = " 💥暴击！💥" if is_crit else ""
        add_points_record(child_id, state, '彩蛋', points_earned, f'完成: {quest["name"]}{crit_text}')
        quest['completed'] = True
        state['bonus_quests'] = bonus_list
        update_child_state(child_id, state)

        loot = get_random_loot()
        loot_text = ""
        if loot['add_points'] > 0:
            state['points'] += loot['add_points']
            add_points_record(child_id, state, '彩蛋掉落', loot['add_points'], loot['name'])
            loot_text = f" 额外掉落 +{loot['add_points']}({loot['name']})"
            update_child_state(child_id, state)

        return jsonify({
            'quest_name': quest['name'],
            'points': points_earned,
            'is_crit': is_crit,
            'loot_effect': f"获得 {points_earned} 金币{crit_text}{loot_text}"
        })

    @app.route('/treasure', methods=['POST'])
    def treasure():
        child_id = session.get('child_id', 'default_child')
        state = get_child_state(child_id)
        tasks = get_tasks()
        enabled_tasks = [t for t in tasks if t.get('enabled', True)]
        if len(state.get('defeated_monsters', [])) != len(enabled_tasks):
            return jsonify({'error': '必须完成全部任务才能开启宝箱'})
        if state.get('treasure_taken_today', False):
            return jsonify({'error': '今天的宝箱已经开启过了'})

        points_earned, is_crit = get_random_points_with_crit(5, 8)
        state['points'] += points_earned
        crit_text = " 💥暴击！💥" if is_crit else ""
        add_points_record(child_id, state, '全清宝藏', points_earned, f'全清宝箱奖励{crit_text}')
        state['treasure_taken_today'] = True
        update_child_state(child_id, state)

        return jsonify({
            'loot_info': f'🎉 全清宝箱奖励 🎉 +{points_earned}金币{crit_text}',
            'reward_points': points_earned,
            'is_crit': is_crit
        })