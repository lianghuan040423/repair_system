# duty.py
from datetime import datetime
from models import DutySchedule

def is_worker_on_duty(worker_id):
    """判断物业人员今天是否值班"""
    today = datetime.now().date()
    duty = DutySchedule.query.filter_by(worker_id=worker_id, duty_date=today).first()
    return duty is not None