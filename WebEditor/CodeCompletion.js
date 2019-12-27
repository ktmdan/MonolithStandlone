/* CodeCompletion 1.0.2 */
var CodeCompletion = {
  isDev: false,

  // these are cached by codeId => []
  cachedCode: {},

  completions: [],

  assignedCodeData: [],
  fetchedCode: [],

  fetchQueue: [],
  fetchQueueRunning: false,
  interval: null,

  // initialize code completion
  // will start searching code open in editor and requesting includes
  init: function() {
    let langTools = ace.require('ace/ext/language_tools');
    var customCompleter = {
      // adds \. so that ace does not close code completion when . is entered
      identifierRegexps: [/[a-zA-Z_0-9\$\-\.\u00A2-\uFFFF]/],

      getCompletions: function(editor, session, pos, prefix, callback) {
        callback(null, CodeCompletion.completions);
      },

      getDocTooltip: function(item) {
        if (item && ! item.docHTML) {
            var desc = (item.desc) ? '<hr></hr>' + item.desc.replace(/,/g , "<br>") : '';
            item.docHTML = [
                "<b>", item.id, "</b>", "<hr></hr>",
                "<b>", item.name, "</b>", desc
            ].join("");
        }
      }
    }
    langTools.addCompleter(customCompleter);

    // start the interval that is checked for code
    CodeCompletion.interval = setInterval(CodeCompletion.findIncludesInterval, 5000);
  },

  // the interval that looks for includes
  findIncludesInterval: function() {
    if (CodeCompletion.isDev)
      console.log('looking for includes...');

    try {
      var codeInEditor = editor.getValue();
      CodeCompletion.pythonFindIncludes(codeInEditor);
    } catch (err) {
      console.log('Error getting code from editor: ' + err);
    }
  },

  // remove data from completions
  removeFromCompleter: function(assignedName) {
    var len = CodeCompletion.completions.length;
    for (var i = len - 1; i >= 0; i--)
      if (CodeCompletion.completions[i].value.indexOf(assignedName) == 0)
        CodeCompletion.completions.splice(i, 1);
  },

  // add fetched code to the ace editor completer
  addToCompleter: function(fetchedCodeData, fetchedCode) {
    // removee previous entries for assigned name
    // assignedname = m in m = PythonGetCode(x)
    CodeCompletion.removeFromCompleter(fetchedCodeData.assignedName);

    try
    {
      var lines = fetchedCode.split('\n');

      for (var i = 0; i < lines.length; i++) {
        // method definition
        if (lines[i].indexOf('def ') == -1)
          continue;

        var line = lines[i];

        // name of method
        var methodName = /def\s*(\w+)\s*\(/.exec(line);
        methodName = methodName[1]

        // arguments
        var args = /\(\s*([^)]+?)\s*\)/.exec(line);
        if (args && args[1])
          args = args[1].split(/\s*,\s*/);
        else
          args = [];

        var nameOfInclude = CodeCompletion.getNameOfInclude(fetchedCodeData.id);

        var completion = {
          name: methodName,
          value: fetchedCodeData.assignedName + '.' + methodName + '(' + args.join(',') + ')',
          meta: nameOfInclude,
          desc: args.join(','),
          id: nameOfInclude
        };

        // push this method definition to ace completions array
        CodeCompletion.completions.push(completion);
        CodeCompletion.cachedCode[fetchedCodeData.id] = fetchedCode;
      }
    } catch(err) {
      console.log('Error added fetched code to completer: ' + err);
    }
  },

  // parse python code and add it to the completions
  pythonFindIncludes: function(code) {
    try
    {
      var currLine = editor.getSelectionRange().start.row;

      var lines = code.split('\n');
      for (var i = 0; i < lines.length; i++) {
        let line = lines[i];

        // skip over the line we are editing to prevent
        // preventable code does not exist errors
        if (i == currLine)
          continue;

        // skip over a line that is comment, starts with #
        if (line.trim().indexOf('#') == 0)
          continue;

        // skip lines without
        if (line.indexOf('PythonGetAndRun') === -1 && line.indexOf('PythonGetCode') === -1)
          continue;

        // dont attempt to pull code id unless ( and ) are present
        if (line.indexOf('(') === -1 || line.indexOf(')')=== -1)
          continue;

        // the name assigned to the loaded script
        // ie assignedName = PythonGetAndRun(xyz)
        var assignedName = line.split('=');
        assignedName = assignedName[0].trim();

        // get the code id ie xyz
        var args = /\(\s*([^)]+?)\s*\)/.exec(line);
        if (args && args[1])
          args = args[1].split(/\s*,\s*/);
        var codeId = args[0];

        // this happens on nested includes
        // ie x = Template(PythonGetCode(y))
        if ( ! CodeCompletion.isDev) {
          if (isNaN(codeId)) {
            // console.log("Error codeId is NaN, skipping " + codeId + "");
            continue;
          }
        }

        // data about the code to be fetched
        let fetchedCodeData = {
          id: codeId,
          assignedName: assignedName
        };

        // am i indexed in fetched code?
        if (CodeCompletion.fetchedCode.indexOf(fetchedCodeData.id) != -1) {
          if (CodeCompletion.cachedCode[fetchedCodeData.id] == undefined)
            continue;

          let assigned = false;

          // check if is part of assigned code data
          for (var a in CodeCompletion.assignedCodeData) {
            // found assigned name ie the x in x = PythonGetCode(y)
            if (CodeCompletion.assignedCodeData[a].assignedName == fetchedCodeData.assignedName)
              // is this the same code id?
              if (CodeCompletion.assignedCodeData[a].id != fetchedCodeData.id) {
                // assign new code id,
                CodeCompletion.assignedCodeData[a].id = fetchedCodeData.id;
                // add to completions
                CodeCompletion.addToCompleter(fetchedCodeData, CodeCompletion.cachedCode[fetchedCodeData.id]);
                // found an assigned name
                assigned = true;
                break;
              }
          }

          // didn't find an assigned name by code was already fetched
          // is new assigned name with cached code
          if ( ! assigned)
            CodeCompletion.addToCompleter(fetchedCodeData, CodeCompletion.cachedCode[fetchedCodeData.id]);

          // continue before fetching code
          continue;
        }

        // adding if before adding it to the queue
        CodeCompletion.fetchedCode.push(fetchedCodeData.id);
        CodeCompletion.assignedCodeData.push(fetchedCodeData);

        CodeCompletion.fetchQueue.push(fetchedCodeData);
        CodeCompletion.startQueue();
      }
    } catch (err) {
      console.log(err);
    }
  },

  // try to start the queue
  // do not if it's already running or queue length is 0
  startQueue: function() {
    if (this.fetchQueueRunning || this.fetchQueue.length == 0)
      return;
    this.doFetchCode();
  },

  // if queue length is 0 exit, set queue running to false
  // fetch code from queue 
  doFetchCode: function() {
    if (this.fetchQueue.length == 0) {
      this.fetchQueueRunning = false;
      return;
    }

    // shift off queue
    // on success, add to completer, continue queue
    // on error, continue queue
    var fetchedCodeData = this.fetchQueue.shift();
    this.fetchCode(
      fetchedCodeData,
      function(fetchedCode) {
        if (fetchedCode != undefined)
          CodeCompletion.addToCompleter(fetchedCodeData, fetchedCode);
          CodeCompletion.doFetchCode();
      },
      function() {
        CodeCompletion.doFetchCode();
      });
  },

  // get the code
  // mark it as fetched
  // return code to callback
  fetchCode: function(fetchedCodeData, onSuccess, onError) {
    var params = (this.isDev)
      ? { url: './' + fetchedCodeData.id + '.py', dataType: 'text' }
      : { url: "WebApi.ashx?req=Code&id=" + fetchedCodeData.id + '&xxxallowexception=1', dataType: 'json' };

    $.ajax({
      url: params.url,
      dataType: params.dataType,
      type: "POST",
      timeout: 10000,
      success: function(data) {
        if (onSuccess != undefined)
          var fetchedCode = (CodeCompletion.isDev) ? data : data.CodeValue;
          onSuccess(fetchedCode);
      },
      error: function() {
        console.log('Error fetching code id: ' + fetchedCodeData.id);
        if (onError != undefined)
          onError();
      }
    })
  },

  // return the name of the included code
  getNameOfInclude: function(codeId) {
    return (this.isDev)
      ? codeId
      : CodeCompletion.findNameInNodesById(codeId, 1, w2ui['sidebar'].nodes);
  },

  // find name of included code in nodes
  findNameInNodesById: function(id, start, nodes) {
    try
    {
      for (var i = start; i < nodes.length; i++) {
        // if id is a number and is a script ( v prefix )
        if (Number.isInteger(nodes[i].id) 
        || (nodes[i].id != undefined && nodes[i].id.indexOf != undefined && nodes[i].id.indexOf("v") == 0))
        {
          // is it the id being search for
          var digits = nodes[i].text.match(/\d+/);
          if (digits.length && digits[0] == id) {
            return nodes[i].text.match(/\w+/)[0];
          }
        }
        // does it have children nodes?
        if (nodes[i].nodes && nodes[i].nodes.length) {
          // check those
          var name = CodeCompletion.findNameInNodesById(id, 0, nodes[i].nodes);
          // found it
          if (name)
            return name;
        }
      }
      // wasn't in these nodes
      return false;
    }
    catch(err) {
      console.log('Error getting name of include ' + err)
    }
  }
}