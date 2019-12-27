# MonolithStandlone
![](https://github.com/ktmdan/MonolithStandlone/workflows/Python%20application/badge.svg)

Monolith is a standalone web based python editor.  

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

![Alt](https://raw.githubusercontent.com/ktmdan/MonolithStandlone/master/docs/monolithscreenshot.png "Screenshot")
