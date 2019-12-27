class PythonRunner(object):
    @staticmethod
    def PythonGetAndRun(codeid):
        l = {}
        return PythonRunner.PythonGetAndRunDict(codeid,l)

    @staticmethod
    def PythonGetAndRunContext(codeid,context):
        #add "context" to the dictionary
        l = { "context": context }
        return PythonRunner.PythonGetAndRunDict(codeid,l)

    
    @staticmethod
    def PythonGetAndRunModule(codeid):
        l = {}
        return PythonRunner.PythonGetAndRunDict(codeid,l)

    @staticmethod
    def PythonGetAndRunDict(codeid,d):
        code = PythonRunner.PythonGetCode(codeid)
        return PythonRunner.PythonRunDict(codeid,code,d)        

    @staticmethod
    def PythonRunDict(codeid,code,d=None):
        import imp,sys
        mymod = imp.new_module('dynamic_' + str(codeid))
        setattr(mymod,'PythonRunDict',PythonRunner.PythonRunDict)
        setattr(mymod,'PythonGetAndRun',PythonRunner.PythonGetAndRun)
        setattr(mymod,'PythonGetAndRunContext',PythonRunner.PythonGetAndRunContext)
        setattr(mymod,'PythonGetAndRunModule',PythonRunner.PythonGetAndRunModule)
        setattr(mymod,'PythonGetCode',PythonRunner.PythonGetCode)
        setattr(mymod,'LogError',PythonRunner.LogError)
        if d: 
            for k,v in d.iteritems():
                setattr(mymod,k,v)
        exec(code,mymod.__dict__)
        return mymod

    @staticmethod
    def PythonGetCode(codeid):
        from dbhelper import dbhelper
        db = dbhelper()
        code = db.GetCodeRaw(codeid)
        return code

    @staticmethod
    def LogError(msg):
        print ('LogError: ' + msg)


