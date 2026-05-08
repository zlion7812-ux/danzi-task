from flask import render_template, session
from utils.data import get_tasks, get_monsters, get_child_state, get_config, get_shop_items, get_task_details


def register_main_routes(app):
    @app.route('/')
    def index():
        child_id = session.get('child_id', 'default_child')
        state = get_child_state(child_id)
        tasks = get_tasks()
        monsters = get_monsters()
        config = get_config()
        streak_rule = config.get('streak_rule', 'login')
        task_details = get_task_details()

        enabled_tasks = [t for t in tasks if t.get('enabled', True)]
        defeated = state.get('defeated_monsters', [])

        # ========== 传送门条件：完成 80% 的任务即可 ==========
        required_percent = 0.8
        required_count = int(len(enabled_tasks) * required_percent)
        if required_count < 1 and len(enabled_tasks) > 0:
            required_count = 1
        all_defeated = len(defeated) >= required_count and len(enabled_tasks) > 0
        # ===================================================

        bonus_active = (state.get('bonus_quests') and len(state.get('bonus_quests', [])) > 0)

        # 构建怪物 ID 到怪物信息的映射字典（提高匹配效率）
        monster_map = {m['id']: m for m in monsters}

        task_list = []
        for task in enabled_tasks:
            # 使用映射字典快速查找怪物
            monster = monster_map.get(task['monster_id'])
            desc = task_details.get(task['name'], task.get('description', ''))

            if monster:
                task_list.append({
                    'id': task['id'],
                    'name': task['name'],
                    'description': desc,
                    'points': task['points'],
                    'icon': monster['icon'],
                    'monster_name': monster['name']
                })
            else:
                # 如果找不到怪物，使用默认问号图标
                task_list.append({
                    'id': task['id'],
                    'name': task['name'],
                    'description': desc,
                    'points': task['points'],
                    'icon': '❓',
                    'monster_name': '未知怪物'
                })

        shop_items = get_shop_items()

        rule_display = "🟢 宽松模式" if streak_rule == "login" else "🔴 严格模式"
        rule_tip = "登录即涨连胜" if streak_rule == "login" else "必须全清才涨连胜"

        return render_template('index.html',
                               tasks=task_list,
                               defeated_ids=defeated,
                               all_defeated=all_defeated,
                               portal_used=state.get('portal_used', False),
                               bonus_active=bonus_active,
                               bonus_quests=state.get('bonus_quests', []),
                               user_points=state['points'],
                               streak=state['streak'],
                               shop_items=shop_items,
                               exchange_history=state.get('exchange_history', [])[:20][::-1],
                               points_history=state.get('points_history', [])[:30],
                               rule_display=rule_display,
                               rule_tip=rule_tip)

    @app.route('/status')
    def status():
        child_id = session.get('child_id', 'default_child')
        state = get_child_state(child_id)
        return {'points': state['points'], 'streak': state['streak']}

    @app.route('/reset_day', methods=['POST'])
    def reset_day():
        child_id = session.get('child_id', 'default_child')
        state = get_child_state(child_id)
        state['defeated_monsters'] = []
        state['portal_used'] = False
        state['bonus_quests'] = []
        state['treasure_taken_today'] = False
        from utils.data import update_child_state
        update_child_state(child_id, state)
        return {'status': 'ok'}

    @app.route('/reset_streak', methods=['POST'])
    def reset_streak():
        child_id = session.get('child_id', 'default_child')
        state = get_child_state(child_id)
        state['streak'] = 1
        from utils.data import update_child_state
        update_child_state(child_id, state)
        return {'status': 'ok'}