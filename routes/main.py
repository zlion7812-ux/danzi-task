from flask import render_template, session, jsonify
from utils.data import get_tasks, get_monsters, get_child_state, get_config, get_shop_items
from datetime import date


def register_main_routes(app):
    @app.route('/')
    def index():
        child_id = session.get('child_id', 'default_child')
        state = get_child_state(child_id)
        tasks = get_tasks()
        monsters = get_monsters()
        config = get_config()
        streak_rule = config.get('streak_rule', 'login')

        enabled_tasks = [t for t in tasks if t.get('enabled', True)]
        defeated = state.get('defeated_monsters', [])

        required_percent = 0.8
        required_count = int(len(enabled_tasks) * required_percent)
        if required_count < 1 and len(enabled_tasks) > 0:
            required_count = 1
        all_defeated = len(defeated) >= required_count and len(enabled_tasks) > 0

        bonus_active = (state.get('bonus_quests') and len(state.get('bonus_quests', [])) > 0)

        monster_map = {m['id']: m for m in monsters}

        task_list = []
        for task in enabled_tasks:
            monster = monster_map.get(task['monster_id'])
            desc = task.get('description', '')

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
        from utils.data import reset_daily_tasks
        reset_daily_tasks(child_id)
        return {'status': 'ok'}

    @app.route('/reset_streak', methods=['POST'])
    def reset_streak():
        child_id = session.get('child_id', 'default_child')
        from utils.data import update_streak
        update_streak(child_id, 1)
        return {'status': 'ok'}

    @app.route('/tasks_list')
    def tasks_list():
        child_id = session.get('child_id', 'default_child')
        state = get_child_state(child_id)
        tasks = get_tasks()
        monsters = get_monsters()
        enabled_tasks = [t for t in tasks if t.get('enabled', True)]
        task_list = []
        for task in enabled_tasks:
            monster = next((m for m in monsters if m['id'] == task['monster_id']), None)
            icon = monster['icon'] if monster else '❓'
            task_list.append({
                'id': task['id'],
                'name': task['name'],
                'icon': icon,
            })
        return jsonify({
            'tasks': task_list,
            'completed_ids': state.get('defeated_monsters', [])
        })

    @app.route('/shop')
    def shop_page():
        child_id = session.get('child_id', 'default_child')
        state = get_child_state(child_id)
        shop_items = get_shop_items()
        return render_template('shop.html',
                               user_points=state['points'],
                               shop_items=shop_items)

    @app.route('/points')
    def points_page():
        child_id = session.get('child_id', 'default_child')
        state = get_child_state(child_id)
        points_history = state.get('points_history', [])[:30]
        return render_template('points.html',
                               user_points=state['points'],
                               points_history=points_history)

    @app.route('/monsters_map')
    def monsters_map():
        tasks = get_tasks()
        monsters = get_monsters()
        monster_map = {m['id']: m for m in monsters}

        result = {}
        for task in tasks:
            monster = monster_map.get(task['monster_id'])
            result[task['id']] = monster['icon'] if monster else '❓'
        return jsonify(result)

    @app.route('/active_timer_status')
    def active_timer_status():
        child_id = session.get('child_id', 'default_child')
        state = get_child_state(child_id)
        timer = state.get('active_timer')
        if timer:
            return jsonify({
                'active': True,
                'task_id': timer['task_id'],
                'task_name': timer['task_name'],
                'start_time': timer['start_time']
            })
        return jsonify({'active': False})

    @app.route('/task_detail/<task_id>')
    def task_detail(task_id):
        tasks = get_tasks()
        monsters = get_monsters()
        monster_map = {m['id']: m for m in monsters}

        task = next((t for t in tasks if t['id'] == task_id), None)
        if not task:
            return jsonify({'error': '任务不存在'}), 404

        monster = monster_map.get(task['monster_id'])

        return jsonify({
            'id': task['id'],
            'name': task['name'],
            'description': task.get('description', '暂无描述'),
            'points': task.get('points', 3),
            'monster_id': task['monster_id'],
            'monster_name': monster['name'] if monster else '未知怪物',
            'monster_icon': monster['icon'] if monster else '❓'
        })