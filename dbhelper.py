import pypyodbc as pyodbc
import sqlite3
from sqlite3 import Error
import json
import traceback
import sys 
import datetime

LDBFN = "db/sqllite.db"

code_create_sql = """
create table if not exists code (
    codeid integer primary key AUTOINCREMENT,
    codename text not null,
    folderid integer not null,
    codevalue text not null,
    codetype text nont null,
    FOREIGN KEY(folderid) REFERENCES folder(folderid)    
);
"""

folder_create_sql = """
create table if not exists folder (
    folderid integer primary key AUTOINCREMENT,
    foldername text not null,
    folderparent integer,
    FOREIGN KEY(folderparent) REFERENCES folder(folderid)
)
"""


codehistory_create_sql = """
create table if not exists codehistory (
    historyid integer primary key AUTOINCREMENT,
    codeid integer not null,
    codevalue text not null,
    changedate text not null,
    FOREIGN KEY(codeid) REFERENCES code(codeid)
)
"""

folder_init_sql = """
insert into folder (foldername)
select 'Root' 
WHERE NOT EXISTS(select 1 from folder where foldername = 'Root' and folderparent is null)
"""

code_init_sql = """
insert into code (codename,folderid,codevalue,codetype)
select 'Test',1,'This is a test','html'
WHERE NOT EXISTS(select 1 from code where codename = 'Test' and folderid = 1)
"""

class dbhelper(object):
    def __init__(self):
        self.lcreate()

    def Test(self):
        return '123'

    def GetTree(self):
        conn = pyodbc.connect('Driver={SQL Server};Server=10.12.2.71;Database=Code;UID=monostandalone;PWD=monostandalone123!')        
        cursor = conn.cursor()
        cursor.execute('set nocount on; select count(*) from codetree')
        row = cursor.fetchone()
        cursor.commit()
        del cursor
        return row[0] if row else None

    def lconn(self):
        return sqlite3.connect(LDBFN)

    def lcreate(self):
        conn = None
        try:
            conn = self.lconn()
            c = conn.cursor()
            c.execute(folder_create_sql)
            c.execute(code_create_sql)
            c.execute(codehistory_create_sql)
            c.execute(folder_init_sql)
            c.execute(code_init_sql)
            conn.commit()
        except Error as e:
            traceback.print_exc(file=sys.stdout)
            print (e)
        finally:
            if conn: conn.close()

    def GetTreePath(self,path):
        if path == None:
            #get the root object
            conn = self.lconn()
            c = conn.cursor()
            sf = "select folderid,foldername,folderparent from folder"# where folderparent is null order by foldername"
            c.execute(sf)
            folderrows = c.fetchall()
            s = "SELECT codeid,codename,folderid,codetype from code"# where folderid in (select folderid from folder where folderparent is null)"
            c.execute(s)
            coderows = c.fetchall()
            if conn: conn.close()
            ret = { 'Nodes': [] }
            f2 = list(filter(lambda x: not x[2],folderrows))
            for f in f2:
                ctn = {
                    'CodeTree': '/1/',
                    'CodeId': f[0],
                    'CodeName': f[1],
                    'CodeInsertBy': 'System',
                    'CodeInsertDate': '2014-12-04 10:36:00',
                    'CodeIsScope': True,
                    'CodeIsSystem': True,
                    'CodeLevel': 1,
                    'CodeType': None,
                    'Nodes': self.recursivenode(f[2],folderrows,coderows),
                    'CodeRevision': None
                    }
                ret['Nodes'].append(ctn)

            return json.dumps(ret)
        else:
            #get a submodule
            return ''

    def recursivenode(self,folderid,folders,codes):
        f2 = list(filter(lambda x: x[2] == folderid ,folders))
        c2 = list(filter(lambda x: x[2] == folderid,codes))
        if len(f2) == 0 and len(c2) == 0: return []
        ret = []
        for f in f2:
            ctn = {
            #'CodeTree': '/1/', #not used
            'CodeId': f[0],
            'CodeName': f[1],
            'CodeInsertBy': 'System', #Used only in history
            'CodeInsertDate': '2014-12-04 10:36:00', #used only in history
            'CodeIsScope': True,
            'CodeIsSystem': True,
            #'CodeLevel': 1, #notused
            'CodeType': None, 
            'Nodes': [],
            'CodeRevision': None
            }            
            ctn['Nodes'] = self.recursivenode(f[0],folders,codes)
            ret.append(ctn)
        for c in c2:
            ctn2 = {
            #'CodeTree': '/1/',
            'CodeId': c[0],
            'CodeName': c[1],
            'CodeInsertBy': 'System', #used only in history
            'CodeInsertDate': '2014-12-04 10:36:00', #used only in history
            'CodeIsScope': False,
            'CodeIsSystem': True,
            #'CodeLevel': 1,
            'CodeType': c[3], #/ace/mode codetype
            'Nodes': [],
            'CodeRevision': None #added to name if set
            }
            ret.append(ctn2)
        return ret

    def GetCode(self,codeid):
        if not codeid: return ''
        codeid = str(codeid)
        conn = self.lconn()
        c = conn.cursor()
        sf = "select codeid,codename,folderid,codetype,codevalue from code where codeid = ?"
        c.execute(sf,[codeid])
        row = c.fetchone()
        #returns, Text: <error message>, relogin=1 redirect to login, 
        ret = {
            'CodeId': row[0],
            'CodeName': row[1],
            'CodeInsertBy': 'System',
            'CodeInsertDate': '2019-01-01',
            'CodeIsSystem': True,
            'CodeType': row[3],
            'CodeValue': row[4],
            'CodeRevision': None
        }
        if conn: conn.close()
        return json.dumps(ret)

    def GetCodeRaw(self,codeid):        
        if not codeid: return ''
        codeid = str(codeid)
        conn = self.lconn()
        c = conn.cursor()
        sf = "select codevalue from code where codeid = ?"
        c.execute(sf,[codeid])
        row = c.fetchone()
        code = row[0]
        if conn: conn.close()
        return code

    def SaveCode(self,codeid,code):
        if not codeid or not code: return ''
        conn = self.lconn()
        c = conn.cursor()
        dt = datetime.datetime.now().isoformat()
        archive = "insert into codehistory (codeid,codevalue,changedate) select codeid,codevalue,'" + dt + "' from code where codeid = ?"
        c.execute(archive,[codeid])
        up = "update code set codevalue = ? where codeid = ?"
        c.execute(up,[code,codeid])
        conn.commit()
        if conn: conn.close()
        return 'SUCCESS'

    def RenameCode(self,codeid,codename):
        if not codeid or not codename: return ''
        conn = self.lconn()
        c = conn.cursor()
        s = "UPDATE code set codename = ? where codeid = ?"
        c.execute(s,[codename,codeid])
        conn.commit()
        if conn: conn.close()
        return 'SUCCESS'

    def NewScope(self,parentfolderid,scopename,issystem):
        #TODO handle issystem
        if not parentfolderid or not scopename or not issystem: return ''
        if parentfolderid == '-1': parentfolderid = None
        conn = self.lconn()
        c = conn.cursor()
        s = "INSERT INTO folder (foldername,folderparent) VALUES (?,?)"
        c.execute(s,[scopename,parentfolderid])
        conn.commit()
        if conn: conn.close()
        return 'SUCCESS'

    def NewCode(self,parentfolderid,codename,issystem,codetype,isversioned):
        if not parentfolderid or not codename or not issystem or not codetype or not isversioned: return ''
        if parentfolderid == '-1': parentfolderid = None
        conn = self.lconn()
        c = conn.cursor()
        s = "INSERT INTO code (codename,folderid,codevalue,codetype) VALUES (?,?,?,?) "
        c.execute(s,[codename,parentfolderid,'',codetype])
        lastrowid = c.lastrowid
        dt = datetime.datetime.now().isoformat()
        s = "INSERT INTO codehistory (codeid,codevalue,changedate) VALUES (?,?,?)"
        c.execute(s,[lastrowid,'',dt])
        conn.commit()
        if conn: conn.close()
        return 'SUCCESS'

    def MoveCode(self,codeID,newScopeID):
        if not codeID or not newScopeID: return ''
        conn = self.lconn()
        c = conn.cursor()
        s = "UPDATE code SET folderid = ? WHERE codeid = ?"
        c.execute(s,[newScopeID,codeID])
        conn.commit()
        if conn: conn.close()
        return 'SUCCESS'

    def CodeHistory(self,codeid):
        #determine how to handle current or insert a dummy record into history
        ret = []
        conn = self.lconn()
        c = conn.cursor()
        s2 = "SELECT codeid,codename,codetype FROM code WHERE codeid = ?"
        c.execute(s2,[codeid])
        tcode = c.fetchone()

        s = "SELECT historyid,codeid,codevalue,changedate FROM codehistory where codeid = ?"
        c.execute(s,[codeid])
        rows = c.fetchall()
        for r in rows:
            ce = {
                'CodeId': r[0],
                'CodeName': tcode[1],
                'CodeInsertBy': 'System',
                'CodeInsertDate': r[3],
                'CodeIsSystem': True,
                'CodeType': tcode[2],
                'CodeValue': r[2],
                'CodeRevision': None
                }
            ret.append(ce)
        if conn: conn.close()
        return json.dumps(ret)

