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

import unittest
from printf import *

class TestFormats(unittest.TestCase):
    def testExtractFunction(self):
        sample = 'if (printf("123456789", "abc", "def");'
        text, fns = extractFunctionCall(sample, 'printf', 'int', 0)

        sample = 'if (printf("%d %s", 1, "def");'
        text, fns = extractFunctionCall(sample, 'printf', 'int', 0)
        #print text, '\n', fns


    def testExtractFunction1(self):
        sample = 'if (printf("123456789", "abc", "def")'
        extractFunctionCall1(sample, 'printf', 0, 0)
        sample = 'printf ( "123456789", "abc", "int", 0)'
        extractFunctionCall1(sample, 'printf', 0, 0)
        sample = 'printf ( "123456789" );'
        extractFunctionCall1(sample, 'printf', 0 , 0)
        sample = 'printf ( "123456789"\n "abcedf" );'
        extractFunctionCall1(sample, 'printf', 0, 0)

    def testArgs(self):
        self.assertEquals([], makeArgList(''))
        self.assertEquals(['int'], makeArgList('%d'))
        self.assertEquals(['int', 'int'], makeArgList('  %d  %d'))
        self.assertEquals([], makeArgList('foobar'))
        self.assertEquals([], makeArgList('%%'))

    def testFormats(self):
        self.assertEquals(0, len(match('')))
        self.assertEquals(1, len(match('%d')))
        self.assertEquals(2, len(match('  %d  %d')))
        self.assertEquals(0, len(match('foobar')))
        self.assertEquals(1, len(match('%%')))

    def testMatch(self):
        (flags, length, ctype) = match("%%")[0]
        self.assertEquals(None, flags)
        self.assertEquals(None, length)
        self.assertEquals('%', ctype)

        (flags, length, ctype) = match("%d")[0]
        self.assertEquals(None, flags)
        self.assertEquals(None, length)
        self.assertEquals('d', ctype)

        (flags, length, ctype) = match("%6d")[0]
        self.assertEquals('6', flags)
        self.assertEquals(None, length)
        self.assertEquals('d', ctype)

        (flags, length, ctype) = match("xxx%06dxxx")[0]
        self.assertEquals('06', flags)
        self.assertEquals(None, length)
        self.assertEquals('d', ctype)

        (flags, length, ctype) = match("%%")[0]
        self.assertEquals(None, flags)
        self.assertEquals(None, length)
        self.assertEquals('%', ctype)

    def testTypes(self):
        (flags, length, ctype) = match('%lld')[0]
        self.assertEquals('long long', format2type(length, ctype))
        (flags, length, ctype) = match('%ld')[0]
        self.assertEquals('long', format2type(length, ctype))
        (flags, length, ctype) = match('%d')[0]
        self.assertEquals('int', format2type(length, ctype))
        (flags, length, ctype) = match('%.3f')[0]
        self.assertEquals('double', format2type(length, ctype))

if __name__ == '__main__':
    unittest.main()
