from apscheduler.schedulers.background import BackgroundScheduler
from services.expiry_service import check_expired_food

def start_scheduler(app):
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_expired_food, "interval", minutes=10)
    scheduler.start()
