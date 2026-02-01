#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : blacklist.py

"""Stata dofile security blacklist definitions.

This module defines dangerous commands and patterns that should be blocked
when executing Stata dofiles, unless dangerous mode is explicitly enabled.
"""

from typing import List, Set

# ============================================================================
# Dangerous Commands
# ============================================================================

#: Commands that allow execution of shell/system commands
DANGEROUS_COMMANDS: Set[str] = {
    "!",          # Unix-style shell escape: !ls
    "!!",         # Extended shell command (xshell synonym): !!vi file.do
    "shell",      # Shell command execution: shell dir
    "xshell",     # Extended shell for Mac/Unix(GUI): xshell vi file.do
    "winexec",    # Windows program execution: winexec notepad.exe
    "unixcmd",    # Unix command execution: unixcmd ls
}


# ============================================================================
# Dangerous Patterns (Regular Expressions)
# ============================================================================

#: Patterns that may indicate dangerous operations
DANGEROUS_PATTERNS: List[str] = [
    # Shell command execution
    r"!\s*\w+",           # Shell escape with command: ! ls, !dir
    r"!!\s*\w+",          # Extended shell with command: !! vi file.do
    r"shell\s+\w+",       # Shell command: shell dir, shell ls
    r"xshell\s+\w+",      # Extended shell: xshell vi file.do
    r"winexec\s+\S+",     # Windows execution: winexec program.exe
    r"unixcmd\s+\w+",     # Unix command: unixcmd ls

    # File operations (potentially dangerous)
    r"erase\s+.*",        # File deletion: erase file.dta
    r"rm\s+.*",           # File deletion (alias): rm file.dta
    r"rmdir\s+.*",        # Directory removal: rmdir mydir
    r"copy\s+.*",         # File copy (can overwrite): copy file1.dta file2.dta

    # Code execution from external files
    r"run\s+.*",          # Run another do-file: run script.do
    r"\bdo\s+.*",         # Execute do-file: do script.do
    r"include\s+.*",      # Include another do-file: include setup.do
]


# ============================================================================
# Metadata
# ============================================================================

__all__ = [
    "DANGEROUS_COMMANDS",
    "DANGEROUS_PATTERNS",
]
