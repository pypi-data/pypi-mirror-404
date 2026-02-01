"""
    Information of logrec below
    <===================================================================>
    Code lib : logrec
    Fill name : Log Recorder
    Author : Git32-Design
    Version : Rel 3.7.3
    create at : 2025/11/8
    lastest update : 2025/12/9
    Used lib : os(Operating system)|time(Time)
    IDE : Visual Studio Code
    Developing language : Python 3.13.0
    Licence : MIT License
    Description : A quick record log's lib, Can search log file, And record(Or write) logs to a file. It's easy, Please use "logging" library. I know, My lib is sucks, But I well publish it to github.
"""

import os # Get file path.
import time # Get time to record logs.
import json # Output json formation.
import csv # Output with CSV.

# I want to add some exceptions in this module.
# 1.Path or file not found.
class LRFileNotFoundError(Exception):
    def __init__(self, filename, path):
        self.filename = filename
        self.path = path
        message = f"File '{filename}' not found"
        if path:
            message += f" in path '{path}'"
        super().__init__(message)
    
    def __str__(self):
        return f"FileError, Error code[001]: {super().__str__()}"

# 2.Line out of range.
class LogOutError(Exception):
    def __init__(self, line):
        self.line = line
        message = f"Line {line} out of range, Error code[002]"
        super().__init__(message)
    
    def __str__(self):
        return f"LogOutError: {super().__str__()}"
    
# 3.Don't read file text(File is empty)
class FileEmptyError(Exception):
    def __init__(self, filename):
        self.filename = filename
        message = f"File '{filename}' is empty, Error code[003]"
        super().__init__(message)
    
    def __str__(self):
        return f"FileEmptyError: {super().__str__()}"

# 4.Not a supported type.
class InvalidTypeError(Exception):
    def __init__(self, obj):
        self.obj = obj
        
        obj_repr = repr(obj)

        if "' mode='" in obj_repr and "encoding='" in obj_repr :
            if hasattr(obj, 'name') :
                type_name = f"file object '{obj.name}'"
            else :
                type_name = "file object"
        elif isinstance(obj, str)  and len(obj) < 256 :
            type_name = f"string path '{obj}'"
        else:
            type_name = f"object of type '{type(obj).__name__}'"
        
        message = f"InvalidTypeError: {type_name} is not supported, Error code[004]"
        super().__init__(message)

# No more :]

# And, I want to add some function.
# 1.Test file type and path.
def check(filepath) -> None:
    if os.path.exists(filepath):
        if filepath.endswith((".txt", ".log")):
            return None
        else:
            raise InvalidTypeError(filepath.split(".")[-1])
    else:
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('')
        except Exception as e:
            raise LRFileNotFoundError(f"Can not create log file: {filepath}, Error msgs : {e}")
    
# 2.Test file is empty.
def empty(filepath) -> None:
    check(filepath)
    with open(filepath, 'r', encoding='utf-8') as file:
        if not file.read().strip():
            raise FileEmptyError(filepath)
        
# 3.Test line is out of range.
def out(filepath, line) -> None:
    check(filepath)
    with open(filepath, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        if line < 0 or line >= len(lines):
            raise LogOutError(line)

# Unit 1
# Record logs of 5 level.
# 1.Normal
def log(filepath, text) : 
    check(filepath)
    Get = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    with open(filepath, "a+", encoding="utf-8") as target:
        target.write(f"[{Get}] Normal log : {text}\n")

# 2.Tips
def tip(filepath, text) : 
    check(filepath)
    Get = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    with open(filepath, "a+", encoding="utf-8") as target:
        target.write(f"[{Get}] Tips log : {text}\n")

# 3.Warning
def warn(filepath, text) : 
    check(filepath)
    Get = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    with open(filepath, "a+", encoding="utf-8") as target:
        target.write(f"[{Get}] Warning log : {text}\n")

# 4.Error
def err(filepath, text) : 
    check(filepath)
    Get = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    with open(filepath, "a+", encoding="utf-8") as target:
        target.write(f"[{Get}] Error log : {text}\n")
        
# 5.Critical error
def crit(filepath, text) : 
    check(filepath)
    Get = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    with open(filepath, "a+", encoding="utf-8") as target:
        target.write(f"[{Get}] Critical error log : {text}\n")

# Unit 2
# Manage logs.
# 1.Read and output logs.
def read(filepath) : 
    check(filepath)
    empty(filepath)
    with open(filepath, "r", encoding="utf-8") as target:
        content = target.read()
        print(content)
        return content

# 2.Search any logs.
def search(filepath, line) :
    check(filepath)
    out(filepath, line)
    empty(filepath)
    with open(filepath, "r", encoding="utf-8") as target:
        lines = target.readlines()
        result = lines[line]
        print(result)
        return result

# 3.Delete any logs.
def rem(filepath, line) :
    check(filepath)
    out(filepath, line)
    empty(filepath)
    with open(filepath, "r", encoding="utf-8") as target:
        lines = target.readlines()
    lines.pop(line)
    with open(filepath, "w", encoding="utf-8") as target:
        target.writelines(lines)
    return True

# 4.Clear logs
def clear(filepath) :
    check(filepath)
    # allow clearing even if file currently empty
    with open(filepath, "w", encoding="utf-8") as target:
        target.write("")
    return True

# 5.Change log
def change(filepath, line, text) :
    check(filepath)
    out(filepath, line)
    empty(filepath)
    with open(filepath, "r", encoding="utf-8") as target:
        lines = target.readlines()
    # ensure the changed line ends with a newline
    if not text.endswith("\n"):
        text = text + "\n"
    lines[line] = text
    with open(filepath, "w", encoding="utf-8") as target:
        target.writelines(lines)
    return True

# 6.Parse log line
def parse_log_line(line: str) -> dict:
    """Parse a log line produced by this module into a dict with keys:
    timestamp, level, message.
    Returns {} if parsing fails.
    """
    if not line or not line.strip():
        return {}
    try:
        # Expect format: [TIMESTAMP] <Level words> log : message
        parts = line.split(']', 1)
        timestamp = parts[0].strip('[').strip()
        rest = parts[1].strip()
        # level is first word(s) until 'log' token
        if 'log :' in rest:
            level_part, msg = rest.split('log :', 1)
            level = level_part.strip()
            message = msg.strip()
        elif 'log:' in rest:
            level_part, msg = rest.split('log:', 1)
            level = level_part.strip()
            message = msg.strip()
        else:
            # fallback: split first token as level
            toks = rest.split(None, 1)
            level = toks[0] if toks else ''
            message = toks[1] if len(toks) > 1 else ''
        return {'timestamp': timestamp, 'level': level, 'message': message}
    except Exception:
        return {}

# 7.Export logs
def export_logs(filepath, out_path, fmt='json'):
    """Export logs to jsonl (default) or csv. Returns number of exported lines.
    fmt: 'json' or 'csv'
    """
    check(filepath)
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    exported = 0
    if fmt == 'json':
        with open(out_path, 'w', encoding='utf-8') as out:
            for ln in lines:
                ln_strip = ln.strip()
                # support input lines that are either plain text logs or json lines
                if not ln_strip:
                    continue
                parsed = {}
                if ln_strip.startswith('{'):
                    try:
                        parsed = json.loads(ln_strip)
                    except Exception:
                        parsed = {}
                else:
                    parsed = parse_log_line(ln)
                if parsed:
                    out.write(json.dumps(parsed, ensure_ascii=False) + '\n')
                    exported += 1
    elif fmt == 'csv':
        with open(out_path, 'w', encoding='utf-8', newline='') as out:
            writer = csv.DictWriter(out, fieldnames=['timestamp', 'level', 'message'])
            writer.writeheader()
            for ln in lines:
                ln_strip = ln.strip()
                if not ln_strip:
                    continue
                if ln_strip.startswith('{'):
                    try:
                        parsed = json.loads(ln_strip)
                    except Exception:
                        parsed = {}
                else:
                    parsed = parse_log_line(ln)
                if parsed:
                    writer.writerow(parsed)
                    exported += 1
    else:
        raise InvalidTypeError(fmt)
    return exported

# Unit 4
# Additional helper functions
# 1.Search by keyword
def search_by_keyword(filepath, keyword, case_sensitive=False):
    """Search logs by keyword and return matching lines.
    Args:
        filepath: Path to log file
        keyword: Keyword to search for
        case_sensitive: If True, perform case-sensitive search (default False)
    Returns:
        List of matching log lines
    """
    check(filepath)
    if not case_sensitive:
        keyword = keyword.lower()
    results = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            search_line = line if case_sensitive else line.lower()
            if keyword in search_line:
                results.append(line.rstrip('\n'))
    return results

# 2.Tail logs
def tail(filepath, n=10):
    """Return the last n lines from log file.
    Args:
        filepath: Path to log file
        n: Number of lines to return (default 10)
    Returns:
        List of last n lines
    """
    check(filepath)
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    return [line.rstrip('\n') for line in lines[-n:]] if lines else []

# Unit 5
# Log informations.
# 1.Get log's time.
def gettime(filepath, line=None) :
    """Return timestamps for all lines or a specific line.
    If line is None, returns list of timestamps for every log line.
    """
    check(filepath)
    with open(filepath, "r", encoding="utf-8") as target:
        lines = target.readlines()
    if line is None:
        times = [ln.split(" ")[0].strip("[]") for ln in lines if ln.strip()]
        for t in times:
            print(t)
        return times
    else:
        out(filepath, line)
        ln = lines[line]
        t = ln.split(" ")[0].strip("[]")
        print(t)
        return t

# 2.Get log's level.
def getlevel(filepath, line=None) :
    """Return log levels for all lines or a specific line.
    If line is None, returns list of levels for every log line.
    """
    check(filepath)
    with open(filepath, "r", encoding="utf-8") as target:
        lines = target.readlines()
    if line is None:
        levels = [ln.split(" ")[1] for ln in lines if ln.strip()]
        for lv in levels:
            print(lv)
        return levels
    else:
        out(filepath, line)
        ln = lines[line]
        lv = ln.split(" ")[1]
        print(lv)
        return lv

# Unit 6
# Appendces
# 1.Credits
def credits() :
    print("""
              Credits below
             <------------->
               Programming
              git32-Design
                Codebuddy
                
                Re-Design
               git32-Design
                
                Processor
              Python 3.13.0
                
             Function design
              git32-Design
             
             Programming tool
            Visual Studio Code
            <----------------->
       Thanks for VScode's extensions
                 CODEBUDDY
           Python Extension Pack
                  Pylance
      <------------------------------>
             Thanks for you using!
       I'll Work hard to make it better!
      <--------------------------------->
                   END...
                  <------> 
    """)

# 2.Version
def version() :
    print("""
          Version
         Dev alpha
           1.0.0
           
        Fixed 0 bugs
       Founded 0 bugs
         1 Updates
          lastest
         2025/11/8
         
           Calls
       1.git32mail@qq.com
      2.Netease minecraft
        Git32Design__
     &___________________&
          """)
        
# 3.License
def license() :
    print("""
                                  MIT License

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
    """)

# Original author's comments:
# Oh, It's end? Impossible!
# You can watch "version" function to know my calls, You can feedback to these.
# Thanks for your using!
# >:]      

# Compatibility aliases
# Provide fatal alias expected by some docs
fatal = crit

# Requires: see ../requirements.txt for external packages used in tests/tools