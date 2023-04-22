import schedule
import time

schedule.every().week.at("12:00").do(exec(open('main.py').read()))

while True:
    schedule.run_pending()
    time.sleep(3000)