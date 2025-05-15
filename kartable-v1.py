#/usr/bin/env python
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
import sqlite3
from sqlite3 import Error
from datetime import datetime
import os

FMT = '%H:%M:%S'
# connect to database
basedir = os.path.abspath(os.path.dirname(__file__))
dbpath = os.path.join(basedir,'kartable.sqlite')

def connect_db():
    try:
        global con , c
        con = sqlite3.connect(dbpath)
        c = con.cursor()
        # return con
    except Error:
        print(Error)

# Create table
def create_table():
    c.execute('''CREATE TABLE IF NOT EXISTS kartable
               (ID INT PRIMARY KEY NOT NULL,status text, year INT, month INT, day INT,hour text, time text, SUM INT)''')
    con.commit()
    con.close()


def show_execute():
    date = datetime.now()
    date_s = gregorian_to_jalali(date.year,date.month,date.day)
    c.execute("SELECT ID,SUM,hour,month FROM kartable  WHERE month = '%s' ORDER BY ID DESC LIMIT 1"%(date_s[1]))
    res = c.fetchone()
    return res

def do_execute(status):
    connect_db()
    res = show_execute()
    print("res in {} is: ".format(status),res)
    date = datetime.now()
    hour = datetime.strftime(date, FMT)
    date_s = gregorian_to_jalali(date.year,date.month,date.day)
    res = show_execute()
    if res == None or res[3] != date_s[1]:
        status = "test"
        print("----> first day of month reset SUM.")
        c.execute("SELECT ID FROM kartable ORDER BY ID DESC LIMIT 1")
        res = c.fetchone()
        print("----> (id) res in first day of month",res)
        c.execute("INSERT INTO kartable VALUES (?,?,?,?,?,?,?,?)",
                            (res[0]+1,"test",date_s[0], date_s[1], date_s[2], hour, date,0))
        con.commit()
        do_execute("signin ")
    if status == "signin ":
        c.execute("INSERT INTO kartable VALUES (?,?,?,?,?,?,?,?)",
                    (res[0]+1,"signin ", date_s[0], date_s[1], date_s[2], hour, date, res[1]))
    elif status == "signout":
        SUM = datetime.strptime(hour, FMT) - datetime.strptime(res[2], FMT)
        print("sum1 is: ",SUM)
        (h, m, s) = str(SUM).split(':')
        SUM = int(h) * 60 + int(m)
        SUM = SUM + res[1]
        print("sum2 is: ",SUM)
        c.execute("INSERT INTO kartable VALUES (?,?,?,?,?,?,?,?)",
                    (res[0]+1,"signout", date_s[0], date_s[1], date_s[2], hour, date, SUM))
    # Save (commit) the changes
    con.commit()

def signin(sts):
    try:
        if sts == "signout" or sts == "test":
            do_execute("signin ")
            messagebox.showinfo("Done", "signing in was successful.")
            print("sign in was successful.")
        else:
            messagebox.showerror("ERROR", "you already signed in!")
            print("you already signed in!")
    except Exception as e:
        con.rollback()
        messagebox.showerror("ERROR", "sign in was not successful.\n --->  {}".format(e))
    finally:
        con.close()

def signout(sts):
    try:
        if sts == "signin ":
            do_execute("signout")
            messagebox.showinfo("Done", "sign out was successful.")
            print("sign out was successful.")
        else:
            messagebox.showerror("ERROR", "you already signed out!")
            print("you already signed out!")
    except Exception as e:
        con.rollback()
        messagebox.showerror("ERROR", "sign out was not successful.\n --->  {}".format(e))
    finally:
        con.close()

def Show():
    try:
        show = Toplevel(win)
        show.title('Show Sum')
        show.geometry("350x400")
        connect_db()
        c.execute("SELECT day,status,hour,SUM FROM kartable WHERE month = {} and year = {}".format(cb.get(),cb2.get()))
        res = c.fetchall()
        # print("res in show: ",res)
        c.execute("SELECT SUM FROM kartable WHERE month = {} and year = {} ORDER BY ID DESC LIMIT 1".format(cb.get(),cb2.get()))
        Sum = c.fetchone()
        print("Sum in show: ",Sum)
        con.close()
        lable1 = Label(show,text="num - day -- status -- hour --- sum -- sum in hour")
        lable1.pack(fill="x")
        # create Listbox and scrollbar for it.
        Lb1 = Listbox(show,height=18)
        n = 1
        for i in res :
            Lb1.insert(n,"{}  -  {}  --  {}  --  {}  ---  {} -- {}:{}".format(n,i[0],i[1],i[2],i[3],i[3]//60,i[3]-(i[3]//60)*60))
            n += 1
        scrollbar = Scrollbar(show)
        scrollbar.pack(side = RIGHT, fill = BOTH)
        Lb1.config(yscrollcommand = scrollbar.set)
        scrollbar.config(command = Lb1.yview)
        Lb1.pack(fill="x")
        lable2 = Label(show,text="{} minutes or {}:{} hours".format(Sum[0],(Sum[0])//60,Sum[0]-((Sum[0])//60)*60))
        lable2.pack(fill="x")
    except Exception as e:
        messagebox.showerror("ERROR", "no data available.\n --->  {}".format(e))
        show.destroy()  
    finally:
        con.close()

def PRINT():
    try:
        connect_db()
        #ID INT PRIMARY KEY NOT NULL,status text, year INT, month INT, day INT,hour text, time text, SUM
        c.execute("SELECT id,status,year,month,day,hour,time,SUM FROM kartable WHERE month = {} and year = {}".format(cb.get(),cb2.get()))
        res = c.fetchall()
        #print("res in PRINT: ",res[0])
        filename = "savefile_of-{}-{}.csv".format(cb2.get(),cb.get())
        filepath = os.path.join(basedir,filename)
        f = open(filepath,"a")
        f.write("number,id,status,year,month,day,hour,time,SUM,SUM in hour\n")
        n = 1
        for i in res:
            f.write(f"{n},{i[0]},{i[1]},{i[2]},{i[3]},{i[4]},{i[5]},{i[6]},{i[7]},{i[7]//60}:{i[7]-(i[7]//60)*60}\n")
            # f.write("{}\t,{}\n".format(n,i))
            n += 1
        messagebox.showinfo("successful", "file saved in: \n-------------\n {}".format(filepath))
        print("record saved in ",filename)
    finally:
        con.close()
        f.close()

################### first run ####################
def first_run():
    connect_db()
    date = datetime.now()
    hour = datetime.strftime(date, FMT)
    date_s = gregorian_to_jalali(date.year,date.month,date.day)
    c.execute("INSERT INTO kartable VALUES (?,?,?,?,?,?,?,?)",
                        (1,"test",date_s[0], date_s[1], date_s[2], hour, date,0))
    con.commit()
    con.close()
################### first run ####################

def Start():
    connect_db()
    print("------------------------------")        
    date = datetime.now()
    date_s= gregorian_to_jalali(date.year,date.month,date.day)        
    c.execute("SELECT SUM,status FROM kartable WHERE month = {} and year = {} ORDER BY ID DESC LIMIT 1".format(date_s[1],date_s[0]))
    # c.execute("SELECT SUM FROM kartable WHERE month = {} ORDER BY ID DESC".format(date[1]))
    SUM = c.fetchone()
    print("today is: ",date_s," --- ",date)
    print("SUM in vorod: ",SUM)    
    # for none type eror
    if SUM== None:
        hour = datetime.strftime(date, FMT)
        c.execute("SELECT ID FROM kartable ORDER BY ID DESC LIMIT 1")
        res = c.fetchone()
        print("----> (id) res in first day of month",res)
        c.execute("INSERT INTO kartable VALUES (?,?,?,?,?,?,?,?)",
                            (res[0]+1,"test",date_s[0], date_s[1], date_s[2], hour, date,0))
        con.commit()
        c.execute("SELECT SUM,status FROM kartable WHERE month = {} and year = {} ORDER BY ID DESC LIMIT 1".format(date_s[1],date_s[0]))
        # c.execute("SELECT SUM FROM kartable WHERE month = {} ORDER BY ID DESC".format(date[1]))
        SUM = c.fetchone()
        print("NEW SUM in vorod: ",SUM)    
    con.close()


    lb = Label(win,text="sum of this month({}/{}):".format(date_s[1],date_s[2]))
    lb.pack(pady=5)
    var = StringVar()
    status=Label(win,textvariable=var)
    try:
        var.set("{} miniutes or {}:{} hours".format(SUM[0],(SUM[0])//60,SUM[0]-((SUM[0])//60)*60))
        lb_sts = Label(win,text="current status: {}".format(SUM[1]))
        lb_sts.pack()
    except Exception as e:
        print("seting var in line 188 has eror --> ",e,",so we set 0 in it.(0 miniutes or 0 hours)")
        var.set("0 miniutes or 0 hours")
    status.pack(pady=7)


    btn_login = ttk.Button(win, text= 'Sign in', command = lambda : signin(SUM[1]))
    btn_login.pack(pady=7)
    btn_signout = ttk.Button(win, text= 'Sign out', command = lambda : signout(SUM[1]))
    btn_signout.pack(pady=7)

    lb_cb = Label(win,text="show sum of blow month(now: {}/{}):".format(date_s[1],date_s[2]))
    lb_cb.pack(pady=10)
    global cb
    cb = ttk.Combobox(win,values=(1,2,3,4,5,6,7,8,9,10,11,12))
    cb.set(date_s[1])
    cb.pack()

    lb2 = Label(win,text="show sum of blow year(now: {}):".format(date_s[0]))
    lb2.pack(pady=5)
    global cb2
    vv = [i for i in range(1400,1440)]
    cb2 = ttk.Combobox(win,values=(vv))
    cb2.set(date_s[0])
    cb2.pack(pady=5)

    btn_show = ttk.Button(win, text= 'show', command = Show)
    btn_show.pack(pady=12)
    btn_print = ttk.Button(win, text= 'save', command = PRINT)
    btn_print.pack(pady=12)


def gregorian_to_jalali(gy, gm, gd):
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    if (gm > 2):
        gy2 = gy + 1
    else:
        gy2 = gy
    days = 355666 + (365 * gy) + ((gy2 + 3) // 4) - ((gy2 + 99) // 100) + ((gy2 + 399) // 400) + gd + g_d_m[gm - 1]
    jy = -1595 + (33 * (days // 12053))
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if (days > 365):
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if (days < 186):
        jm = 1 + (days // 31)
        jd = 1 + (days % 31)
    else:
        jm = 7 + ((days - 186) // 30)
        jd = 1 + ((days - 186) % 30)
    return [jy, jm, jd]



if __name__ == "__main__":
    win = Tk()
    win.geometry("300x400")
    win.resizable(False, False)
    win.title('kartable')
    date = datetime.now()
    date_s = gregorian_to_jalali(date.year,date.month,date.day)
    #####################
    if not os.path.exists(dbpath):
        print("kartable database dosent exists. so we create it :)")
        connect_db()        
        create_table()
        first_run()
    else:
        print("kartable database already exists so we use it.")
    #####################
    Start()
    win.mainloop()
