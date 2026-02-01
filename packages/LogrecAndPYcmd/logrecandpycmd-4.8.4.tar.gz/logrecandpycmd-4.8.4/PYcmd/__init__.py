"""
    Information of PYcmd below
    <===================================================================>
    Code lib : PYcmd
    Fill name : Python Command Prompt
    Author : Git32-Design
    Version : Rel 2.1.1
    create at : 2025/11/8
    lastest update : 2026/1/31
    Used lib : os(Operating system)|math(Mathematical functions)|random(Random number)|time(Time)|pathlib(Path handling)|ast(Abstract syntax trees)|operator(Operators)|sys(System)|logrec(Log recording)
    IDE : Visual Studio Code
    Developing language : Python 3.13.0
    Licence : MIT License
    Description : This program is a command prompt tool for managing files.
"""

from PYcmd import (\
    # Valid commands
    read, write, create, delete, listdir, copy,\
    rename, info, mkdir, rmdir, compare, pwd,\
    cd, stats, math_func, calc, rand, showt,\
    help, clear, command, mainloop, mainpack, _build_cli,\
    run_cli, cli_and_main, pathlib\
    
)

# Module metadata (PEP 396 compliant)
__version__ = "2.1.1"
__author__ = "Git32-Design"
__author_email__ = "git32mail@qq.com"
__license__ = "MIT"
__copyright__ = "Copyright (c) 2025 Git32-Design"
__maintainer__ = "Git32-Design"
__maintainer_email__ = "git32mail@qq.com"

# PyPI package metadata
__title__ = "LogrecAndPYcmd"
__summary__ = "This program is a command prompt tool for managing files."
__description__ = "This program is a command prompt tool for managing files."
__long_description__ = """\
PYcmd is a command-line tool that provides file management operations including read, write, 
create, delete, copy, rename, directory operations, and comparison. It also includes math 
calculations, random number generation, time display, and a safe expression evaluator. 
The tool supports both interactive mode and CLI usage with logging capabilities.
"""
__keywords__ = ["file", "management", "command line", "cmd", "cli", "tool", "python", "logrec", "log", "logger"]
__project_urls__ = {
    "Homepage": "https://github.com/Git32-Design/logrec-and-PYcmd",
    "Documentation": "None",
    "Repository": "https://github.com/Git32-Design/logrec-and-PYcmd.git",
    "Bug Tracker": "https://github.com/Git32-Design/logrec-and-PYcmd/issues",
}
__classifiers__ = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "Intended Audience :: System Administrators",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: System :: Logging",
    "Topic :: System :: Systems Administration",
    "Topic :: Utilities",
]
__python_requires__ = ">=3.8"

# Standard metadata
__doc__ = """
    Information of PYcmd below
    <===================================================================>
    Code lib : PYcmd
    Fill name : Python Command Prompt
    Author : Git32-Design
    Version : Alpha 1.1.1
    create at : 2025/11/8
    lastest update : 2026/1/31
    Used lib : os(Operating system)|math(Mathematical functions)|random(Random number)|time(Time)|pathlib(Path handling)|ast(Abstract syntax trees)|operator(Operators)|sys(System)|logrec(Log recording)
    IDE : Visual Studio Code
    Developing language : Python 3.13.0
    Licence : MIT License
    Description : This program is a command prompt tool for managing files.
"""


# Export all public functions
__all__ = [
    # Valid commands
    'read', 'write', 'create', 'delete', 'listdir', 'copy',\
    'rename', 'info', 'mkdir', 'rmdir', 'compare', 'pwd',\
    'cd', 'stats', 'math_func', 'calc', 'rand', 'showt',\
    'help', 'clear', 'command', 'mainloop', 'mainpack', '_build_cli',\
    'run_cli', 'cli_and_main',\
]

# Convenience imports for common use cases
class PythonCmd:
    """Convenience class for Python command operations"""

    def __init__(self, log_path=None):
        self.log_path = log_path or f"{pathlib.Path(__file__).parent.absolute()}/PYcmd log record.log"

    # File operations
    def read(self, filepath):
        """Read file and print content"""
        return read(filepath)

    def write(self, filepath, line, bitnum, content):
        """Write text to file at specific line and position"""
        return write(filepath, line, bitnum, content)

    def create(self, filename, filepath, type, text):
        """Create a new file"""
        return create(filename, filepath, type, text)

    def delete(self, filepath):
        """Delete a file"""
        return delete(filepath)

    def copy(self, source, destination):
        """Copy file to destination"""
        return copy(source, destination)

    def rename(self, filepath, new_name):
        """Rename file"""
        return rename(filepath, new_name)

    def compare(self, file1, file2):
        """Compare two files"""
        return compare(file1, file2)

    def info(self, filepath):
        """Show file basic information"""
        return info(filepath)

    def stats(self, filepath):
        """Show detailed file statistics"""
        return stats(filepath)

    # Directory operations
    def listdir(self, directory="."):
        """List files in directory"""
        return listdir(directory)

    def mkdir(self, dirpath, dirname):
        """Create directory"""
        return mkdir(dirpath, dirname)

    def rmdir(self, dirname):
        """Remove directory"""
        return rmdir(dirname)

    def pwd(self):
        """Print working directory"""
        return pwd()

    def cd(self, path):
        """Change directory"""
        return cd(path)

    # Math operations
    def math_func(self, function):
        """Return math constants"""
        return math_func(function)

    def calc(self, exp):
        """Calculate math expression"""
        return calc(exp)

    def rand(self, mode, start, end):
        """Generate random number"""
        return rand(mode, start, end)

    # Utility operations
    def showt(self):
        """Show current time"""
        return showt()

    def help(self):
        """Show command help"""
        return help()

    def clear(self):
        """Clear screen"""
        return clear()

    # Main program operations
    def command(self, c):
        """Execute command"""
        return command(c)

    def mainloop(self):
        """Run main loop"""
        return mainloop()

    def mainpack(self):
        """Run main program"""
        return mainpack()

    # CLI operations
    def run_cli(self, argv=None):
        """Run CLI mode"""
        return run_cli(argv)

    def cli_and_main(self):
        """Run interactive or CLI mode"""
        return cli_and_main()


# Requires: see ../requirements.txt for external packages used in tests/tools