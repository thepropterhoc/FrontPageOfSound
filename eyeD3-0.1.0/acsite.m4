dnl
dnl  Copyright (C) 2002  Travis Shirk <travis@pobox.com>
dnl
dnl  This program is free software; you can redistribute it and/or modify
dnl  it under the terms of the GNU General Public License as published by
dnl  the Free Software Foundation; either version 2 of the License, or
dnl  (at your option) any later version.
dnl
dnl  This program is distributed in the hope that it will be useful,
dnl  but WITHOUT ANY WARRANTY; without even the implied warranty of
dnl  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
dnl  GNU General Public License for more details.
dnl
dnl  You should have received a copy of the GNU General Public License
dnl  along with this program; if not, write to the Free Software
dnl  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
dnl

AC_DEFUN([ACX_CHECK_PYTHON2], [
   PYTHON=""
   AC_PATH_PROGS([PYTHON], [python2 python])
   if test -z ${PYTHON}; then 
      AC_MSG_ERROR([python version 2.2 could not be found])
   elif test "`basename ${PYTHON}`" != "python2"; then
      dnl Test the interpreter for v 2.2
      AC_MSG_CHECKING([if ${PYTHON} is version 2.2])
      if ${PYTHON} -c 'import sys; print sys.version' | grep "^2." > /dev/null 2>&1; then
         AC_MSG_RESULT([yes])
      else
         AC_MSG_RESULT([no])
         AC_MSG_ERROR([python version 2.2 could not be found])
      fi 
   fi
])

AC_DEFUN([ACX_ID3LIB], [
   ID3LIB_CXXFLAGS=""
   ID3LIB_LIBS=""
   AC_MSG_CHECKING([for id3lib])
   for rootDir in /usr /usr/local; do
      if test -r ${rootDir}/include/id3/tag.h &&
         test -r ${rootDir}/lib/libid3.so -o -r ${rootDir}/lib/libid3.a && 
	 test -r /usr/lib/libz.so -o -r /usr/lib/libz.a; then
	 if test ${rootDir} != "/usr"; then
	    ID3LIB_CXXFLAGS="-I${rootDir}/include"
	    ID3LIB_LIBS="-L${rootDir}/lib -lid3 -lz"
	 else
	    ID3LIB_LIBS="-lid3 -lz"
	 fi
      fi
   done

   if test -z "${ID3LIB_LIBS}"; then
      AC_MSG_RESULT([no])
      AC_MSG_WARN([id3lib not found, test program will not be built])
      HAVE_ID3LIB="no"
      AC_SUBST([HAVE_ID3LIB])
   else
      AC_MSG_RESULT([yes])
      AC_SUBST([ID3LIB_CXXFLAGS])
      AC_SUBST([ID3LIB_LIBS])
      AC_DEFINE([HAVE_ID3LIB], 1, [id3lib headers and libs available]) 
      HAVE_ID3LIB="yes"
      AC_SUBST([HAVE_ID3LIB])
   fi
])
