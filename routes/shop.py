from flask import request, jsonify, session
from datetime import datetime
from utils.data import get_child_state, update_child_state, add_points_record, get_shop_items, add_exchange_record, \
    increment_weekly_exchange, get_weekly_exchange_count
from utils.game import is_weekend


def register_shop_routes(app):
    @app.route('/buy', methods=['POST'])
    def buy():
        data = request.get_json()
        item_id = data['item_id']
        child_id = session.get('child_id', 'default_child')
        state = get_child_state(child_id)

        shop_items = get_shop_items()
        item = next((i for i in shop_items if i['id'] == item_id), None)
        if not item:
            return jsonify({'error': '商品不存在'})

        if item.get('type') == 'weekend_only' and not is_weekend():
            return jsonify({'error': '这个道具只能在周末兑换！'})

        if item.get('weekly_limit'):
            week_num = datetime.today().isocalendar()[1]
            key = f"{item_id}_{week_num}"
            count = get_weekly_exchange_count(child_id, key)
            if count >= item['weekly_limit']:
                return jsonify({'error': f'本周已兑换{item["weekly_limit"]}次，不能再兑换了！'})

        if state['points'] < item['price']:
            return jsonify({'error': f'积分不足，需要{item["price"]}积分'})

        # 扣除积分
        old_points = state['points']
        state['points'] -= item['price']

        # 记录积分变动
        add_points_record(child_id, '兑换', -item['price'], f'兑换 {item["name"]}', state['points'])

        # 记录兑换历史
        add_exchange_record(child_id, item['name'], item['price'])

        # 更新周限购
        if item.get('weekly_limit'):
            week_num = datetime.today().isocalendar()[1]
            key = f"{item_id}_{week_num}"
            increment_weekly_exchange(child_id, key)

        # 更新state中的exchange_history用于显示
        state.setdefault('exchange_history', []).insert(0, {
            'time': datetime.now().strftime('%H:%M'),
            'item_name': item['name'],
            'price': item['price']
        })

        update_child_state(child_id, state)
        return jsonify({'message': f'兑换 {item["name"]} 成功！剩余{state["points"]}积分'})