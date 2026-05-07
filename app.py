from flask import Flask
from routes.main import register_main_routes
from routes.fight import register_fight_routes
from routes.shop import register_shop_routes
from routes.admin import register_admin_routes

app = Flask(__name__)
app.secret_key = 'danzi_secret_key_2026'

# 注册所有路由模块
register_main_routes(app)
register_fight_routes(app)
register_shop_routes(app)
register_admin_routes(app)

if __name__ == '__main__':
    print("=" * 50)
    print("🐉 蛋仔勇者之路 启动！")
    print("🌐 访问地址:")
    print("   主页面: http://127.0.0.1:5001")
    print("   管理后台: http://127.0.0.1:5001/admin/login")
    print("   初始密码: admin123")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5001, debug=True)