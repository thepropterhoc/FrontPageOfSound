#include "opus.h"

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

static PyObject*
OpusDecoder_new(PyTypeObject *type,
                PyObject *args, PyObject *kwds)
{
    decoders_OpusDecoder *self;

    self = (decoders_OpusDecoder *)type->tp_alloc(type, 0);

    return (PyObject *)self;
}

int
OpusDecoder_init(decoders_OpusDecoder *self,
                 PyObject *args, PyObject *kwds)
{
    char *filename;
    int error;

    self->opus_file = NULL;
    self->audiotools_pcm = NULL;
    self->channels = NULL;
    self->closed = 0;

    if (!PyArg_ParseTuple(args, "s", &filename))
        return -1;

    if ((self->opus_file = op_open_file(filename, &error)) == NULL) {
        PyErr_SetString(PyExc_ValueError, "error opening Opus file");
        return -1;
    }

    self->channel_count = op_channel_count(self->opus_file, -1);

    if ((self->audiotools_pcm = open_audiotools_pcm()) == NULL)
        return -1;

    self->channels = aa_int_new();

    return 0;
}

void
OpusDecoders_dealloc(decoders_OpusDecoder *self)
{
    if (self->opus_file != NULL)
        op_free(self->opus_file);

    Py_XDECREF(self->audiotools_pcm);

    if (self->channels != NULL)
        self->channels->del(self->channels);

    Py_TYPE(self)->tp_free((PyObject*)self);
}

/*the OpusDecoder.sample_rate attribute getter*/
static PyObject*
OpusDecoder_sample_rate(decoders_OpusDecoder *self, void *closure)
{
    /*always 48 kHz*/
    const int sample_rate = 48000;

    return Py_BuildValue("i", sample_rate);
}

/*the OpusDecoder.bits_per_sample attribute getter*/
static PyObject*
OpusDecoder_bits_per_sample(decoders_OpusDecoder *self, void *closure)
{
    /*always 16 bps*/
    const int bits_per_sample = 16;

    return Py_BuildValue("i", bits_per_sample);
}

/*the OpusDecoder.channels attribute getter*/
static PyObject*
OpusDecoder_channels(decoders_OpusDecoder *self, void *closure)
{
    return Py_BuildValue("i", self->channel_count);
}

/*the OpusDecoder.channel_mask attribute getter*/
static PyObject*
OpusDecoder_channel_mask(decoders_OpusDecoder *self, void *closure)
{
    /*use same channel mapping as Ogg Vorbis*/
    int channel_mask;

    enum {
        fL  = 0x1,
        fR  = 0x2,
        fC  = 0x4,
        LFE = 0x8,
        bL  = 0x10,
        bR  = 0x20,
        bC  = 0x100,
        sL  = 0x200,
        sR  = 0x400
    };

    switch (self->channel_count) {
    case 1:
        /*fC*/
        channel_mask = fC;
        break;
    case 2:
        /*fL fR*/
        channel_mask = fL | fR;
        break;
    case 3:
        /*fL fR fC*/
        channel_mask = fL | fR | fC;
        break;
    case 4:
        /*fL fR bL bR*/
        channel_mask = fL | fR | bL | bR;
        break;
    case 5:
        /*fL fR fC bL bR*/
        channel_mask = fL | fR | fC | bL | bR;
        break;
    case 6:
        /*fL fR fC LFE bL bR*/
        channel_mask = fL | fR | fC | LFE | bL | bR;
        break;
    case 7:
        /*fL fR fC LFE bC sL sR*/
        channel_mask = fL | fR | fC | LFE | bC | sL | sR;
        break;
    case 8:
        /*fL fR fC LFE bL bR sL sR*/
        channel_mask = fL | fR | fC | LFE | bL | bR | sL | sR;
        break;
    default:
        /*undefined*/
        channel_mask = 0x0;
        break;
    }

    return Py_BuildValue("i", channel_mask);
}

/*assume at least 120ms across 8 channels, minimum*/
#define BUF_SIZE 5760 * 8

/*the OpusDecoder.read() method*/
static PyObject*
OpusDecoder_read(decoders_OpusDecoder* self, PyObject *args)
{
    static opus_int16 pcm[BUF_SIZE];
    int pcm_frames_read;

    if (self->closed) {
        PyErr_SetString(PyExc_ValueError, "stream is closed");
        return NULL;
    }

    if ((pcm_frames_read = op_read(self->opus_file,
                                   pcm,
                                   BUF_SIZE,
                                   NULL)) >= 0) {
        const int channel_count = op_head(self->opus_file, -1)->channel_count;
        aa_int *channels = self->channels;
        int c;

        channels->reset(channels);

        /*split buffer by channel*/
        for (c = 0; c < channel_count; c++) {
            a_int *channel = channels->append(channels);
            int i;

            channel->resize(channel, pcm_frames_read);
            for (i = 0; i < pcm_frames_read; i++) {
                a_append(channel, pcm[c + (i * channel_count)]);
            }
        }

        /*reorder channels to .wav order if necessary*/
        switch (channel_count) {
        case 1:
        case 2:
        default:
            /*no change*/
            break;
        case 3:
            /*fL fC fR -> fL fR fC*/
            a_int_swap(channels->_[1], channels->_[2]);
            break;
        case 4:
            /*fL fR bL bR -> fL fR bL bR*/
            /*no change*/
            break;
        case 5:
            /*fL fC fR bL bR -> fL fR fC bL bR*/
            a_int_swap(channels->_[1], channels->_[2]);
            break;
        case 6:
            /*fL fC fR bL bR LFE -> fL fR fC bL bR LFE*/
            a_int_swap(channels->_[1], channels->_[2]);

            /*fL fR fC bL bR LFE -> fL fR fC LFE bR bL*/
            a_int_swap(channels->_[3], channels->_[5]);

            /*fL fR fC LFE bR bL -> fL fR fC LFE bL bR*/
            a_int_swap(channels->_[4], channels->_[5]);
            break;
        case 7:
            /*fL fC fR sL sR bC LFE -> fL fR fC sL sR bC LFE*/
            a_int_swap(channels->_[1], channels->_[2]);

            /*fL fR fC sL sR bC LFE -> fL fR fC LFE sR bC sL*/
            a_int_swap(channels->_[3], channels->_[6]);

            /*fL fR fC LFE sR bC sL -> fL fR fC LFE bC sR sL*/
            a_int_swap(channels->_[4], channels->_[5]);

            /*fL fR fC LFE bC sR sL -> fL fR fC LFE bC sL sR*/
            a_int_swap(channels->_[5], channels->_[6]);
            break;
        case 8:
            /*fL fC fR sL sR bL bR LFE -> fL fR fC sL sR bL bR LFE*/
            a_int_swap(channels->_[1], channels->_[2]);

            /*fL fR fC sL sR bL bR LFE -> fL fR fC LFE sR bL bR sL*/
            a_int_swap(channels->_[3], channels->_[6]);

            /*fL fR fC LFE sR bL bR sL -> fL fR fC LFE bL sR bR sL*/
            a_int_swap(channels->_[4], channels->_[5]);

            /*fL fR fC LFE bL sR bR sL -> fL fR fC LFE bL bR sR sL*/
            a_int_swap(channels->_[5], channels->_[6]);

            /*fL fR fC LFE bL bR sR sL -> fL fR fC LFE bL bR sL sR*/
            a_int_swap(channels->_[6], channels->_[7]);
            break;
        }

        /*return new FrameList object*/
        return aa_int_to_FrameList(self->audiotools_pcm,
                                   channels,
                                   16);
    } else {
        /*some sort of read error occurred*/
        PyErr_SetString(PyExc_ValueError, "error reading from file");
        return NULL;
    }
}

/*the OpusDecoder.close() method*/
static PyObject*
OpusDecoder_close(decoders_OpusDecoder* self, PyObject *args)
{
    self->closed = 1;
    Py_INCREF(Py_None);
    return Py_None;
}
