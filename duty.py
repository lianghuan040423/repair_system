# duty.py
from datetime import datetime
from models import DutySchedule

def is_worker_on_duty(worker_id):
    """判断物业人员今天是否在值班时间段内"""
    today = datetime.now().date()
    duty = DutySchedule.query.filter(
        DutySchedule.worker_id == worker_id,
        DutySchedule.start_date <= today,
        DutySchedule.end_date >= today
    ).first()
    return duty is not None