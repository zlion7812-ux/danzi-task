"""
数据库模型定义
所有数据表结构统一在这里定义
"""

# 这个文件定义了数据库中的所有表结构
# 后面我们会用 SQLite 来存储数据

# 表结构说明：
#
# 1. users - 用户基本信息
#    - child_id: 孩子ID（主键）
#    - points: 当前积分
#    - streak: 连胜天数
#    - last_date: 最后登录日期
#    - portal_used: 今日是否用过传送门
#    - treasure_taken_today: 今日是否开过宝箱
#
# 2. daily_completed - 每日完成的任务
#    - child_id: 孩子ID
#    - task_id: 任务ID
#    - date: 完成日期
#
# 3. points_history - 积分变动历史
#    - child_id: 孩子ID
#    - time: 变动时间
#    - source: 来源（讨伐/彩蛋/魔法掉落/兑换等）
#    - change: 变动值（正数增加，负数减少）
#    - description: 描述
#    - total: 变动后的总积分
#
# 4. exchange_history - 兑换历史
#    - child_id: 孩子ID
#    - time: 兑换时间
#    - item_name: 物品名称
#    - price: 兑换价格
#
# 5. weekly_exchanges - 周限购记录
#    - child_id: 孩子ID
#    - key: 限购键（格式：商品ID_周数）
#    - count: 本周已兑换次数
#
# 6. bonus_quests - 彩蛋任务
#    - child_id: 孩子ID
#    - date: 日期
#    - quest_data: 任务数据（JSON格式）
#
# 7. active_timer - 活跃计时器
#    - child_id: 孩子ID
#    - task_id: 任务ID
#    - task_name: 任务名称
#    - start_time: 开始时间
#
# 8. config - 系统配置（新增）
#    - key: 配置键名
#    - value: 配置值（JSON格式）
#
# 9. tasks - 任务配置（新增，替代JSON文件）
#    - id: 任务ID
#    - name: 任务名称
#    - monster_id: 关联的怪物ID
#    - description: 任务描述
#    - default_points: 默认积分
#    - enabled: 是否启用
#    - order: 显示顺序
#
# 10. monsters - 怪物配置（新增，替代JSON文件）
#     - id: 怪物ID
#     - name: 怪物名称
#     - icon: 图标
#     - default_points: 默认积分
#     - description: 描述
#
# 11. shop_items - 商品配置（新增，替代JSON文件）
#     - id: 商品ID
#     - name: 商品名称
#     - price: 价格
#     - icon: 图标
#     - type: 类型（normal/weekend_only）
#     - weekly_limit: 周限购次数
#     - description: 描述
#
# 12. loot_items - 掉落物品配置（新增，替代JSON文件）
#     - id: 物品ID
#     - name: 物品名称
#     - add_points: 增加积分
#     - weight: 权重
#     - effect: 效果描述
#     - description: 描述
#
# 13. bonus_quest_items - 彩蛋任务池（新增，替代JSON文件）
#     - id: 任务ID
#     - name: 任务名称
#     - desc: 任务描述
#     - points_min: 最小积分
#     - points_max: 最大积分
#     - description: 详细描述
