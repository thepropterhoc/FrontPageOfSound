#!/usr/bin/python

# Audio Tools, a module and set of tools for manipulating audio data
# Copyright (C) 2007-2014  Brian Langenberger

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA


from audiotools import (AudioFile, InvalidFile, PCMReader)
from audiotools.pcm import FrameList


class InvalidAU(InvalidFile):
    pass


class AuReader(object):
    def __init__(self, au_filename):
        from audiotools.bitstream import BitstreamReader
        from audiotools.text import (ERR_AU_INVALID_HEADER,
                                     ERR_AU_UNSUPPORTED_FORMAT)

        self.file = open(au_filename, "rb")
        (magic_number,
         self.data_offset,
         data_size,
         encoding_format,
         self.sample_rate,
         self.channels) = BitstreamReader(self.file, 0).parse("4b 5* 32u")

        if (magic_number != '.snd'):
            raise ValueError(ERR_AU_INVALID_HEADER)
        try:
            self.bits_per_sample = {2: 8, 3: 16, 4: 24}[encoding_format]
        except KeyError:
            raise ValueError(ERR_AU_UNSUPPORTED_FORMAT)

        self.channel_mask = {1: 0x4, 2: 0x3}.get(self.channels, 0)
        self.bytes_per_pcm_frame = ((self.bits_per_sample // 8) *
                                    self.channels)
        self.total_pcm_frames = (data_size // self.bytes_per_pcm_frame)
        self.remaining_pcm_frames = self.total_pcm_frames

    def read(self, pcm_frames):
        # try to read requested PCM frames or remaining frames
        requested_pcm_frames = min(max(pcm_frames, 1),
                                   self.remaining_pcm_frames)
        requested_bytes = (self.bytes_per_pcm_frame *
                           requested_pcm_frames)
        pcm_data = self.file.read(requested_bytes)

        # raise exception if data block exhausted early
        if (len(pcm_data) < requested_bytes):
            from audiotools.text import ERR_AU_TRUNCATED_DATA
            raise IOError(ERR_AU_TRUNCATED_DATA)
        else:
            self.remaining_pcm_frames -= requested_pcm_frames

            # return parsed chunk
            return FrameList(pcm_data,
                             self.channels,
                             self.bits_per_sample,
                             True,
                             True)

    def seek(self, pcm_frame_offset):
        if (pcm_frame_offset < 0):
            from audiotools.text import ERR_NEGATIVE_SEEK
            raise ValueError(ERR_NEGATIVE_SEEK)

        # ensure one doesn't walk off the end of the file
        pcm_frame_offset = min(pcm_frame_offset,
                               self.total_pcm_frames)

        # position file in data block
        self.file.seek(self.data_offset +
                       (pcm_frame_offset *
                        self.bytes_per_pcm_frame), 0)
        self.remaining_pcm_frames = (self.total_pcm_frames -
                                     pcm_frame_offset)

        return pcm_frame_offset

    def close(self):
        self.file.close()


def au_header(sample_rate,
              channels,
              bits_per_sample,
              total_pcm_frames):
    """given a set of integer stream attributes,
    returns header string of entire Au header

    may raise ValueError if the total size of the file is too large"""

    from audiotools.bitstream import build

    if ((channels *
         (bits_per_sample // 8) *
         total_pcm_frames) >= 2 ** 32):
         raise ValueError("PCM data too large for Sun AU file")
    else:
        return build("4b 5*32u",
                     False,
                     (".snd",
                      24,
                      (channels *
                       (bits_per_sample // 8) *
                       total_pcm_frames),
                      {8: 2, 16: 3, 24: 4}[bits_per_sample],
                      sample_rate,
                      channels))


class AuAudio(AudioFile):
    """a Sun AU audio file"""

    SUFFIX = "au"
    NAME = SUFFIX
    DESCRIPTION = u"Sun Au"

    def __init__(self, filename):
        AudioFile.__init__(self, filename)

        from audiotools.bitstream import BitstreamReader
        from audiotools.text import (ERR_AU_INVALID_HEADER,
                                     ERR_AU_UNSUPPORTED_FORMAT)

        try:
            f = open(filename, 'rb')

            (magic_number,
             self.__data_offset__,
             self.__data_size__,
             encoding_format,
             self.__sample_rate__,
             self.__channels__) = BitstreamReader(f, 0).parse("4b 5* 32u")
        except IOError as msg:
            raise InvalidAU(str(msg))

        if (magic_number != '.snd'):
            raise InvalidAU(ERR_AU_INVALID_HEADER)
        try:
            self.__bits_per_sample__ = {2: 8, 3: 16, 4: 24}[encoding_format]
        except KeyError:
            raise InvalidAU(ERR_AU_UNSUPPORTED_FORMAT)

    def lossless(self):
        """returns True"""

        return True

    def bits_per_sample(self):
        """returns an integer number of bits-per-sample this track contains"""

        return self.__bits_per_sample__

    def channels(self):
        """returns an integer number of channels this track contains"""

        return self.__channels__

    def channel_mask(self):
        from audiotools import ChannelMask

        """returns a ChannelMask object of this track's channel layout"""

        if (self.channels() <= 2):
            return ChannelMask.from_channels(self.channels())
        else:
            return ChannelMask(0)

    def sample_rate(self):
        """returns the rate of the track's audio as an integer number of Hz"""

        return self.__sample_rate__

    def total_frames(self):
        """returns the total PCM frames of the track as an integer"""

        return (self.__data_size__ //
                (self.__bits_per_sample__ // 8) //
                self.__channels__)

    def seekable(self):
        """returns True if the file is seekable"""

        return True

    def to_pcm(self):
        """returns a PCMReader object containing the track's PCM data"""

        return AuReader(self.filename)

    def pcm_split(self):
        """returns a pair of data strings before and after PCM data

        the first contains all data before the PCM content of the data chunk
        the second containing all data after the data chunk"""

        import struct

        f = open(self.filename, 'rb')
        (magic_number, data_offset) = struct.unpack(">4sI", f.read(8))
        header = f.read(data_offset - struct.calcsize(">4sI"))
        return (struct.pack(">4sI%ds" % (len(header)),
                            magic_number, data_offset, header), "")

    @classmethod
    def from_pcm(cls, filename, pcmreader,
                 compression=None, total_pcm_frames=None):
        """encodes a new file from PCM data

        takes a filename string, PCMReader object,
        optional compression level string and
        optional total_pcm_frames integer
        encodes a new audio file from pcmreader's data
        at the given filename with the specified compression level
        and returns a new AuAudio object"""

        from audiotools import EncodingError
        from audiotools import DecodingError
        from audiotools import CounterPCMReader
        from audiotools import transfer_framelist_data

        if (pcmreader.bits_per_sample not in (8, 16, 24)):
            from audiotools import Filename
            from audiotools import UnsupportedBitsPerSample
            from audiotools.text import ERR_UNSUPPORTED_BITS_PER_SAMPLE
            raise UnsupportedBitsPerSample(
                ERR_UNSUPPORTED_BITS_PER_SAMPLE %
                {"target_filename": Filename(filename),
                 "bps": pcmreader.bits_per_sample})

        try:
            header = au_header(pcmreader.sample_rate,
                               pcmreader.channels,
                               pcmreader.bits_per_sample,
                               total_pcm_frames if total_pcm_frames
                               is not None else 0)
        except ValueError as err:
            raise EncodingError(str(err))

        try:
            f = open(filename, "wb")
        except IOError as err:
            raise EncodingError(str(err))

        counter = CounterPCMReader(pcmreader)
        f.write(header)
        try:
            transfer_framelist_data(counter, f.write, True, True)
        except (IOError, ValueError) as err:
            cls.__unlink__(filename)
            raise EncodingError(str(err))

        if (total_pcm_frames is not None):
            if (total_pcm_frames != counter.frames_written):
                # ensure written number of PCM frames
                # matches total_pcm_frames argument
                from audiotools.text import ERR_TOTAL_PCM_FRAMES_MISMATCH
                cls.__unlink__(filename)
                raise EncodingError(ERR_TOTAL_PCM_FRAMES_MISMATCH)
            else:
                f.close()
        else:
            # go back and rewrite populated header
            # with counted number of PCM frames
            f.seek(0, 0)
            f.write(au_header(pcmreader.sample_rate,
                              pcmreader.channels,
                              pcmreader.bits_per_sample,
                              counter.frames_written))
            f.close()

        return AuAudio(filename)

    @classmethod
    def track_name(cls, file_path, track_metadata=None, format=None,
                   suffix=None):
        """constructs a new filename string

        given a plain string to an existing path,
        a MetaData-compatible object (or None),
        a UTF-8-encoded Python format string
        and an ASCII-encoded suffix string (such as "mp3")
        returns a plain string of a new filename with format's
        fields filled-in and encoded as FS_ENCODING
        raises UnsupportedTracknameField if the format string
        contains invalid template fields"""

        if (format is None):
            format = "track%(track_number)2.2d.au"
        return AudioFile.track_name(file_path, track_metadata, format,
                                    suffix=cls.SUFFIX)
