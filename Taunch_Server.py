from contextlib import closing
from genericpath import isfile
import os
import random
from shutil import copyfile
import sqlite3
import string
import hashlib
import datetime
from time import gmtime, strftime
import json

from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash, render_template, json, jsonify, request
import flask
from flask.helpers import make_response
import flask.views
from flask.wrappers import Request
from werkzeug.utils import secure_filename

DATABASE = 'test.db '  #test.db taunch.db
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'
server_started = True
UPLOAD_FOLDER = "/Users/johnespinosa/Documents/pythonWorkspace/ThesisVersions/static/images/"# "/home/jcespin2/public_html/scgi-bin/static/images"
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif']) #{1,2,3} :)
# set the secret key.  keep this really secret:

app = Flask(__name__)
app.config.from_object(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'w\x9a\xfek\x89uG\xd4\xe3\xc7\x10\x89\x0ei\xc3[\x8a\xacp\xb4B\x93\xcd\x14'

'''CONSTANTS'''
FAILURE = -1
SUCCESS = 0
CREATE_MEMORY_PAGE = "create_memory_page.html"

class View(flask.views.MethodView):
    
    def get(self):
        '''
        Construct the html of the webpage when Taunch is initially loaded.
        @return: http response
        '''
        if 'username' in session:
            username = session['username']
            if(user_exists(username, g.db)):
                return return_home(request, g.db)
            else:
                return render_template('login.html') 
        else:
            return render_template('login.html')
'''       
def add_cors_header(response):
    allow = 'HEAD, OPTIONS, GET, POST'

    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = allow
    response.headers['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response
app.after_request(add_cors_header)
'''    
def change_name(old_name, new_name, db):
   if user_exists(old_name, db) and session['username'] == "John Espinosa":
        user_query = db.execute('select * from userInfo')
        #change this so that users that are friends with ids change when a user changes their id
        #or decouple id with display name
        info_list = [dict(username = row[0], password=row[1],friends=row[2],memories=row[3]) for row in user_query.fetchall()]
        for user in info_list :
            if old_name in user['friends'] :
                old_friends = user['friends']
                db.execute("UPDATE userInfo SET friends='" + old_friends.replace(old_name, new_name) + "' WHERE user='" + user['username'] + "'")
        db.execute("UPDATE userInfo SET user='" + new_name+ "' WHERE user='" + old_name + "'")
        db.execute("UPDATE comments SET owner='" + new_name+ "' WHERE owner='" + old_name + "'")
        db.execute("UPDATE memories SET owner='" + new_name+ "' WHERE owner='" + old_name + "'")
        db.commit()

@app.route('/update_name', methods = ['POST'])
def update_name():
    old_name = request.form['old_name_input']
    new_name = request.form['new_name_input']
    change_name(old_name, new_name, g.db)
    return redirect('/')
    
    
def user_exists(user_id, db):
    user_query = db.execute('select * from userInfo WHERE user= ?', [user_id])
    info_list = [dict(username = row[0], password=row[1],friends=row[2],memories=row[3]) for row in user_query.fetchall()]
    return len(info_list) == 1

@app.route('/edit_friends')
def edit_friends():
    '''
    Load the page that allows the user to edit their friends.
    @return html associated with the edit friends page
    '''
    username = session['username'] # request.cookies.get('username')
    userInfo = get_info(username, g.db)
    friends = userInfo["friends"].split(',')
    return render_template('edit_friends.html',friends=friends)

def get_video_id(youtube_url):
    '''
    Extracts the video id from a youtube url.
    @param youtube_url: The url associated with a youtube video
    @return: the id of the youtube video 
    '''
    id_index = youtube_url.find("=") + 1;
    return youtube_url[id_index:id_index + 11]
    
def get_memory(memory_id, db):
    '''
    Gets all the memories associated with a memory id (there should only be one)
    @param memory_id: the id of the memory you want information about
    @return: an array of memory dictionaries
    '''
    memory_query = db.execute('select * from memories WHERE id=' + memory_id)
    memory_list = [dict(id = row[0], title=row[1],comment_ids=row[2], owner= row[3]) for row in memory_query.fetchall()]
    if(len(memory_list) != 1):
        return None
    return memory_list[0]
    

def get_comment(comment_id, db):
    '''
    Gets all the information associated with a comment id (there should only be one array entry)
    Note comments with reply_ids of NONE are replies and cannot be replied to.
    @param comment_id: the id of the comment you want information about
    @return: an array of comment dictionaries
    '''
    comment_query = db.execute('select * from comments WHERE id=' + comment_id)
    comments = [dict(id = row[0],content=row[1],type=row[2],reply_ids=row[3], owner=row[4], isVisible = row[5], date = row[6]) for row in comment_query.fetchall()]
    if(len(comments) == 1):
        if(comments[0]['reply_ids'] != "NONE" and comments[0]['reply_ids'] != ""):
            comments[0]['replies'] = get_from_list(comments[0]['reply_ids'], get_comment, db)
        else:
            comments[0]['replies'] = None
        return comments[0]
    else:
        return None
            

def get_from_list(my_list, get_function, db):
    '''
    Gets an array of value dictionaries from a list of ids using the get_function to query the database
    @param list: comma separated list of ids to query from
    @param get_function: the function used to query the database with the ids
    @return: an array of dictionaries 
    '''
    if(my_list == ""):
        return None
    ids = my_list.split(',')
    values = []
    for my_id in ids:
        values.append(get_function(my_id, db)) #use a map (list comprehension this puts ids -> return one line here
    return values

def file_name_exists(file_name, db):
    used_image_names = db.execute('select content from comments WHERE type="' + 'image"')
    used_names = [dict(file_name = row[0]) for row in used_image_names.fetchall()]
    for curr_name in used_names:
        if curr_name["file_name"] == file_name:
            return True
    return False

@app.route('/upload_img/<memory_id>', methods = ['POST'])
def upload_img(memory_id):
    '''
    Uploads a single image added by the user. A new file name is assigned to this image, it is saved to the the 
    appropriate folder with this new name, and the new name is returned to the frontend so that it can be grouped into
    an appropriate gallery.
    '''
    #file = request.files['file']
    uploaded_files = request.files.getlist("file[]")
    result = ""
    for file in uploaded_files:
        if file != None and file.filename != "" and allowed_file(file.filename):  #If the comment is an image
            filename = ""
            while(file_name_exists(filename, g.db) or filename == ""): #biggest hack ever...
                filename = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(30))
            path_and_name, fileExtension = os.path.splitext(file.filename)
            filename = secure_filename(filename + fileExtension)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            if result == "":
                result = filename
            else :
                result = result + "," + filename
            #return filename
        
        else:
            return return_home(request, g.db)
    return json.dumps({'results': result})



@app.route('/memory_page/<memory_id>')
def memory_page(memory_id):
    '''
    Loads a memory page from a memory html link.
    @param memory_id: the id associated with the memory page being loaded
    @return: the html associated with the memory page
    '''
    this_memory = get_memory(memory_id, g.db)
    this_user = session['username'] # request.cookies.get('username')
    comments = get_from_list(this_memory["comment_ids"], get_comment,g.db)
    return render_template('memory_page.html', memory=this_memory, comments=comments, can_add_friend = is_owner_of_memory(this_user, memory_id, g.db))

def add_to_comma_seperated_list(my_list, addition):
    '''
    Concatenates addition to the end of list with appropriate comma usage.
    @param list: A string that is a comma separated list
    @param addition: A string with will be concationated to the end of list
    @return: A string with addition combined with list.
    '''
    if(my_list == ""):
        return addition
    else:
        return my_list + "," + addition

def add_reply_to_list(parent_id, new_reply_id, db):
    '''
    This function adds a reply with id new_reply_id to the comment with id parent_id
    @param parent_id: the id of the comment which is being replied to
    @param new_reply_id: the id of the comment which is the reply
    '''
    parent_comment_info = get_comment(parent_id, db)
    comment_reply_list = parent_comment_info["reply_ids"]
    comment_reply_list = add_to_comma_seperated_list(comment_reply_list, new_reply_id)
    db.execute("UPDATE comments SET reply_ids='" + comment_reply_list + "' WHERE id=" + parent_id)
    db.commit()

def add_comment_to_list(memory_id, comment_id, db):
    '''
    This function addeds a comment to a memory.
    @param memory_id: the id of the memory you want to add a comment to
    @param comment_id: the id of the comment being added
    '''
    memory_info = get_memory(memory_id, db)
    #memory_comment_list is a comma separated list of usernames with no extraneous whitespace
    memory_comment_list = memory_info["comment_ids"]
    memory_comment_list = add_to_comma_seperated_list(memory_comment_list, comment_id)
    db.execute("UPDATE memories SET comment_ids='" + memory_comment_list + "' WHERE id=" + memory_id)
    db.commit()

def allowed_file(filename):
    '''
    This function checks to see if a file can be handled by the server.
    @param filename: the name of the file you are checking
    @return: true if the file is a valid file to handle, false otherwise
    '''
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/delete_comment/<memory_id>/<comment_id>', methods = ['POST','GET'])
def delete_comment(memory_id, comment_id):
    this_user = session['username']
    if (is_contributor_of_memory(this_user, memory_id, g.db)):
        g.db.execute("UPDATE comments SET isVisible = 'False' WHERE id = ?", [comment_id])
        g.db.commit()
        
        remove_comment_from_memory(comment_id, memory_id, g.db)
    return redirect("/memory_page/" + str(memory_id))
        

@app.route('/create_comment/comment/<memory_id>', methods = ['POST'])
def create_comment(memory_id):
    '''
    Handles a comment post action in a memory page.
    @param memory_id: the id of the memory a comment is being created in
    @return: the html associated with memory_id on successful comment posting, else the homepage
    '''
    comment_content = request.form['content'] #HAVE STRING CONSTANTS at top
    parent_id_list = request.form.getlist("reply_parent") # the comment being replied to, length 0 array if no such parent
    reply_children = "" # is "NONE" if the current comment is a reply, else ""
    
    if(len(parent_id_list) == 1): # if replying to someone
        reply_children = "NONE"
        
    this_user = session['username'] # request.cookies.get('username')
    
    #Add comment to the database
    g.db.execute('insert into comments (content, type, reply_ids, owner, isVisible, date) values (?, ?, ?, ?, ?, ?)', [comment_content, "comment", reply_children, this_user, "True", get_curr_time_ams()])
    g.db.commit()
    
    this_memory, comments = handleReply(parent_id_list, memory_id)
    
    return redirect("/memory_page/" + str(memory_id))

    #return render_template('memory_page.html', memory=this_memory, comments=comments, can_add_friend = is_owner_of_memory(this_user, memory_id, g.db))

def get_curr_time_ams():
    gmt = gmtime()
    currtime = (gmt.tm_year, gmt.tm_mon, gmt.tm_mday, gmt.tm_hour + 2, gmt.tm_min, 0)
    if(gmt.tm_min < 10):
        return "{1}-{2}-{0} {3}:0{4}".format(*currtime)
    else:
        return "{1}-{2}-{0} {3}:{4}".format(*currtime)



@app.route('/create_comment/video/<memory_id>', methods = ['POST'])
def create_video_comment(memory_id):
    '''
    Handles a comment post action in a memory page.
    @param memory_id: the id of the memory a comment is being created in
    @return: the html associated with memory_id on successful comment posting, else the homepage
    '''
    comment_content = request.form['content'] #HAVE STRING CONSTANTS at top
    parent_id_list = request.form.getlist("reply_parent") # the comment being replied to, length 0 array if no such parent
    reply_children = "" # is "NONE" if the current comment is a reply, else ""
    
    if(len(parent_id_list) == 1): # if replying to someone
        reply_children = "NONE"
        
    comment_content = get_video_id(comment_content)
    this_user = session['username'] # request.cookies.get('username')
    
    #get time
    
    
    #Add comment to the database
    g.db.execute('insert into comments (content, type, reply_ids, owner, isVisible, date) values (?, ?, ?, ?, ?, ?)', [comment_content, "video", reply_children, this_user, "True", get_curr_time_ams()])
    g.db.commit()
    
    this_memory, comments = handleReply(parent_id_list, memory_id)
    return redirect("/memory_page/" + str(memory_id))

@app.route('/create_comment/image/<memory_id>', methods = ['POST'])
def create_image_comment(memory_id):
    '''
    Handles a comment post action in a memory page.
    @param memory_id: the id of the memory a comment is being created in
    @return: the html associated with memory_id on successful comment posting, else the homepage
    '''
    comment_content = request.form['content'] #HAVE STRING CONSTANTS at top
    parent_id_list = request.form.getlist("reply_parent") # the comment being replied to, length 0 array if no such parent
    reply_children = "" # is "NONE" if the comment being created is a reply, else ""
    if comment_content == "":
         return redirect("/memory_page/" + str(memory_id))

    if(len(parent_id_list) == 1): # if replying to someone
        reply_children = "NONE"
        
    this_user = session['username'] # request.cookies.get('username')
    
    #Add comment to the database
    g.db.execute('insert into comments (content, type, reply_ids, owner, isVisible, date) values (?, ?, ?, ?, ?, ?)', [comment_content, "image", reply_children, this_user, "True", get_curr_time_ams()])
    g.db.commit()
    
    this_memory, comments = handleReply(parent_id_list, memory_id)
    return redirect("/memory_page/" + str(memory_id))

@app.route('/create_reply/text/<memory_id>', methods = ['POST'])
def create_text_reply(memory_id):
    '''
    @param memory_id: the id of the memory to which the reply is being added
    '''
    comment_content = request.form['content'] #HAVE STRING CONSTANTS at top
    parent_id_list = [request.form['parent_id']] # the comment being replied to, length 0 array if no such parent
    reply_children = "NONE" # is "NONE" if the current comment is a reply, else ""
        
    this_user = session['username'] # request.cookies.get('username')
    
    #Add comment to the database
    g.db.execute('insert into comments (content, type, reply_ids, owner, isVisible, date) values (?, ?, ?, ?, ?, ?)', [comment_content, "comment", reply_children, this_user, "True", get_curr_time_ams()])
    g.db.commit()
    
    this_memory, comments = handleReply(parent_id_list, memory_id)
    return  this_user + "," + comment_content

@app.route('/create_reply/video/<memory_id>', methods = ['POST'])
def create_video_reply(memory_id):
    comment_content = request.form['content'] #HAVE STRING CONSTANTS at top
    parent_id_list = [request.form['parent_id']] # the comment being replied to, length 0 array if no such parent
    reply_children = "NONE" # is "NONE" if the current comment is a reply, else ""
    comment_content = get_video_id(comment_content)
    this_user = session['username'] # request.cookies.get('username')
    
    #Add comment to the database
    g.db.execute('insert into comments (content, type, reply_ids, owner, isVisible, date) values (?, ?, ?, ?, ?, ?)', [comment_content, "video", reply_children, this_user, "True", get_curr_time_ams()])
    g.db.commit()
    
    this_memory, comments = handleReply(parent_id_list, memory_id)
    return  this_user + "," + comment_content

@app.route('/create_reply/image/<memory_id>', methods = ['POST'])
def image(memory_id):
    comment_content = request.form['content'] #HAVE STRING CONSTANTS at top
    parent_id_list = [request.form['parent_id']] # the comment being replied to, length 0 array if no such parent
    reply_children = "" # is "NONE" if the comment being created is a reply, else ""
    if comment_content == "":
         return ""

    if(len(parent_id_list) == 1): # if replying to someone
        reply_children = "NONE"
        
    this_user = session['username'] # request.cookies.get('username')
    
    #Add comment to the database
    g.db.execute('insert into comments (content, type, reply_ids, owner, isVisible, date) values (?, ?, ?, ?, ?, ?)', [comment_content, "image", reply_children, this_user, "True", get_curr_time_ams()])
    g.db.commit()
    
    this_memory, comments = handleReply(parent_id_list, memory_id)
    return  this_user + "," + comment_content

def handleReply(parent_id_list, memory_id):
    '''
    Figures out whether the comment being added is a reply or a stand along comment
    '''
    comment_query = g.db.execute('select * from comments')
    new_comment_id = len([dict(id=row[0]) for row in comment_query.fetchall()]) # Get the id of the current comment
    #new comment id = number of comments there currently are
    # above code could cause concurency issues what if length the same for two instances of this program?
    if (len(parent_id_list) == 0): #If no comment was selected to be replied to.
        # add the current comment to the current memory's comment list
        add_comment_to_list(memory_id, str(new_comment_id), g.db)
    else:
        add_reply_to_list(parent_id_list[0], str(new_comment_id), g.db) # add the current comment to the parent comment's list of replies
    this_memory = get_memory(memory_id, g.db)
    comments = get_from_list(this_memory["comment_ids"], get_comment, g.db)
    return this_memory, comments

def is_owner_of_memory(user_id, memory_id, db):
    memory_query = db.execute('select * from memories where owner = "' + user_id +'"')
    memory_list = [dict(id = row[0], title=row[1],comment_ids=row[2], owner= row[3]) for row in memory_query.fetchall()]
    for memory in memory_list:
        if str(memory['id']) == memory_id :
            return True
    return False

def is_contributor_of_memory(user_id, memory_id, db):
    user_query = db.execute('select * from userInfo where user = "' + user_id +'"')
    user_list = [dict(user = row[0], password=row[1],friends=row[2], memories= row[3]) for row in user_query.fetchall()]
    for user in user_list:
        return (str(memory_id)) in (str(user["memories"]))
    return False

@app.route('/add_friend_to_memory/<memory_id>', methods = ['POST'])
def add_friend_to_memory(memory_id):
    this_user = session['username'] # request.cookies.get('username')
    friend_added_to_memory = request.form['new_friend']
    add_friend_error = False
    if not is_friends_with(this_user, friend_added_to_memory, g.db):
        add_friend_error = True
    else:
        memory_add_status = add_memory_to_list(friend_added_to_memory, str(memory_id), g.db)
        add_friend_error = (memory_add_status == FAILURE)
    this_memory = get_memory(memory_id, g.db)
    comments = get_from_list(this_memory["comment_ids"], get_comment, g.db)
    return render_template('memory_page.html', memory=this_memory, comments=comments, add_friend_error=add_friend_error, can_add_friend = is_owner_of_memory(this_user, memory_id, g.db))

@app.route('/create_memory_page', methods = ['POST'])
def create_memory_page():
    '''
    Handle user created a new memory page from the homepage.
    @return: html associated with the home page
    '''
    memory_title = request.form['memory_title']
    this_user = session['username'] # request.cookies.get('username')
    g.db.execute('insert into memories (title, comment_ids, owner) values (?, ?, ?)', [memory_title, "", this_user])
    g.db.commit()
    memory_query = g.db.execute('select * from memories')
    new_memory_id = len([dict(id = row[0],title=row[1],comment_ids=row[2], owner=row[3]) for row in memory_query.fetchall()])
    add_memory_to_list(this_user, str(new_memory_id), g.db)
    add_memory_to_list("John Espinosa", str(new_memory_id), g.db)
    return return_home(request, g.db)
    
def add_memory_to_list(user, new_memory_id, db):
    '''
    Adds a memory to a user's memory list.
    @param user: the username of the user to add a memory id to
    @param new_memory_id: the id of the memory being added to the user's list 
    @return: SUCCESS if memory successfully added, FAILURE otherwise.
    '''
    user_info = get_info(user, db)
    if(user_info == None):
        return FAILURE
    
    #src_friend_list is a comma separated list of friend usernames with no extraneous whitespace
    user_memory_list = user_info["memories"]
    if(new_memory_id in user_memory_list):
        return FAILURE
    
    #if a friend has not been added yet we cannot have a "," in the beginning of src_friend_list
    user_memory_list = add_to_comma_seperated_list(user_memory_list, new_memory_id)
    
    db.execute("UPDATE userInfo SET memories='" + user_memory_list + "' WHERE user='" + user + "'")
    db.commit()
    return SUCCESS


@app.route('/home')
def home():
    return return_home(request, g.db)
  
@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('username', None)
    return redirect('/')

@app.route('/login', methods = ['POST'])
def login():
    '''
    Handle the user logging in.
    @return the html associated with a successful or unsuccessful login
    '''
    if request.method == 'POST':
        username = request.form['username_input']
        password = request.form['password_input']
        hashed_password = hashlib.sha512(password + username).hexdigest()
        user_info_query = g.db.execute('select * from userInfo WHERE user="' + username + '" AND password="' + hashed_password + '"')
        user_info = [dict(username = row[0],password=row[1],memory_list=row[3]) for row in user_info_query.fetchall()]
        if(len(user_info) == 1 and "username" in user_info[0]): #check if only one db entry has username and password
            username = user_info[0]["username"]
            memories = get_from_list(user_info[0]["memory_list"], get_memory, g.db)
            resp = make_response(render_template('home.html', username=username, memories=memories))
            #resp.set_cookie('username', username)
            session['username'] = username
            return redirect('/')
        return render_template('login.html',login_fail=True) #if login is invalid reload the login page
    else:
        return render_template('login.html',login_fail=False) #if login is invalid reload the login page

def return_home(request, db):
    '''
    Returns a user to the homepage with information from the request given
    @param request: The request from the frontend
    @return: The html associated with the homepage.
    '''
    this_user = session['username'] #request.cookies.get('username')
    user_info = get_info(this_user, db)
    memories = get_from_list(user_info["memories"], get_memory, db)
    return render_template('home.html', username=this_user, memories=memories) #RETURN with MEMORIES

@app.route('/add_friend', methods = ['POST'])
def add_friend():
    '''
    Handle the user adding a friend.
    @return the html associated with a successful or unsuccessful friend addition
    '''
    this_user = session['username'] #request.cookies.get('username') # the username of the user adding the friend
    friend_to_add = request.form["username_input"]
    add_friend_successful = (modify_friends(this_user, friend_to_add, add_friend_to_list, g.db) == SUCCESS)
    if(add_friend_successful):
        return return_home(request, g.db)
    else:
        #second argument gets the friends list of the user attempting to add their friend and displays the list on the page.
        return render_template('edit_friends.html', friends=get_info(this_user, g.db)["friends"].split(","), add_fail=True)
            
@app.route('/sign_up')
def sign_up():
    '''
    Load the html associated with a user clicked the sign up href.
    @return html associated with sign up.
    '''
    return render_template("sign_up.html")

@app.route('/submit_sign_up', methods = ['POST'])
def submit_sign_up():
    '''
    Handle user submitting information in an attempt to sign up for Taunch.
    @return the html associated with a successful or unsuccessful sign up.
    '''
    username = request.form['username_input']
    password = request.form['password_input'] # username and password attempting to be added as an account
    userInfoQuery = g.db.execute('select * from userInfo WHERE user="' + username + '"')
    userInfo = [dict(username = row[0],password=row[1]) for row in userInfoQuery.fetchall()]
    # if the new username does not match any other username and is not empty and does not contain a "," character
    if(len(userInfo) == 0 and not "," in username and username != "" and len(username) < 60):
        #last two elements of the array "" because not memories or friends yet.
        hashed_password = hashlib.sha512(password + username).hexdigest()
        g.db.execute('insert into userInfo (user, password, friends, memories) values (?, ?, ?, ?)', [username, hashed_password, "", ""])
        g.db.commit()
        return render_template('login.html') 
    else:
        return render_template('sign_up.html', sign_up_fail=True)
    
@app.route('/remove_friend', methods = ['POST']) #
def remove_friend():
    '''
    Handle the user deleting a friend.
    @return the html associated with the successful or unsuccessful deletion of a friend
    '''
    this_user = session['username'] #request.cookies.get('username') # the username of the user deleting their friend
    friend_to_delete = request.form["username_input"]
    defriend_successful = (modify_friends(this_user, friend_to_delete, remove_friend_from_list, g.db) == SUCCESS)
    if(defriend_successful):
        this_user = session['username'] #request.cookies.get('username')
        userInfo = get_info(this_user, g.db)
        memories = get_from_list(userInfo["memories"], get_memory, g.db)
        return render_template('home.html', username=this_user, memories=memories)
    else:
        #second argument get's the friends list of the user attempting to add their friend and displays it on the page.
        return render_template('edit_friends.html', friends=get_info(this_user, g.db)["friends"].split(","), delete_fail=True)
  
def modify_friends(friend1, friend2, friend_function, db):
    '''
    This function checks if it is able to create a friendship between friend1 and friend2 and then 
    creates that friendship if it is able.
    @var friend1: One friend in the new friendship
    @var friend2: The other friend in the new friendship
    @return: SUCCESS if friendship created, FAILURE otherwise
    '''
    if( not account_exists(friend1, db) or not account_exists(friend2, db) or friend1 == friend2 ): 
            return FAILURE
    if(friend_function(friend1, friend2, db) == FAILURE):
        return FAILURE
    if(friend_function(friend2, friend1, db) == FAILURE):
        return FAILURE
    return SUCCESS

def get_info(friend, db):
    '''
    Get the information associated with a user with respect to Taunch.
    @param friend: username of the person you wish to get info about
    @return the Taunch information associated with user in an array, or none if the user doesn't exist
    '''
    friend_query = db.execute('select * from userInfo WHERE user="' + friend + '"')
    info_list = [dict(username = row[0], password=row[1],friends=row[2],memories=row[3]) for row in friend_query.fetchall()]
    if(len(info_list) != 1):
        return None
    return info_list[0]

def account_exists(friend, db):
    '''
    Checks to see if the given username has an account associated with it or not
    @var friend: the username of the account you want to check exists.
    @return: a boolean, true if there is account associated with friend, false otherwise.
    '''
    #usernames are unique so there should be a 1 to 1, onto mapping of usernames to db entries.
    return get_info(friend, db) != None

def is_friends_with(src, friend, db):
    '''
    Checks to see if two users are friends (order shouldn't matter).
    @var src: the first friend in the friendship
    @var friend: the second friend in the friendship
    @return: True if friend is in src's friend list, false otherwise
    '''
    src_info = get_info(src, db)
    return friend in src_info["friends"] #check if friend is in src_info's friend list.

def add_friend_to_list(src, added_friend, db):
    '''
    Assumes that a friendship can be created between src and added_friend
    Adds added_friend to src's friend list. (Creates one direction of the friendship)
    @param src: the user who is having a user added to zir friend list
    @param friend: the friend being added to src's friend list
    '''
    if(is_friends_with(src, added_friend, db)):
            return FAILURE
    src_friend_info = get_info(src, db)
    #src_friend_list is a comma separated list of friend usernames with no extraneous whitespace
    src_friend_list = src_friend_info["friends"]
    #if a friend has not been added yet we cannot have a "," in the beginning of src_friend_list
    src_friend_list = add_to_comma_seperated_list(src_friend_list, added_friend)
    db.execute("UPDATE userInfo SET friends='" + src_friend_list + "' WHERE user='" + src + "'")
    db.commit()
    return SUCCESS

def get_memory_info(memory_id, db):
    memory_query = db.execute('select * from memories where id = ?', [memory_id])
    return[dict(id = row[0],title=row[1],comment_ids=row[2], owner=row[3]) for row in memory_query.fetchall()]

def remove_comment_from_memory(comment_id, memory_id, db): #decorator do setups and checks
    '''
    Assumes that a friendship can be destroyed between src and added_friend
    Removes added_friend from src's friend list.
    @var src: the user who is having a user added to zir friend list
    @var friend: the friend being added to src's friend list
    '''
    
    memory_info = get_memory_info(memory_id, db)
    #src_friend_list is a comma separated list of friend usernames with no extraneous whitespace
    comment_list = memory_info[0]["comment_ids"]
    comment_list_array = comment_list.split(",")
    comment_list_array.remove(str(comment_id))
    db.execute("UPDATE memories SET comment_ids='" + ",".join(comment_list_array) + "' WHERE id='" + memory_id + "'")
    db.commit()
    return SUCCESS

def remove_friend_from_list(src, removed_friend, db): #decorator do setups and checks
    '''
    Assumes that a friendship can be destroyed between src and added_friend
    Removes added_friend from src's friend list.
    @var src: the user who is having a user added to zir friend list
    @var friend: the friend being added to src's friend list
    '''
    if not is_friends_with(src, removed_friend, db):
        return FAILURE
    
    src_friend_info = get_info(src, db)
    #src_friend_list is a comma separated list of friend usernames with no extraneous whitespace
    src_friend_list = src_friend_info["friends"]
    src_friend_list_array = src_friend_list.split(",")
    src_friend_list_array.remove(removed_friend)
    db.execute("UPDATE userInfo SET friends='" + ",".join(src_friend_list_array) + "' WHERE user='" + src + "'")
    db.commit()
    return SUCCESS
  
@app.before_request
def before_request():
    '''
    Connects to the database before every query.
    '''
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    '''
    Closes the connection to the database after every query.
    '''
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()
        
def init_db():
    '''
    Initializes the database associated with schema.sql.
    '''
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
        
def connect_db():
    '''
    Connects the Taunch server to the sqlite db.
    '''
    return sqlite3.connect(app.config['DATABASE']) #test database

app.add_url_rule("/", view_func=View.as_view('main'), methods=['GET', 'POST'])

