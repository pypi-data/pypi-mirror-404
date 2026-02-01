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

from .logrec import (\
    
    # Log recording functions
    log, tip, warn, err, crit,
    
    # Log management functions
    read, search, rem, clear, change,
    
    # extra helpers
    search_by_keyword, tail,
    
    # export/rotation
    parse_log_line, export_logs,
    
    # Log information functions
    gettime, getlevel,
    
    # Appendix functions
    credits, version, license
)

# Module metadata (PEP 396 compliant)
__version__ = "3.7.3"
__author__ = "Git32-Design"
__author_email__ = "git32mail@qq.com"
__license__ = "MIT"
__copyright__ = "Copyright (c) 2025 Git32-Design"
__maintainer__ = "Git32-Design"
__maintainer_email__ = "git32mail@qq.com"

# PyPI package metadata
__title__ = "Log Recorder"
__summary__ = "A quick record log's library with search and management capabilities"
__description__ = "A quick record log's library with search and management capabilities"
__long_description__ = """\
Log Recorder is a simple yet powerful Python library for recording and managing log files.
It provides easy-to-use functions for writing logs of different levels, searching through
log entries, and managing log files. While Python's built-in logging module is recommended
for production use, this library offers a lightweight alternative for quick logging tasks.
"""
__keywords__ = ["log", "logger", "recording", "search", "management", "file", "logging", "debug"]
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
    "License :: OSI Approved :: MIT License",
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
    Information of logrec below
    <===================================================================>
    Code lib : logrec
    Fill name : Log Recorder
    Author : Git32-Design
    Version : Rel 3.7.3
    create at : 2025/11/8
    lastest update : 2026/1/31
    Used lib : os(Operating system)|time(Time)
    IDE : Visual Studio Code
    Developing language : Python 3.13.0
    Licence : MIT License
    Description : A quick record log's lib, Can search log file, And record(Or write) logs to a file. It's easy, Please use "logging" library. I know, My lib is sucks, But I well publish it to github. 
"""


# Export all public functions
__all__ = [
    # Log recording
    'log', 'tip', 'warn', 'err', 'fatal',
    
    # Log management
    'read', 'search', 'rem', 'clear', 'change', 'search_by_keyword', 'tail',
    'parse_log_line', 'export_logs',
    
    # Log information
    'gettime', 'getlevel',
    
    # Appendix
    'credits', 'version', 'license'
]

# Convenience imports for common use cases
class LogRecorder:
    """Convenience class for log recording operations"""
    
    def __init__(self, filepath):
        self.filepath = filepath
    
    def log(self, text):
        """Record normal log"""
        return log(self.filepath, text)
    
    def tip(self, text):
        """Record tip log"""
        return tip(self.filepath, text)
    
    def warn(self, text):
        """Record warning log"""
        return warn(self.filepath, text)
    
    def err(self, text):
        """Record error log"""
        return err(self.filepath, text)
    
    def crit(self, text):
        """Record fatal error log"""
        return crit(self.filepath, text)
    
    def read(self):
        """Read and output logs"""
        return read(self.filepath)
    
    def search(self, line):
        """Search specific log line"""
        return search(self.filepath, line)
    
    def remove(self, line):
        """Remove specific log line"""
        return rem(self.filepath, line)
    
    def clear(self):
        """Clear all logs"""
        return clear(self.filepath)
    
    def change(self, line, text):
        """Change specific log line"""
        return change(self.filepath, line, text)
    
    def parse_log_line(self, line):
        """Parse a log line into its components"""
        return parse_log_line(line)
    
    def export_logs(self, out_path, fmt='json'):
        """Export logs to specified format"""
        return export_logs(self.filepath, out_path, fmt)
    
    def get_time(self):
        """Get log times"""
        return gettime(self.filepath)
    
    def get_level(self):
        """Get log levels"""
        return getlevel(self.filepath)
    
    def credits(self):
        """Show credits"""
        return credits()
    
    def version(self):
        """Show version"""
        return version()
    
    def license(self):
        """Show license"""
        return license()

# Requires: see ../requirements.txt for external packages used in tests/tools