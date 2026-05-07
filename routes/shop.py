from flask import request, jsonify, session
from datetime import datetime
from utils.data import get_child_state, update_child_state, add_points_record, get_shop_items
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
            weekly_exchanges = state.get('weekly_exchanges', {})
            week_num = datetime.today().isocalendar()[1]
            key = f"{item_id}_{week_num}"
            count = weekly_exchanges.get(key, 0)
            if count >= item['weekly_limit']:
                return jsonify({'error': f'本周已兑换{item["weekly_limit"]}次，不能再兑换了！'})

        if state['points'] < item['price']:
            return jsonify({'error': f'积分不足，需要{item["price"]}积分'})

        state['points'] -= item['price']
        add_points_record(child_id, state, '兑换', -item['price'], f'兑换 {item["name"]}')

        if item.get('weekly_limit'):
            weekly_exchanges = state.get('weekly_exchanges', {})
            week_num = datetime.today().isocalendar()[1]
            key = f"{item_id}_{week_num}"
            weekly_exchanges[key] = weekly_exchanges.get(key, 0) + 1
            state['weekly_exchanges'] = weekly_exchanges

        state.setdefault('exchange_history', []).insert(0, {
            'time': datetime.now().strftime('%H:%M'),
            'item_name': item['name'],
            'price': item['price']
        })
        update_child_state(child_id, state)
        return jsonify({'message': f'兑换 {item["name"]} 成功！剩余{state["points"]}积分'})