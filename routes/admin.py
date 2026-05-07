from flask import render_template, request, session, jsonify, redirect, url_for
from utils.auth import login_required
from utils.data import get_tasks, get_monsters, get_config, save_tasks, save_monsters, save_config, DATA_FILE
import os


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

    @app.route('/admin/add_task', methods=['POST'])
    @login_required
    def admin_add_task():
        data = request.get_json()
        tasks = get_tasks()
        import uuid
        new_id = f"task_{uuid.uuid4().hex[:8]}"
        new_order = len(tasks) + 1
        new_task = {
            'id': new_id,
            'monster_id': data['monster_id'],
            'name': data['name'],
            'description': data.get('description', ''),
            'points': data['points'],
            'enabled': True,
            'order': new_order
        }
        tasks.append(new_task)
        save_tasks(tasks)
        return jsonify({'status': 'ok'})

    @app.route('/admin/update_task', methods=['POST'])
    @login_required
    def admin_update_task():
        data = request.get_json()
        tasks = get_tasks()
        for task in tasks:
            if task['id'] == data['task_id']:
                task['name'] = data['name']
                task['description'] = data.get('description', '')
                task['monster_id'] = data['monster_id']
                task['points'] = data['points']
                task['order'] = data.get('order', 0)
                task['enabled'] = data.get('enabled', True)
                break
        save_tasks(tasks)
        return jsonify({'status': 'ok'})

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

    @app.route('/logout')
    def logout():
        session.pop('admin_logged_in', None)
        return redirect(url_for('index'))

    # ========== 重置所有数据 ==========
    @app.route('/admin/reset_all_data', methods=['POST'])
    @login_required
    def admin_reset_all_data():
        """重置所有孩子数据"""
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
        return jsonify({'status': 'ok'})