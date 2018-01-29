'''
Created on Nov 13, 2013

@author: John Espinosa
'''
from _pyio import StringIO
import Taunch_Server
import os
import sqlite3
import tempfile
import unittest
#pip install flask test mock pypy!!!

class Test(unittest.TestCase):

    def sign_up_user(self, user):
        db = sqlite3.connect(Taunch_Server.app.config['DATABASE'])
        memories = ""
        if(user == "mom"):
            memories="1,2"
        db.execute('insert into userInfo (user, password, friends, memories) values (?, ?, ?, ?)', [user, "password", "", memories])
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
        db = sqlite3.connect(Taunch_Server.app.config['DATABASE'])
        db.execute('insert into comments (content, type, reply_ids) values (?, ?, ?)', ["hello", "comment", "2"])
        db.commit()
        db.execute('insert into comments (content, type, reply_ids) values (?, ?, ?)', ["goodbye", "comment", ""])
        db.commit()
        db.execute('insert into comments (content, type, reply_ids) values (?, ?, ?)', ["mom commenting", "comment", ""])
        db.commit()
        db.execute('insert into memories (title, comment_ids) values (?, ?)', ["mom memories", "1,2"])
        db.commit()
        db.execute('insert into memories (title, comment_ids) values (?, ?)', ["lonely memory", ""])
        db.commit()

    def delete_all_users(self):
        db = sqlite3.connect(Taunch_Server.app.config['DATABASE'])
        db.execute("drop table if exists userInfo;")
        db.commit()
        db.execute("create table userInfo (user text not null,password text not null,friends text not null,memories text not null);")
        db.commit()
        db.execute("drop table if exists memories;")
        db.commit()
        db.execute("create table memories (id integer primary key autoincrement,title text not null,comment_ids text);")
        db.commit()
        db.execute("drop table if exists comments;")
        db.commit()
        db.execute("create table comments (id integer primary key autoincrement,content text,type text,reply_ids text);")
        db.commit()
        
    def test_add_friend_to_memory(self):
        db = sqlite3.connect(Taunch_Server.app.config['DATABASE'])
        Taunch_Server.modify_friends("mom", "darth", Taunch_Server.add_friend_to_list, db)
        Taunch_Server.modify_friends("darth", "mom", Taunch_Server.add_friend_to_list, db)
        rv = self.app.post('/login', data=dict(username_input='mom', password_input="password"), follow_redirects=True)
        rv = self.app.get("/memory_page/1", follow_redirects=True)
        rv = self.app.post("/add_friend_to_memory/1", data=dict(new_friend='darth'), follow_redirects=True)
        rv = self.app.post('/login', data=dict(username_input='darth', password_input="password"), follow_redirects=True)
        self.assertTrue("mom memories" in str(rv.data), "Darth did not get the memory!")
        
    def test_add_memory(self):
        rv = self.app.post('/login', data=dict(username_input='darth', password_input="password"), follow_redirects=True)
        rv = self.app.post("/create_memory_page", data=dict(memory_title='new memory added yay'), follow_redirects=True)
        self.assertTrue("new memory added yay" in str(rv.data), "incorrect memory addition")
        
        ''' Check database modified correctly '''
        db = sqlite3.connect(Taunch_Server.app.config['DATABASE']) #mock unit testing
        memoryInfoQuery = db.execute('select * from memories WHERE id=3')
        memoryInfo = [dict(title = row[1], comment_ids=row[2]) for row in memoryInfoQuery.fetchall()]
        self.assertEqual(memoryInfo[0]["title"], "new memory added yay", "incorrect db addition")
        self.assertEqual(memoryInfo[0]["comment_ids"], "", "incorrect db addition")
        
    def test_visit_memory(self):
        rv = self.app.post('/login', data=dict(username_input='darth', password_input="password"), follow_redirects=True)
        rv = self.app.get("/memory_page/1", follow_redirects=True)
        self.assertTrue("mom memories" in str(rv.data), "incorrect memory addition")
        
    def test_setUp(self):        
        db = sqlite3.connect(Taunch_Server.app.config['DATABASE'])
        friend_query = db.execute('select * from userInfo')
        friends = [dict(username = row[0], password=row[1],friends=row[2],memories=row[3]) for row in friend_query.fetchall()]
        self.assertEqual(len(friends), 3, "Wrong number of people added.")
        
    def test_add_comment(self):
        db = sqlite3.connect(Taunch_Server.app.config['DATABASE'])
        rv = self.app.post('/login', data=dict(username_input='mom', password_input="password"), follow_redirects=True)
        rv = self.app.get("/memory_page/1", follow_redirects=True)
        rv = self.app.post('/create_comment/1', data={'file':(None, ""),'content':'my comment added', 'type':"comment",}, follow_redirects=True)
        self.assertTrue("my comment added" in str(rv.data), "incorrect memory addition")
        
        ''' Check database modified correctly '''
        memoryInfoQuery = db.execute('select * from comments WHERE id=4')
        memoryInfo = [dict(content = row[1], type=row[2]) for row in memoryInfoQuery.fetchall()]
        self.assertEqual(memoryInfo[0]["content"], "my comment added", "Wrong Content")
        self.assertEqual(memoryInfo[0]["type"], "comment", "Wrong Type")
        
    def test_get_memories_from_list(self):
        db = sqlite3.connect(Taunch_Server.app.config['DATABASE'])
        result = Taunch_Server.get_from_list("1,2", Taunch_Server.get_memory, db)
        print result
        self.assertTrue("'title': u'mom memories'" in str(result))
        self.assertTrue("'title': u'lonely memory'" in str(result))
        self.assertTrue("'comment_ids': u'1,2'" in str(result))
        self.assertTrue("'comment_ids': u''" in str(result))
        self.assertTrue("'id': 1" in str(result))
        self.assertTrue("'id': 2" in str(result))
        self.assertEqual(len(result), 2)
        
    def test_get_video_id(self):
        video_id = Taunch_Server.get_video_id("http://www.youtube.com/watch?v=vzT8EqhuYxA")
        self.assertEqual(video_id, "vzT8EqhuYxA", "Incorrect video id.")
        
    def test_get_memory(self):
        db = sqlite3.connect(Taunch_Server.app.config['DATABASE'])
        memory = Taunch_Server.get_memory("2", db)
        self.assertEqual(memory["comment_ids"], "", "Incorrect comment_ids")
        self.assertEqual(memory["id"], 2, "Incorrect id.")
        self.assertEqual(memory["title"], "lonely memory", "Incorrect title.")
        
    def test_get_comment(self):
        db = sqlite3.connect(Taunch_Server.app.config['DATABASE'])
        comment = Taunch_Server.get_comment("1", db)
        self.assertEqual(comment["content"], "hello", "Incorrect comment message")
        self.assertEqual(comment["type"], "comment", "Incorrect comment message")
        self.assertEqual(comment["reply_ids"], "2", "Incorrect comment message")
        
    def test_get_comments_from_list(self):
        db = sqlite3.connect(Taunch_Server.app.config['DATABASE'])
        comment_list = Taunch_Server.get_from_list("1,2", Taunch_Server.get_comment,db)
        self.assertEqual(len(comment_list) , 2, "Incorrect Number of comments")
        comment1 = Taunch_Server.get_comment("1", db)
        comment2 = Taunch_Server.get_comment("2", db)
        self.assertEqual(comment1, comment_list[0], "Comment 1 not in list.")
        self.assertEqual(comment2, comment_list[1], "Comment 2 not in list.")
        
    def test_add_reply_to_list_with_replys(self):
        db = sqlite3.connect(Taunch_Server.app.config['DATABASE'])
        Taunch_Server.add_reply_to_list("1", "3", db)
        self.assertEqual(Taunch_Server.get_comment("1", db)["reply_ids"], "2,3", "Added reply")
        
    def test_add_reply_to_list_no_replys(self):
        db = sqlite3.connect(Taunch_Server.app.config['DATABASE'])
        Taunch_Server.add_reply_to_list("2", "3", db)
        self.assertEqual(Taunch_Server.get_comment("2", db)["reply_ids"], "3", "Added reply")
        
    def test_allowed_file(self):
        self.assertTrue(Taunch_Server.allowed_file("me.jpg"))
        self.assertTrue(Taunch_Server.allowed_file("me.png"))
        self.assertFalse(Taunch_Server.allowed_file("me.py"))
        
    def test_add_memory_to_list(self):
        db = sqlite3.connect(Taunch_Server.app.config['DATABASE'])
        Taunch_Server.add_memory_to_list("mom", "3", db)
        self.assertEqual(Taunch_Server.get_info("mom", db)["memories"], "1,2,3", "Added memory not correct")
        
    def test_add_friends(self):
        db = sqlite3.connect(Taunch_Server.app.config['DATABASE'])
        self.assertEqual(Taunch_Server.modify_friends("mom", "darth", Taunch_Server.add_friend_to_list, db), Taunch_Server.SUCCESS, "Add not successful")
        self.assertEqual(Taunch_Server.get_info("mom", db)["friends"], "darth", "new friend new added.")
        self.assertEqual(Taunch_Server.get_info("darth", db)["friends"], "mom", "new friend new added.")
        self.assertEqual(Taunch_Server.modify_friends("mom", "yoda", Taunch_Server.add_friend_to_list, db), Taunch_Server.SUCCESS, "Add not successful")
        self.assertEqual(Taunch_Server.get_info("mom", db)["friends"], "darth,yoda", "new friend new added.")
        self.assertEqual(Taunch_Server.get_info("yoda", db)["friends"], "mom", "new friend new added.")
        
    def test_unsuccessful_add_friends(self):
        db = sqlite3.connect(Taunch_Server.app.config['DATABASE'])
        self.assertEqual(Taunch_Server.modify_friends("mom", "yoda", Taunch_Server.add_friend_to_list, db), Taunch_Server.SUCCESS, "Add not successful")
        self.assertEqual(Taunch_Server.modify_friends("mom", "NonexistantUser", Taunch_Server.add_friend_to_list, db), Taunch_Server.FAILURE, "Add not successful")
        self.assertEqual(Taunch_Server.modify_friends("mom", "yoda", Taunch_Server.add_friend_to_list, db), Taunch_Server.FAILURE, "Add successful when shouldn't be")
        self.assertEqual(Taunch_Server.modify_friends("nonExistant User", "yoda", Taunch_Server.add_friend_to_list, db), Taunch_Server.FAILURE, "Add successful when shouldn't be")
        
    def test_defriend_friends(self):
        db = sqlite3.connect(Taunch_Server.app.config['DATABASE'])
        self.assertEqual(Taunch_Server.modify_friends("mom", "darth", Taunch_Server.add_friend_to_list, db), Taunch_Server.SUCCESS, "Add not successful")
        self.assertEqual(Taunch_Server.modify_friends("mom", "darth", Taunch_Server.remove_friend_from_list, db), Taunch_Server.SUCCESS, "Add not successful")
        self.assertEqual(Taunch_Server.get_info("mom", db)["friends"], "", "new friend new added.")
        self.assertEqual(Taunch_Server.get_info("darth", db)["friends"], "", "new friend new added.")
        
    def test_unsuccessful_defriend_friends(self):
        db = sqlite3.connect(Taunch_Server.app.config['DATABASE'])
        self.assertEqual(Taunch_Server.modify_friends("mom", "yoda", Taunch_Server.remove_friend_from_list, db), Taunch_Server.FAILURE, "Add successful when shouldn't be")
        self.assertEqual(Taunch_Server.modify_friends("mom", "NonexistantUser", Taunch_Server.remove_friend_from_list, db), Taunch_Server.FAILURE, "Add successful when shouldn't be")
        self.assertEqual(Taunch_Server.modify_friends("nonExistant User", "yoda", Taunch_Server.remove_friend_from_list, db), Taunch_Server.FAILURE, "Add successful when shouldn't be")

    def test_get_info(self):
        db = sqlite3.connect(Taunch_Server.app.config['DATABASE'])
        mom_info = Taunch_Server.get_info("mom", db)
        self.assertEqual(mom_info["username"], "mom", "Incorrect username.")
        self.assertEqual(mom_info["password"], "password", "Incorrect username.")
        self.assertEqual(mom_info["friends"], "", "Incorrect username.")
        self.assertEqual(mom_info["memories"], "1,2", "Incorrect username.")
        
    def test_account_exists(self):
        db = sqlite3.connect(Taunch_Server.app.config['DATABASE'])
        self.assertTrue(Taunch_Server.account_exists("mom", db), "Account actually exists.")
        self.assertFalse(Taunch_Server.account_exists("non-existant", db), "Account doesn't exist.")
    
    def test_is_friends_with(self):
        db = sqlite3.connect(Taunch_Server.app.config['DATABASE'])
        self.assertEqual(Taunch_Server.modify_friends("mom", "darth", Taunch_Server.add_friend_to_list, db), Taunch_Server.SUCCESS, "Add not successful")
        self.assertTrue(Taunch_Server.is_friends_with("mom", "darth", db), "They are friends")
        self.assertTrue(Taunch_Server.is_friends_with("darth", "mom", db), "They are friends")
        self.assertFalse(Taunch_Server.is_friends_with("mom", "yoda", db), "They aren't friends")
        
    def test_add_friend_to_list(self):
        db = sqlite3.connect(Taunch_Server.app.config['DATABASE'])
        self.assertEqual(Taunch_Server.add_friend_to_list("mom", "darth", db), Taunch_Server.SUCCESS, "Addition not successful.")
        self.assertTrue(Taunch_Server.is_friends_with("mom", "darth", db), "They are friends")
        self.assertFalse(Taunch_Server.is_friends_with("darth", "mom", db), "They aren't friends")
        self.assertEqual(Taunch_Server.add_friend_to_list("mom", "darth", db), Taunch_Server.FAILURE, "Addition successful when it shouldn't be.")
        
    def test_remove_friend_from_list(self):
        db = sqlite3.connect(Taunch_Server.app.config['DATABASE'])
        self.assertEqual(Taunch_Server.remove_friend_from_list("darth", "mom", db), Taunch_Server.FAILURE, "Removal successful when it shouldn't be.")
        Taunch_Server.modify_friends("mom", "darth", Taunch_Server.add_friend_to_list, db)
        self.assertEqual(Taunch_Server.remove_friend_from_list("darth", "mom", db), Taunch_Server.SUCCESS, "Removal not successful.")
        self.assertTrue(Taunch_Server.is_friends_with("mom", "darth", db), "They are friends")
        self.assertFalse(Taunch_Server.is_friends_with("darth", "mom", db), "They aren't friends")
        
    def test_dup_img(self):
        db = sqlite3.connect(Taunch_Server.app.config['DATABASE'])
        self.assertFalse(Taunch_Server.file_name_exists("mom.jpg", db), "mom.jpg exists when it shouldn't.")
        db.execute('insert into comments (content, type, reply_ids) values (?, ?, ?)', ["mom.jpg", "image", ""])
        db.commit()
        self.assertTrue(Taunch_Server.file_name_exists("mom.jpg", db), "mom.jpg doesn't exist when it should.")
    
        
    
''' MOCK UNIT TESTING '''

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()