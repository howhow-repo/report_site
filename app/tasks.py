from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore, register_job

scheduler = BackgroundScheduler()
scheduler.add_jobstore(DjangoJobStore(), 'default')


@register_job(scheduler, 'interval', id='test', seconds=10, replace_existing=True)
def test():
    # 具体要执行的代码
    print(f'{datetime.now()} loopppp')
    pass


scheduler.start()
