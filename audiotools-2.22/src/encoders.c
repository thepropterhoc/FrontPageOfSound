#include <Python.h>
#include "mod_defs.h"
#include "bitstream.h"
#include "encoders.h"

/********************************************************
 Audio Tools, a module and set of tools for manipulating audio data
 Copyright (C) 2007-2014  Brian Langenberger

 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program; if not, write to the Free Software
 Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
*******************************************************/

extern PyTypeObject encoders_ALACEncoderType;

MOD_INIT(encoders)
{
    PyObject* m;

    MOD_DEF(m, "encoders", "low-level audio format encoders",  module_methods)

    encoders_ALACEncoderType.tp_new = PyType_GenericNew;
    if (PyType_Ready(&encoders_ALACEncoderType) < 0)
        return MOD_ERROR_VAL;

    Py_INCREF(&encoders_ALACEncoderType);
    PyModule_AddObject(m, "ALACEncoder",
                       (PyObject *)&encoders_ALACEncoderType);

    return MOD_SUCCESS_VAL(m);
}
