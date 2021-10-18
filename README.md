# MonolithStandlone
![](https://github.com/ktmdan/MonolithStandlone/workflows/Python%20application/badge.svg)

Monolith is a standalone web based python editor.  This project was created because we needed a way to run one off processes and have complete history of the code base.  This could easily be done with Git or the like but the advantage is that this can execute code off a central remote repository (this is still being worked on.)

All code is saved in a Sqllite3 database.

Code is designed to be compatible with IronPython so version 2.7 is what its currently using now.  

## How to run
```
pip install pypyodbc
ipy MonolithStandalone.py
```
Open browser to http://localhost:8000

To run an application designed in Monolith, where 5 is the codeid shown in the editor.
```
ipy -c "from PythonRunner import PythonRunner as pr;m=pr.PythonGetAndRun('5');print m.Test();"
```

## Custom Injected Commands
PythonGetAndRun(codeid) : get the code and return it as a script object
```
m = PythonGetAndRun(5)
r = m.Test()
LogError(r)
```

PythonGetAndRunDict(codeid,dict) : run the code adding dict to the global dictionary 
```
l = { 'version': 1 }
m = PythonGetAndRunDict(5,l)
r = m.Test()
LogError(r)
```

PythonGetCode(codeid) : Get just the code
```
code = PythonGetCode(5)
LogError(code)
```

LogError(msg) : Log an error to the console using print

![Alt](https://raw.githubusercontent.com/ktmdan/MonolithStandlone/master/docs/monolithscreenshot.png "Screenshot")
