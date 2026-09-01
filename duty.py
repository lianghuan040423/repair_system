# duty.py
from datetime import datetime
from models import DutySchedule

def is_worker_on_duty(worker_id):
<<<<<<< HEAD
    """判断物业人员今天是否在值班时间段内"""
    today = datetime.now().date()
    duty = DutySchedule.query.filter(
        DutySchedule.worker_id == worker_id,
        DutySchedule.start_date <= today,
        DutySchedule.end_date >= today
    ).first()
=======
    """判断物业人员今天是否值班"""
    today = datetime.now().date()
    duty = DutySchedule.query.filter_by(worker_id=worker_id, duty_date=today).first()
>>>>>>> 5e036f6a408ae0904899abe4af4904da810d9e9e
    return duty is not None