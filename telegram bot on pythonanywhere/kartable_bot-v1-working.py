import telepot
import sqlite3
from sqlite3 import Error
from datetime import datetime
import pytz
import os
import time
import urllib3
from telepot.namedtuple import ReplyKeyboardMarkup

# تنظیم منطقه زمانی
tehran_tz = pytz.timezone('Asia/Tehran')
FMT = '%H:%M:%S'


proxy_url = "http://proxy.server:3128"
telepot.api._pools = {
    'default': urllib3.ProxyManager(proxy_url=proxy_url, num_pools=3, maxsize=10, retries=False, timeout=30),
}
telepot.api._onetime_pool_spec = (urllib3.ProxyManager, dict(proxy_url=proxy_url, num_pools=1, maxsize=1, retries=False, timeout=30))

# توکن ربات تلگرام
TOKEN = '7327927652:AAFEpz9tqZZt6vw5LJcRKfKRrpMoi-duRqI'
bot = telepot.Bot(TOKEN)

# تنظیمات پایگاه داده
basedir = os.path.abspath(os.path.dirname(__file__))
dbpath = os.path.join(basedir, 'kartable.sqlite')

# --- توابع پایگاه داده ---
def connect_db():
    try:
        con = sqlite3.connect(dbpath)
        c = con.cursor()
        return con, c
    except Error as e:
        print(e)
        return None, None

def create_table():
    con, c = connect_db()
    if not con:
        return
    c.execute('''CREATE TABLE IF NOT EXISTS kartable
               (ID INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INT NOT NULL,
                status TEXT,
                year INT,
                month INT,
                day INT,
                hour TEXT,
                time TEXT,
                SUM INT)''')
    con.commit()
    con.close()

create_table()

def gregorian_to_jalali(gy, gm, gd):
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    gy2 = gy + 1 if gm > 2 else gy
    days = 355666 + (365 * gy) + ((gy2 + 3) // 4) - ((gy2 + 99) // 100) + ((gy2 + 399) // 400) + gd + g_d_m[gm - 1]
    jy = -1595 + (33 * (days // 12053))
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    jm = 1 + (days // 31) if days < 186 else 7 + ((days - 186) // 30)
    jd = 1 + (days % 31) if days < 186 else 1 + ((days - 186) % 30)
    return [jy, jm, jd]

def do_execute(chat_id, status, manual_date=None):
    con, c = connect_db()
    if not con:
        return "❌ خطای اتصال به پایگاه داده."
    try:
        date = manual_date if manual_date else datetime.now(tehran_tz)
        hour = date.strftime(FMT)
        date_s = gregorian_to_jalali(date.year, date.month, date.day)

        # اصلاح کوئری برای دریافت فیلد time به جای hour
        c.execute("SELECT SUM, time, status FROM kartable WHERE chat_id = ? AND year = ? AND month = ? ORDER BY ID DESC LIMIT 1",
                  (chat_id, date_s[0], date_s[1]))
        res = c.fetchone()

        if not res:
            c.execute("INSERT INTO kartable (chat_id, status, year, month, day, hour, time, SUM) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                      (chat_id, "test", date_s[0], date_s[1], date_s[2], hour, date.strftime("%Y-%m-%d %H:%M:%S"), 0))
            con.commit()
            res = (0, date.strftime("%Y-%m-%d %H:%M:%S"), "test")

        if status == "signin ":
            c.execute("INSERT INTO kartable (chat_id, status, year, month, day, hour, time, SUM) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                      (chat_id, "signin ", date_s[0], date_s[1], date_s[2], hour, date.strftime("%Y-%m-%d %H:%M:%S"), res[0]))
            con.commit()
        elif status == "signout":
            if res[2] != "signin ":
                return "❌ ابتدا باید ورود ثبت شده باشد."
            # تبدیل زمان قبلی با استفاده از فیلد time و منطقه زمانی
            prev_time = tehran_tz.localize(datetime.strptime(res[1], "%Y-%m-%d %H:%M:%S"))
            delta = date - prev_time
            total_minutes = delta.seconds // 60
            new_sum = res[0] + total_minutes
            c.execute("INSERT INTO kartable (chat_id, status, year, month, day, hour, time, SUM) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                      (chat_id, "signout", date_s[0], date_s[1], date_s[2], hour, date.strftime("%Y-%m-%d %H:%M:%S"), new_sum))
            con.commit()
        return "✅ عملیات موفقیت‌آمیز بود."
    except Exception as e:
        con.rollback()
        return f"❌ خطا: {str(e)}"
    finally:
        con.close()

def handle_signin(chat_id):
    con, c = connect_db()
    if not con:
        return "❌ خطای پایگاه داده."
    try:
        date_s = gregorian_to_jalali(datetime.now(tehran_tz).year, datetime.now(tehran_tz).month, datetime.now(tehran_tz).day)
        c.execute("SELECT status FROM kartable WHERE chat_id = ? AND year = ? AND month = ? ORDER BY ID DESC LIMIT 1",
                  (chat_id, date_s[0], date_s[1]))
        res = c.fetchone()
        status = res[0] if res else None

        if status in ("signout", "test", None):
            result = do_execute(chat_id, "signin ")
            return "✅ ورود شما در {} ثبت شد.".format(datetime.now(tehran_tz).strftime('%Y-%m-%d %H:%M:%S'))
        else:
            return "❌ قبلاً وارد شده‌اید."
    except Exception as e:
        return f"❌ خطا: {str(e)}"
    finally:
        con.close()

def handle_signout(chat_id):
    con, c = connect_db()
    if not con:
        return "❌ خطای پایگاه داده."
    try:
        date_s = gregorian_to_jalali(datetime.now(tehran_tz).year, datetime.now(tehran_tz).month, datetime.now(tehran_tz).day)
        # اصلاح کوئری برای دریافت فیلد time
        c.execute("SELECT status, time FROM kartable WHERE chat_id = ? AND year = ? AND month = ? ORDER BY ID DESC LIMIT 1",
                  (chat_id, date_s[0], date_s[1]))
        res = c.fetchone()

        if res and res[0] == "signin ":
            # تبدیل زمان قبلی با استفاده از فیلد time
            prev_time = tehran_tz.localize(datetime.strptime(res[1], "%Y-%m-%d %H:%M:%S"))
            delta = datetime.now(tehran_tz) - prev_time
            total_minutes = delta.seconds // 60 + delta.days * 1440
            result = do_execute(chat_id, "signout")
            return "✅ خروج شما در {} ثبت شد. مدت زمان: {} ساعت و {} دقیقه".format(
                datetime.now(tehran_tz).strftime('%Y-%m-%d %H:%M:%S'),
                total_minutes // 60,
                total_minutes % 60
            )
        else:
            return "❌ ابتدا باید ورود ثبت شود."
    except Exception as e:
        return f"❌ خطا: {str(e)}"
    finally:
        con.close()

def handle_show(chat_id, month=None, year=None):
    con, c = connect_db()
    if not con:
        return "❌ خطای پایگاه داده."
    try:
        if not month or not year:
            date_s = gregorian_to_jalali(datetime.now(tehran_tz).year, datetime.now(tehran_tz).month, datetime.now(tehran_tz).day)
            month = date_s[1]
            year = date_s[0]

        c.execute("SELECT day, status, hour, SUM FROM kartable WHERE chat_id = ? AND year = ? AND month = ? ORDER BY ID",
                  (chat_id, year, month))
        entries = c.fetchall()

        response = f"📅 گزارش کارهای {year}/{month}:\n"
        for entry in entries:
            response += f"\nروز {entry[0]}: {entry[1]} در {entry[2]} - {entry[3]} دقیقه"

        c.execute("SELECT SUM FROM kartable WHERE chat_id = ? AND year = ? AND month = ? ORDER BY ID DESC LIMIT 1",
                  (chat_id, year, month))
        total = c.fetchone()
        if total:
            response += f"\n\nمجموع: {total[0]} دقیقه ({total[0] // 60} ساعت و {total[0] % 60} دقیقه)"
        return response
    except Exception as e:
        return f"❌ خطا: {str(e)}"
    finally:
        con.close()




def handle_print(chat_id, month=None, year=None):
    con, c = connect_db()
    if not con:
        return "❌ خطای پایگاه داده."
    try:
        if not month or not year:
            date_s = gregorian_to_jalali(datetime.now(tehran_tz).year, datetime.now(tehran_tz).month, datetime.now(tehran_tz).day)
            month = date_s[1]
            year = date_s[0]

        # خواندن داده‌ها از دیتابیس
        c.execute("SELECT day, status, hour, SUM FROM kartable WHERE chat_id = ? AND year = ? AND month = ? ORDER BY ID",
                  (chat_id, year, month))
        entries = c.fetchall()
        import csv
        # ایجاد فایل CSV
        csv_filename = f"kartable_{year}_{month}.csv"
        csv_filepath = os.path.join(basedir, csv_filename)
        with open(csv_filepath, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["روز", "وضعیت", "ساعت", "مجموع دقیقه"])
            for entry in entries:
                writer.writerow([entry[0], entry[1], entry[2], entry[3]])

        # ارسال فایل CSV و دیتابیس
        with open(csv_filepath, 'rb') as csv_file, open(dbpath, 'rb') as db_file:
            bot.sendDocument(chat_id, csv_file, caption=f"📄 فایل CSV برای {year}/{month}")
            bot.sendDocument(chat_id, db_file, caption="📦 فایل دیتابیس")

        # حذف فایل CSV موقت
        os.remove(csv_filepath)
        return "✅ فایل‌ها با موفقیت ارسال شدند."
    except Exception as e:
        return f"❌ خطا: {str(e)}"
    finally:
        con.close()






# --- مدیریت پیام‌ها با Long Polling ---
last_update_id = 0

def process_message(msg):
    global last_update_id
    content_type, chat_type, chat_id = telepot.glance(msg)
    if content_type == 'text':
        text = msg['text']
        if text.startswith("/start"):
            text = msg['text']

            if text.startswith("/start"):
                keyboard = ReplyKeyboardMarkup(keyboard=[
            ["/signin", "/signout"],
            ["/show", "/manual","/print"],], resize_keyboard=True, one_time_keyboard=False)

            bot.sendMessage(chat_id, "✅ لطفاً یکی از گزینه‌های زیر را انتخاب کنید:", reply_markup=keyboard)
        elif text.startswith("/signin"):
            response = handle_signin(chat_id)
            bot.sendMessage(chat_id, response)

        elif text.startswith("/signout"):
            response = handle_signout(chat_id)
            bot.sendMessage(chat_id, response)

        elif text.startswith("/show"):
            parts = text.split()
            month, year = None, None
            if len(parts) >= 2: month = int(parts[1])
            if len(parts) >= 3: year = int(parts[2])
            response = handle_show(chat_id, month, year)
            bot.sendMessage(chat_id, response)

        elif text.startswith("/print"):
            parts = text.split()
            month, year = None, None
            if len(parts) >= 2: month = int(parts[1])
            if len(parts) >= 3: year = int(parts[2])
            response = handle_print(chat_id, month, year)
            bot.sendMessage(chat_id, response)

        elif text.startswith("/manual"):
            try:
                _, date_str, time_str, status = text.split()
                manual_date = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
                if status == "signin": status = "signin "
                result = do_execute(chat_id, status, manual_date)
                bot.sendMessage(chat_id, result)
            except:
                bot.sendMessage(chat_id, "❌ فرمت صحیح: /manual YYYY-MM-DD HH:MM:SS signin/signout")

        else:
            bot.sendMessage(chat_id, "❌ دستور نامعتبر!")

# حلقه اصلی برای دریافت پیام‌ها
while True:
    try:
        updates = bot.getUpdates(offset=last_update_id + 1, timeout=10)

        for update in updates:
            last_update_id = update['update_id']
            process_message(update['message'])

    except Exception as e:
        print(f"Error: {str(e)}")
        time.sleep(5)