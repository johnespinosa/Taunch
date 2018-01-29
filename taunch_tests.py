import Taunch_Server
import os
import sqlite3
import tempfile
import unittest

class Taunch_ServerTestCase(unittest.TestCase):
    
    def sign_up_user(self, user):
        db = sqlite3.connect(Taunch_Server.app.config['DATABASE'])
        db.execute('insert into userInfo (user, password, friends, memories) values (?, ?, ?, ?)', [user, "password", "", ""])
        db.commit()
    
    def tearDown(self):
        os.close(self.db_fd)
        #os.close(self.db_fd)
        #os.unlink(Taunch_Server.app.config['DATABASE'])
        pass
    def setUp(self):
        self.delete_all_users()
        self.db_fd, Taunch_Server.app.config['DATABASE'] = tempfile.mkstemp()
        Taunch_Server.app.config['TESTING'] = True
        self.app = Taunch_Server.app.test_client()
        Taunch_Server.init_db()
        self.sign_up_user("mom")
        self.sign_up_user("darth")
        self.sign_up_user("yoda")  
        
    def test_login(self):
        rv = self.app.post('/login', data=dict(username_input='darth', password_input="password"), follow_redirects=True)
        assert "Edit Friends" in str(rv.data)
        rv = self.app.post('/login', data=dict(username_input='darth', password_input="wrong password"), follow_redirects=True)
        assert "Password or username incorrect. Please try again." in str(rv.data) #make self.asserts instead
        
    def test_submit_sign_up(self): #flask testing!!!!!! sql alchemy restful api
        db = sqlite3.connect(Taunch_Server.app.config['DATABASE'])
        rv = self.app.post('/submit_sign_up', data=dict(username_input='darth', password_input="password"), follow_redirects=True)
        assert "That username already exists. Please enter a new username and password." in str(rv.data)
        rv = self.app.post('/submit_sign_up', data=dict(username_input='erdkunde', password_input="password"), follow_redirects=True)
        assert "Login" in str(rv.data)
        friend_query = db.execute('select * from userInfo where user="erdkunde"')
        friends = [dict(username = row[0], password=row[1],friends=row[2],memories=row[3]) for row in friend_query.fetchall()]
        assert len(friends) == 1
        assert friends[0]["password"] == "password"
        
        
    def test_add_friend(self):
        db = sqlite3.connect(Taunch_Server.app.config['DATABASE']) #mock unit testing
        rv = self.app.post('/login', data=dict(username_input='darth', password_input="password"), follow_redirects=True)
        rv = self.app.post('/add_friend',data=dict(username_input="yoda"))
        rv = self.app.post('/add_friend',data=dict(username_input="mom"))
        assert not "That person does not exist please try again." in str(rv.data)
        rv = self.app.post('/add_friend',data=dict(username_input="larry"))
        assert "That person does not exist please try again." in str(rv.data)
        
        ''' Check page displays correctly. '''
        rv = self.app.get('/edit_friends')
        assert "mom" in str(rv.data)
        assert "yoda" in str(rv.data)
        assert not "larry" in str(rv.data)
        
        ''' Check database modified correctly '''
        userInfoQuery = db.execute('select * from userInfo WHERE user="darth"')
        userInfo = [dict(username = row[0], password=row[1],friends=row[2],memories=row[3]) for row in userInfoQuery.fetchall()]
        assert userInfo[0]["friends"] == "yoda,mom" #check darth's friends in memory
        userInfoQuery = db.execute('select * from userInfo WHERE user="yoda"')
        userInfo = [dict(username = row[0], password=row[1],friends=row[2],memories=row[3]) for row in userInfoQuery.fetchall()]
        assert userInfo[0]["friends"] == "darth" #check yoda's friends in memory
        
    def test_remove_friend(self):
        db = sqlite3.connect(Taunch_Server.app.config['DATABASE'])
        rv = self.app.post('/login', data=dict(username_input='darth', password_input="password"), follow_redirects=True)
        rv = self.app.post('/add_friend',data=dict(username_input="yoda"))
        rv = self.app.post('/add_friend',data=dict(username_input="mom"))
        rv = self.app.post('/remove_friend',data=dict(username_input="yoda"))
        rv = self.app.post('/remove_friend',data=dict(username_input="dieumgebung"))
        
        ''' Check pages displays correctly. '''
        assert "You cannot delete a person" in str(rv.data)
        rv = self.app.get('/edit_friends')
        assert "mom" in str(rv.data)
        assert not "yoda" in str(rv.data)
        assert not "dieumgebung" in str(rv.data)
        
        ''' Check database modified correctly '''
        userInfoQuery = db.execute('select * from userInfo WHERE user="darth"')
        userInfo = [dict(username = row[0], password=row[1],friends=row[2],memories=row[3]) for row in userInfoQuery.fetchall()]
        assert userInfo[0]["friends"] == "mom" #check darth's friends in memory
        userInfoQuery = db.execute('select * from userInfo WHERE user="yoda"')
        userInfo = [dict(username = row[0], password=row[1],friends=row[2],memories=row[3]) for row in userInfoQuery.fetchall()]
        assert userInfo[0]["friends"] == "" #check yoda's friends in memory
        
    def delete_all_users(self):
        db = sqlite3.connect(Taunch_Server.app.config['DATABASE'])
        userInfoQuery = db.execute('select * from userInfo')
        userInfo = [dict(username = row[0],password=row[1]) for row in userInfoQuery.fetchall()]
        for userDataPacket in userInfo:
            db.execute("DELETE FROM userInfo where user='" + userDataPacket["username"] + "'")
            db.commit()
        
    def test_setUp(self):        
        db = sqlite3.connect(Taunch_Server.app.config['DATABASE'])
        friend_query = db.execute('select * from userInfo')
        friends = [dict(username = row[0], password=row[1],friends=row[2],memories=row[3]) for row in friend_query.fetchall()]
        assert len(friends) == 3
        
if __name__ == '__main__':
    unittest.main()