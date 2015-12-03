a pre-processing step for C and C++ programs to convert printf and other similar functions into an alternate form for truly type-safe checking.

More documentation to come, but for now see http://blog.modp.com/2008/10/type-safe-printf.html

To use:

```
./printf.py < INFILE.c > OUTFILE.c
gcc -Wconversion -Werror OUTFILE.c
```
