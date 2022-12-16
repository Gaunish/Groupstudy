import sqlite3
from flask import session
from datetime import datetime
import time

def question_append(rows, user_id):
    lst = []
    curr = sqlite3.connect("database.db")
    conn = curr.cursor()
    for row in rows:
        comm_change = list(row)
            
        comm_change.append(comment_no(row[0]))
        comm_change.append(like_dislike_no(row[0], True))
        comm_change.append(like_dislike_no(row[0], False))
        comm_change.append(is_like(row[0], user_id))
 
        lst.append(comm_change)
    
    rows = tuple(lst)
    curr.close()
    return rows

def question_append_user_comm(rows, user_id):
    lst = []
    curr = sqlite3.connect("database.db")
    conn = curr.cursor()
    for row in rows:
        comm_change = list(row)

        conn.execute("select * from users where ref_id = :id", dict(id = row[5]))
        user_row = conn.fetchall()
        comm_change.append(user_row[0][1])

        conn.execute("select * from topic where topic_id = :id", dict(id = row[4]))
        topic_row = conn.fetchall()
        comm_change.append(topic_row[0][1])

        is_follow = check_follow(row[4], user_id)
        comm_change.append(is_follow)

        lst.append(comm_change)
    
    rows = tuple(lst)
    curr.close()
    return rows

def like_dislike_no(qid, like):
    curr = sqlite3.connect("database.db")
    conn = curr.cursor()
    conn.execute("Select count(*) from like_question where question_id = :qid and is_liked = :like", dict(qid = qid, like = like))
    like_dislike_no = conn.fetchall()
    curr.close()
    return like_dislike_no[0][0]

def comment_no(qid):
    curr = sqlite3.connect("database.db")
    conn = curr.cursor()
    conn.execute("Select COUNT(*) from comment where q_id = :id", dict(id = qid))
    user_row = conn.fetchall()
    curr.close()
    return user_row[0][0]

def is_like(qid, user_id):
    curr = sqlite3.connect("database.db")
    conn = curr.cursor()
    conn.execute("Select * from like_question where question_id = :qid and user_id = :id", dict(qid = qid, id = user_id))
    row_like = conn.fetchall()
    if len(row_like) == 0:
        is_liked = 'none'
    elif row_like[0][2] == True:
        is_liked = 'true'
    else:
        is_liked = 'false'
    curr.close()
    return is_liked

def check_follow(topic_id, user_id):

    curr = sqlite3.connect("database.db")
    conn = curr.cursor()
    conn.execute("select * from follow_topic where topic_id = :id and user_id = :uid", dict(id = topic_id, uid = user_id))
    follow_row = conn.fetchall()
    curr.close()

    if len(follow_row) != 0:
        return True    
    return False

def delete_if_present(quest_id):
    curr = sqlite3.connect("database.db")
    conn = curr.cursor()
    conn.execute("select * from like_question where question_id = :id and user_id = :uid", dict(id = quest_id, uid = session["user_id"]))
    follow_row = conn.fetchall()
    curr.close()

    if len(follow_row) != 0:
        curr = sqlite3.connect("database.db")
        conn = curr.cursor()
        conn.execute("delete from like_question where question_id = :id and user_id = :uid", dict(id = quest_id, uid = session["user_id"]))
        curr.commit()
        curr.close()   


def check_followed(q_id, user_id):
    curr = sqlite3.connect("database.db")
    conn = curr.cursor()
    conn.execute("select * from follow_question where question_id = :id and user_id = :uid", dict(id = q_id, uid = user_id))
    follow_row = conn.fetchall()
    curr.close()

    if len(follow_row) != 0:
        return True
            
    return False

def topic_topic_id(topic_id):
    curr = sqlite3.connect("database.db")
    conn = curr.cursor()
    conn.execute("select * from topic where topic_id = :id", dict(id = topic_id))
    topic_row = conn.fetchall()    
    curr.close()
    return topic_row

def question_q_id(quest_id):
    curr = sqlite3.connect("database.db")
    conn = curr.cursor()
    conn.execute("Select * from question where q_id = :id", dict(id = quest_id))
    row = conn.fetchall()
    curr.close()
    return row

def insert_like_question(quest_id, user_id, like, time):
    curr = sqlite3.connect("database.db")
    conn = curr.cursor()
    conn.execute("insert into like_question(question_id, user_id, is_liked, time) values(:qid, :uid, :liked, :time)", dict(qid = quest_id, uid = user_id, liked = like, time = time))
    curr.commit()
    curr.close()

def follower_no_topic(topic_id):
    curr = sqlite3.connect("database.db")
    conn = curr.cursor()
    conn.execute("select count(*) from follow_topic where topic_id = :id", dict(id = topic_id))
    follow_row = conn.fetchall()
    curr.close()

    return follow_row[0][0]

def popular_time_calc(now):

    prev = datetime(now.year - 1, now.month, now.day, now.hour, now.minute, now.second, now.microsecond)
    return prev

def trending_time_calc(now):
    hour = now.hour
    day = now.day
    month = now.month
    year = now.year


    if now.hour < 12:
        hour += 12

        if month == 1:
            month = 12
            year -= 1
        else:
            month -= 1

        if now.month == 3:
            day = 28
        else:
            day = 30

    else:
        hour -= 12

    prev = datetime(year, month, day, hour, now.minute, now.second, now.microsecond)
    return prev

def question_rows(timed):
    curr = sqlite3.connect("database.db")
    conn = curr.cursor()
    conn.execute("Select q.* from question as q join like_question as l  on q.q_id = l.question_id join comment as c on q.q_id = c.q_id  where q.create_time >= :time group by q.q_id order by count(c.q_id) desc, count(l.question_id) desc", dict(time = timed))
    rows = conn.fetchall()        
    curr.close()

    rows = question_append(rows, session["user_id"])
    rows = question_append_user_comm(rows, session["user_id"])
    time_calc(rows, 3)

    lst = img_extend(rows)    

    return lst

def topic_rows_find(rows):
    rows = question_append(rows, session["user_id"])
    rows = question_append_user_comm(rows, session["user_id"])
    time_calc(rows, 3)

    lst = img_extend(rows)
    return lst

def question_rows_trending(timed):
    curr = sqlite3.connect("database.db")
    conn = curr.cursor()
    conn.execute("Select q.* from question as q join like_question as l  on q.q_id = l.question_id join comment as c on q.q_id = c.q_id  where q.create_time >= :time group by q.q_id order by count(c.q_id) desc, count(l.question_id) desc", dict(time = timed))
    rows = conn.fetchall()        
    curr.close()

    rows = question_append(rows, session["user_id"])
    rows = question_append_user_comm(rows, session["user_id"])
    time_calc(rows, 3)

    lst = img_extend(rows)    
    return lst

def topic_rows(timed):
    curr = sqlite3.connect("database.db")
    conn = curr.cursor()
    conn.execute("Select t.* from topic as t join follow_topic as f on t.topic_id = f.topic_id where f.follow_time >= :time group by t.topic_id order by count(f.topic_id) desc limit 5", dict(time = timed))
    topic_rows = conn.fetchall()        
    curr.close()
    lst = []
    for row in topic_rows:
        lst_row = list(row)
            
        check_followed = check_follow(row[0], session["user_id"])
        lst_row.append(check_followed)

        member_no = follower_no_topic(row[0])
        lst_row.append(member_no)

        lst.append(lst_row)

    return lst

def search_question_query(search_string):
    curr = sqlite3.connect("database.db")
    conn = curr.cursor()
    conn.execute("select * from question where name like :query" , dict(query = search_string))
    question_query = conn.fetchall()
    curr.close()

    question_query = question_append(question_query, session["user_id"])
    question_query = question_append_user_comm(question_query, session["user_id"])
    time_calc(question_query, 3)
    lst = img_extend(question_query)

    return lst

def total_question_query(query_text):
    search_string = f"_{query_text}_"
    search_string2 = f"%{query_text}%"
        
    question_dash = list(search_question_query(search_string))
    question_percent = list(search_question_query(search_string2))
    
    question_dash.extend(question_percent)
    print(question_dash)
    
    return question_dash

def search_topic_query(search_string):
    curr = sqlite3.connect("database.db")
    conn = curr.cursor()
    conn.execute("select * from topic where name like :query" , dict(query = search_string))
    topic_total = conn.fetchall()
    curr.close()

    return listify_topic(topic_total)

def listify_topic(topic_total):
    topic_total_list = []
    for rowed in topic_total:
        list_row = list(rowed)
        list_row.append(check_follow(rowed[0], session["user_id"]))
        topic_total_list.append(list_row)

    return topic_total_list

def total_topic_query(query_text):
    search_string = f"_{query_text}_"
    search_string2 = f"%{query_text}%"
        
    topic_dash = search_topic_query(search_string)
    topic_percent = search_topic_query(search_string2)
        
    topic_dash.extend(topic_percent)
    return topic_dash

def search_topic_query_limit(search_string, limited):
    curr = sqlite3.connect("database.db")
    conn = curr.cursor()
    conn.execute("select * from topic where name like :query limit :limited" , dict(query = search_string, limited = limited))
    topic_total = conn.fetchall()
    curr.close()

    return listify_topic(topic_total)

def total_topic_query_limit(query_text):
    search_string = f"_{query_text}_"
    search_string2 = f"%{query_text}%"
        
    topic_dash = search_topic_query_limit(search_string, 3)
    
    if len(topic_dash) < 3:
        topic_percent = search_topic_query_limit(search_string2, 3 - len(topic_dash))
        
    topic_dash.extend(topic_percent)
    return topic_dash

def follow_topic_like(topic_id, user_id):

    is_follow=check_follow(topic_id, session["user_id"])
    
    if is_follow == True:
        curr = sqlite3.connect("database.db")
        conn = curr.cursor()
        conn.execute("delete from follow_topic where topic_id = :id and user_id = :uid", dict(id = topic_id, uid = user_id))
        curr.commit()
        curr.close()
    else:
        curr = sqlite3.connect("database.db")
        conn = curr.cursor()
        conn.execute("insert into follow_topic(user_id, topic_id, follow_time) values(:uid, :id, :timed)", dict(id = topic_id, uid = user_id, timed = datetime.now()))
        curr.commit()
        curr.close()


def time_calc(rows, i):
    for row in rows:
        time_count = ""
        timed = datetime(*time.strptime(row[i], "%Y-%m-%d %H:%M:%S.%f")[:6])
        now = datetime.now()
        no_of_years = now.year - timed.year
        
        no_of_month = now.month - timed.month
        if no_of_month < 0:
            no_of_month = 12 + no_of_month
        
        no_of_day = now.day - timed.day
        if no_of_day < 0:
            no_of_day = 30 + no_of_day
        
        no_of_hour = now.hour - timed.hour

        if no_of_hour < 0:
            no_of_hour = 24 + no_of_hour
        
        no_of_minute = now.minute - timed.minute
        if no_of_minute < 0:
            no_of_minute = 60 + no_of_minute
        
        if no_of_years == 1 and no_of_day >= 300:
            time_count = " About an year ago"
        elif no_of_years != 0 and no_of_years != 1:
            time_count = str(no_of_years) + " years ago"
        else:
            if no_of_month == 1:
                time_count = " 1 month ago"
            elif no_of_years != 0 :
                time_count =  str(no_of_month) + " months ago"
            else:
                if no_of_day == 1:
                    time_count = " 1 day ago"
                elif no_of_day != 0 :
                    time_count =  str(no_of_day) + " days ago"
                else:
                    if no_of_hour > 5:
                        time_count = " few hours ago"
                    elif no_of_hour == 1:
                        time_count = "1 hour ago"
                    elif no_of_hour != 0 :
                        time_count =  str(no_of_hour) + " hours ago"
                    else:
                        if no_of_minute > 20:
                            time_count = " few minutes ago"
                        elif no_of_minute == 1:
                            time_count = "1 minute ago"
                        elif no_of_minute != 0 :
                            time_count =  str(no_of_minute) + " minutes ago"
                        else:
                            time_count = " Just Now"
        
        row.append(time_count)

def get_img(quest_id):
    curr = sqlite3.connect("database.db")
    conn = curr.cursor()
    conn.execute("Select * from question_img where q_id = :id", dict(id = quest_id))
    img_name = conn.fetchall()
    curr.close()

    filename = ""
    if len(img_name) == 1:
        filename = img_name[0][1]

    return filename

def img_extend(rows):
    lst = []
    for row in rows:
        lst_row = list(row)
        filed = get_img(lst_row[0])
        lst_row.append(filed)
        lst.append(lst_row)
    
    return lst