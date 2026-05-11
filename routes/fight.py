from flask import request, jsonify, session
from datetime import datetime
import random
from utils.data import get_tasks, get_monsters, get_child_state, update_child_state, add_points_record, add_defeated_monster
from utils.game import get_task_rank, TASK_RANKS, get_random_points_with_crit, get_random_loot, check_time_limit, \
    calculate_reading_reward, calculate_sport_reward, can_start_sport, calculate_jump_rope_reward, can_start_jump_rope


def register_fight_routes(app):
    # ========== 复习/阅读/运动/跳绳：开始计时 ==========
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

        # 跳绳任务和运动任务：检查时间限制（20:50前）
        if "跳绳" in task_name or "运动" in task_name:
            if "跳绳" in task_name:
                can_start, sport_msg = can_start_jump_rope()
            else:
                can_start, sport_msg = can_start_sport()
            if not can_start:
                return jsonify({'error': sport_msg})

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

    # ========== 结束计时 ==========
    @app.route('/end_timer', methods=['POST'])
    def end_timer():
        data = request.get_json()
        task_name = data.get('task_name')
        jump_count = data.get('jump_count', None)

        child_id = session.get('child_id', 'default_child')
        state = get_child_state(child_id)

        if not state.get('active_timer'):
            return jsonify({'error': '没有进行中的任务'})

        timer = state['active_timer']
        if timer['task_name'] != task_name:
            return jsonify({'error': '任务名称不匹配'})

        tasks = get_tasks()
        monsters = get_monsters()
        task = next((t for t in tasks if t['id'] == timer['task_id']), None)
        if not task:
            return jsonify({'error': '任务不存在'})

        if timer['task_id'] in state.get('defeated_monsters', []):
            state['active_timer'] = None
            update_child_state(child_id, state)
            return jsonify({'error': '这个任务已经完成过了'})

        # ========== 跳绳任务：特殊积分计算 ==========
        if "跳绳" in task['name']:
            if jump_count is None:
                return jsonify({'error': '请输入跳绳个数'})

            total_points, reward_desc, is_qualified = calculate_jump_rope_reward(jump_count)

            if not is_qualified:
                return jsonify({'error': reward_desc})

            is_crit = random.random() < 0.2
            if is_crit:
                total_points = total_points * 2
                crit_text = " 💥暴击！💥"
            else:
                crit_text = ""

            state['points'] += total_points
            add_defeated_monster(child_id, timer['task_id'])
            add_points_record(child_id, '讨伐', total_points, f'完成任务: {task["name"]} ({reward_desc}){crit_text}', state['points'])

            loot = get_random_loot()
            loot_text = ""
            if loot['add_points'] > 0:
                state['points'] += loot['add_points']
                add_points_record(child_id, '魔法掉落', loot['add_points'], f'{loot["name"]}', state['points'])
                loot_text = f" 额外掉落 +{loot['add_points']}({loot['name']})"

            state['active_timer'] = None
            enabled_tasks = [t for t in tasks if t.get('enabled', True)]
            all_defeated = len(state['defeated_monsters']) == len(enabled_tasks)
            update_child_state(child_id, state)

            monster = next((m for m in monsters if m['id'] == task['monster_id']), None)
            monster_name = monster['name'] if monster else task['name']

            return jsonify({
                'status': 'ok',
                'message': f'🎉 {task["name"]}完成！{reward_desc}{crit_text}{loot_text}',
                'monster_name': monster_name,
                'points_earned': total_points,
                'jump_count': jump_count,
                'is_crit': is_crit,
                'loot_add': loot['add_points'],
                'loot_effect': loot['effect'],
                'all_defeated': all_defeated
            })

        # ========== 运动任务（原有逻辑） ==========
        elif "运动" in task['name']:
            start_time = datetime.fromisoformat(timer['start_time'])
            end_time = datetime.now()
            minutes = int((end_time - start_time).total_seconds() / 60)

            if minutes < 10:
                return jsonify({'error': f'运动时长不足10分钟（当前{minutes}分钟），无法完成'})

            total_points, reward_desc = calculate_sport_reward(minutes)
            if total_points == 0:
                return jsonify({'error': reward_desc})

            is_crit = random.random() < 0.2
            if is_crit:
                total_points = total_points * 2
                crit_text = " 💥暴击！💥"
            else:
                crit_text = ""

            state['points'] += total_points
            add_defeated_monster(child_id, timer['task_id'])
            add_points_record(child_id, '讨伐', total_points, f'完成任务: {task["name"]} ({reward_desc}){crit_text}', state['points'])

            loot = get_random_loot()
            loot_text = ""
            if loot['add_points'] > 0:
                state['points'] += loot['add_points']
                add_points_record(child_id, '魔法掉落', loot['add_points'], f'{loot["name"]}', state['points'])
                loot_text = f" 额外掉落 +{loot['add_points']}({loot['name']})"

            state['active_timer'] = None
            enabled_tasks = [t for t in tasks if t.get('enabled', True)]
            all_defeated = len(state['defeated_monsters']) == len(enabled_tasks)
            update_child_state(child_id, state)

            monster = next((m for m in monsters if m['id'] == task['monster_id']), None)
            monster_name = monster['name'] if monster else task['name']

            return jsonify({
                'status': 'ok',
                'message': f'🎉 {task["name"]}完成！{reward_desc}{crit_text}{loot_text}',
                'monster_name': monster_name,
                'points_earned': total_points,
                'minutes': minutes,
                'is_crit': is_crit,
                'loot_add': loot['add_points'],
                'loot_effect': loot['effect'],
                'all_defeated': all_defeated
            })

        # ========== 阅读/复习：原有积分计算 ==========
        else:
            start_time = datetime.fromisoformat(timer['start_time'])
            end_time = datetime.now()
            minutes = int((end_time - start_time).total_seconds() / 60)

            if minutes < 15:
                return jsonify({'error': f'时长不足15分钟（当前{minutes}分钟），请继续学习！'})

            base_points, extra_points, total_points, reward_desc = calculate_reading_reward(minutes)
            is_crit = random.random() < 0.2
            if is_crit:
                total_points = total_points * 2
                crit_text = " 💥暴击！💥"
            else:
                crit_text = ""

            state['points'] += total_points
            add_defeated_monster(child_id, timer['task_id'])
            add_points_record(child_id, '讨伐', total_points, f'完成任务: {task["name"]} ({reward_desc}){crit_text}', state['points'])

            loot = get_random_loot()
            loot_text = ""
            if loot['add_points'] > 0:
                state['points'] += loot['add_points']
                add_points_record(child_id, '魔法掉落', loot['add_points'], f'{loot["name"]}', state['points'])
                loot_text = f" 额外掉落 +{loot['add_points']}({loot['name']})"

            state['active_timer'] = None
            enabled_tasks = [t for t in tasks if t.get('enabled', True)]
            all_defeated = len(state['defeated_monsters']) == len(enabled_tasks)
            update_child_state(child_id, state)

            monster = next((m for m in monsters if m['id'] == task['monster_id']), None)
            monster_name = monster['name'] if monster else task['name']

            return jsonify({
                'status': 'ok',
                'message': f'🎉 {task["name"]}完成！{reward_desc}{crit_text}{loot_text}',
                'monster_name': monster_name,
                'points_earned': total_points,
                'minutes': minutes,
                'is_crit': is_crit,
                'loot_add': loot['add_points'],
                'loot_effect': loot['effect'],
                'all_defeated': all_defeated
            })

    # ========== 普通任务（起床、作业、物品归位） ==========
    @app.route('/fight', methods=['POST'])
    def fight():
        try:
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

            if "起床" not in task['name'] and "运动" not in task['name'] and "跳绳" not in task['name']:
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
                    rank = get_task_rank(task['name'])
                    rank_range = TASK_RANKS[rank]['range']
                    base_min, base_max = rank_range
                    points_earned, is_crit = get_random_points_with_crit(base_min, base_max)
                    crit_text = " 💥暴击！💥" if is_crit else ""
                    message_suffix = f"获得 {points_earned} 金币{crit_text}"

                    state['points'] += points_earned
                    add_defeated_monster(child_id, task_id)
                    add_points_record(child_id, '讨伐', points_earned, f'完成任务: {task["name"]} (早起){crit_text}', state['points'])

                    loot = get_random_loot()
                    loot_text = ""
                    if loot['add_points'] > 0:
                        state['points'] += loot['add_points']
                        add_points_record(child_id, '魔法掉落', loot['add_points'], f'{loot["name"]}', state['points'])
                        loot_text = f" 额外掉落 +{loot['add_points']}({loot['name']})"
                else:
                    points_earned = 1
                    is_crit = False
                    crit_text = ""
                    message_suffix = f"获得 {points_earned} 金币（迟到了，明天早点起哦）"

                    state['points'] += points_earned
                    add_defeated_monster(child_id, task_id)
                    add_points_record(child_id, '讨伐', points_earned, f'完成任务: {task["name"]} (迟到)', state['points'])
                    loot_text = ""
                    loot = {'add_points': 0, 'effect': '无掉落', 'name': ''}

                all_defeated = len(state['defeated_monsters']) == len(enabled_tasks)
                update_child_state(child_id, state)

                return jsonify({
                    'message': f'{message_suffix}{loot_text}',
                    'monster_name': monster_name,
                    'base_points': points_earned,
                    'is_crit': is_crit,
                    'loot_add': loot.get('add_points', 0),
                    'loot_effect': loot.get('effect', ''),
                    'loot_name': loot.get('name', ''),
                    'all_defeated': all_defeated,
                    'points_earned': points_earned + loot.get('add_points', 0),
                    'error': None
                })

            # ========== 其他普通任务（作业、物品归位） ==========
            rank = get_task_rank(task['name'])
            rank_range = TASK_RANKS[rank]['range']
            base_min, base_max = rank_range
            points_earned, is_crit = get_random_points_with_crit(base_min, base_max)
            crit_text = " 💥暴击！💥" if is_crit else ""

            state['points'] += points_earned
            add_defeated_monster(child_id, task_id)
            add_points_record(child_id, '讨伐', points_earned, f'完成任务: {task["name"]}{crit_text}', state['points'])

            loot = get_random_loot()
            loot_text = ""
            if loot['add_points'] > 0:
                state['points'] += loot['add_points']
                add_points_record(child_id, '魔法掉落', loot['add_points'], f'{loot["name"]}', state['points'])
                loot_text = f" 额外掉落 +{loot['add_points']}({loot['name']})"

            all_defeated = len(state['defeated_monsters']) == len(enabled_tasks)
            update_child_state(child_id, state)

            return jsonify({
                'message': f'讨伐成功！获得 {points_earned} 金币{crit_text}{loot_text}',
                'monster_name': monster_name,
                'base_points': points_earned,
                'is_crit': is_crit,
                'loot_add': loot.get('add_points', 0),
                'loot_effect': loot.get('effect', ''),
                'loot_name': loot.get('name', ''),
                'all_defeated': all_defeated,
                'points_earned': points_earned + loot.get('add_points', 0),
                'error': None
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)})

    # ========== 以下路由保持不变（portal, complete_bonus, treasure） ==========
    @app.route('/portal', methods=['POST'])
    def portal():
        child_id = session.get('child_id', 'default_child')
        state = get_child_state(child_id)
        tasks = get_tasks()
        enabled_tasks = [t for t in tasks if t.get('enabled', True)]

        required_percent = 0.8
        required_count = int(len(enabled_tasks) * required_percent)
        if required_count < 1 and len(enabled_tasks) > 0:
            required_count = 1

        if len(state.get('defeated_monsters', [])) < required_count:
            return jsonify(
                {'error': f'需要完成至少 {required_count} 个任务才能开启传送门（共{len(enabled_tasks)}个任务）'})

        if state.get('portal_used', False):
            return jsonify({'error': '传送门今日已经开启过了'})

        state['portal_used'] = True
        from utils.game import generate_bonus_quests
        bonus_quests = generate_bonus_quests()
        state['bonus_quests'] = bonus_quests
        from utils.data import save_bonus_quests
        save_bonus_quests(child_id, bonus_quests)
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

        points_range = quest.get('points_range', [1, 4])
        points_earned, is_crit = get_random_points_with_crit(points_range[0], points_range[1])

        state['points'] += points_earned
        crit_text = " 💥暴击！💥" if is_crit else ""
        add_points_record(child_id, '彩蛋', points_earned, f'完成: {quest["name"]}{crit_text}', state['points'])

        quest['completed'] = True
        state['bonus_quests'] = bonus_list
        from utils.data import save_bonus_quests
        save_bonus_quests(child_id, bonus_list)
        update_child_state(child_id, state)

        loot = get_random_loot()
        loot_text = ""
        if loot['add_points'] > 0:
            state['points'] += loot['add_points']
            add_points_record(child_id, '彩蛋掉落', loot['add_points'], loot['name'], state['points'])
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
        add_points_record(child_id, '全清宝藏', points_earned, f'全清宝箱奖励{crit_text}', state['points'])
        state['treasure_taken_today'] = True
        update_child_state(child_id, state)

        return jsonify({
            'loot_info': f'🎉 全清宝箱奖励 🎉 +{points_earned}金币{crit_text}',
            'reward_points': points_earned,
            'is_crit': is_crit
        })