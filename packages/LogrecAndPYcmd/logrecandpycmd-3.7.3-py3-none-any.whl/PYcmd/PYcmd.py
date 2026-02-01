"""
    Information of PYcmd below
    <===================================================================>
    Program : PYcmd
    Fill name : Python Command prompt tool
    Author : Git32-Design
    Version : Dev Alpha 1.0.0
    create at : 2025/11/8
    lastest update : 2025/11/8
    Used lib : os(Managing files)|math(Calculating)|random(Generate random number)|time(Get time string)|pathlib(Get current path)|logrec(Custom lib, Managing logs)
    Developing at : Visual Studio Code
    Developing language : Python 3.13.0
    Licence : MIT License
    Description : This program is a command prompt tool for managing files.
"""

# import "os" lib to manage file  
import os  
# import "math" lib to calculating
import math
# import "random" lib to generate random numbers
import random 
# import "time" lib to get current time and date arg
import time
# import "pathlib" lib to get current path
import pathlib
# import "ast" and "operator" lib to calculate math expression
import ast
import operator as _operator
# import "sys" lib to get parent folder path for import custom module -- logrec
import sys
# Get parent folder path
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.absolute()))
# import "logrec" to record logs
import logrec

# Define record path string
path = f"{pathlib.Path(__file__).parent.absolute()}/PYcmd log record.log"

# define functions  
def read(filepath):  
    try:   
        if not os.path.exists(filepath):  
            print(f"File '{filepath}' not found.")  
            return   
        with open(filepath, 'r') as file:  
            content = file.read()
        print(content) 
        logrec.log(path,f"args : read file {filepath}, Result: Running function successfuly.")
    except Exception as e:  
        print(f"Error reading file: {e}")  
        logrec.err(path,f"args : read file {filepath}, Result: Path not found | No permission to access or other error. Err : {e}")

def write(filepath, line, bitnum, content):  
    try:  
        if not os.path.exists(filepath):  
            print(f"File '{filepath}' not found.")  
            return  
          
        with open(filepath, 'r') as file:  
            lines = file.readlines()  
        
        if line < 0 or line >= len(lines):  
            print(f"Line number {line} is out of range.")  
            logrec.err(path,f"args : write file {filepath}|{line}|{bitnum}|{content}, Result: Line number out of range.")
            return  
          
        current_line = lines[line]  
          
        if bitnum < 0 or bitnum > len(current_line):  
            print(f"Position {bitnum} is out of range for line {line}.")  
            return  
          
        modified_line = current_line[:bitnum] + content + current_line[bitnum:]  
        lines[line] = modified_line  
          
        with open(filepath, 'w') as file:  
            file.writelines(lines)  
              
        print(f"Successfully wrote to file at line {line}, position {bitnum}.")  
          
        logrec.log(path,f"args : write file {filepath}|{line}|{bitnum}|{content}, Result: Running function successfuly.")
    except Exception as e:  
        print(f"Error writing to file: {e}")  
        logrec.err(path,f"args : write file {filepath}|{line}|{bitnum}|{content}, Result: Path not found | No permission to access or other error. Err : {e}")

def create(filename,filepath,type,text) :
    try :
        file = f"{filepath}/{filename}.{type}"
        with open(file,"w") as f:
            f.write(text)
        logrec.log(path,f"args : create file {filename}.{type}|{filepath}|{text}, Result: Running function successfuly.")
    except Exception as e :
        print(e)
        logrec.err(path,f"args : create file {filename}.{type}|{filepath}|{text}, Result: Path not found | No permission to access or other error. Err : {e}")

def delete(filepath):  
    try:  
        if not os.path.exists(filepath):  
            print(f"File '{filepath}' not found.")  
            return  
        os.remove(filepath)  
        print(f"File '{filepath}' deleted successfully.")  
        logrec.log(path,f"args : delete file {filepath}, Result: Running function successfuly.")
    except Exception as e:  
        print(f"Error deleting file: {e}")  
        logrec.err(path,f"args : delete file {filepath}, Result: Path not found | No permission to access or other error. Err : {e}")

def listdir(directory="."):  
    try:  
        files = os.listdir(directory)  
        print(f"Files in '{directory}':")  
        for file in files:  
            print(f"- {file}")  
        logrec.log(path,f"args : listdir {directory}, Result: Running function successfuly.")
    except Exception as e:  
        print(f"Error listing directory: {e}")  
        logrec.err(path,f"args : listdir {directory}, Result: Path not found | No permission to access or other error. Err : {e}")

def copy(source, destination):  
    try:  
        if not os.path.exists(source):  
            print(f"Source file '{source}' not found.")  
            return  
        with open(source, 'rb') as src_file:  
            with open(destination, 'wb') as dest_file:  
                dest_file.write(src_file.read())  
        print(f"File copied from '{source}' to '{destination}'.")  
        logrec.log(path,f"args : copy file {source}|{destination}, Result: Running function successfuly.")
    except Exception as e:  
        print(f"Error copying file: {e}")  
        logrec.err(path,f"args : copy file {source}|{destination}, Result: Path not found | No permission to access or other error. Err : {e}")

def rename(filepath, new_name):  
    try:  
        if not os.path.exists(filepath):  
            print(f"File '{filepath}' not found.")  
            return  
        os.rename(filepath, new_name)  
        print(f"File renamed from '{filepath}' to '{new_name}'.")  
        logrec.log(path,f"args : rename file {filepath}|{new_name}, Result: Running function successfuly.")
    except Exception as e:  
        print(f"Error renaming file: {e}")  
        logrec.err(path,f"args : rename file {filepath}|{new_name}, Result: Path not found | No permission to access or other error. Err : {e}")

def info(filepath):  
    try:  
        if not os.path.exists(filepath):  
            print(f"File '{filepath}' not found.")  
            return  
        size = os.path.getsize(filepath)  
        modified_time = os.path.getmtime(filepath)  
        print(f"File: {filepath}")  
        print(f"Size: {size} bytes")  
        print(f"Last modified: {modified_time}")  
        logrec.log(path,f"args : info file {filepath}, Result: Running function successfuly.")
    except Exception as e:  
        print(f"Error getting file info: {e}")  
        logrec.err(path,f"args : info file {filepath}, Result: Path not found | No permission to access or other error. Err : {e}")

def mkdir(dirpath,dirname):  
    try:  
        os.mkdir(f"{dirpath}/{dirname}")  
        print(f"Directory '{dirname}' created successfully.")  
        logrec.log(path,f"args : mkdir {dirpath}|{dirname}, Result: Running function successfuly.")
    except Exception as e:  
        print(f"Error creating directory: {e}")  
        logrec.err(path,f"args : mkdir {dirpath}|{dirname}, Result: Path not found | No permission to access or other error. Err : {e}")

def rmdir(dirname):  
    try:  
        os.rmdir(dirname)  
        print(f"Directory '{dirname}' removed successfully.")  
        logrec.log(path,f"args : rmdir {dirname}, Result: Running function successfuly.")
    except Exception as e:  
        print(f"Error removing directory: {e}")  
        logrec.err(path,f"args : rmdir {dirname}, Result: Path not found | No permission to access or other error. Err : {e}")

def compare(file1, file2):   
    try:  
        with open(file1, 'rb') as f1, open(file2, 'rb') as f2:  
            if f1.read() == f2.read():  
                print("Files are identical")  
                logrec.log(path,f"args : compare file {file1}|{file2}, Result: Two files is identical.")
            else:  
                print("Files are different")  
                logrec.log(path,f"args : compare file {file1}|{file2}, Result: Two files is different.")
    except Exception as e:  
        print(f"Error comparing files: {e}")  
        logrec.err(path,f"args : compare file {file1}|{file2}, Result: Path not found | No permission to access or other error. Err : {e}")

def pwd():   
    print(os.getcwd())  
    logrec.log(path,f"args : pwd, Result: Running function successfuly.")

def cd(path):   
    try:  
        os.chdir(path)  
        print(f"Changed directory to: {os.getcwd()}")  
        logrec.log(path,f"args : cd {path}, Result: Running function successfuly.")
    except Exception as e:  
        print(f"Error changing directory: {e}")  
        logrec.err(path,f"args : cd {path}, Result: Path not found | No permission to access or other error. Err : {e}")

def stats(filepath):   
    try:  
        stat = os.stat(filepath)  
        print(f"File: {filepath}")  
        print(f"Size: {stat.st_size} bytes")  
        print(f"Created: {stat.st_ctime}")  
        print(f"Modified: {stat.st_mtime}")  
        print(f"Accessed: {stat.st_atime}")  
        logrec.log(path,f"args : stats {filepath}, Result: Running function successfuly.")
    except Exception as e:  
        print(f"Error getting stats: {e}")  
        logrec.err(path,f"args : stats {filepath}, Result: Path not found | No permission to access or other error. Err : {e}")


def math_func(function) :
    try :
        func = function.lower()
    except : 
        pass
    if func == "pi" or func == "π" :
        print(math.pi)
        logrec.log(path,f"args : math_func {function}, Result: Returned π.")
    elif func == "tau" or function == "τ" :
        print(math.pi * 2)
        logrec.log(path,f"args : math_func {function}, Result: Returned τ.")
    elif function == "phi" or function == "Φ" :
        print(1.618)
        logrec.log(path,f"args : math_func {function}, Result: Returned φ.")
    elif function == "e" or function == "euler" :
        print(math.e)
        logrec.log(path,f"args : math_func {function}, Result: Returned e.")
    else :
        print("your function is invalid, wait for update!")
        logrec.err(path,f"args : math_func {function}, Result: Invalid function.")

def calc(exp) :
    # safe expression evaluator using ast
    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Num):
            return node.n
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.BinOp):
            left = _eval(node.left)
            right = _eval(node.right)
            op = _BINOP.get(type(node.op))
            if op is None:
                raise ValueError("Unsupported operator")
            return op(left, right)
        if isinstance(node, ast.UnaryOp):
            operand = _eval(node.operand)
            op = _UNARYOP.get(type(node.op))
            if op is None:
                raise ValueError("Unsupported unary operator")
            return op(operand)
        if isinstance(node, ast.Call):
            # allow math functions only
            func = node.func
            if isinstance(func, ast.Attribute):
                # math.sin -> Name(math).attr
                val = _eval(func.value)
                raise ValueError("Unsupported call")
            elif isinstance(func, ast.Name):
                fname = func.id
                if fname in _MATH_FUNCS:
                    args = [_eval(a) for a in node.args]
                    return _MATH_FUNCS[fname](*args)
            raise ValueError("Unsupported function call")
        raise ValueError("Unsupported expression")

    try:
        # prepare environment
        _BINOP = {
            ast.Add: _operator.add,
            ast.Sub: _operator.sub,
            ast.Mult: _operator.mul,
            ast.Div: _operator.truediv,
            ast.FloorDiv: _operator.floordiv,
            ast.Mod: _operator.mod,
            ast.Pow: _operator.pow,
        }
        _UNARYOP = {ast.UAdd: _operator.pos, ast.USub: _operator.neg}
        # expose some math functions
        _MATH_FUNCS = {k: getattr(math, k) for k in ('sin','cos','tan','sqrt','log','exp') if hasattr(math, k)}
        node = ast.parse(exp, mode='eval')
        result = _eval(node)
        print(f"Calculating Successfully, Calculating expression : {exp}, Result is : {result}.")
        logrec.log(path,f"args : calc {exp}, Result: Calculating expression : {exp}, Result is : {result}.")
    except Exception as e:
        print(f"Expression condition isn't passed or unsafe expression: {e}")
        logrec.err(path,f"args : calc {exp}, Result: Calculating expression : Danger expression. Err: {e}")
    

def rand(mode,start,end) :
    try:
        if mode == "int" :
            print(random.randint(start,end))
            logrec.log(path,f"args : rand {mode}|{start}|{end}, Result: Running function successfuly.")
        elif mode == "float" :
            print(random.uniform(start,end))
            logrec.log(path,f"args : rand {mode}|{start}|{end}, Result: Running function successfuly.")
        else :
            print("invalid mode!")
            logrec.err(path,f"args : rand {mode}|{start}|{end}, Result: Invalid mode.")
    except Exception as e :
        print(e)
        
def showt():
    print(f'Time of now:{time.strftime("%H:%M:%S")}')
    print(f'Date of today:{time.strftime("%Y-%m-%d")}')
    print(f'Weekday of today:{time.strftime("%A")}')
    logrec.log(path,f"args : showt, Result: Getted formated time string.")

def help() :
    print("commands is below")
    print("- read : read file and print file text")
    print("- write : write text in file")
    print("- create : create a file to a path")
    print("- delete : remove a file")
    print("- copy : copy file to other path")
    print("- rename : rename file")
    print("- compare : compare the contents of two files")
    print("- listdir : list the files and subdirectories in the directory")
    print("- mkdir : create an new direction")
    print("- rmdir : remove an empty direction")
    print("- pwd : print working direction")
    print("- cd : change working direction")
    print("- info : show file basic information")
    print("- stats : show detailed file statistics")
    print("- mathfunc : return math constants")
    print("- calc : calculate math expression")
    print("- rand : generate random integer number or random floating-point number")
    print("- exit : exit pythonCMD program")
    print("- showt : show time of now or today")
    print("- out : output a text, like \"echo\" in cmd")
    print("- help : show this command help")
    print("- credits : show credits list")
    print("- version : show version")
    print("- license : show license")
    print("- clear : clear screen")
    print("I'll append more functions in the program(update)...")
    logrec.log(path,f"args : help, Result: Outputed command list.")

def clear():  
    os.system('cls' if os.name == 'nt' else 'clear')
    logrec.log(path,f"args : clear, Result: Screen cleared.")
    mainpack()

def command(c):
    try : 
        if c == "help" :
            help()
        elif c == "read" :
            arg1 = input("input \"filepath\" arg ->")
            read(arg1)
        elif c == "write" :
            arg1 = input("input \"filepath\" arg ->")
            arg2 = input("input \"line\" arg ->")
            arg3 = input("input\"bitnum\" arg ->")
            arg4 = input("input \"content\" arg ->")
            write(arg1,arg2,arg3,arg4)
        elif c == "create":
            arg1 = input("input \"filename\" arg ->")
            arg2 = input("input \"filepath\" arg ->")
            arg3 = input("input \"type\" arg ->")
            arg4 = input("input \"text\" arg ->")
            create(arg1,arg2,arg3,arg4)
        elif c == "delete":
            arg1 = input("input \"filepath\" arg ->")
            delete(arg1)
        elif c == "listdir":
            arg1 = input("input \"directory\" arg ->")
            listdir(arg1)
        elif c == "copy":
            arg1 = input("input \"source\" arg ->")
            arg2 = input("input \"destination\" arg ->")
            copy(arg1,arg2)
        elif c == "rename":
            arg1 = input("input \"filepath\" arg ->")
            arg2 = input("input \"new_name\" arg ->")
            rename(arg1,arg2)
        elif c == "info":
            arg1 = input("input \"filepath\" arg ->")
            info(arg1)
        elif c == "mkdir":
            arg1 = input("input \"dirpath\" arg ->")
            arg2 = input("input \"dirname\" arg ->")
            mkdir(arg1,arg2)
        elif c == "rmdir":
            arg1 = input("input \"dirname\" arg ->")
            rmdir(arg1)
        elif c == "compare":
            arg1 = input("input \"file1\" arg ->")
            arg2 = input("input \"file2\" arg ->")
            compare(arg1,arg2)
        elif c == "pwd":
            pwd()
        elif c == "cd":
            arg1 = input("input \"path\" arg ->")
            cd(arg1)
        elif c == "stats":
            arg1 = input("input \"filepath\" arg ->")
            stats(arg1)
        elif c == "mathfunc":
            arg1 = input("input \"function\" arg ->")
            math_func(arg1)
        elif c == "calc":
            arg1 = input("input \"expression\" arg ->")
            calc(arg1)
        elif c == "rand":
            arg1 = input("input \"mode\" arg ->")
            arg2 = int(input("input \"start\" arg ->"))
            arg3 = int(input("input \"end\" arg ->"))
            rand(arg1,arg2,arg3)
        elif c == "showt":
            showt()
        elif c == "out":
            arg1 = input("input \"text\" arg ->")
            print(arg1)
        elif c == "version":
            print("This program is developing phase, version:Dev alpha 1.0.0 published version(have bug :3), New version is developing...")
        elif c == "credits":
            print("[Credits-\n MC:git32server \n github:Git32-Design \n QQmail:git32mail@qq.com] \n Thank codebuddy to help\n Thanks for you using this program!\n Author is a student, He's programming not professional, If you have some problem, Please contact me by QQmail or github, Thanks!")
        elif c == "license":
            print("""
MIT License

Copyright (c) 2025 Git32-Design

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

Contact: git32mail@qq.com
GitHub: Git32-Design
        """)
        elif c == "clear":
            clear()
        else :
            if c != "exit" :
                print("invalid command,please try other commands")
    except Exception as e:
        print(f"Checking args data or running function have some error, The author well fix this error, Some error messages : {e}")
        
def mainloop():
    print("Copyright[C] platform=Windows | author=[Git32-Design]")
    logrec.log(path,f"args : mainloop, Result: PYcmd is running...")
    while True:       
        cmd = input(f"this program running in {os.getcwd()}, now|input \"help\" to get command list > ")
        command(cmd.lower())
        if cmd == "exit" :
            break
        
        
def mainpack():
    mainloop()
    print("PYcmd Dev alpha 1.0 .0\nExiting...\nThanks for you use this program!")
    logrec.log(path,f"args : mainpack, Result: PYcmd exit.")
    time.sleep(random.randint(2, 5))


def _build_cli():
    import argparse
    parser = argparse.ArgumentParser(prog='PYcmd')
    sub = parser.add_subparsers(dest='cmd')

    sub.add_parser('read').add_argument('filepath')
    sub.add_parser('delete').add_argument('filepath')
    sub.add_parser('listdir').add_argument('directory', nargs='?', default='.')
    c_write = sub.add_parser('write')
    c_write.add_argument('filepath')
    c_write.add_argument('line', type=int)
    c_write.add_argument('pos', type=int)
    c_write.add_argument('content')
    sub.add_parser('calc').add_argument('expression')
    return parser


def run_cli(argv=None):
    parser = _build_cli()
    args = parser.parse_args(argv)
    if args.cmd == 'read':
        read(args.filepath)
    elif args.cmd == 'delete':
        delete(args.filepath)
    elif args.cmd == 'listdir':
        listdir(args.directory)
    elif args.cmd == 'write':
        write(args.filepath, args.line, args.pos, args.content)
    elif args.cmd == 'calc':
        calc(args.expression)
    else:
        parser.print_help()
    
def cli_and_main():
    # if CLI args provided, run CLI; otherwise run interactive mainpack
    if len(sys.argv) > 1:
        run_cli(sys.argv[1:])
    else:
        mainpack()
    logrec.log(path,f"args : __main__, Result: Exit succesfully.")

if __name__ == "__main__":
    cli_and_main()

# Requires: see ../requirements.txt for external packages used in tests/tools
# If you want to watch more information, Please check my other account, Account name is in "credits" function.
# At end, We want to update this program's lastest version, At that time, We will stop update.
# Yes, It's start.
# I'm learning on my own. I'm researching python/C++/Markup language/mcfunction and other.