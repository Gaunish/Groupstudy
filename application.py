#importing all dependencies
import os
from flask import Flask, render_template, redirect, g, session, request, flash, url_for, send_from_directory
from flask_session import Session
from flask_mail import Mail, Message
from tempfile import mkdtemp
import sqlite3
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from helper import login_required, apology, apology2
from functions import *
from datetime import datetime
from random import randint  


#configuring app
app = Flask(__name__)

#Ensure template are auto reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

#configure session to filesystem
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["MAIL_SERVER"]='smtp.gmail.com'  
app.config["MAIL_PORT"] = 465      
app.config["MAIL_USERNAME"] = ''  
app.config['MAIL_PASSWORD'] = ''  
app.config['MAIL_USE_TLS'] = False  
app.config['MAIL_USE_SSL'] = True
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png', '.gif']
app.config['UPLOAD_PATH'] = 'static/Images'

Session(app)

class user_otp():
    otp = []
secret_user_info = user_otp()


#Ensure responses arent cached/verification
@app.after_request
def after_response(response):
    response.headers['Cache-Control'] = "no-cache, no-store, must-revalidate"
    response.headers['Expires'] = 0
    response.headers['Pragma'] = "no-cache"
    return response

#Redirects to the front page
@app.route('/')
def index():
    return render_template("front.html")
    

#Redirects to the main page
@app.route('/home', methods = ["GET"])
@login_required
def home():
    if request.method == "GET":     
        
        now = datetime.now()
        trending_time = trending_time_calc(now)
        popular_time = popular_time_calc(now)

        trending_row = question_rows_trending(trending_time)
        popular_row = question_rows(popular_time)

        trending_topic = topic_rows(trending_time)
        popular_topic = topic_rows(popular_time)
   
        return render_template("home.html", trending_row = trending_row, popular_row = popular_row, trending_topic = trending_topic, popular_topic = popular_topic)



@app.route('/login', methods = ["GET", "POST"])
def login():

    #Forgetting any previous stores user_id
    session.clear()

    #checking if user has entered via webpage
    if request.method == "POST":
        
        #checking if user has entered not null values
        if not request.form.get("username"):
            return apology("Must provide username", 403)

        if not request.form.get("password"):
            return apology("Must provide password", 403)
        
        #connect database
        curr = sqlite3.connect("database.db")
        conn = curr.cursor()
        conn.execute("Select * from users where username = :user", dict(user = request.form.get("username")))
        rows = conn.fetchall()
        curr.close()
        
        if len(rows) != 1 or not check_password_hash(rows[0][3], request.form.get("password")):
            return apology("Invalid username or password", 403)
 

        #storing user_id for session throughout
        session["user_id"] = rows[0][0]
        return redirect("/home") 
    
    else:
        return render_template("login.html")

@app.route('/register', methods = ["GET", "POST"])
def register():
    
    #Forgetting any previous stores user_id
    session.clear()

    #checking if user has entered via webpage
    if request.method == "POST":

        if not request.form.get("username"):
            return apology("must provide username", 403)    
    
        if not request.form.get("password"):
            return apology("must provide password", 403)
        
        if not request.form.get("confirm-password"):
            return apology("must confirm password", 403)
        
        if not request.form.get("email"):
            return apology("must provide email", 403)

        if not request.form.get("password") == request.form.get("confirm-password") : 
            return apology("passwords do not match", 403)

        # check if username is unique
        #connect database
        curr = sqlite3.connect("database.db")
        conn = curr.cursor()
        conn.execute("Select * from users where username = :name", dict(name = request.form.get("username")))
        row_name = conn.fetchall()
        curr.close()

        if len(row_name) != 0:
            return apology("Username is already taken")

        # check if email-id is unique
        #connect database
        curr = sqlite3.connect("database.db")
        conn = curr.cursor()
        conn.execute("Select * from users where email_id = :email", dict(email = request.form.get("email")))
        row_email = conn.fetchall()
        curr.close()

        if len(row_email) != 0:
            return apology("Email-id is already taken")
        

        try:
            hash = generate_password_hash(request.form.get("password"))
        except:
            return apology("Unexpected error")

        #connect database
        curr = sqlite3.connect("database.db")
        conn = curr.cursor()
        conn.execute("insert into users(username, email_id, Hash) values(:username, :email, :password)", dict(username = request.form.get("username"), password = hash, email = request.form.get("email")))
        curr.commit()
        curr.close()

        curr = sqlite3.connect("database.db")
        conn = curr.cursor()
        conn.execute("select * from users where username = :user", dict(user = request.form.get("username")))
        user_row = conn.fetchall()
        curr.close()

        
        email = request.form.get("email")
        mail = Mail(app)  
        otp = randint(000000,999999)
        msg = Message('OTP',sender = 'gaunishgarg@gmail.com', recipients = [email])  
        msg.body = str(otp)  
        mail.send(msg)

        secret_user_info.otp = []
        secret_user_info.otp.append(otp)
        secret_user_info.otp.append(user_row[0][0])

        return redirect(url_for('is_verified'))
    else:
        return render_template("register.html")

@app.route('/verify_now',  methods = ["GET", 'POST'])
def verify_now():
    if request.method == "POST":  
        user_otp = request.form.get('otp') 

        if secret_user_info.otp[0] == int(user_otp):  
            #connect database
            curr = sqlite3.connect("database.db")
            conn = curr.cursor()
            conn.execute("update users set is_verified = :bool_val, verified_time = :time where ref_id = :id", dict(bool_val = True, time = datetime.now(), id = session["user_id"]))
            curr.commit()
            curr.close()
        
        else:
            return apology("otp is not valid", 403)
        
        return redirect("/profile")

    else:
        #Connect Database
        curr = sqlite3.connect("database.db")
        conn = curr.cursor()
        conn.execute("select * from users where ref_id = :id", dict(id = session["user_id"]))
        user_row = conn.fetchall()
        curr.close()

        mail = Mail(app)  
        otp = randint(000000,999999)
        msg = Message('OTP',sender = 'gaunishgarg@gmail.com', recipients = [user_row[0][2]])  
        msg.body = str(otp)  
        mail.send(msg)

        secret_user_info.otp = []
        secret_user_info.otp.append(otp)
        secret_user_info.otp.append(user_row[0][0])

        return render_template("verification1.html")


@app.route('/verification', methods = ["GET", 'POST'])
def is_verified():
    if request.method == "POST":    
        user_otp = request.form.get('otp')  
        
        if secret_user_info.otp[0] == int(user_otp):  
            #connect database
            curr = sqlite3.connect("database.db")
            conn = curr.cursor()
            conn.execute("update users set is_verified = :bool_val, verified_time = :time where ref_id = :id", dict(bool_val = True, time = datetime.now(), id = secret_user_info.otp[1]))
            curr.commit()
            curr.close()

            secret_user_info.otp = []

        else:
            return apology2("otp is not valid", 403)

        session["user_id"] = secret_user_info.otp[1]
        secret_user_info.otp = []
        return redirect("/home")

    else:
        return render_template("verification.html")


@app.route('/forgot_password', methods = ["GET", 'POST'])
def enter_email():
    if request.method == "POST":

        email = request.form.get("email")

        #connect database
        curr = sqlite3.connect("database.db")
        conn = curr.cursor()
        conn.execute("select * from users where email_id = :email", dict(email=email))
        user_info = conn.fetchall()
        curr.close()

        if len(user_info) != 1:
            return apology("email-id is not valid")
        
        mail = Mail(app)  
        otp = randint(000000,999999)
        msg = Message('OTP',sender = 'gaunishgarg@gmail.com', recipients = [email])  
        msg.body = str(otp)  
        mail.send(msg)

        secret_user_info.otp = []
        secret_user_info.otp.append(otp)
        secret_user_info.otp.append(user_info[0][0])
        print(secret_user_info.otp)
        return redirect(url_for('enter_otp'))
    
    else:
        return render_template("forgot_email.html")

@app.route('/forgot_verify', methods = ["GET", 'POST'])
def enter_otp():
    if request.method == "POST":
        user_otp = request.form.get('otp')  
        
        if secret_user_info.otp[0] == int(user_otp):  
            
            #connect database
            curr = sqlite3.connect("database.db")
            conn = curr.cursor()
            conn.execute("select is_verified from users where ref_id = :id", dict(id = secret_user_info.otp[1]))
            is_verify = conn.fetchall()
            curr.close()

            if is_verify[0][0] == False:
                #connect database
                curr = sqlite3.connect("database.db")
                conn = curr.cursor()
                conn.execute("update users set is_verified = :bool_val, verified_time = :time where ref_id = :id", dict(bool_val = True, time = datetime.now(), id = secret_user_info.otp[1]))
                curr.commit()
                curr.close()
        
        else:
            return apology("otp is not valid", 403)

        session["user_id"] = secret_user_info.otp[1]
        return redirect("/change_password")

    else:
        print(secret_user_info.otp)
        return render_template("forgot_verify.html")

@app.route('/change_password', methods = ["GET", 'POST'])
def enter_new_pass():
    if request.method == "POST":
        
        if not request.form.get("password"):
            return apology("must provide password", 403)
        
        if not request.form.get("confirm-password"):
            return apology("must confirm password", 403)
        
        if not request.form.get("password") == request.form.get("confirm-password") : 
            return apology("passwords do not match", 403)

        try:
            hash = generate_password_hash(request.form.get("password"))
        except:
            return apology("Unexpected error")

        #connect database
        curr = sqlite3.connect("database.db")
        conn = curr.cursor()
        conn.execute("update users set Hash = :password where ref_id = :id", dict(password = hash, id = secret_user_info.otp[1]))
        curr.commit()
        curr.close()

        session["user_id"] = secret_user_info.otp[1]
        secret_user_info.otp = []
        return redirect("/home")
    else:
        return render_template("change_password.html")

@app.route('/create_comm', methods = ["GET", 'POST'])
@login_required
def create():
    if request.method == "POST":
        if not request.form.get("topic"):
            return apology2("Topic not entered")


        if not request.form.get("abstracted"):
            return apology2("Abstract not entered")

        #connect database
        curr = sqlite3.connect("database.db")
        conn = curr.cursor()
        conn.execute("Select * from topic where name = :name", dict(name = request.form.get("topic")))
        row = conn.fetchall()
        curr.close()

        if len(row) != 0:
            return apology2("Topic name is already present")
        
        #connect database
        curr = sqlite3.connect("database.db")
        conn = curr.cursor()
        conn.execute("insert into topic(name, description, user_id, buffer, Abstract) values(:name, :desc, :user, 0, :abstracted)", dict(name = request.form.get("topic"), desc = request.form.get("textarea1"), user = session['user_id'], abstracted = request.form.get("abstracted")))
        curr.commit()
        curr.close()

        return redirect("/home")

    else:
        return render_template("create_comm.html")

@app.route('/follow_comm')
@login_required
def following():

    #connect database
    curr = sqlite3.connect("database.db")
    conn = curr.cursor()
    conn.execute("Select * from topic where topic_id in (select topic_id from follow_topic where user_id = :id)", dict(id = session["user_id"]))
    rows = conn.fetchall()        
    curr.close()

    #connect database
    curr = sqlite3.connect("database.db")
    conn = curr.cursor()
    lst = []
    for row in rows:
        change_row = list(row)
        conn.execute("Select username from users where ref_id = :id", dict(id = row[4]))
        user_row = conn.fetchall()       

        change_row.append(user_row[0][0])
        is_follow = check_follow(row[0], session["user_id"])
        change_row.append(is_follow)

        conn.execute("Select count(*) from follow_topic where topic_id = :id", dict(id = row[0]))
        subscriber_count = conn.fetchall()
        change_row.append(subscriber_count[0][0])


        lst.append(change_row)
    curr.close()
        
    return render_template("following_comm.html", rows=lst)

@app.route('/created_comm')
@login_required
def comm_created():
    
    #connect database
    curr = sqlite3.connect("database.db")
    conn = curr.cursor()
    conn.execute("Select * from topic where user_id = :id", dict(id = session["user_id"]))
    rows = conn.fetchall()        
    curr.close()

    #connect database
    curr = sqlite3.connect("database.db")
    conn = curr.cursor()
    lst = []
    for row in rows:
        change_row = list(row)
        conn.execute("Select username from users where ref_id = :id", dict(id = row[4]))
        
        user_row = conn.fetchall()       
        change_row.append(user_row[0][0])
        is_follow = check_follow(row[0], session["user_id"])
        change_row.append(is_follow)
        
        conn.execute("Select count(*) from follow_topic where topic_id = :id", dict(id = row[0]))
        subscriber_count = conn.fetchall()
        change_row.append(subscriber_count[0][0])
        
        lst.append(change_row)

    curr.close()


        
    return render_template("created_comm.html", rows=lst)


@app.route('/create_ques', methods = ["GET", "POST"])
@login_required
def createtopic():
    if request.method == "POST":
        if not request.form.get("topic"):
            return apology2("title not entered")
        if not request.form.get("formgroup"):
            return apology2("no option selected")
        if not request.form.get("desc2"):
            return apology2("description not entered")
        
        
        #connect database
        curr = sqlite3.connect("database.db")
        conn = curr.cursor()
        conn.execute("Select * from topic where name = :name", dict(name = request.form.get("formgroup")))
        rows = conn.fetchall()
        curr.close()

        if len(rows) != 1:
            return apology2("Internal error")

        #connect database
        curr = sqlite3.connect("database.db")
        conn = curr.cursor()
        conn.execute("insert into question(name, description, create_time, topics_id, user_id) values(:name, :desc, :timed, :topiced, :user)", dict(name = request.form.get("topic"), desc = request.form.get("desc2"), timed = datetime.now(), topiced = rows[0][0], user = session["user_id"]))
        curr.commit()
        curr.close()

        #connect database
        curr = sqlite3.connect("database.db")
        conn = curr.cursor()
        conn.execute("select * from question where name = :name and description = :desc and topics_id = :topiced and user_id = :user", dict(name = request.form.get("topic"), desc = request.form.get("desc2"), topiced = rows[0][0], user = session["user_id"]))
        q_row = conn.fetchall()
        curr.close()

        uploaded_file = request.files['input_file']
        if uploaded_file.filename != '':
            file_ext = os.path.splitext(uploaded_file.filename)[1]
            
            if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                return apology2("invalid FIle type")
            
            filename = os.path.join(app.config['UPLOAD_PATH'], str(q_row[0][0]))
            uploaded_file.save(filename)
            file_string = "/" + str(filename)

            #connect database
            curr = sqlite3.connect("database.db")
            conn = curr.cursor()
            conn.execute("insert into question_img(q_id, img_name) values(:id, :name)", dict(id = q_row[0][0], name = str(file_string)))
            curr.commit()
            curr.close()

        return redirect("/home")
        
    else:
        #connect database
        curr = sqlite3.connect("database.db")
        conn = curr.cursor()
        conn.execute("Select name from topic")
        rows = conn.fetchall()
        curr.close()
        return render_template("create_ques.html", rows=rows)


@app.route('/follow_ques')
@login_required
def following_ques():
 #connect database
    curr = sqlite3.connect("database.db")
    conn = curr.cursor()
    conn.execute("Select * from question where q_id in (select question_id from follow_question where user_id = :id) order by create_time desc", dict(id = session["user_id"]))
    rows = conn.fetchall()        
    curr.close()
    
    rows = question_append(rows, session["user_id"])
    rows = question_append_user_comm(rows, session["user_id"])
    time_calc(rows, 3)
    lst = img_extend(rows)
        
    return render_template("following_ques.html", rows=lst)

@app.route('/created_ques')
@login_required
def active_ques():
 #connect database
    curr = sqlite3.connect("database.db")
    conn = curr.cursor()
    conn.execute("Select * from question where user_id = :id order by create_time desc", dict(id = session["user_id"]))
    rows = conn.fetchall()        
    curr.close()
    
    rows = question_append(rows, session["user_id"])
    rows = question_append_user_comm(rows, session["user_id"])
    time_calc(rows, 3)
    lst = img_extend(rows)
        
    return render_template("created_ques.html", rows=lst)


@app.route("/questions/<quest_id>/<title>/<time>/<topic_id>",methods = ["GET", "POST"])
@login_required
def dynamicq(quest_id, title, time, topic_id):
        if request.method == "GET":
            #connect database
            is_liked = ''

            row = question_q_id(quest_id)
            row_topic = topic_topic_id(topic_id)

            curr = sqlite3.connect("database.db")
            conn = curr.cursor()
            conn.execute("Select * from comment where q_id = :id", dict(id = quest_id))
            comment_topic = conn.fetchall()
            curr.close()

            is_liked = is_like(quest_id, session["user_id"])
        
            curr = sqlite3.connect("database.db")
            conn = curr.cursor()
            lst = []
            for comms in comment_topic:
                    comm_change = list(comms)
                    conn.execute("Select * from users where ref_id = :id", dict(id = comms[4]))
                    user_row = conn.fetchall()
                    comm_change.append(user_row[0][1])
                    lst.append(comm_change)
            curr.close()
            time_calc(lst, 2)


            like_no = like_dislike_no(quest_id, True)
            dislike_no = like_dislike_no(quest_id, False)

            comm_change = list(row[0])
            comm_change.append(comment_no(quest_id))
            row = tuple(comm_change)

            filename = get_img(quest_id)

            return render_template("question.html",row=row, topic=row_topic, comments=lst, is_follow=check_followed(quest_id, session["user_id"]), is_like = is_liked, like_no=like_no, dislike_no = dislike_no, filename = filename)  

        else:

            #connect database
            comment_text = request.form.get("comment")
            if comment_text == "":
                return
            curr = sqlite3.connect("database.db")
            conn = curr.cursor()
            conn.execute("insert into comment(comment_text, create_time, q_id, user_id) values(:comment, :time, :qid, :userid)", dict(comment=comment_text, time= datetime.now(), qid=quest_id, userid=session["user_id"]))
            curr.commit()
            curr.close()
            return redirect(url_for('dynamicq', quest_id=quest_id, title=title, time=time, topic_id=topic_id))
            

@app.route("/question/<quest_id>/<title>/<time>/<topic_id>",methods = ["GET", "POST"])
@login_required
def dynamicq2(quest_id, title, time, topic_id):
    is_follow=check_followed(quest_id, session["user_id"])

    if is_follow == True:
        curr = sqlite3.connect("database.db")
        conn = curr.cursor()
        conn.execute("delete from follow_question where question_id = :id and user_id = :uid", dict(id = quest_id, uid = session["user_id"]))
        curr.commit()
        curr.close()
            
    else:
        curr = sqlite3.connect("database.db")
        conn = curr.cursor()
        conn.execute("insert into follow_question(question_id, user_id, follow_time) values(:id, :uid, :timed)", dict(id = quest_id, uid = session["user_id"], timed = datetime.now()))
        curr.commit()
        curr.close()

    return redirect(url_for('dynamicq', quest_id=quest_id, title=title, time=time, topic_id=topic_id))


@app.route("/question_liked/<quest_id>/<title>/<time>/<topic_id>",methods = ["GET", "POST"])
@login_required
def is_liked(quest_id, title, time, topic_id):
    delete_if_present(quest_id)
    
    if request.form['like_dislike'] == 'like':
        insert_like_question(quest_id, session["user_id"], True, datetime.now())
    elif request.form['like_dislike'] == 'dislike':
        insert_like_question(quest_id, session["user_id"], False, datetime.now())

    return redirect(url_for('dynamicq', quest_id=quest_id, title=title, time=time, topic_id=topic_id))


@app.route("/home_liked/<quest_id>",methods = ["GET", "POST"])
@login_required
def is_liked2(quest_id):
    delete_if_present(quest_id)
    
    if request.form['like_dislike'] == 'like':
        insert_like_question(quest_id, session["user_id"], True, datetime.now()) 
    elif request.form['like_dislike'] == 'dislike':
        insert_like_question(quest_id, session["user_id"], False, datetime.now())

    return redirect(url_for('home'))  

@app.route("/topic_liked/<quest_id>/<topic_id>",methods = ["GET", "POST"])
@login_required
def is_liked_topic(quest_id, topic_id):
    delete_if_present(quest_id)
    
    if request.form['like_dislike'] == 'like':
        insert_like_question(quest_id, session["user_id"], True, datetime.now())
    elif request.form['like_dislike'] == 'dislike':
        insert_like_question(quest_id, session["user_id"], False, datetime.now())

    return redirect(url_for('dynamic_topic', topic_id=topic_id))     
  

@app.route("/Topic/<topic_id>", methods = ['GET', 'POST'])  
@login_required
def dynamic_topic(topic_id):
    if request.method == "GET":
        #connect database
        topic_row = topic_topic_id(topic_id)

        curr = sqlite3.connect("database.db")
        conn = curr.cursor()
        conn.execute("select * from question where topics_id = :id", dict(id = topic_id))
        rows = conn.fetchall()
        curr.close()

        rows = topic_rows_find(rows)      
        return render_template("Topic.html", topic_row=topic_row, question_row=rows, is_follow=check_follow(topic_id, session["user_id"]))
    
    else:
        
        follow_topic_like(topic_id, session["user_id"])
        
        return redirect(url_for('dynamic_topic', topic_id = topic_id))
            
@app.route("/Topic_like/<topic_id>", methods = ['GET', 'POST'])  
@login_required
def dynamic_topic_like(topic_id):

    follow_topic_like(topic_id, session["user_id"])
    return redirect(url_for('home')) 



@app.route("/search/q", methods = ['GET', 'POST'])
@login_required
def search_text():
    if request.method == "POST":

        query_text = request.form["search_query"]
        question_total = total_question_query(query_text)
        topic_total = total_topic_query_limit(query_text)

        return render_template("searched.html", query_text = query_text, question_total = question_total, topic_total = topic_total)

    

@app.route("/search/q/<query_text>", methods = ['GET', 'POST'])
@login_required
def search_texted_get(query_text):
    if request.method == "GET":

        question_total = total_question_query(query_text)
        topic_total = total_topic_query_limit(query_text)

        return render_template("searched.html", query_text = query_text, question_total = question_total, topic_total = topic_total)


@app.route("/search/community/<query_text>", methods = ['GET', 'POST'])
@login_required
def comm_text(query_text):
    if request.method == "GET":
        topic_total = total_topic_query(query_text)
        return render_template("search_comm.html", query_text = query_text, topic_total = topic_total)

@app.route("/search/posts/<query_text>", methods = ['GET', 'POST'])
@login_required
def post_text(query_text):
    if request.method == "GET":
        question_total = total_question_query(query_text)
        return render_template("search_post.html", query_text = query_text, question_total = question_total)



@app.route('/profile', methods = ['GET', 'POST'])
@login_required
def view_profile():
    if request.method == "GET":
        
        user_analytics = []

        #connect database
        curr = sqlite3.connect("database.db")
        conn = curr.cursor()
        conn.execute("select * from users where ref_id = :id", dict(id = session["user_id"]))
        row = conn.fetchall()
        curr.close()

        #connect database
        curr = sqlite3.connect("database.db")
        conn = curr.cursor()
        conn.execute("select count(*) from follow_topic where user_id = :id", dict(id = session["user_id"]))
        follow_topic_row = conn.fetchall()
        curr.close()

        user_analytics.append(follow_topic_row[0][0])

        #connect database
        curr = sqlite3.connect("database.db")
        conn = curr.cursor()
        conn.execute("select count(*) from topic where user_id = :id", dict(id = session["user_id"]))
        topic_row = conn.fetchall()
        curr.close()

        user_analytics.append(topic_row[0][0])

        #connect database
        curr = sqlite3.connect("database.db")
        conn = curr.cursor()
        conn.execute("select count(*) from follow_question where user_id = :id", dict(id = session["user_id"]))
        follow_question_row = conn.fetchall()
        curr.close()

        user_analytics.append(follow_question_row[0][0])

        #connect database
        curr = sqlite3.connect("database.db")
        conn = curr.cursor()
        conn.execute("select count(*) from like_question where user_id = :id and is_liked = :like", dict(id = session["user_id"], like = True))
        like_question_row = conn.fetchall()
        curr.close()

        user_analytics.append(like_question_row[0][0])

        #connect database
        curr = sqlite3.connect("database.db")
        conn = curr.cursor()
        conn.execute("select count(*) from like_question where user_id = :id and is_liked = :like", dict(id = session["user_id"], like = False))
        dislike_question_row = conn.fetchall()
        curr.close()

        user_analytics.append(dislike_question_row[0][0])
        birth_date = ""

        if row[0][4] == 1:
            timed = datetime(*time.strptime(row[0][5], "%Y-%m-%d %H:%M:%S.%f")[:6])
            birth_date = str(timed.day) + "/" + str(timed.month) + "/" + str(timed.year)
        
        return render_template("profile.html", user_info = row[0], birth_date=birth_date, user_analytics=user_analytics)

@app.route('/logout', methods = ['GET'])
@login_required
def logout():
    session.pop('user_id', None)
    return redirect("/")


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
