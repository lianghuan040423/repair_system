# models.py
from datetime import datetime
from sqlalchemy import Integer
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, relationship
from sqlalchemy import MetaData, String, ForeignKey, DateTime
from typing import List
from datetime import datetime, timedelta

# 全局db实例，由app.py传入初始化
db = SQLAlchemy()


# 定义命名约定的Base类
class Base(DeclarativeBase):
    metadata = MetaData(naming_convention={
        "ix": 'ix_%(column_0_label)s',
        "uq": "uq_%(table_name)s_%(column_0_repr)s",
        "ck": "ck_%(table_name)s_%(column_0_repr)s",
        "fk": "fk_%(table_name)s_%(column_0_repr)s",
        "pk": "pk_%(table_name)s"
    })


# 房间表
class Room(db.Model):
    __tablename__ = 'room'
    id: Mapped[int] = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False, comment='房间id')
    building_id: Mapped[int] = db.Column(db.Integer, nullable=False, index=True,
                                         comment='所属楼栋id（逻辑关联，无物理外键）')
    room_no: Mapped[String] = db.Column(db.String(20), nullable=False, comment='房间号，如101')
    status: Mapped[String] = db.Column(db.Integer, default=0, comment='0-空置 1-已入住')
    create_time: Mapped[DateTime] = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    update_time: Mapped[DateTime] = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now,
                                              comment='更新时间')


# 栋楼表_主表
class Building(db.Model):
    __tablename__ = 'building'
    id: Mapped[int] = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False, comment='楼栋id')
    building_no: Mapped[str] = db.Column(db.String(20), nullable=False, comment='楼栋号')
    create_time: Mapped[datetime] = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    update_time: Mapped[datetime] = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now,
                                              comment='更新时间')


# 报修类型表
class RepairType(db.Model):
    __tablename__ = 'repair_type'
    id: Mapped[int] = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False, comment='类型id')
    type_name: Mapped[str] = db.Column(db.String(50), nullable=False, unique=True, comment='报修类型名称')
    sort: Mapped[int] = db.Column(db.Integer, default=0, comment='排序值')
    create_time: Mapped[datetime] = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    update_time: Mapped[datetime] = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now,
                                              comment='更新时间')


# 用户模型
class User(db.Model):
    __tablename__ = 'user'
    id: Mapped[int] = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False, comment='用户id')
    room_id: Mapped[int] = db.Column(db.Integer, nullable=True, index=True, comment='关联房间id，工作人员可为空')  # 逻辑关联
    phone: Mapped[str] = db.Column(db.String(11), unique=True, nullable=False, comment='手机号')
    building_no: Mapped[str] = db.Column(db.String(20), nullable=False, comment='栋楼号')
    room_no: Mapped[str] = db.Column(db.String(20), nullable=False, comment='房间号')
    name: Mapped[str] = db.Column(db.String(30), default='', comment='真实姓名')
    password: Mapped[str] = db.Column(db.String(100), nullable=False, comment='加密密码')
    role: Mapped[str] = db.Column(db.String(20), default='user', comment='user或worker,admin')
    user_status: Mapped[str] = db.Column(db.String(20), comment='用户账户状态 正常/禁用/未检验')
    create_time: Mapped[datetime] = db.Column(db.DateTime, default=datetime.now, comment='注册时间')
    update_time: Mapped[datetime] = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now,comment='更新时间')
    audit_id: Mapped[int] = db.Column(db.Integer, default=1,comment="审核状态，0=待审核 1=已通过（物业注册专用，住户默认通过）")

    # ===== 修改：明确指定外键为 RepairOrder.user_id =====
    repair_order: Mapped[List["RepairOrder"]] = relationship(
        back_populates="user",
        foreign_keys="[RepairOrder.user_id]"  # 关键修改
    )


# 报修工单表
class RepairOrder(db.Model):
    __tablename__ = 'repair_order'
    id: Mapped[int] = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False, comment='工单id')
    user_id: Mapped[int] = db.Column(db.Integer, ForeignKey('user.id'), nullable=False, comment='关联提交工单的用户id')
    worker_id: Mapped[int] = db.Column(db.Integer, ForeignKey('user.id'), nullable=True,
                                       comment='处理该工单的物业人员id')  # 新增
    building_id: Mapped[int] = db.Column(db.Integer, nullable=False, index=True, comment='关联栋楼')
    room_id: Mapped[int] = db.Column(db.Integer, nullable=False, index=True, comment='关联房间')
    title: Mapped[str] = db.Column(db.String(50), nullable=False, comment='报修标题')
    content: Mapped[str] = db.Column(db.Text, comment='报修描述')
    img_url: Mapped[str] = db.Column(db.String(255), comment='上传图片路径')
    status: Mapped[Integer] = db.Column(Integer, nullable=False, comment='工单状态 0：待维修 1：维修中 2：已完成')
    building: Mapped[str] = db.Column(db.String(20), nullable=False, comment='保修楼栋（方便物业）')
    room: Mapped[str] = db.Column(db.String(20), nullable=False, comment='报修房号（便于物业筛选）')
    submit_time: Mapped[datetime] = db.Column(db.DateTime, nullable=False, comment='工单提交时间')
    finish_time: Mapped[datetime | None] = db.Column(db.DateTime, comment='完工时间')
    # 在 RepairOrder 类中添加
    start_time: Mapped[datetime | None] = db.Column(db.DateTime, nullable=True, comment='维修开始时间（记录工单何时变为维修中）')

    # 关系定义（明确指定外键）
    user: Mapped["User"] = relationship(
        foreign_keys=[user_id],
        back_populates="repair_order"
    )
    worker: Mapped["User"] = relationship(
        foreign_keys=[worker_id]
    )


# 公告表
class Notice(db.Model):
    __tablename__ = 'notice'
    id: Mapped[int] = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False, comment='公告id')
    title: Mapped[str] = db.Column(db.String(100), nullable=False, comment='公告标题')
    content: Mapped[str] = db.Column(db.Text, nullable=False, comment='公告内容')
    publish_user_id: Mapped[int] = db.Column(db.Integer, ForeignKey('user.id'), nullable=False, comment='发布人id')
    create_time: Mapped[datetime] = db.Column(db.DateTime, default=datetime.now, comment='发布时间')
    update_time: Mapped[datetime] = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

# ===================== 验证码表（忘记密码用） =====================
class SmsCode(db.Model):
    __tablename__ = 'sms_code'
    id: Mapped[int] = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False, comment='id')
    phone: Mapped[str] = db.Column(db.String(11), nullable=False, index=True, comment='手机号')
    code: Mapped[str] = db.Column(db.String(10), nullable=False, comment='验证码')
    create_time: Mapped[datetime] = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    expire_time: Mapped[datetime] = db.Column(db.DateTime, nullable=False, comment='过期时间')
    used: Mapped[int] = db.Column(db.Integer, default=0, comment='0-未使用 1-已使用')

# ===================== 值班表 =====================
class DutySchedule(db.Model):
    __tablename__ = 'duty_schedule'
    id: Mapped[int] = db.Column(db.Integer, primary_key=True, autoincrement=True)
    worker_id: Mapped[int] = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    duty_date: Mapped[datetime] = db.Column(db.Date, nullable=False)
    create_time: Mapped[datetime] = db.Column(db.DateTime, default=datetime.now)

    __table_args__ = (
        db.UniqueConstraint('worker_id', 'duty_date', name='uq_worker_duty_date'),
    )
