from flask import render_template, request, session, jsonify, redirect, url_for
from utils.auth import login_required
from utils.data import get_tasks, get_monsters, get_config, save_tasks, save_monsters, save_config, reset_daily_tasks, \
    update_streak, get_child_state, update_child_state, add_points_record, get_shop_items, add_shop_item, update_shop_item, delete_shop_item
import os
import json

DB_FILE = 'danzi_data.db'


def register_admin_routes(app):
    @app.route('/admin/login', methods=['GET', 'POST'])
    def admin_login():
        if request.method == 'POST':
            password = request.form.get('password')
            config = get_config()
            if password == config.get('admin_password', 'admin123'):
                session['admin_logged_in'] = True
                return redirect(url_for('admin'))
            else:
                return '<h3>密码错误</h3><a href="/admin/login">重新登录</a>'
        return '''
            <!DOCTYPE html>
            <html>
            <head><meta charset="UTF-8"><title>管理员登录</title><style>body{background:#1a1a2e;font-family:sans-serif;display:flex;justify-content:center;align-items:center;height:100vh;} .card{background:#16213e;padding:30px;border-radius:20px;} input{padding:10px;margin:10px 0;width:100%;} button{background:#44aa44;padding:10px;border:none;color:white;width:100%;cursor:pointer;}</style></head>
            <body><div class="card"><h2>🐉 管理员登录</h2><form method="post"><input type="password" name="password" placeholder="请输入密码" autofocus><button type="submit">登录</button></form></div></body>
            </html>
        '''

    @app.route('/admin')
    @login_required
    def admin():
        return render_template('admin.html')

    @app.route('/admin/data')
    @login_required
    def admin_data():
        tasks = get_tasks()
        monsters = get_monsters()
        config = get_config()
        return jsonify({'tasks': tasks, 'monsters': monsters, 'config': config})

    @app.route('/admin/task/<task_id>')
    @login_required
    def admin_get_task(task_id):
        tasks = get_tasks()
        task = next((t for t in tasks if t['id'] == task_id), None)
        if not task:
            return jsonify({'error': '任务不存在'}), 404
        return jsonify(task)

    @app.route('/admin/update_task', methods=['POST'])
    @login_required
    def admin_update_task():
        data = request.get_json()
        task_id = data.get('task_id')
        tasks = get_tasks()
        task = next((t for t in tasks if t['id'] == task_id), None)
        if not task:
            return jsonify({'error': '任务不存在'}), 404
        task['name'] = data.get('name', task['name'])
        task['monster_id'] = data.get('monster_id', task['monster_id'])
        task['points'] = data.get('points', task['points'])
        task['order'] = data.get('order', task.get('order', 999))
        task['description'] = data.get('description', task.get('description', ''))
        task['enabled'] = data.get('enabled', task.get('enabled', True))
        save_tasks(tasks)
        return jsonify({'status': 'ok', 'task': task})

    @app.route('/admin/add_task', methods=['POST'])
    @login_required
    def admin_add_task():
        data = request.get_json()
        tasks = get_tasks()
        import uuid
        new_id = f"task_{uuid.uuid4().hex[:8]}"
        max_order = max([t.get('order', 0) for t in tasks]) if tasks else 0
        new_task = {
            'id': new_id,
            'name': data.get('name', '新任务'),
            'monster_id': data.get('monster_id'),
            'points': data.get('points', 3),
            'order': data.get('order', max_order + 1),
            'description': data.get('description', ''),
            'enabled': data.get('enabled', True)
        }
        tasks.append(new_task)
        save_tasks(tasks)
        return jsonify({'status': 'ok', 'task': new_task})

    @app.route('/admin/delete_task', methods=['POST'])
    @login_required
    def admin_delete_task():
        data = request.get_json()
        tasks = get_tasks()
        tasks = [t for t in tasks if t['id'] != data['task_id']]
        save_tasks(tasks)
        return jsonify({'status': 'ok'})

    @app.route('/admin/add_monster', methods=['POST'])
    @login_required
    def admin_add_monster():
        data = request.get_json()
        monsters = get_monsters()
        import uuid
        new_id = f"mon_{uuid.uuid4().hex[:8]}"
        new_monster = {
            'id': new_id,
            'name': data['name'],
            'icon': data.get('icon', '👾'),
            'default_points': data['default_points'],
            'description': data.get('description', '')
        }
        monsters.append(new_monster)
        save_monsters(monsters)
        return jsonify({'status': 'ok'})

    @app.route('/admin/update_monster', methods=['POST'])
    @login_required
    def admin_update_monster():
        data = request.get_json()
        monsters = get_monsters()
        for monster in monsters:
            if monster['id'] == data['monster_id']:
                monster['name'] = data['name']
                monster['icon'] = data.get('icon', '👾')
                monster['default_points'] = data['default_points']
                monster['description'] = data.get('description', '')
                break
        save_monsters(monsters)
        return jsonify({'status': 'ok'})

    @app.route('/admin/delete_monster', methods=['POST'])
    @login_required
    def admin_delete_monster():
        data = request.get_json()
        monsters = get_monsters()
        monsters_to_save = [m for m in monsters if m['id'] != data['monster_id']]
        save_monsters(monsters_to_save)
        return jsonify({'status': 'ok'})

    # ========== 商品管理接口 ==========
    @app.route('/admin/shop_items')
    @login_required
    def admin_get_shop_items():
        items = get_shop_items()
        return jsonify(items)

    @app.route('/admin/shop_item/<int:item_id>')
    @login_required
    def admin_get_shop_item(item_id):
        items = get_shop_items()
        item = next((i for i in items if i['id'] == item_id), None)
        if not item:
            return jsonify({'error': '商品不存在'}), 404
        return jsonify(item)

    @app.route('/admin/add_shop_item', methods=['POST'])
    @login_required
    def admin_add_shop_item():
        data = request.get_json()
        new_item = add_shop_item(data)
        return jsonify({'status': 'ok', 'item': new_item})

    @app.route('/admin/update_shop_item', methods=['POST'])
    @login_required
    def admin_update_shop_item():
        data = request.get_json()
        item_id = data.get('id')
        if not item_id:
            return jsonify({'error': '商品ID不能为空'}), 400
        update_shop_item(item_id, data)
        return jsonify({'status': 'ok'})

    @app.route('/admin/delete_shop_item', methods=['POST'])
    @login_required
    def admin_delete_shop_item():
        data = request.get_json()
        item_id = data.get('id')
        if not item_id:
            return jsonify({'error': '商品ID不能为空'}), 400
        success = delete_shop_item(item_id)
        if success:
            return jsonify({'status': 'ok'})
        else:
            return jsonify({'error': '商品不存在'}), 404

    @app.route('/admin/update_config', methods=['POST'])
    @login_required
    def admin_update_config():
        data = request.get_json()
        config = get_config()
        if 'streak_rule' in data:
            config['streak_rule'] = data['streak_rule']
        if 'admin_password' in data and data['admin_password']:
            config['admin_password'] = data['admin_password']
        save_config(config)
        return jsonify({'status': 'ok'})

    @app.route('/logout')
    def logout():
        session.pop('admin_logged_in', None)
        return redirect(url_for('index'))

    @app.route('/admin/reset_child_day', methods=['POST'])
    @login_required
    def admin_reset_child_day():
        child_id = 'default_child'
        reset_daily_tasks(child_id)
        return jsonify({'status': 'ok'})

    @app.route('/admin/reset_streak', methods=['POST'])
    @login_required
    def admin_reset_streak():
        child_id = 'default_child'
        update_streak(child_id, 1)
        return jsonify({'status': 'ok'})

    @app.route('/admin/reset_all_data', methods=['POST'])
    @login_required
    def admin_reset_all_data():
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
        from utils.data import init_db
        init_db()
        return jsonify({'status': 'ok'})

    @app.route('/admin/adjust_points', methods=['POST'])
    @login_required
    def admin_adjust_points():
        data = request.get_json()
        amount = data.get('amount')
        reason = data.get('reason', '管理员调整')

        if amount is None:
            return jsonify({'error': '请输入积分数量'})

        if amount == 0:
            return jsonify({'error': '调整数量不能为0'})

        child_id = 'default_child'
        state = get_child_state(child_id)

        if amount < 0 and state['points'] + amount < 0:
            return jsonify({'error': f'积分不足！当前积分：{state["points"]}，无法扣除{-amount}分'})

        old_points = state['points']
        state['points'] += amount

        add_points_record(child_id, '管理员调整', amount, reason, state['points'])
        update_child_state(child_id, state)

        return jsonify({
            'status': 'ok',
            'old_points': old_points,
            'new_points': state['points'],
            'amount': amount,
            'message': f'{"增加" if amount > 0 else "扣除"} {abs(amount)} 积分成功！'
        })