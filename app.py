# app.py
import hashlib
import config
from flask import Flask, request, jsonify
from flask_migrate import Migrate
from flask_cors import CORS
from sqlalchemy.exc import IntegrityError
import traceback
from sqlalchemy import text
import random
from datetime import datetime, timedelta
import bcrypt

# 关键：从models统一导入db和所有数据模型
<<<<<<< HEAD
from models import db, Room, Building, User, RepairOrder, Notice, SmsCode, DutySchedule
=======
from models import db, Room, Building, RepairType, User, RepairOrder, Notice, SmsCode, DutySchedule
>>>>>>> 5e036f6a408ae0904899abe4af4904da810d9e9e

# Flask实例初始化
app = Flask(__name__)
app.config.from_object(config)

# 绑定db到app、迁移、跨域
db.init_app(app)
migrate = Migrate(app, db)
CORS(app)

# ===================== 工具函数：bcrypt密码加密 =====================
def hash_password(raw_password: str) -> str:
    """
    对明文密码进行bcrypt哈希加密
    :param raw_password: 明文密码
    :return: bcrypt哈希后的字符串
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(raw_password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

# 首页路由
@app.route('/', methods=['GET'])
def index():
    return {'msg':"服务器连接成功！注册接口地址：/api/user/register"}

import time
from functools import wraps

def api_cost_log(func):
    """接口耗时日志装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        resp = func(*args, **kwargs)
        cost = round((time.time() - start) * 1000, 2)
        path = request.path
        data = request.get_json(silent=True) or {}
        phone = data.get("phone", "")
        print(f"【接口耗时】路径:{path} 手机号:{phone} 耗时:{cost} ms")
        return resp
    return wrapper

# ========= 用户注册接口 =========
@app.route('/api/user/register', methods=['POST'])
@api_cost_log
def user_register():
    try:
        db.session.rollback()
        db.session.remove()
        print("【初始化日志】已清空本次请求数据库会话缓存，杜绝历史脏数据干扰查询")
        db.session.execute(text("SET TRANSACTION ISOLATION LEVEL READ COMMITTED;"))
        data = request.get_json()
        if not data:
            return jsonify({
                'code': 400,
                'msg': '请求参数为空，请检查请求头是否为application/json',
                'data': None
            }), 400
        phone = data.get('phone')
        password = data.get('password')
        name = data.get('name', '')  # 改为 name
        building_no = data.get('building_no')
        room_no = data.get('room_no')
        role = data.get('role', 'user')
        print(f"【参数接收日志】前端传入手机号: {phone}, 账号角色: {role}")
        if not phone or not password:
            return jsonify({'code': 400, 'msg': '手机号和密码不能为空', 'data': None}), 400
        if not (len(phone) == 11 and phone.isdigit()):
            return jsonify({'code': 400, 'msg': '手机号格式不正确，必须是11位数字', 'data': None}), 400
        if role not in ['user', 'worker']:
            return jsonify({'code': 400, 'msg': '角色参数错误，只能是user或worker', 'data': None}), 400
        hashed_pwd = hash_password(password)
        room_id = None
        room = None
        if role == 'user':
            if not building_no or not room_no:
                return jsonify({'code': 400, 'msg': '住户注册必须填写楼栋号，房间号', 'data': None}), 400
            building = Building.query.filter_by(building_no=building_no).first()
            if not building:
                building = Building(building_no=building_no)
                db.session.add(building)
                db.session.flush()
                print(f"【楼栋操作日志】未检索到楼栋{building_no}，已新建楼栋，楼栋主键ID: {building.id}")
            else:
                print(f"【楼栋操作日志】检索到已有楼栋{building_no}，楼栋主键ID: {building.id}")
            room = Room(building_id=building.id, room_no=room_no, status=0)
            db.session.add(room)
            db.session.flush()
            print(f"【房间操作日志】新增房间数据，房间主键ID: {room.id}")
            if room.status == 1:
                db.session.rollback()
                return jsonify({'code': 400, 'msg': f'该楼栋{building_no}房间{room_no}已被占用', 'data': None}), 400
            room_id = room.id
        # 核心改动：使用原子INSERT IGNORE单条SQL插入用户
        insert_sql = text("""
                          INSERT IGNORE INTO `user` 
            (phone, password, name, room_id, building_no, room_no, role, user_status, audit_id, create_time)
            VALUES (:phone, :pwd, :name, :rid, :bno, :rno, :role, '正常', :audit, NOW())
                          """)
        result = db.session.execute(
            insert_sql,
            params={
                "phone": phone,
                "pwd": hashed_pwd,
                "name": name,  # 改为 name
                "rid": room_id,
                "bno": building_no,
                "rno": room_no,
                "role": role,
                "audit": 1 if role == 'user' else 0
            }
        )
        affect_rows = result.rowcount
        if affect_rows == 0:
            db.session.rollback()
            print("【原子SQL拦截】手机号已存在，返回409")
            return jsonify({'code': 409, 'msg': '该手机号已注册，请直接登录', 'data': None}), 409
        if role == 'user' and room:
            room.status = 1
        db.session.commit()
        print("【事务提交日志】楼栋、房间、用户全部数据提交数据库完成，注册事务结束")
        new_user = User.query.filter_by(phone=phone).first()
        create_time_str = new_user.create_time.strftime('%Y-%m-%d %H:%M:%S') if new_user.create_time else ""
        return jsonify({
            'code': 200,
            'msg': '注册成功',
            'data': {
                'user_id': new_user.id,
                'phone': new_user.phone,
                'name': new_user.name,  # 改为 name
                'role': new_user.role,
                'building_no': building_no if building_no else None,
                'room_no': room_no if room_no else None,
                'room_id': room_id,
                'create_time': create_time_str
            }
        }), 200
    except IntegrityError:
        db.session.rollback()
        db.session.remove()
        print("【兜底异常日志】数据库唯一约束报错，手机号已存在，返回409")
        return jsonify({'code': 409, 'msg': '注册失败，手机号已存在', 'data': None}), 409
    except Exception as e:
        db.session.rollback()
        db.session.remove()
        traceback.print_exc()
        print(f"【全局异常日志】注册接口运行异常，错误详情: {str(e)}")
<<<<<<< HEAD
        return jsonify({'code': 500, 'msg': '服务器繁忙，请稍后再试', 'data': None}), 500
=======
        return jsonify({'code': 500, 'msg': f'服务器错误: {str(e)}', 'data': None}), 500
>>>>>>> 5e036f6a408ae0904899abe4af4904da810d9e9e

# ===================== 登录接口 =====================
@app.route('/api/user/login', methods=['POST'])
@api_cost_log
def user_login():
    try:
        db.session.rollback()
        db.session.remove()
        data = request.get_json()
        if not data:
            return jsonify({
                "code": 400,
                "msg": "请求参数不能为空，请传入JSON格式数据",
                "data": None
            }), 400
        phone = data.get("phone")
        password = data.get("password")
        if not phone or not password:
            return jsonify({
                "code": 400,
                "msg": "手机号和密码不能为空",
                "data": None
            }), 400
        if not (len(phone) == 11 and phone.isdigit()):
            return jsonify({
                "code": 400,
                "msg": "手机号必须是11位纯数字",
                "data": None
            }), 400
        user = User.query.filter_by(phone=phone).first()
        if not user:
            return jsonify({
                "code": 401,
                "msg": "该手机号未注册，请先注册",
                "data": None
            }), 401
        # bcrypt密码验证
        if not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            return jsonify({
                "code": 401,
                "msg": "密码输入错误",
                "data": None
            }), 401
        if user.user_status != "正常":
            return jsonify({
                "code": 403,
                "msg": f"账号状态异常：{user.user_status}，禁止登录",
                "data": None
            }), 403
        if user.role == "worker":
            if user.audit_id == 0:
                return jsonify({
                    "code": 403,
                    "msg": "物业账号待管理员审核，暂时无法登录",
                    "data": None
                }), 403
            login_data = {
                "user_id": user.id,
                "phone": user.phone,
                "name": user.name,  # 改为 name
                "role": user.role,
                "audit_id": user.audit_id,
                "login_type": "物业端"
            }
        elif user.role == "admin":
            login_data = {
                "user_id": user.id,
                "phone": user.phone,
                "name": user.name,  # 改为 name
                "role": "admin",
                "login_type": "管理员端"
            }
        else:
            login_data = {
                "user_id": user.id,
                "phone": user.phone,
                "name": user.name,  # 改为 name
                "role": user.role,
                "room_id": user.room_id,
                "building_no": user.building_no,
                "room_no": user.room_no,
                "audit_id": user.audit_id,
                "login_type": "住户端"
            }
        return jsonify({
            "code": 200,
            "msg": "登录成功",
            "data": login_data
        }), 200
    except Exception as e:
        db.session.rollback()
        db.session.remove()
        traceback.print_exc()
        return jsonify({
            "code": 500,
            "msg": f"服务器异常：{str(e)}",
            "data": None
        }), 500

# ===================== 获取当前登录用户信息接口 =====================
@app.route('/api/user/info', methods=['POST'])
@api_cost_log
def get_user_info():
    try:
        db.session.rollback()
        db.session.remove()
        data = request.get_json()
        if not data or not data.get("phone"):
            return jsonify({"code":400,"msg":"缺少手机号参数","data":None}),400
        phone = data.get("phone")
        user = db.session.query(User).filter(User.phone == phone).first()
        if not user:
            return jsonify({"code":401,"msg":"用户不存在，请重新登录","data":None}),401
        print("后端查询到用户原始数据：", user.phone, user.building_no, user.room_no)
        if user.user_status != "正常":
            return jsonify({"code":403,"msg":"账号状态异常","data":None}),403
        if user.role == "worker" and user.audit_id == 0:
            return jsonify({"code":403,"msg":"账号待审核","data":None}),403
        if user.role == "user":
            res_data = {
                "user_id": user.id,
                "phone": user.phone,
                "name": user.name,  # 改为 name
                "role": user.role,
                "role_name": "住户端",
                "building_no": user.building_no if user.building_no else "",
                "room_no": user.room_no if user.room_no else "",
                "room_id": user.room_id,
                "account_status": user.user_status,
                "audit_id": user.audit_id
            }
        else:
            res_data = {
                "user_id": user.id,
                "phone": user.phone,
                "name": user.name,  # 改为 name
                "role": user.role,
                "role_name": "物业端",
                "account_status": user.user_status,
                "audit_id": user.audit_id
            }
        return jsonify({"code":200,"msg":"获取用户信息成功","data":res_data}),200
    except Exception as e:
        db.session.rollback()
        db.session.remove()
        traceback.print_exc()
        return jsonify({"code":500,"msg":f"服务器异常：{str(e)}","data":None}),500

# ===================== 住户提交报修工单接口 =====================
@app.route('/api/repair/add', methods=['POST'])
@api_cost_log
def add_repair_order():
    try:
        db.session.rollback()
        db.session.remove()
        data = request.get_json()
        phone = data.get("phone")
        title = data.get("title")
        content = data.get("content","")
        img_url = data.get("img_url", "")
        if not phone or not title:
            return jsonify({"code":400,"msg":"手机号、报修标题不能为空","data":None}),400
        user = User.query.filter_by(phone=phone).first()
        if not user:
            return jsonify({"code":401,"msg":"用户不存在","data":None}),401
        if user.role != "user":
            return jsonify({"code":403,"msg":"物业账号不能提交报修","data":None}),403
        if user.user_status != "正常":
            return jsonify({"code":403,"msg":"账号异常无法提交报修","data":None}),403
        new_order = RepairOrder(
            user_id=user.id,
            building_id=0,
            room_id=user.room_id,
            title=title,
            content=content,
            img_url=img_url,
            status=0,
            building=user.building_no,
            room=user.room_no,
            submit_time=datetime.now(),
            finish_time=None,
            worker_id=None
        )
        db.session.add(new_order)
        db.session.commit()
        return jsonify({
            "code":200,
            "msg":"报修提交成功，物业会尽快处理",
            "data":{"order_id":new_order.id}
        }),200
    except Exception as e:
        db.session.rollback()
        db.session.remove()
        traceback.print_exc()
<<<<<<< HEAD
        return jsonify({"code":500,"msg":"服务器繁忙,请稍后重试","data":None}),500
=======
        return jsonify({"code":500,"msg":f"提交报修失败：{str(e)}","data":None}),500
>>>>>>> 5e036f6a408ae0904899abe4af4904da810d9e9e

# ===================== 住户查询本人报修工单列表（带物业人员信息） =====================
@app.route('/api/repair/my_list', methods=['POST'])
@api_cost_log
def get_my_repair_list():
    try:
        db.session.rollback()
        db.session.remove()
        data = request.get_json()
        phone = data.get("phone")
        filter_status = data.get("status")
        if not phone:
            return jsonify({"code":400,"msg":"缺少手机号","data":None}),400
        user = User.query.filter_by(phone=phone).first()
        if not user or user.role != "user":
            return jsonify({"code":403,"msg":"仅住户可查看个人工单","data":None}),403
        query = RepairOrder.query.filter_by(user_id=user.id)
        if filter_status is not None and filter_status != "":
            try:
                status_int = int(filter_status)
                query = query.filter_by(status=status_int)
            except ValueError:
                pass
        order_list = query.order_by(RepairOrder.submit_time.desc()).all()
        res_arr = []
        for item in order_list:
            status_text = {0:"待维修",1:"维修中",2:"已完成"}[item.status]
            worker_name = ""
            worker_phone = ""
            if item.worker_id:
                worker = User.query.filter_by(id=item.worker_id).first()
                if worker:
                    worker_name = worker.name or ""  # 改为 name
                    worker_phone = worker.phone or ""
            res_arr.append({
                "order_id": item.id,
                "title": item.title,
                "content": item.content,
                "building": item.building,
                "room": item.room,
                "status": item.status,
                "status_text": status_text,
                "submit_time": item.submit_time.strftime("%Y-%m-%d %H:%M"),
                "finish_time": item.finish_time.strftime("%Y-%m-%d %H:%M") if item.finish_time else "",
                "worker_name": worker_name,  # 改为 name
                "worker_phone": worker_phone
            })
        return jsonify({"code":200,"msg":"查询成功","data":res_arr}),200
    except Exception as e:
        db.session.rollback()
        db.session.remove()
        traceback.print_exc()
        return jsonify({"code":500,"msg":f"查询工单失败：{str(e)}","data":None}),500

# ===================== 物业查询所有工单（过滤：仅显示未分配或分配给自己的工单） =====================
@app.route('/api/repair/all_list', methods=['POST'])
@api_cost_log
def get_all_repair_list():
    try:
        db.session.rollback()
        db.session.remove()
        data = request.get_json()
        phone = data.get("phone")
        filter_status = data.get("status")

        if not phone:
            return jsonify({"code": 400, "msg": "缺少手机号", "data": None}), 400

        user = User.query.filter_by(phone=phone).first()
        if not user or user.role != "worker" or user.audit_id != 1:
            return jsonify({"code": 403, "msg": "无权限查看工单", "data": None}), 403

        # ===== 核心过滤：只显示未分配(worker_id为空)或分配给自己的工单 =====
        query = RepairOrder.query.filter(
            (RepairOrder.worker_id == user.id) | (RepairOrder.worker_id.is_(None))
        )

        # 状态筛选
        if filter_status is not None and filter_status != "":
            try:
                status_int = int(filter_status)
                query = query.filter_by(status=status_int)
            except ValueError:
                pass

        order_list = query.order_by(RepairOrder.submit_time.desc()).all()

        # 判断当前物业人员是否值班（决定能否操作）
        can_modify = False
        today = datetime.now().date()
<<<<<<< HEAD
        duty = DutySchedule.query.filter(
            DutySchedule.worker_id == user.id,
            DutySchedule.start_date <= today,
            DutySchedule.end_date >= today
        ).first()
=======
        duty = DutySchedule.query.filter_by(worker_id=user.id, duty_date=today).first()
>>>>>>> 5e036f6a408ae0904899abe4af4904da810d9e9e
        if duty:
            can_modify = True

        res_arr = []
        for item in order_list:
            submit_user = User.query.filter_by(id=item.user_id).first()
            status_text = {0: "待维修", 1: "维修中", 2: "已完成"}[item.status]

            worker_name = ""
            worker_phone = ""
            if item.worker_id:
                worker = User.query.filter_by(id=item.worker_id).first()
                if worker:
                    worker_name = worker.name or ""
                    worker_phone = worker.phone or ""

            remaining_time = ""
            if item.status == 1 and item.start_time:
                from datetime import timedelta
                expire_time = item.start_time + timedelta(hours=24)
                now = datetime.now()
                if now < expire_time:
                    diff = expire_time - now
                    hours = int(diff.total_seconds() // 3600)
                    minutes = int((diff.total_seconds() % 3600) // 60)
                    remaining_time = f"剩余{hours}小时{minutes}分钟"
                else:
                    remaining_time = "已超时，请尽快完成"

            res_arr.append({
                "order_id": item.id,
                "submit_phone": submit_user.phone if submit_user else "",
                "submit_name": submit_user.name if submit_user else "",
                "title": item.title,
                "content": item.content,
                "building": item.building,
                "room": item.room,
                "status": item.status,
                "status_text": status_text,
                "submit_time": item.submit_time.strftime("%Y-%m-%d %H:%M"),
                "finish_time": item.finish_time.strftime("%Y-%m-%d %H:%M") if item.finish_time else "",
                "worker_name": worker_name,
                "worker_phone": worker_phone,
                "remaining_time": remaining_time,
                "img_url": item.img_url or "",
                "can_modify": can_modify   # 前端据此显示操作按钮
            })

        return jsonify({"code": 200, "msg": "查询成功", "data": res_arr}), 200

    except Exception as e:
        db.session.rollback()
        db.session.remove()
        traceback.print_exc()
        return jsonify({"code": 500, "msg": f"查询工单失败：{str(e)}", "data": None}), 500

# ===================== 物业修改工单状态接口（行锁 + 明确冲突） =====================
@app.route('/api/repair/update_status', methods=['POST'])
@api_cost_log
def update_repair_status():
    try:
        data = request.get_json()
        phone = data.get("phone")
        order_id = data.get("order_id")
        new_status = data.get("status")

        if not phone or not order_id or new_status is None:
            return jsonify({"code": 400, "msg": "参数缺失", "data": None}), 400

        new_status = int(new_status)
        if new_status not in [0, 1, 2]:
            return jsonify({"code": 400, "msg": "状态只能是0/1/2", "data": None}), 400

        worker = User.query.filter_by(phone=phone).first()
        if not worker or worker.role != "worker" or worker.audit_id != 1:
            return jsonify({"code": 403, "msg": "无操作权限", "data": None}), 403

        today = datetime.now().date()
<<<<<<< HEAD
        duty = DutySchedule.query.filter(
            DutySchedule.worker_id == worker.id,
            DutySchedule.start_date <= today,
            DutySchedule.end_date >= today
        ).first()
=======
        duty = DutySchedule.query.filter_by(worker_id=worker.id, duty_date=today).first()
>>>>>>> 5e036f6a408ae0904899abe4af4904da810d9e9e
        if not duty:
            return jsonify({"code": 403, "msg": "您今天未值班，无法修改工单状态", "data": None}), 403

        # 行锁：确保并发安全
        order = RepairOrder.query.filter_by(id=order_id).with_for_update().first()
        if not order:
            return jsonify({"code": 404, "msg": "工单不存在", "data": None}), 404

        old_status = order.status

        # 如果状态已相同，返回冲突（让前端知道没有实际修改）
        if old_status == new_status:
            return jsonify({
                "code": 409,
                "msg": "工单状态已被其他人员修改为相同状态，无需重复操作",
                "data": {"current_status": old_status}
            }), 409

        # 状态流转校验
        if old_status == 2 and new_status != 2:
            return jsonify({"code": 400, "msg": "已完成的工单不能回退状态", "data": None}), 400

        if old_status == 0 and new_status == 2:
            return jsonify({"code": 400, "msg": "待维修工单不能直接完成，请先设为维修中", "data": None}), 400

        # 记录处理人
        if order.worker_id is None or order.worker_id == 0:
            order.worker_id = worker.id

        # 更新状态
        if new_status == 1 and old_status != 1:
            order.start_time = datetime.now()

        order.status = new_status

        if new_status == 2:
            order.finish_time = datetime.now()

        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "工单状态更新成功",
            "data": {
                "old_status": old_status,
                "new_status": new_status,
                "worker_name": worker.name
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({"code": 500, "msg": f"更新失败：{str(e)}", "data": None}), 500

# ===================== 管理员接口 =====================
@app.route('/api/admin/get_wait_worker', methods=['POST'])
@api_cost_log
def get_wait_worker():
    try:
        db.session.rollback()
        db.session.remove()
        data = request.get_json()
        admin_phone = data.get("admin_phone")
        admin = User.query.filter_by(phone=admin_phone).first()
        if not admin or admin.role != "admin":
            return jsonify({"code":403,"msg":"无管理员权限","data":None}),403
        wait_list = User.query.filter(User.role=="worker", User.audit_id==0).all()
        res = []
        for u in wait_list:
            res.append({
                "id":u.id,
                "phone":u.phone,
                "name":u.name,  # 改为 name
                "create_time":u.create_time.strftime("%Y-%m-%d %H:%M") if u.create_time else ""
            })
        return jsonify({"code":200,"msg":"查询成功","data":res}),200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"code":500,"msg":str(e),"data":None}),500

@app.route('/api/admin/audit_worker', methods=['POST'])
@api_cost_log
def audit_worker():
    try:
        db.session.rollback()
        db.session.remove()
        data = request.get_json()
        admin_phone = data.get("admin_phone")
        target_id = data.get("id")
        opt_type = int(data.get("type"))
        admin = User.query.filter_by(phone=admin_phone).first()
        if not admin or admin.role != "admin":
            return jsonify({"code":403,"msg":"无权限操作","data":None}),403
        worker = User.query.get(target_id)
        if not worker or worker.role != "worker":
            return jsonify({"code":404,"msg":"用户不存在","data":None}),404
        if opt_type == 1:
            worker.audit_id = 1
            worker.user_status = "正常"
            msg = "审核通过"
        elif opt_type == 2:
            worker.user_status = "禁用"
            msg = "已拒绝该账号申请"
        else:
            return jsonify({"code":400,"msg":"操作类型错误","data":None}),400
        db.session.commit()
        return jsonify({"code":200,"msg":msg,"data":None}),200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"code":500,"msg":str(e),"data":None}),500

# ===================== 忘记密码 - 发送验证码（生产版） =====================
@app.route('/api/user/send_reset_code', methods=['POST'])
@api_cost_log
def send_reset_code():
    try:
        db.session.rollback()
        db.session.remove()
        data = request.get_json()
        phone = data.get("phone")

        if not phone:
            return jsonify({"code": 400, "msg": "手机号不能为空", "data": None}), 400
        if not (len(phone) == 11 and phone.isdigit()):
            return jsonify({"code": 400, "msg": "手机号格式不正确", "data": None}), 400

        user = User.query.filter_by(phone=phone).first()
        if not user:
            return jsonify({"code": 404, "msg": "该手机号未注册", "data": None}), 404

        recent = SmsCode.query.filter(
            SmsCode.phone == phone,
            SmsCode.create_time >= datetime.now() - timedelta(minutes=1)
        ).count()
        if recent >= 3:
            return jsonify({"code": 429, "msg": "操作过于频繁，请稍后再试", "data": None}), 429

        code = ''.join(random.choices('0123456789', k=6))
        expire_time = datetime.now() + timedelta(minutes=5)

        SmsCode.query.filter_by(phone=phone, used=0).delete()

        new_code = SmsCode(
            phone=phone,
            code=code,
            expire_time=expire_time,
            used=0
        )
        db.session.add(new_code)
        db.session.commit()

        print(f"【验证码】手机号: {phone} 验证码: {code}")

        return jsonify({"code": 200, "msg": "验证码已发送，请注意查收", "data": None}), 200
    except Exception as e:
        db.session.rollback()
        db.session.remove()
        traceback.print_exc()
        return jsonify({"code": 500, "msg": f"发送验证码失败：{str(e)}", "data": None}), 500

# ===================== 忘记密码 - 重置密码 =====================
@app.route('/api/user/reset_password', methods=['POST'])
@api_cost_log
def reset_password():
    try:
        db.session.rollback()
        db.session.remove()
        data = request.get_json()
        phone = data.get("phone")
        code = data.get("code")
        new_password = data.get("new_password")

        if not phone or not code or not new_password:
            return jsonify({"code": 400, "msg": "参数不完整", "data": None}), 400
        if not (len(phone) == 11 and phone.isdigit()):
            return jsonify({"code": 400, "msg": "手机号格式不正确", "data": None}), 400
        if len(new_password) < 6:
            return jsonify({"code": 400, "msg": "密码至少6位", "data": None}), 400

        user = User.query.filter_by(phone=phone).first()
        if not user:
            return jsonify({"code": 404, "msg": "用户不存在", "data": None}), 404

        sms_record = SmsCode.query.filter_by(phone=phone, code=code, used=0).first()
        if not sms_record:
            return jsonify({"code": 400, "msg": "验证码错误或已使用", "data": None}), 400

        if datetime.now() > sms_record.expire_time:
            return jsonify({"code": 400, "msg": "验证码已过期，请重新获取", "data": None}), 400

        sms_record.used = 1

        user.password = hash_password(new_password)
        db.session.commit()

        return jsonify({"code": 200, "msg": "密码重置成功，请重新登录", "data": None}), 200
    except Exception as e:
        db.session.rollback()
        db.session.remove()
        traceback.print_exc()
        return jsonify({"code": 500, "msg": f"重置密码失败：{str(e)}", "data": None}), 500

# ===================== 图片上传接口 =====================
import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'mp4', 'mov', 'avi'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/upload', methods=['POST'])
@api_cost_log
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({"code": 400, "msg": "没有文件", "data": None}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"code": 400, "msg": "文件名为空", "data": None}), 400

        if not allowed_file(file.filename):
            return jsonify({"code": 400, "msg": "不支持的文件格式", "data": None}), 400

        original_name = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_name = f"{timestamp}_{original_name}"

        file_path = os.path.join(UPLOAD_FOLDER, unique_name)
        file.save(file_path)

        file_url = f"http://{request.host}/static/uploads/{unique_name}"

        return jsonify({
            "code": 200,
            "msg": "上传成功",
            "data": {"url": file_url}
        }), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"code": 500, "msg": f"上传失败：{str(e)}", "data": None}), 500

# ===================== 清理过期图片 =====================
def clean_expired_images():
    with app.app_context():
        try:
            from datetime import timedelta
            threshold = datetime.now() - timedelta(days=3)

            expired_orders = RepairOrder.query.filter(
                RepairOrder.img_url != '',
                RepairOrder.img_url.isnot(None),
                RepairOrder.submit_time <= threshold
            ).all()

            if not expired_orders:
                print("【图片清理】没有需要清理的过期图片")
                return

            deleted_files = 0
            deleted_orders = 0

            for order in expired_orders:
                urls = order.img_url.split(',')
                for url in urls:
                    if url and url.strip():
                        filename = url.strip().split('/')[-1]
                        filepath = os.path.join(UPLOAD_FOLDER, filename)
                        if os.path.exists(filepath):
                            os.remove(filepath)
                            deleted_files += 1
                            print(f"【图片清理】删除文件: {filepath}")
                order.img_url = ''
                deleted_orders += 1

            db.session.commit()
            print(f"【图片清理】完成: 清理了 {deleted_files} 个图片文件, 涉及 {deleted_orders} 个工单")
        except Exception as e:
            db.session.rollback()
            print(f"【图片清理】发生错误: {str(e)}")

from apscheduler.schedulers.background import BackgroundScheduler

def auto_complete_job():
    try:
        with app.app_context():
            from app import auto_complete_orders
            auto_complete_orders()
        print(f"【定时任务】执行自动完成超时工单")
    except Exception as e:
        print(f"【定时任务】执行失败：{e}")

scheduler = BackgroundScheduler()

scheduler.add_job(func=auto_complete_job, trigger="interval", hours=1, id="auto_complete")

scheduler.add_job(
    func=clean_expired_images,
    trigger='cron',
    hour=2,
    minute=0,
    id='clean_expired_images'
)
print("【定时任务】图片清理任务已注册（每天凌晨2点执行）")

scheduler.start()

import atexit
atexit.register(lambda: scheduler.shutdown())

@app.route('/api/admin/clean_images', methods=['POST'])
@api_cost_log
def manual_clean_images():
    try:
        clean_expired_images()
        return jsonify({"code": 200, "msg": "图片清理已执行", "data": None}), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": f"清理失败: {str(e)}", "data": None}), 500

# ===================== 值班管理接口 =====================
@app.route('/api/admin/duty/list', methods=['POST'])
@api_cost_log
def get_duty_list():
    try:
        data = request.get_json()
        admin_phone = data.get("admin_phone")

        admin = User.query.filter_by(phone=admin_phone).first()
        if not admin or admin.role != "admin":
            return jsonify({"code": 403, "msg": "无权限", "data": None}), 403

<<<<<<< HEAD
        duties = DutySchedule.query.order_by(DutySchedule.start_date.desc()).all()
=======
        duties = DutySchedule.query.order_by(DutySchedule.duty_date.desc()).all()
>>>>>>> 5e036f6a408ae0904899abe4af4904da810d9e9e
        result = []
        for d in duties:
            worker = User.query.get(d.worker_id)
            result.append({
                "id": d.id,
                "worker_id": d.worker_id,
<<<<<<< HEAD
                "worker_name": worker.name if worker else "",
                "worker_phone": worker.phone if worker else "",
                "start_date": d.start_date.strftime("%Y-%m-%d") if d.start_date else "",
                "end_date": d.end_date.strftime("%Y-%m-%d") if d.end_date else ""
            })
        return jsonify({"code": 200, "msg": "查询成功", "data": result}), 200
    except Exception as e:
        traceback.print_exc()  # 关键：打印错误堆栈
        return jsonify({"code": 500, "msg": '服务器繁忙，请稍后重试', "data": None}), 500
=======
                "worker_name": worker.name if worker else "",  # 改为 name
                "worker_phone": worker.phone if worker else "",
                "duty_date": d.duty_date.strftime("%Y-%m-%d")
            })
        return jsonify({"code": 200, "msg": "查询成功", "data": result}), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e), "data": None}), 500
>>>>>>> 5e036f6a408ae0904899abe4af4904da810d9e9e

@app.route('/api/admin/duty/add', methods=['POST'])
@api_cost_log
def add_duty():
    try:
        data = request.get_json()
        admin_phone = data.get("admin_phone")
        worker_id = data.get("worker_id")
<<<<<<< HEAD
        start_date = data.get("start_date")
        end_date = data.get("end_date")
=======
        duty_date = data.get("duty_date")
>>>>>>> 5e036f6a408ae0904899abe4af4904da810d9e9e

        admin = User.query.filter_by(phone=admin_phone).first()
        if not admin or admin.role != "admin":
            return jsonify({"code": 403, "msg": "无权限", "data": None}), 403

        worker = User.query.get(worker_id)
        if not worker or worker.role != "worker":
            return jsonify({"code": 400, "msg": "物业人员不存在", "data": None}), 400

<<<<<<< HEAD
        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"code": 400, "msg": "日期格式错误，请使用 YYYY-MM-DD", "data": None}), 400
        except TypeError:
            return jsonify({"code": 400, "msg": "开始日期和结束日期不能为空", "data": None}), 400

        if start_date_obj > end_date_obj:
            return jsonify({"code": 400, "msg": "开始日期不能晚于结束日期", "data": None}), 400

        overlap = DutySchedule.query.filter(
            DutySchedule.worker_id == worker_id,
            DutySchedule.start_date <= end_date_obj,
            DutySchedule.end_date >= start_date_obj
        ).first()
        if overlap:
            return jsonify({
                "code": 400,
                "msg": f"该员工在 {overlap.start_date} 至 {overlap.end_date} 已有排班，请勿重复添加",
                "data": None
            }), 400

        new_duty = DutySchedule(
            worker_id=worker_id,
            start_date=start_date_obj,
            end_date=end_date_obj
        )
        db.session.add(new_duty)
        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "添加值班成功",
            "data": {"id": new_duty.id, "start_date": str(start_date_obj), "end_date": str(end_date_obj)}
        }), 200
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()  # 关键：打印错误堆栈
        return jsonify({"code": 500, "msg":'服务器繁忙，请稍后重试', "data": None}), 500
=======
        if duty_date:
            duty_date_obj = datetime.strptime(duty_date, "%Y-%m-%d").date()
        else:
            duty_date_obj = datetime.now().date()

        existing = DutySchedule.query.filter_by(worker_id=worker_id, duty_date=duty_date_obj).first()
        if existing:
            return jsonify({"code": 400, "msg": "该人员当天已排班", "data": None}), 400

        new_duty = DutySchedule(worker_id=worker_id, duty_date=duty_date_obj)
        db.session.add(new_duty)
        db.session.commit()

        return jsonify({"code": 200, "msg": "添加值班成功", "data": {"id": new_duty.id}}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": str(e), "data": None}), 500
>>>>>>> 5e036f6a408ae0904899abe4af4904da810d9e9e

@app.route('/api/admin/duty/remove', methods=['POST'])
@api_cost_log
def remove_duty():
    try:
        data = request.get_json()
        admin_phone = data.get("admin_phone")
        duty_id = data.get("duty_id")

        admin = User.query.filter_by(phone=admin_phone).first()
        if not admin or admin.role != "admin":
            return jsonify({"code": 403, "msg": "无权限", "data": None}), 403

        duty = DutySchedule.query.get(duty_id)
        if not duty:
            return jsonify({"code": 404, "msg": "值班记录不存在", "data": None}), 404

        db.session.delete(duty)
        db.session.commit()
        return jsonify({"code": 200, "msg": "取消值班成功", "data": None}), 200
    except Exception as e:
        db.session.rollback()
<<<<<<< HEAD
        return jsonify({"code": 500, "msg": '服务器繁忙，请稍后重试', "data": None}), 500
=======
        return jsonify({"code": 500, "msg": str(e), "data": None}), 500
>>>>>>> 5e036f6a408ae0904899abe4af4904da810d9e9e

@app.route('/api/admin/workers', methods=['POST'])
@api_cost_log
def get_all_workers():
    try:
        data = request.get_json()
        admin_phone = data.get("admin_phone")

        admin = User.query.filter_by(phone=admin_phone).first()
        if not admin or admin.role != "admin":
            return jsonify({"code": 403, "msg": "无权限", "data": None}), 403

        workers = User.query.filter_by(role="worker", audit_id=1).all()
        result = []
        for w in workers:
            result.append({
                "id": w.id,
                "name": w.name,  # 改为 name
                "phone": w.phone
            })
        return jsonify({"code": 200, "msg": "查询成功", "data": result}), 200
    except Exception as e:
<<<<<<< HEAD
        return jsonify({"code": 500, "msg" : '服务器繁，请稍后重试', "data": None}), 500
=======
        return jsonify({"code": 500, "msg": str(e), "data": None}), 500
>>>>>>> 5e036f6a408ae0904899abe4af4904da810d9e9e

# ===================== 公告接口 =====================
@app.route('/api/notice/latest', methods=['GET'])
@api_cost_log
def get_latest_notice():
    try:
        notice = Notice.query.order_by(Notice.create_time.desc()).first()
        if not notice:
            return jsonify({
                "code": 200,
                "msg": "暂无公告",
                "data": None
            }), 200
        return jsonify({
            "code": 200,
            "msg": "查询成功",
            "data": {
                "id": notice.id,
                "title": notice.title,
                "content": notice.content[:100] + ("..." if len(notice.content) > 100 else ""),
                "create_time": notice.create_time.strftime("%Y-%m-%d %H:%M")
            }
        }), 200
    except Exception as e:
<<<<<<< HEAD
        return jsonify({"code": 500, "msg" : '服务器繁，请稍后重试', "data": None}), 500
=======
        return jsonify({"code": 500, "msg": str(e), "data": None}), 500
>>>>>>> 5e036f6a408ae0904899abe4af4904da810d9e9e

@app.route('/api/notice/list', methods=['POST'])
@api_cost_log
def get_notice_list():
    try:
        notices = Notice.query.order_by(Notice.create_time.desc()).all()
        result = []
        for n in notices:
            result.append({
                "id": n.id,
                "title": n.title,
                "create_time": n.create_time.strftime("%Y-%m-%d %H:%M")
            })
        return jsonify({"code": 200, "msg": "查询成功", "data": result}), 200
    except Exception as e:
<<<<<<< HEAD
        return jsonify({"code": 500, "msg" : '服务器繁，请稍后重试', "data": None}), 500
=======
        return jsonify({"code": 500, "msg": str(e), "data": None}), 500
>>>>>>> 5e036f6a408ae0904899abe4af4904da810d9e9e

@app.route('/api/notice/detail', methods=['POST'])
@api_cost_log
def get_notice_detail():
    try:
        data = request.get_json()
        notice_id = data.get("id")
        if not notice_id:
            return jsonify({"code": 400, "msg": "缺少公告ID", "data": None}), 400

        notice = Notice.query.get(notice_id)
        if not notice:
            return jsonify({"code": 404, "msg": "公告不存在", "data": None}), 404

        return jsonify({
            "code": 200,
            "msg": "查询成功",
            "data": {
                "id": notice.id,
                "title": notice.title,
                "content": notice.content,
                "create_time": notice.create_time.strftime("%Y-%m-%d %H:%M"),
                "update_time": notice.update_time.strftime("%Y-%m-%d %H:%M") if notice.update_time else ""
            }
        }), 200
    except Exception as e:
<<<<<<< HEAD
        return jsonify({"code": 500, "msg" : '服务器繁，请稍后重试', "data": None}), 500
=======
        return jsonify({"code": 500, "msg": str(e), "data": None}), 500
>>>>>>> 5e036f6a408ae0904899abe4af4904da810d9e9e

# ===================== 公告管理接口（管理员） =====================
@app.route('/api/admin/notice/add', methods=['POST'])
@api_cost_log
def admin_add_notice():
    try:
        data = request.get_json()
        admin_phone = data.get("admin_phone")
        title = data.get("title")
        content = data.get("content")

        admin = User.query.filter_by(phone=admin_phone).first()
        if not admin or admin.role != "admin":
            return jsonify({"code": 403, "msg": "无管理员权限", "data": None}), 403

        if not title or not content:
            return jsonify({"code": 400, "msg": "标题和内容不能为空", "data": None}), 400

        new_notice = Notice(
            title=title,
            content=content,
            publish_user_id=admin.id,
            create_time=datetime.now(),
            update_time=datetime.now()
        )
        db.session.add(new_notice)
        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "公告发布成功",
            "data": {"id": new_notice.id}
        }), 200
    except Exception as e:
        db.session.rollback()
<<<<<<< HEAD
        return jsonify({"code": 500, "msg" : '服务器繁，请稍后重试', "data": None}), 500
=======
        return jsonify({"code": 500, "msg": str(e), "data": None}), 500
>>>>>>> 5e036f6a408ae0904899abe4af4904da810d9e9e

@app.route('/api/admin/notice/edit', methods=['POST'])
@api_cost_log
def admin_edit_notice():
    try:
        data = request.get_json()
        admin_phone = data.get("admin_phone")
        notice_id = data.get("id")
        title = data.get("title")
        content = data.get("content")

        admin = User.query.filter_by(phone=admin_phone).first()
        if not admin or admin.role != "admin":
            return jsonify({"code": 403, "msg": "无管理员权限", "data": None}), 403

        notice = Notice.query.get(notice_id)
        if not notice:
            return jsonify({"code": 404, "msg": "公告不存在", "data": None}), 404

        if title:
            notice.title = title
        if content:
            notice.content = content
        notice.update_time = datetime.now()

        db.session.commit()
        return jsonify({"code": 200, "msg": "公告更新成功", "data": None}), 200
    except Exception as e:
        db.session.rollback()
<<<<<<< HEAD
        return jsonify({"code": 500, "msg" : '服务器繁，请稍后重试', "data": None}), 500
=======
        return jsonify({"code": 500, "msg": str(e), "data": None}), 500
>>>>>>> 5e036f6a408ae0904899abe4af4904da810d9e9e

@app.route('/api/admin/notice/delete', methods=['POST'])
@api_cost_log
def admin_delete_notice():
    try:
        data = request.get_json()
        admin_phone = data.get("admin_phone")
        notice_id = data.get("id")

        admin = User.query.filter_by(phone=admin_phone).first()
        if not admin or admin.role != "admin":
            return jsonify({"code": 403, "msg": "无管理员权限", "data": None}), 403

        notice = Notice.query.get(notice_id)
        if not notice:
            return jsonify({"code": 404, "msg": "公告不存在", "data": None}), 404

        db.session.delete(notice)
        db.session.commit()
        return jsonify({"code": 200, "msg": "公告删除成功", "data": None}), 200
    except Exception as e:
        db.session.rollback()
<<<<<<< HEAD
        return jsonify({"code": 500, "msg" : '服务器繁，请稍后重试', "data": None}), 500
=======
        return jsonify({"code": 500, "msg": str(e), "data": None}), 500
>>>>>>> 5e036f6a408ae0904899abe4af4904da810d9e9e

# ===================== 管理员管理接口 =====================
@app.route('/api/admin/add_admin', methods=['POST'])
@api_cost_log
def add_admin():
    try:
        data = request.get_json()
        admin_phone = data.get("admin_phone")
        new_phone = data.get("new_phone")
        new_password = data.get("new_password")
        new_name = data.get("new_name", '')  # 改为 name

        admin = User.query.filter_by(phone=admin_phone).first()
        if not admin or admin.role != "admin":
            return jsonify({"code": 403, "msg": "无管理员权限", "data": None}), 403

        if User.query.filter_by(phone=new_phone).first():
            return jsonify({"code": 400, "msg": "该手机号已注册", "data": None}), 400

        if len(new_password) < 6:
            return jsonify({"code": 400, "msg": "密码至少6位", "data": None}), 400

        new_admin = User(
            phone=new_phone,
            password=hash_password(new_password),
            name=new_name or '管理员',  # 改为 name
            role='admin',
            building_no='',
            room_no='',
            user_status='正常',
            audit_id=1
        )
        db.session.add(new_admin)
        db.session.commit()

        return jsonify({
            "code": 200,
            "msg": "管理员添加成功",
            "data": {"phone": new_phone}
        }), 200
    except Exception as e:
        db.session.rollback()
<<<<<<< HEAD
        return jsonify({"code": 500, "msg" : '服务器繁，请稍后重试', "data": None}), 500
=======
        return jsonify({"code": 500, "msg": str(e), "data": None}), 500
>>>>>>> 5e036f6a408ae0904899abe4af4904da810d9e9e

@app.route('/api/admin/list', methods=['POST'])
@api_cost_log
def admin_list():
    try:
        data = request.get_json()
        admin_phone = data.get("admin_phone")

        admin = User.query.filter_by(phone=admin_phone).first()
        if not admin or admin.role != "admin":
            return jsonify({"code": 403, "msg": "无管理员权限", "data": None}), 403

        admins = User.query.filter_by(role="admin").all()
        result = []
        for u in admins:
            result.append({
                "id": u.id,
                "phone": u.phone,
                "name": u.name,  # 改为 name
                "create_time": u.create_time.strftime("%Y-%m-%d %H:%M") if u.create_time else ""
            })
        return jsonify({"code": 200, "msg": "查询成功", "data": result}), 200
    except Exception as e:
<<<<<<< HEAD
        return jsonify({"code": 500, "msg" : '服务器繁，请稍后重试', "data": None}), 500
=======
        return jsonify({"code": 500, "msg": str(e), "data": None}), 500
>>>>>>> 5e036f6a408ae0904899abe4af4904da810d9e9e

@app.route('/api/admin/delete_admin', methods=['POST'])
@api_cost_log
def delete_admin():
    try:
        data = request.get_json()
        admin_phone = data.get("admin_phone")
        target_id = data.get("target_id")

        admin = User.query.filter_by(phone=admin_phone).first()
        if not admin or admin.role != "admin":
            return jsonify({"code": 403, "msg": "无管理员权限", "data": None}), 403

        target = User.query.get(target_id)
        if not target:
            return jsonify({"code": 404, "msg": "用户不存在", "data": None}), 404

        if target.role != "admin":
            return jsonify({"code": 400, "msg": "只能删除管理员账号", "data": None}), 400

        if target.id == admin.id:
            return jsonify({"code": 400, "msg": "不能删除自己", "data": None}), 400

        db.session.delete(target)
        db.session.commit()
        return jsonify({"code": 200, "msg": "删除成功", "data": None}), 200
    except Exception as e:
        db.session.rollback()
<<<<<<< HEAD
        return jsonify({"code": 500, "msg" : '服务器繁，请稍后重试', "data": None}), 500
=======
        return jsonify({"code": 500, "msg": str(e), "data": None}), 500
>>>>>>> 5e036f6a408ae0904899abe4af4904da810d9e9e

# ===================== 管理员获取总工单数 =====================
@app.route('/api/admin/total_orders', methods=['POST'])
@api_cost_log
def admin_total_orders():
    """管理员获取系统中所有工单总数"""
    try:
        data = request.get_json()
        admin_phone = data.get("admin_phone")

        admin = User.query.filter_by(phone=admin_phone).first()
        if not admin or admin.role != "admin":
            return jsonify({"code": 403, "msg": "无管理员权限", "data": None}), 403

        total = RepairOrder.query.count()
        return jsonify({
            "code": 200,
            "msg": "查询成功",
            "data": {"total": total}
        }), 200
    except Exception as e:
<<<<<<< HEAD
        return jsonify({"code": 500, "msg" : '服务器繁，请稍后重试', "data": None}), 500
# 程序入口
if __name__ == '__main__':
=======
        return jsonify({"code": 500, "msg": str(e), "data": None}), 500
# 程序入口
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
>>>>>>> 5e036f6a408ae0904899abe4af4904da810d9e9e
    app.run(host='0.0.0.0', port=5000, debug=False)