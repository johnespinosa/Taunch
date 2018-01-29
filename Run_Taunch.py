import Taunch_Server

def split_comma(string):
    return string.split(',')

def split_new_line(string):
    arr = string.split("\r\n")
    return arr

Taunch_Server.app.debug = True
#Taunch_Server.init_db()
Taunch_Server.app.jinja_env.filters['split_comma'] = split_comma
Taunch_Server.app.jinja_env.filters['split_new_line'] = split_new_line
Taunch_Server.app.run()