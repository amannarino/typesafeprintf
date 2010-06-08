#!/usr/bin/env python
#
# The MIT License
#
# Copyright (c) 2008 Nicholas Galbreath
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

# For background:
# http://blog.client9.com/2008/10/type-safe-printf.html
# http://code.google.com/p/typesafeprintf/

from __future__ import with_statement

import os
import re
import shutil
import string
import sys
import traceback
from optparse import OptionParser

functions = [
    {
        'fname'  : 'asprintf',
        'rtype'  : 'int',
        'format_pos': 1,
        'atype0' : 'char **'
        },
    {
        'fname' : 'fprintf',
        'rtype' : 'int',
        'format_pos': 1,
        'atype0' : 'FILE*'
        },
    {
        'fname': 'printf',
        'rtype': 'void',
        'format_pos': 0
        },
    {
        'fname': 'snprintf',
        'rtype': 'int',
        'format_pos': 2,
        'atype0': 'char *',
        'atype1': 'size_t'
        },
    {
        'fname': 'sprintf',
        'rtype': 'int',
        'format_pos': 1,
        'atype0': 'char *',
        }
    ]

typesmap = {
    'd': 'int',
    'i': 'int',
    'u': 'unsigned int',
    'o': 'unsigned int',
    'x': 'unsigned int',
    'X': 'unsigned int',
    'ld': 'long',
    'li': 'long',
    'lu': 'unsigned long',
    'lo': 'unsigned long',
    'lx': 'unsigned long',
    'lX': 'unsigned long',
    'lld': 'long long',
    'lli': 'long long',
    'llu': 'unsigned long long',
    'llo': 'unsigned long long',
    'llx': 'unsigned long long',
    'llX': 'unsigned long long',
    'hd': 'short',
    'hi': 'short',
    'hhd': 'char',
    'hhi': 'char',
    'hhu': 'unsigned char',
    'hu': 'unsigned short',
    'o': 'unsigned int',
    's': 'const char*',
    'p': 'void*',
    'f': 'double',
    'F': 'double',
    'e': 'double',
    'E': 'double',
    'g': 'double',
    'G': 'double',
    'Lf': 'long double',
    'LF': 'long double',
    'Le': 'long double',
    'LE': 'long double',
    'Lg': 'long double',
    'LG': 'long double',
    'c' : 'char'
    }

def extractFunctionCall(text, fname, rtype, format_pos, atype0=None, atype1=None):
    count = 0;
    pos = 0
    outlines = []
    try:
        while pos < len(text):
            count += 1
            mo = extractFunctionCall1(text, fname, pos, format_pos)
            if mo is None:
                break
            
            # function name start
            # format arg start
            # format arg end
            fstart, qstart, qend = mo
            
            format = text[qstart:qend]
            suffix = '_%d' % count
            newname = fname + suffix
            text = text[0:fstart] + newname + text[fstart+len(fname):]
            pos = qend + len(suffix)
            
            types = makeArgList(format)
            names = [ "a%d" % i for i in range(len(types)) ]
            arglist = ', '.join([ "%s %s" % i for i in zip(types,names)])
            vars = ', '.join(names)
            
            if len(vars) > 0:
                vars = format + ", " + vars
            else:
                vars = format
            if atype1 is not None:
                vars = "b1, " + vars
            if atype0 is not None:
                vars = "b0, " + vars

            
            if len(arglist) > 0:
                arglist = 'const char* format __attribute__((unused)), ' + arglist
            else:
                arglist = 'const char* format __attribute__((unused))'

            if atype1 is not None:
                arglist = atype1 + " b1, " + arglist
            if atype0 is not None:
                arglist = atype0 + "b0, " + arglist

            # now make a function
            outlines.append("static %s %s(%s) {" % (rtype, newname, arglist))
            if rtype == 'void':
                outlines.append("   %s(%s);" % (fname, vars))
            else:
                outlines.append("  return %s(%s);" % (fname, vars))
            outlines.append("}\n\n")

    except Exception,e:
        print "Got exception ", e
        traceback.print_exc(e)
        pass

    return text, '\n'.join(outlines)

def extractFunctionCall1(text, fname, pos, format_pos):
    """
    returns None if none found or a triple containing the index of
    the start of the function name, start and end indexes of the format argument
    """

    while True:
        idx = text.find(fname, pos)
        if idx == -1:
            return None

        # check for matches of "printf" in "fprintf"
        # make sure previous char is not [a-zA-Z0-9_]
        prevchar = text[idx-1]
        if prevchar in string.letters or prevchar in string.digits or prevchar == '_':
            pos = idx + len(fname)
            continue

        # check for printf-style class methods
        elif prevchar == '.' or (text[idx-2:idx-1] == '->'):
            pos = idx + len(fname)
            continue

        # start of function name
        fstart = idx
        idx += len(fname)

        # after function name, it better start with '('
        while text[idx] in string.whitespace: idx += 1
        if text[idx] != '(':
            pos = idx
            continue
        idx += 1
        while text[idx] in string.whitespace: idx += 1

        # skip over initial arguments
        for i in range(format_pos):
            while text[idx] != ',': idx += 1
            idx += 1
            while text[idx] in string.whitespace: idx += 1

        # next arg is the format string which starts with a quote
        if text[idx] != '"':
            pos = idx
            continue

        qstart = idx
        idx += 1

        # now extract the format string
        # handle case where string litteral is split, e.g.
        # printf("a" "b") is same as printf("ab")
        #
        while idx < len(text):
            while text[idx] != '"': idx += 1
            if text[idx-1] == '\\':
                idx += 1
                continue
            idx += 1
            qend = idx
            while text[idx] in string.whitespace: idx += 1

            c = text[idx]
            if c == ',' or c == ')':
                return (fstart,qstart,qend)
            elif c == '"':
                idx += 1
                continue
            else:
                pos = idx
                # break out string grabbing loop
                break

        
# % FLAGS LENGTH TYPE
format = re.compile('%([0123456789# +.-]*)(hh|h|l|ll|z|j|t)?([%diufFeFgGxXoscpn])')
def format2type(length, type):
    """ Convert a 'printf' type to a C type """
    if length is None:
        length = ''
    val = "%s%s" % (length, type)
    t = typesmap[val]
    return t

def match(s):
    """
    input is start of a format string specifier (starts with '%')
    return 3-tuple of 'flags' (formatting),
       'length' (8,16,32, or 64 bits) and 'type' (int, double, etc)
    """
    f = []
    for mo in format.finditer(s):
        flags = mo.group(1)
        if not flags:
            flags = None
        f.append( (flags, mo.group(2), mo.group(3)))
    return f

def makeArgList(fstr):
    args = match(fstr)
    atypes = []
    count = 1
    for a in args:
        if a[2] in ['%']:
            continue
        t = format2type(a[1], a[2])
        atypes.append(t)
        count += 1
    return atypes

def removeInclude(text, filename, prefix='', suffix='_varargs.h'):
    """ Removes the special include file """
    includeline =  '#include "%s%s%s"' % (prefix,filename,suffix)
    return text.replace(includeline + '\n', '')

def insertAutogenerated(text, toinsert):
    """
    Inserts autogenerated text right after the last #include statement
    """

    if re.match(r'^\s*$', toinsert):
        return text

    inserttext  = "\n/* VARARG TRANSFORMATION START */\n/* This is autogenerated */\n\n"
    inserttext += toinsert
    inserttext += "/* VARARG TRANSFORMATION END */\n"

    # look for each line and find LAST #include
    # we'll insert our include right afterwards

    lines = text.split('\n')
    gotfirst = False
    gotlast = False
    insertPoint = None
    for i in xrange(len(lines)):
        if lines[i].startswith('#include'):
            if not gotfirst:
                gotfirst = True
        else:
            if gotfirst:
                gotfirst = False
                insertPoint = i

    if insertPoint is None:
        # TODO: Ought to have some kind of error recovery here?
        pass

    lines.insert(insertPoint, inserttext)
    return '\n'.join(lines)

def transformStream(input, output, options):
    """
    Applies the printf transformation from the given input
    stream, writing the results to the given output stream.
    """
    text = input.read()

    inserttext = []
    for i in functions:
        text, fns = extractFunctionCall(text, **i)
        inserttext.append(fns)

    text2 = insertAutogenerated(text, '\n'.join(inserttext))

    output.write(text2)

def transformFile(file, options):
    """
    Applies the printf transformation to a single file.
    """
    orig_file = file + options.suffix
    shutil.copy(file, orig_file)
    # TODO: Better line handling?  (Text versus binary.)
    with open(orig_file, 'r') as input:
        with open(file, 'w') as output:
            transformStream(input, output, options)

def transformDirectory(path, options):
    """
    Recursively applies the printf transformation to every file in the
    directory.
    """

	# Omit header files for now; they shouldn't have any printf calls,
	# and their transformed functions could conflict with source files.
	#file_re = '.*\.(c|C|cpp|cc|cxx|h|hpp|hxx)$'
	file_re = '.*\.(c|C|cpp|cc|cxx)$'

    for root, dirs, files in os.walk(path):
        for file in [f for f in files if re.match(file_re, f)]:
            transformFile(os.path.join(root, file), options)

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-R", "--recursive",
        action="store_true", dest="recursive",
        help="recursively process subdirectories")
    parser.add_option("-S", "--suffix",
        action="store", dest="suffix", default=".orig",
        help="suffix for backup files (default .orig)")
    (options, args) = parser.parse_args()

    if options.recursive and not args:
        args = ['.']
    for arg in args:
        if not os.path.isdir(arg):
            transformFile(arg, options)
        elif options.recursive:
            transformDirectory(arg, options)
        else:
            print >> sys.stderr, "Skipping directory %s (--recursive was not specified)" % arg
    if len(args) == 0:
        print >> sys.stderr, "No filenames given, processing stdin instead..."
        transformStream(sys.stdin, sys.stdout, options)

# vim:et

