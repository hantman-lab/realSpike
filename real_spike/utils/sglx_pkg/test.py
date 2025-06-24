from sys import version_info
from ctypes import *

if version_info >= (3,8):
    sglx = CDLL( "libSglxApi.so", winmode=0 )
else:
    sglx = CDLL( "libSglxApi.so" )


hSglx = sglx.c_sglx_createHandle()