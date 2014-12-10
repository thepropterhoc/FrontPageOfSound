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

"""the core Python Audio Tools module"""

import sys
import re
import os
import os.path
import ConfigParser
import optparse
import audiotools.pcm as pcm
from functools import total_ordering


class RawConfigParser(ConfigParser.RawConfigParser):
    """extends RawConfigParser to provide additional methods"""

    def get_default(self, section, option, default):
        """returns a default if option is not found in section"""

        try:
            return self.get(section, option)
        except ConfigParser.NoSectionError:
            return default
        except ConfigParser.NoOptionError:
            return default

    def set_default(self, section, option, value):
        try:
            self.set(section, option, value)
        except ConfigParser.NoSectionError:
            self.add_section(section)
            self.set(section, option, value)

    def getint_default(self, section, option, default):
        """returns a default int if option is not found in section"""

        try:
            return self.getint(section, option)
        except ConfigParser.NoSectionError:
            return default
        except ConfigParser.NoOptionError:
            return default

    def getboolean_default(self, section, option, default):
        """returns a default boolean if option is not found in section"""

        try:
            return self.getboolean(section, option)
        except ConfigParser.NoSectionError:
            return default
        except ConfigParser.NoOptionError:
            return default


config = RawConfigParser()
config.read([os.path.join("/etc", "audiotools.cfg"),
             os.path.join(sys.prefix, "etc", "audiotools.cfg"),
             os.path.expanduser('~/.audiotools.cfg')])

BUFFER_SIZE = 0x100000
FRAMELIST_SIZE = 0x100000 // 4


class __system_binaries__(object):
    def __init__(self, config):
        self.config = config

    def __getitem__(self, command):
        try:
            return self.config.get("Binaries", command)
        except ConfigParser.NoSectionError:
            return command
        except ConfigParser.NoOptionError:
            return command

    def can_execute(self, command):
        if (os.sep in command):
            return os.access(command, os.X_OK)
        else:
            for path in os.environ.get('PATH', os.defpath).split(os.pathsep):
                if (os.access(os.path.join(path, command), os.X_OK)):
                    return True
            return False

BIN = __system_binaries__(config)

DEFAULT_CDROM = config.get_default("System", "cdrom", "/dev/cdrom")

FREEDB_SERVICE = config.getboolean_default("FreeDB", "service", True)
FREEDB_SERVER = config.get_default("FreeDB", "server", "us.freedb.org")
FREEDB_PORT = config.getint_default("FreeDB", "port", 80)

MUSICBRAINZ_SERVICE = config.getboolean_default("MusicBrainz", "service", True)
MUSICBRAINZ_SERVER = config.get_default("MusicBrainz", "server",
                                        "musicbrainz.org")
MUSICBRAINZ_PORT = config.getint_default("MusicBrainz", "port", 80)

ADD_REPLAYGAIN = config.getboolean_default("ReplayGain", "add_by_default",
                                           True)

VERSION = "2.22"

DEFAULT_FILENAME_FORMAT = '%(track_number)2.2d - %(track_name)s.%(suffix)s'
FILENAME_FORMAT = config.get_default("Filenames", "format",
                                     DEFAULT_FILENAME_FORMAT)

FS_ENCODING = config.get_default("System", "fs_encoding",
                                 sys.getfilesystemencoding())
if (FS_ENCODING is None):
    FS_ENCODING = 'UTF-8'

IO_ENCODING = config.get_default("System", "io_encoding", "UTF-8")

VERBOSITY_LEVELS = ("quiet", "normal", "debug")
DEFAULT_VERBOSITY = config.get_default("Defaults", "verbosity", "normal")
if (DEFAULT_VERBOSITY not in VERBOSITY_LEVELS):
    DEFAULT_VERBOSITY = "normal"

DEFAULT_TYPE = config.get_default("System", "default_type", "wav")


# field name -> (field string, text description) mapping
def __format_fields__():
    from audiotools.text import (METADATA_TRACK_NAME,
                                 METADATA_TRACK_NUMBER,
                                 METADATA_TRACK_TOTAL,
                                 METADATA_ALBUM_NAME,
                                 METADATA_ARTIST_NAME,
                                 METADATA_PERFORMER_NAME,
                                 METADATA_COMPOSER_NAME,
                                 METADATA_CONDUCTOR_NAME,
                                 METADATA_MEDIA,
                                 METADATA_ISRC,
                                 METADATA_CATALOG,
                                 METADATA_COPYRIGHT,
                                 METADATA_PUBLISHER,
                                 METADATA_YEAR,
                                 METADATA_DATE,
                                 METADATA_ALBUM_NUMBER,
                                 METADATA_ALBUM_TOTAL,
                                 METADATA_COMMENT,
                                 METADATA_SUFFIX,
                                 METADATA_ALBUM_TRACK_NUMBER,
                                 METADATA_BASENAME)
    return {u"track_name": (u"%(track_name)s",
                            METADATA_TRACK_NAME),
            u"track_number": (u"%(track_number)2.2d",
                              METADATA_TRACK_NUMBER),
            u"track_total": (u"%(track_total)d",
                             METADATA_TRACK_TOTAL),
            u"album_name": (u"%(album_name)s",
                            METADATA_ALBUM_NAME),
            u"artist_name": (u"%(artist_name)s",
                             METADATA_ARTIST_NAME),
            u"performer_name": (u"%(performer_name)s",
                                METADATA_PERFORMER_NAME),
            u"composer_name": (u"%(composer_name)s",
                               METADATA_COMPOSER_NAME),
            u"conductor_name": (u"%(conductor_name)s",
                                METADATA_CONDUCTOR_NAME),
            u"media": (u"%(media)s",
                       METADATA_MEDIA),
            u"ISRC": (u"%(ISRC)s",
                      METADATA_ISRC),
            u"catalog": (u"%(catalog)s",
                         METADATA_CATALOG),
            u"copyright": (u"%(copyright)s",
                           METADATA_COPYRIGHT),
            u"publisher": (u"%(publisher)s",
                           METADATA_PUBLISHER),
            u"year": (u"%(year)s",
                      METADATA_YEAR),
            u"date": (u"%(date)s",
                      METADATA_DATE),
            u"album_number": (u"%(album_number)d",
                              METADATA_ALBUM_NUMBER),
            u"album_total": (u"%(album_total)d",
                             METADATA_ALBUM_TOTAL),
            u"comment": (u"%(comment)s",
                         METADATA_COMMENT),
            u"suffix": (u"%(suffix)s",
                        METADATA_SUFFIX),
            u"album_track_number": (u"%(album_track_number)s",
                                    METADATA_ALBUM_TRACK_NUMBER),
            u"basename": (u"%(basename)s",
                          METADATA_BASENAME)}

FORMAT_FIELDS = __format_fields__()
FORMAT_FIELD_ORDER = (u"track_name",
                      u"artist_name",
                      u"album_name",
                      u"track_number",
                      u"track_total",
                      u"album_number",
                      u"album_total",
                      u"performer_name",
                      u"composer_name",
                      u"conductor_name",
                      u"catalog",
                      u"ISRC",
                      u"publisher",
                      u"media",
                      u"year",
                      u"date",
                      u"copyright",
                      u"comment",
                      u"suffix",
                      u"album_track_number",
                      u"basename")


def __default_quality__(audio_type):
    quality = DEFAULT_QUALITY.get(audio_type, "")
    try:
        if (quality not in TYPE_MAP[audio_type].COMPRESSION_MODES):
            return TYPE_MAP[audio_type].DEFAULT_COMPRESSION
        else:
            return quality
    except KeyError:
        return ""


if (config.has_option("System", "maximum_jobs")):
    MAX_JOBS = config.getint_default("System", "maximum_jobs", 1)
else:
    try:
        import multiprocessing
        MAX_JOBS = multiprocessing.cpucount()
    except (ImportError, AttributeError):
        MAX_JOBS = 1


class OptionParser(optparse.OptionParser):
    """extends OptionParser to use IO_ENCODING as text encoding

    this ensures the encoding remains consistent if --help
    output is piped to a pager vs. sent to a tty
    """

    def _get_encoding(self, file):
        return IO_ENCODING

OptionGroup = optparse.OptionGroup


class DummyOutput(object):
    """a writable FILE-like object which generates no output"""

    def __init__(self):
        pass

    def isatty(self):
        return False

    def write(self, s):
        return

    def flush(self):
        return

    def close(self):
        return


class Messenger(object):
    """this class is for displaying formatted output in a consistent way"""

    def __init__(self, executable, options):
        """executable is a plain string of what script is being run

        this is typically for use by the usage() method"""

        self.executable = executable
        if (hasattr(options, "verbosity") and (options.verbosity == "quiet")):
            self.__stdout__ = DummyOutput()
            self.__stderr__ = DummyOutput()
        else:
            self.__stdout__ = sys.stdout
            self.__stderr__ = sys.stderr

    def output_isatty(self):
        return self.__stdout__.isatty()

    def info_isatty(self):
        return self.__stderr__.isatty()

    def error_isatty(self):
        return self.__stderr__.isatty()

    def output(self, s):
        """displays an output message unicode string to stdout

        this appends a newline to that message"""

        self.__stdout__.write(s.encode(IO_ENCODING, 'replace'))
        self.__stdout__.write(os.linesep)

    def partial_output(self, s):
        """displays a partial output message unicode string to stdout

        this flushes output so that message is displayed"""

        self.__stdout__.write(s.encode(IO_ENCODING, 'replace'))
        self.__stdout__.flush()

    def info(self, s):
        """displays an informative message unicode string to stderr

        this appends a newline to that message"""

        self.__stderr__.write(s.encode(IO_ENCODING, 'replace'))
        self.__stderr__.write(os.linesep)

    def partial_info(self, s):
        """displays a partial informative message unicode string to stdout

        this flushes output so that message is displayed"""

        self.__stderr__.write(s.encode(IO_ENCODING, 'replace'))
        self.__stderr__.flush()

    # what's the difference between output() and info() ?
    # output() is for a program's primary data
    # info() is for incidental information
    # for example, trackinfo(1) should use output() for what it displays
    # since that output is its primary function
    # but track2track should use info() for its lines of progress
    # since its primary function is converting audio
    # and tty output is purely incidental

    def error(self, s):
        """displays an error message unicode string to stderr

        this appends a newline to that message"""

        self.__stderr__.write("*** Error: ")
        self.__stderr__.write(s.encode(IO_ENCODING, 'replace'))
        self.__stderr__.write(os.linesep)

    def os_error(self, oserror):
        """displays an properly formatted OSError exception to stderr

        this appends a newline to that message"""

        self.error(u"[Errno %d] %s: '%s'" %
                   (oserror.errno,
                    oserror.strerror.decode('utf-8', 'replace'),
                    Filename(oserror.filename)))

    def warning(self, s):
        """displays a warning message unicode string to stderr

        this appends a newline to that message"""

        self.__stderr__.write("*** Warning: ")
        self.__stderr__.write(s.encode(IO_ENCODING, 'replace'))
        self.__stderr__.write(os.linesep)

    def usage(self, s):
        """displays the program's usage unicode string to stderr

        this appends a newline to that message"""

        self.__stderr__.write("*** Usage: ")
        self.__stderr__.write(self.executable.decode('ascii'))
        self.__stderr__.write(" ")
        self.__stderr__.write(s.encode(IO_ENCODING, 'replace'))
        self.__stderr__.write(os.linesep)

    def ansi_clearline(self):
        """generates a set of clear line ANSI escape codes to stdout

        this works only if stdout is a tty.  Otherwise, it does nothing
        for example:
        >>> msg = Messenger("audiotools")
        >>> msg.partial_output(u"working")
        >>> time.sleep(1)
        >>> msg.ansi_clearline()
        >>> msg.output(u"done")
        """

        if (self.__stdout__.isatty()):
            self.__stdout__.write((u"\u001B[0G" +  # move cursor to column 0
                                   # clear everything after cursor
                                   u"\u001B[0K").encode(IO_ENCODING))
            self.__stdout__.flush()

    def ansi_uplines(self, lines):
        """moves the cursor up by the given number of lines"""

        if (self.__stdout__.isatty()):
            self.__stdout__.write(u"\u001B[%dA" % (lines))
            self.__stdout__.flush()

    def ansi_cleardown(self):
        """clears the remainder of the screen from the cursor downward"""

        if (self.__stdout__.isatty()):
            self.__stdout__.write(u"\u001B[0J")
            self.__stdout__.flush()

    def ansi_clearscreen(self):
        """clears the entire screen and moves cursor to upper left corner"""

        if (self.__stdout__.isatty()):
            self.__stdout__.write(u"\u001B[2J")
            self.__stdout__.write(u"\u001B[1;1H")
            self.__stdout__.flush()

    def terminal_size(self, fd):
        """returns the current terminal size as (height, width)"""

        import fcntl
        import termios
        import struct

        # this isn't all that portable, but will have to do
        return struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))


class SilentMessenger(Messenger):
    def __init__(self):
        self.executable = ""
        self.__stdout__ = DummyOutput()
        self.__stderr__ = DummyOutput()


def khz(hz):
    """given an integer sample rate value in Hz,
    returns a unicode kHz value with suffix

    the string is typically 7-8 characters wide"""

    num = hz // 1000
    den = (hz % 1000) // 100
    if (den == 0):
        return u"%dkHz" % (num)
    else:
        return u"%d.%dkHz" % (num, den)


class output_text(tuple):
    """a class for formatting unicode strings for display"""

    COLORS = {"black",
              "red",
              "green",
              "yellow",
              "blue",
              "magenta",
              "cyan",
              "white"}

    STYLES = {"bold",
              "underline",
              "blink",
              "inverse"}

    def __new__(cls, unicode_string, fg_color=None, bg_color=None, style=None):
        """unicode_string is the text to be displayed

        fg_color and bg_color may be one of:
        'black', 'red', 'green', 'yellow',
        'blue', 'magenta', 'cyan', 'white'

        style may be one of:
        'bold', 'underline', 'blink', 'inverse'
        """

        import unicodedata

        CHAR_WIDTHS = {"Na": 1,
                       "A": 1,
                       "W": 2,
                       "F": 2,
                       "N": 1,
                       "H": 1}

        string = unicodedata.normalize("NFC", unicode(unicode_string))

        return cls.__construct__(
            unicode_string=string,
            char_widths=tuple([CHAR_WIDTHS.get(
                               unicodedata.east_asian_width(char), 1)
                               for char in string]),
            fg_color=fg_color,
            bg_color=bg_color,
            style=style,
            open_codes=cls.__open_codes__(fg_color, bg_color, style),
            close_codes=cls.__close_codes__(fg_color, bg_color, style))

    @classmethod
    def __construct__(cls,
                      unicode_string,
                      char_widths,
                      fg_color,
                      bg_color,
                      style,
                      open_codes,
                      close_codes):
        # 0 - original Unicode string
        # 1 - tuple of widths for each character in string
        # 2 - foreground color string
        # 3 - background color string
        # 4 - style string
        # 5 - open escape codes for TTY output
        # 6 - close escape codes for TTY output

        return tuple.__new__(cls,
                             [unicode(unicode_string),
                              tuple(char_widths),
                              fg_color,
                              bg_color,
                              style,
                              open_codes,
                              close_codes])

    def __repr__(self):
        return "output_text(%s, %s, %s, %s)" % \
            (repr(self[0]),
             repr(self[2]),
             repr(self[3]),
             repr(self[4]))

    @classmethod
    def __open_codes__(cls, fg_color, bg_color, style):
        open_codes = []

        if (fg_color is not None):
            if (fg_color not in cls.COLORS):
                raise ValueError("invalid fg_color %s" % (repr(fg_color)))
            else:
                open_codes.append({"black": 30,
                                   "red": 31,
                                   "green": 32,
                                   "yellow": 33,
                                   "blue": 34,
                                   "magenta": 35,
                                   "cyan": 36,
                                   "white": 37}[fg_color])

        if (bg_color is not None):
            if (bg_color not in cls.COLORS):
                raise ValueError("invalid bg_color %s" % (repr(bg_color)))
            else:
                open_codes.append({"black": 40,
                                   "red": 41,
                                   "green": 42,
                                   "yellow": 43,
                                   "blue": 44,
                                   "magenta": 45,
                                   "cyan": 46,
                                   "white": 47}[bg_color])

        if (style is not None):
            if (style not in cls.STYLES):
                raise ValueError("invalid style %s" % (repr(style)))
            else:
                open_codes.append({"bold": 1,
                                   "underline": 4,
                                   "blink": 5,
                                   "inverse": 7}[style])

        if (len(open_codes) > 0):
            return u"\u001B[%sm" % (u";".join(map(unicode, open_codes)))
        else:
            return u""

    @classmethod
    def __close_codes__(cls, fg_color, bg_color, style):
        close_codes = []

        if (fg_color is not None):
            if (fg_color not in cls.COLORS):
                raise ValueError("invalid fg_color %s" % (repr(fg_color)))
            else:
                close_codes.append(39)

        if (bg_color is not None):
            if (bg_color not in cls.COLORS):
                raise ValueError("invalid bg_color %s" % (repr(bg_color)))
            else:
                close_codes.append(49)

        if (style is not None):
            if (style not in cls.STYLES):
                raise ValueError("invalid style %s" % (repr(style)))
            else:
                close_codes.append({"bold": 22,
                                    "underline": 24,
                                    "blink": 25,
                                    "inverse": 27}[style])

        if (len(close_codes) > 0):
            return u"\u001B[%sm" % (u";".join(map(unicode, close_codes)))
        else:
            return u""

    def __unicode__(self):
        return self[0]

    def __len__(self):
        return sum(self[1])

    def fg_color(self):
        """returns the foreground color as a string, or None"""

        return self[2]

    def bg_color(self):
        """returns the background color as a string, or None"""

        return self[3]

    def style(self):
        """returns the style as a string, or None"""

        return self[4]

    def set_format(self, fg_color=None, bg_color=None, style=None):
        """returns a new output_text with the given format"""

        return output_text.__construct__(
            unicode_string=self[0],
            char_widths=self[1],
            fg_color=fg_color,
            bg_color=bg_color,
            style=style,
            open_codes=output_text.__open_codes__(fg_color,
                                                  bg_color,
                                                  style),
            close_codes=output_text.__close_codes__(fg_color,
                                                    bg_color,
                                                    style))

    def has_formatting(self):
        """returns True if the text has formatting set"""

        return ((self[2] is not None) or
                (self[3] is not None) or
                (self[4] is not None))

    def format(self, is_tty=False):
        """returns unicode text formatted depending on is_tty"""

        if (is_tty and self.has_formatting()):
            return u"%s%s%s" % (self[5], self[0], self[6])
        else:
            return self[0]

    def head(self, display_characters):
        """returns a text object truncated to the given length

        characters at the end of the string are removed as needed

        due to double-width characters,
        the size of the string may be smaller than requested"""

        if (display_characters < 0):
            raise ValueError("display characters must be >= 0")

        output_chars = []
        output_widths = []

        for (char, width) in zip(self[0], self[1]):
            if (width <= display_characters):
                output_chars.append(char)
                output_widths.append(width)
                display_characters -= width
            else:
                break

        return output_text.__construct__(
            unicode_string=u"".join(output_chars),
            char_widths=output_widths,
            fg_color=self[2],
            bg_color=self[3],
            style=self[4],
            open_codes=self[5],
            close_codes=self[6])

    def tail(self, display_characters):
        """returns a text object truncated to the given length

        characters at the beginning of the string are removed as needed

        due to double-width characters,
        the size of the string may be smaller than requested"""

        if (display_characters < 0):
            raise ValueError("display characters must be >= 0")

        output_chars = []
        output_widths = []

        for (char, width) in zip(reversed(self[0]),
                                 reversed(self[1])):
            if (width <= display_characters):
                output_chars.append(char)
                output_widths.append(width)
                display_characters -= width
            else:
                break

        return output_text.__construct__(
            unicode_string=u"".join(reversed(output_chars)),
            char_widths=reversed(output_widths),
            fg_color=self[2],
            bg_color=self[3],
            style=self[4],
            open_codes=self[5],
            close_codes=self[6])

    def split(self, display_characters):
        """returns a tuple of text objects

        the first is up to 'display_characters' in length
        the second contains the remainder of the string

        due to double-width characters,
        the first string may be smaller than requested"""

        if (display_characters < 0):
            raise ValueError("display characters must be >= 0")

        head_chars = []
        head_widths = []
        tail_chars = []
        tail_widths = []
        for (char, width) in zip(self[0], self[1]):
            if (width <= display_characters):
                head_chars.append(char)
                head_widths.append(width)
                display_characters -= width
            else:
                tail_chars.append(char)
                tail_widths.append(width)
                display_characters = -1

        return (output_text.__construct__(unicode_string=u"".join(head_chars),
                                          char_widths=head_widths,
                                          fg_color=self[2],
                                          bg_color=self[3],
                                          style=self[4],
                                          open_codes=self[5],
                                          close_codes=self[6]),
                output_text.__construct__(unicode_string=u"".join(tail_chars),
                                          char_widths=tail_widths,
                                          fg_color=self[2],
                                          bg_color=self[3],
                                          style=self[4],
                                          open_codes=self[5],
                                          close_codes=self[6]))

    def join(self, output_texts):
        """returns output_list joined by our formatted text"""

        def join_iter(texts):
            first_sent = False
            for text in texts:
                if (not first_sent):
                    yield text
                    first_sent = True
                else:
                    yield self
                    yield text

        return output_list(join_iter(output_texts))


class output_list(output_text):
    """a class for formatting multiple unicode strings as a unit

    Note that a styled list enclosing styled text isn't likely
    to nest as expected since styles are reset to the terminal default
    rather than to what they were initially.

    So it's best to either style the internal elements
    or style the list, but not both."""

    def __new__(cls, output_texts, fg_color=None, bg_color=None, style=None):
        """output_texts is an iterable of output_text objects or unicode"""

        return cls.__construct__(
            output_texts=[t if isinstance(t, output_text) else
                          output_text(t) for t in output_texts],
            fg_color=fg_color,
            bg_color=bg_color,
            style=style,
            open_codes=cls.__open_codes__(fg_color, bg_color, style),
            close_codes=cls.__close_codes__(fg_color, bg_color, style))

    @classmethod
    def __construct__(cls,
                      output_texts,
                      fg_color,
                      bg_color,
                      style,
                      open_codes,
                      close_codes):
        # 0 - list of output_text objects
        # 1 - foreground color string
        # 2 - background color string
        # 3 - style string
        # 4 - open escape codes for TTY output
        # 5 - close escape code for TTY output
        return tuple.__new__(cls,
                             [tuple(output_texts),
                              fg_color,
                              bg_color,
                              style,
                              open_codes,
                              close_codes])

    def __repr__(self):
        return "output_list(%s, %s, %s, %s)" % \
            (repr(self[0]),
             repr(self[1]),
             repr(self[2]),
             repr(self[3]))

    def __unicode__(self):
        return u"".join(map(unicode, self[0]))

    def __len__(self):
        return sum(map(len, self[0]))

    def fg_color(self):
        """returns the foreground color as a string"""

        return self[1]

    def bg_color(self):
        """returns the background color as a string"""

        return self[2]

    def style(self):
        """returns the style as a string"""

        return self[3]

    def set_format(self, fg_color=None, bg_color=None, style=None):
        """returns a new output_list with the given format"""

        return output_list.__construct__(
            output_texts=self[0],
            fg_color=fg_color,
            bg_color=bg_color,
            style=style,
            open_codes=output_list.__open_codes__(fg_color,
                                                  bg_color,
                                                  style),
            close_codes=output_list.__close_codes__(fg_color,
                                                    bg_color,
                                                    style))

    def has_formatting(self):
        """returns True if the output_list itself has formatting set"""

        return ((self[1] is not None) or
                (self[2] is not None) or
                (self[3] is not None))

    def format(self, is_tty=False):
        """returns unicode text formatted depending on is_tty"""

        # display escape codes around entire list
        # or on individual text items
        # but not both

        if (is_tty and self.has_formatting()):
            return u"%s%s%s" % (
                self[4],
                u"".join([t.format(False) for t in self[0]]),
                self[5])
        else:
            return u"".join([t.format(is_tty) for t in self[0]])

    def head(self, display_characters):
        """returns a text object truncated to the given length

        characters at the end of the string are removed as needed

        due to double-width characters,
        the size of the string may be smaller than requested"""

        if (display_characters < 0):
            raise ValueError("display characters must be >= 0")

        output_texts = []

        for text in self[0]:
            if (len(text) <= display_characters):
                output_texts.append(text)
                display_characters -= len(text)
            else:
                output_texts.append(text.head(display_characters))
                break

        return output_list.__construct__(
            output_texts=output_texts,
            fg_color=self[1],
            bg_color=self[2],
            style=self[3],
            open_codes=self[4],
            close_codes=self[5])

    def tail(self, display_characters):
        """returns a text object truncated to the given length

        characters at the beginning of the string are removed as needed

        due to double-width characters,
        the size of the string may be smaller than requested"""

        if (display_characters < 0):
            raise ValueError("display characters must be >= 0")

        output_texts = []

        for text in reversed(self[0]):
            if (len(text) <= display_characters):
                output_texts.append(text)
                display_characters -= len(text)
            else:
                output_texts.append(text.tail(display_characters))
                break

        return output_list.__construct__(
            output_texts=reversed(output_texts),
            fg_color=self[1],
            bg_color=self[2],
            style=self[3],
            open_codes=self[4],
            close_codes=self[5])

    def split(self, display_characters):
        """returns a tuple of text objects

        the first is up to 'display_characters' in length
        the second contains the remainder of the string

        due to double-width characters,
        the first string may be smaller than requested
        """

        if (display_characters < 0):
            raise ValueError("display characters must be >= 0")

        head_texts = []
        tail_texts = []

        for text in self[0]:
            if (len(text) <= display_characters):
                head_texts.append(text)
                display_characters -= len(text)
            elif (display_characters >= 0):
                (head, tail) = text.split(display_characters)
                head_texts.append(head)
                tail_texts.append(tail)
                display_characters = -1
            else:
                tail_texts.append(text)

        return (output_list.__construct__(output_texts=head_texts,
                                          fg_color=self[1],
                                          bg_color=self[2],
                                          style=self[3],
                                          open_codes=self[4],
                                          close_codes=self[5]),
                output_list.__construct__(output_texts=tail_texts,
                                          fg_color=self[1],
                                          bg_color=self[2],
                                          style=self[3],
                                          open_codes=self[4],
                                          close_codes=self[5]))


class output_table(object):
    def __init__(self):
        """a class for formatting rows for display"""

        self.__rows__ = []

    def row(self):
        """returns a output_table_row object which columns can be added to"""

        row = output_table_row()
        self.__rows__.append(row)
        return row

    def blank_row(self):
        """inserts a blank table row with no output"""

        self.__rows__.append(output_table_blank())

    def divider_row(self, dividers):
        """adds a row of unicode divider characters

        there should be one character in dividers per output column"""

        self.__rows__.append(output_table_divider(dividers))

    def format(self, is_tty=False):
        """yields one unicode formatted string per row depending on is_tty"""

        if (len(self.__rows__) == 0):
            # no rows, so do nothing
            return

        row_columns = {len(r) for r in self.__rows__ if
                       not isinstance(r, output_table_blank)}

        if (len(row_columns) == 0):
            # all rows are blank
            for row in self.__rows__:
                # blank rows ignore column widths
                yield row.format(None, is_tty)
        elif (len(row_columns) == 1):
            column_widths = [
                max([row.column_width(col) for row in self.__rows__])
                for col in
                range(len([r for r in self.__rows__ if
                           not isinstance(r, output_table_blank)][0]))]

            for row in self.__rows__:
                yield row.format(column_widths, is_tty)
        else:
            raise ValueError("all rows must have same number of columns")


class output_table_row(object):
    def __init__(self):
        """a class for formatting columns for display"""

        self.__columns__ = []

    def __len__(self):
        return len(self.__columns__)

    def add_column(self, text, alignment="left"):
        """adds text, which may be unicode or a formatted output_text object

        alignment may be 'left', 'center', 'right'"""

        if (alignment not in ("left", "center", "right")):
            raise ValueError("alignment must be 'left', 'center', or 'right'")

        self.__columns__.append(
            (text if isinstance(text, output_text) else output_text(text),
             alignment))

    def column_width(self, column):
        return len(self.__columns__[column][0])

    def format(self, column_widths, is_tty=False):
        """returns formatted row as unicode"""

        def align_left(text, width, is_tty):
            spaces = width - len(text)

            if (spaces > 0):
                return text.format(is_tty) + u" " * spaces
            else:
                return text.format(is_tty)

        def align_right(text, width, is_tty):
            spaces = width - len(text)

            if (spaces > 0):
                return u" " * spaces + text.format(is_tty)
            else:
                return text.format(is_tty)

        def align_center(text, width, is_tty):
            left_spaces = (width - len(text)) // 2
            right_spaces = width - (left_spaces + len(text))

            if ((left_spaces + right_spaces) > 0):
                return (u" " * left_spaces +
                        text.format(is_tty) +
                        u" " * right_spaces)
            else:
                return text.format(is_tty)

        # attribute to method mapping
        align_meth = {"left": align_left,
                      "right": align_right,
                      "center": align_center}

        assert(len(column_widths) == len(self.__columns__))

        return u"".join([align_meth[alignment](text, width, is_tty)
                         for ((text, alignment), width) in
                         zip(self.__columns__, column_widths)]).rstrip()


class output_table_divider(object):
    """a class for formatting a row of divider characters"""

    def __init__(self, dividers):
        self.__dividers__ = dividers[:]

    def __len__(self):
        return len(self.__dividers__)

    def column_width(self, column):
        return 0

    def format(self, column_widths, is_tty=False):
        """returns formatted row as unicode"""

        assert(len(column_widths) == len(self.__dividers__))

        return u"".join([divider * width
                         for (divider, width) in
                         zip(self.__dividers__, column_widths)]).rstrip()


class output_table_blank(object):
    """a class for an empty table row"""

    def __init__(self):
        pass

    def column_width(self, column):
        return 0

    def format(self, column_widths, is_tty=False):
        """returns formatted row as unicode"""

        return u""


class ProgressDisplay(object):
    """a class for displaying incremental progress updates to the screen"""

    def __init__(self, messenger):
        """takes a Messenger object for displaying output"""

        self.messenger = messenger
        self.progress_rows = []
        self.empty_slots = []
        self.displayed_rows = 0

    def add_row(self, output_line):
        """returns ProgressRow to be displayed

        output_line is a unicode string"""

        if (len(self.empty_slots) == 0):
            # no slots to reuse, so append new row
            index = len(self.progress_rows)
            row = ProgressRow(self, index, output_line)
            self.progress_rows.append(row)
            return row
        else:
            # reuse first available slot
            index = self.empty_slots.pop(0)
            row = ProgressRow(self, index, output_line)
            self.progress_rows[index] = row
            return row

    def remove_row(self, row_index):
        """removes the given row index and frees the slot for reuse"""

        self.empty_slots.append(row_index)
        self.progress_rows[row_index] = None

    def display_rows(self):
        """outputs the current state of all progress rows"""

        if (sys.stdout.isatty()):
            (screen_height,
             screen_width) = self.messenger.terminal_size(sys.stdout)

            for row in self.progress_rows:
                if (((row is not None) and
                     (self.displayed_rows < screen_height))):
                    self.messenger.output(row.unicode(screen_width))
                    self.displayed_rows += 1

    def clear_rows(self):
        """clears all previously displayed output rows, if any"""

        if (sys.stdout.isatty() and (self.displayed_rows > 0)):
            self.messenger.ansi_clearline()
            self.messenger.ansi_uplines(self.displayed_rows)
            self.messenger.ansi_cleardown()
            self.displayed_rows = 0

    def output_line(self, line):
        """displays a line of text to the Messenger's output
        after any previous rows have been cleared
        and before any new rows have been displayed"""

        self.messenger.output(line)


class ProgressRow(object):
    """a class for displaying a single row of progress output

    it should be returned from ProgressDisplay.add_row()
    rather than instantiated directly"""

    def __init__(self, progress_display, row_index, output_line):
        """progress_display is a ProgressDisplay object

        row_index is this row's output index

        output_line is a unicode string"""

        from time import time

        self.progress_display = progress_display
        self.row_index = row_index
        self.output_line = output_text(output_line)
        self.current = 0
        self.total = 1
        self.start_time = time()

    def update(self, current, total):
        """updates our row with the current progress values"""

        self.current = min(current, total)
        self.total = total

    def finish(self):
        """indicate output is finished and the row will no longer be needed"""

        self.progress_display.remove_row(self.row_index)

    def unicode(self, width):
        """returns a unicode string formatted to the given width"""

        from time import time

        try:
            time_spent = time() - self.start_time

            split_point = (width * self.current) // self.total
            estimated_total_time = (time_spent * self.total) / self.current
            estimated_time_remaining = int(round(estimated_total_time -
                                                 time_spent))
            time_remaining = u" %2.1d:%2.2d" % (estimated_time_remaining // 60,
                                                estimated_time_remaining % 60)
        except ZeroDivisionError:
            split_point = 0
            time_remaining = u" --:--"

        if (len(self.output_line) + len(time_remaining) > width):
            # truncate output line and append time remaining
            truncated = self.output_line.tail(
                width - (len(time_remaining) + 1))
            combined_line = output_list(
                # note that "truncated" may be smaller than expected
                # so pad with more ellipsises if needed
                [u"\u2026" * (width - (len(truncated) +
                                       len(time_remaining))),
                 truncated,
                 time_remaining])
        else:
            # add padding between output line and time remaining
            combined_line = output_list(
                [self.output_line,
                 u" " * (width - (len(self.output_line) +
                                  len(time_remaining))),
                 time_remaining])

        # turn whole line into progress bar
        (head, tail) = combined_line.split(split_point)

        return (head.set_format(fg_color="white",
                                bg_color="blue").format(True) +
                tail.format(True))


class SingleProgressDisplay(ProgressDisplay):
    """a specialized ProgressDisplay for handling a single line of output"""

    def __init__(self, messenger, progress_text):
        """takes a Messenger class and unicode string for output"""

        ProgressDisplay.__init__(self, messenger)
        self.row = self.add_row(progress_text)

        from time import time

        self.time = time
        self.last_updated = 0

    def update(self, current, total):
        """updates the output line with new current and total values"""

        now = self.time()
        if ((now - self.last_updated) > 0.25):
            self.clear_rows()
            self.row.update(current, total)
            self.display_rows()
            self.last_updated = now


class ReplayGainProgressDisplay(ProgressDisplay):
    """a specialized ProgressDisplay for handling ReplayGain application"""

    def __init__(self, messenger):
        """takes a Messenger and whether ReplayGain is lossless or not"""

        ProgressDisplay.__init__(self, messenger)

        from time import time
        from audiotools.text import RG_ADDING_REPLAYGAIN

        self.time = time
        self.last_updated = 0

        self.row = self.add_row(RG_ADDING_REPLAYGAIN)

        if (sys.stdout.isatty()):
            self.initial_message = self.initial_message_tty
            self.update = self.update_tty
            self.final_message = self.final_message_tty
        else:
            self.initial_message = self.initial_message_nontty
            self.update = self.update_nontty
            self.final_message = self.final_message_nontty

    def initial_message_tty(self):
        """displays a message that ReplayGain application has started"""

        pass

    def initial_message_nontty(self):
        """displays a message that ReplayGain application has started"""

        from audiotools.text import RG_ADDING_REPLAYGAIN_WAIT

        self.messenger.info(RG_ADDING_REPLAYGAIN_WAIT)

    def update_tty(self, current, total):
        """updates the current status of ReplayGain application"""

        now = self.time()
        if ((now - self.last_updated) > 0.25):
            self.clear_rows()
            self.row.update(current, total)
            self.display_rows()
            self.last_updated = now

    def update_nontty(self, current, total):
        """updates the current status of ReplayGain application"""

        pass

    def final_message_tty(self):
        """displays a message that ReplayGain application is complete"""

        from audiotools.text import RG_REPLAYGAIN_ADDED

        self.clear_rows()
        self.messenger.info(RG_REPLAYGAIN_ADDED)

    def final_message_nontty(self):
        """displays a message that ReplayGain application is complete"""

        pass


class UnsupportedFile(Exception):
    """raised by open() if the file can be opened but not identified"""

    pass


class InvalidFile(Exception):
    """raised during initialization if the file is invalid in some way"""

    pass


class EncodingError(IOError):
    """raised if an audio file cannot be created correctly from from_pcm()
    due to an error by the encoder"""

    def __init__(self, error_message):
        IOError.__init__(self)
        self.error_message = error_message

    def __reduce__(self):
        return (EncodingError, (self.error_message, ))

    def __str__(self):
        if (isinstance(self.error_message, unicode)):
            return self.error_message.encode('ascii', 'replace')
        else:
            return str(self.error_message)

    def __unicode__(self):
        return unicode(self.error_message)


class UnsupportedChannelMask(EncodingError):
    """raised if the encoder does not support the file's channel mask"""

    def __init__(self, filename, mask):
        from audiotools.text import ERR_UNSUPPORTED_CHANNEL_MASK

        EncodingError.__init__(
            self,
            ERR_UNSUPPORTED_CHANNEL_MASK %
            {"target_filename": Filename(filename),
             "assignment": ChannelMask(mask)})


class UnsupportedChannelCount(EncodingError):
    """raised if the encoder does not support the file's channel count"""

    def __init__(self, filename, count):
        from audiotools.text import ERR_UNSUPPORTED_CHANNEL_COUNT

        EncodingError.__init__(
            self,
            ERR_UNSUPPORTED_CHANNEL_COUNT %
            {"target_filename": Filename(filename),
             "channels": count})


class UnsupportedBitsPerSample(EncodingError):
    """raised if the encoder does not support the file's bits-per-sample"""

    def __init__(self, filename, bits_per_sample):
        from audiotools.text import ERR_UNSUPPORTED_BITS_PER_SAMPLE

        EncodingError.__init__(
            self,
            ERR_UNSUPPORTED_BITS_PER_SAMPLE %
            {"target_filename": Filename(filename),
             "bps": bits_per_sample})


class DecodingError(IOError):
    """raised if the decoder exits with an error

    typically, a from_pcm() method will catch this error
    and raise EncodingError"""

    def __init__(self, error_message):
        IOError.__init__(self)
        self.error_message = error_message


def file_type(file):
    """given a seekable file stream
    returns an AudioFile-compatible class that stream is a type of
    or None of the stream's type is unknown

    the AudioFile class is not guaranteed to be available"""

    start = file.tell()
    header = file.read(37)
    file.seek(start, 0)

    if ((header[4:8] == "ftyp") and (header[8:12] in ('mp41',
                                                      'mp42',
                                                      'M4A ',
                                                      'M4B '))):

        # possibly ALAC or M4A

        from audiotools.bitstream import BitstreamReader
        from audiotools.m4a import get_m4a_atom

        reader = BitstreamReader(file, 0)

        # so get contents of moov->trak->mdia->minf->stbl->stsd atom
        try:
            stsd = get_m4a_atom(reader,
                                "moov", "trak", "mdia",
                                "minf", "stbl", "stsd")[1]
            (stsd_version, descriptions,
             atom_size, atom_type) = stsd.parse("8u 24p 32u 32u 4b")

            if (atom_type == "alac"):
                # if first description is "alac" atom, it's an ALAC
                return ALACAudio
            elif (atom_type == "mp4a"):
                # if first description is "mp4a" atom, it's M4A
                return M4AAudio
            else:
                # otherwise, it's unknown
                return None
        except KeyError:
            # no stsd atom, so unknown
            return None
        except IOError:
            # error reading atom, so unknown
            return None
    elif ((header[0:4] == "FORM") and (header[8:12] == "AIFF")):
        return AiffAudio
    elif (header[0:4] == ".snd"):
        return AuAudio
    elif (header[0:4] == "fLaC"):
        return FlacAudio
    elif ((len(header) >= 4) and (header[0] == "\xFF")):
        # possibly MP3 or MP2

        from audiotools.bitstream import parse

        # header is at least 32 bits, so no IOError is possible
        (frame_sync,
         mpeg_id,
         layer_description,
         protection,
         bitrate,
         sample_rate,
         pad,
         private,
         channels,
         mode_extension,
         copy,
         original,
         emphasis) = parse("11u 2u 2u 1u 4u 2u 1u " +
                           "1u 2u 2u 1u 1u 2u", False, header)
        if (((frame_sync == 0x7FF) and
             (mpeg_id == 3) and
             (layer_description == 1) and
             (bitrate != 0xF) and
             (sample_rate != 3) and
             (emphasis != 2))):
            # MP3s are MPEG-1, Layer-III
            return MP3Audio
        elif ((frame_sync == 0x7FF) and
              (mpeg_id == 3) and
              (layer_description == 2) and
              (bitrate != 0xF) and
              (sample_rate != 3) and
              (emphasis != 2)):
            # MP2s are MPEG-1, Layer-II
            return MP2Audio
        else:
            # nothing else starts with an initial byte of 0xFF
            # so the file is unknown
            return None
    elif (header[0:4] == "OggS"):
        # possibly Ogg FLAC, Ogg Vorbis or Ogg Opus
        if (header[0x1C:0x21] == "\x7FFLAC"):
            return OggFlacAudio
        elif (header[0x1C:0x23] == "\x01vorbis"):
            return VorbisAudio
        elif (header[0x1C:0x26] == "OpusHead\x01"):
            return OpusAudio
        else:
            return None
    elif (header[0:5] == "ajkg\x02"):
        return ShortenAudio
    elif (header[0:4] == "wvpk"):
        return WavPackAudio
    elif ((header[0:4] == "RIFF") and (header[8:12] == "WAVE")):
        return WaveAudio
    elif ((len(header) >= 10) and
          (header[0:3] == "ID3") and
          (ord(header[3]) in (2, 3, 4))):
        # file contains ID3v2 tag
        # so it may be MP3, MP2, FLAC or TTA

        # determine sync-safe tag size and skip entire tag
        tag_size = 0
        for b in header[6:10]:
            tag_size = (tag_size << 7) | (ord(b) & 0x7F)
        file.seek(start + 10 + tag_size, 0)

        t = file_type(file)
        # only return type which might be wrapped in ID3v2 tags
        if (((t is None) or
             (t is MP3Audio) or
             (t is MP2Audio) or
             (t is FlacAudio) or
             (t is TrueAudio))):
            return t
        else:
            return None
    elif (header[0:4] == "TTA1"):
        return TrueAudio
    else:
        return None


# save a reference to Python's regular open function
__open__ = open


def open(filename):
    """returns an AudioFile located at the given filename path

    this works solely by examining the file's contents
    after opening it
    raises UnsupportedFile if it's not a file we support based on its headers
    raises InvalidFile if the file appears to be something we support,
    but has errors of some sort
    raises IOError if some problem occurs attempting to open the file
    """

    f = __open__(filename, "rb")
    try:
        audio_class = file_type(f)
        if ((audio_class is not None) and audio_class.available(BIN)):
            return audio_class(filename)
        else:
            raise UnsupportedFile(filename)
    finally:
        f.close()


class DuplicateFile(Exception):
    """raised if the same file is included more than once"""

    def __init__(self, filename):
        """filename is a Filename object"""

        self.filename = filename

    def __unicode__(self):
        from audiotools.text import ERR_DUPLICATE_FILE

        return ERR_DUPLICATE_FILE % (self.filename,)


class DuplicateOutputFile(Exception):
    """raised if the same output file is generated more than once"""

    def __init__(self, filename):
        """filename is a Filename object"""

        self.filename = filename

    def __unicode__(self):
        from audiotools.text import ERR_DUPLICATE_OUTPUT_FILE

        return ERR_DUPLICATE_OUTPUT_FILE % (self.filename,)


class OutputFileIsInput(Exception):
    """raised if an output file is the same as an input file"""

    def __init__(self, filename):
        """filename is a Filename object"""

        self.filename = filename

    def __unicode__(self):
        from audiotools.text import ERR_OUTPUT_IS_INPUT

        return ERR_OUTPUT_IS_INPUT % (self.filename,)


class Filename(tuple):
    def __new__(cls, filename):
        """filename is a string of the file on disk"""

        if (isinstance(filename, cls)):
            return filename
        else:
            filename = str(filename)
            try:
                stat = os.stat(filename)
                return tuple.__new__(cls, [os.path.normpath(filename),
                                           stat.st_dev,
                                           stat.st_ino])
            except OSError:
                return tuple.__new__(cls, [os.path.normpath(filename),
                                           None,
                                           None])

    def open(self, mode):
        """returns a file object of this filename opened
        with the given mode"""

        return __open__(self[0], mode)

    def disk_file(self):
        """returns True if the file exists on disk"""

        return (self[1] is not None) and (self[2] is not None)

    def dirname(self):
        """returns the directory name (no filename) of this file"""

        return Filename(os.path.dirname(self[0]))

    def basename(self):
        """returns the basename (no directory) of this file"""

        return Filename(os.path.basename(self[0]))

    def expanduser(self):
        """returns a Filename object with user directory expanded"""

        return Filename(os.path.expanduser(self[0]))

    def __repr__(self):
        return "Filename(%s, %s, %s)" % \
            (repr(self[0]), repr(self[1]), repr(self[2]))

    def __eq__(self, filename):
        if (isinstance(filename, Filename)):
            if (self.disk_file() and filename.disk_file()):
                # both exist on disk,
                # so they compare equally if st_dev and st_ino match
                return (self[1] == filename[1]) and (self[2] == filename[2])
            elif ((not self.disk_file()) and (not filename.disk_file())):
                # neither exist on disk,
                # so they compare equally if their paths match
                return self[0] == filename[0]
            else:
                # one or the other exists on disk
                # but not both, so they never match
                return False
        else:
            return False

    def __ne__(self, filename):
        return not self == filename

    def __hash__(self):
        if (self.disk_file()):
            return hash((None, self[1], self[2]))
        else:
            return hash((self[0], self[1], self[2]))

    def __str__(self):
        return self[0]

    def __unicode__(self):
        return self[0].decode(FS_ENCODING, "replace")


def sorted_tracks(audiofiles):
    """given a list of AudioFile objects
    returns a list of them sorted
    by track_number and album_number, if found
    """

    return sorted(audiofiles, key=lambda f: f.__sort_key__())


def open_files(filename_list, sorted=True, messenger=None,
               no_duplicates=False, warn_duplicates=False,
               opened_files=None, unsupported_formats=None):
    """returns a list of AudioFile objects
    from a list of filename strings or Filename objects

    if "sorted" is True, files are sorted by album number then track number

    if "messenger" is given, warnings and errors when opening files
    are sent to the given Messenger-compatible object

    if "no_duplicates" is True, including the same file twice
    raises a DuplicateFile whose filename value
    is the first duplicate filename as a Filename object

    if "warn_duplicates" is True, including the same file twice
    results in a warning message to the messenger object, if given

    "opened_files" is a set object containing previously opened
    Filename objects and which newly opened Filename objects are added to

    "unsupported_formats" is a set object containing the .NAME strings
    of AudioFile objects which have already been displayed
    as unsupported in order to avoid displaying duplicate messages
    """

    from audiotools.text import (ERR_DUPLICATE_FILE,
                                 ERR_OPEN_IOERROR)

    if (opened_files is None):
        opened_files = set()
    if (unsupported_formats is None):
        unsupported_formats = set()

    to_return = []

    for filename in map(Filename, filename_list):
        if (filename in opened_files):
            if (no_duplicates):
                raise DuplicateFile(filename)
            elif (warn_duplicates and (messenger is not None)):
                messenger.warning(ERR_DUPLICATE_FILE % (filename,))
        else:
            opened_files.add(filename)

        try:
            f = __open__(str(filename), "rb")
            try:
                audio_class = file_type(f)
            finally:
                f.close()
            if (audio_class is not None):
                if (audio_class.available(BIN)):
                    # is a supported audio type with needed binaries
                    to_return.append(audio_class(str(filename)))
                elif ((messenger is not None) and
                      (audio_class.NAME not in unsupported_formats)):
                    # is a supported audio type without needed binaries
                    # or libraries
                    audio_class.missing_components(messenger)

                    # but only display format binaries message once
                    unsupported_formats.add(audio_class.NAME)
            else:
                # not a support audio type
                pass
        except IOError as err:
            if (messenger is not None):
                messenger.warning(ERR_OPEN_IOERROR % (filename,))
        except InvalidFile as err:
            if (messenger is not None):
                messenger.error(unicode(err))

    return (sorted_tracks(to_return) if sorted else to_return)


def open_directory(directory, sorted=True, messenger=None):
    """yields an AudioFile via a recursive search of directory

    files are sorted by album number/track number by default,
    on a per-directory basis
    any unsupported files are filtered out
    error messages are sent to messenger, if given
    """

    for (basedir, subdirs, filenames) in os.walk(directory):
        if (sorted):
            subdirs.sort()
        for audiofile in open_files([os.path.join(basedir, filename)
                                     for filename in filenames],
                                    sorted=sorted,
                                    messenger=messenger):
            yield audiofile


def group_tracks(tracks):
    """takes an iterable collection of tracks

    yields list of tracks grouped by album
    where their album_name and album_number match, if possible"""

    collection = {}
    for track in tracks:
        metadata = track.get_metadata()
        if (metadata is not None):
            collection.setdefault((metadata.album_number,
                                   metadata.album_name), []).append(track)
        else:
            collection.setdefault(None, []).append(track)

    for key in sorted(collection.keys()):
        yield collection[key]


class UnknownAudioType(Exception):
    """raised if filename_to_type finds no possibilities"""

    def __init__(self, suffix):
        self.suffix = suffix

    def error_msg(self, messenger):
        from audiotools.text import ERR_UNSUPPORTED_AUDIO_TYPE

        messenger.error(ERR_UNSUPPORTED_AUDIO_TYPE % (self.suffix,))


class AmbiguousAudioType(UnknownAudioType):
    """raised if filename_to_type finds more than one possibility"""

    def __init__(self, suffix, type_list):
        self.suffix = suffix
        self.type_list = type_list

    def error_msg(self, messenger):
        from audiotools.text import (ERR_AMBIGUOUS_AUDIO_TYPE,
                                     LAB_T_OPTIONS)

        messenger.error(ERR_AMBIGUOUS_AUDIO_TYPE % (self.suffix,))
        messenger.info(LAB_T_OPTIONS %
                       (u" or ".join([u"\"%s\"" % (t.NAME.decode('ascii'))
                                      for t in self.type_list])))


def filename_to_type(path):
    """given a path to a file, return its audio type based on suffix

    for example:
    >>> filename_to_type("/foo/file.flac")
    <class audiotools.__flac__.FlacAudio at 0x7fc8456d55f0>

    raises an UnknownAudioType exception if the type is unknown
    raise AmbiguousAudioType exception if the type is ambiguous
    """

    (path, ext) = os.path.splitext(path)
    if (len(ext) > 0):
        ext = ext[1:]   # remove the "."
        SUFFIX_MAP = {}
        for audio_type in TYPE_MAP.values():
            SUFFIX_MAP.setdefault(audio_type.SUFFIX, []).append(audio_type)
        if (ext in SUFFIX_MAP.keys()):
            if (len(SUFFIX_MAP[ext]) == 1):
                return SUFFIX_MAP[ext][0]
            else:
                raise AmbiguousAudioType(ext, SUFFIX_MAP[ext])
        else:
            raise UnknownAudioType(ext)
    else:
        raise UnknownAudioType(ext)


class ChannelMask(object):
    """an integer-like class that abstracts a PCMReader's channel assignments

    all channels in a FrameList will be in RIFF WAVE order
    as a sensible convention
    but which channel corresponds to which speaker is decided by this mask
    for example, a 4 channel PCMReader with the channel mask 0x33
    corresponds to the bits 00110011
    reading those bits from right to left (least significant first)
    the "front_left", "front_right", "back_left", "back_right"
    speakers are set

    therefore, the PCMReader's 4 channel FrameLists are laid out as follows:

    channel 0 -> front_left
    channel 1 -> front_right
    channel 2 -> back_left
    channel 3 -> back_right

    since the "front_center" and "low_frequency" bits are not set,
    those channels are skipped in the returned FrameLists

    many formats store their channels internally in a different order
    their PCMReaders will be expected to reorder channels
    and set a ChannelMask matching this convention
    and, their from_pcm() functions will be expected to reverse the process

    a ChannelMask of 0 is "undefined",
    which means that channels aren't assigned to *any* speaker
    this is an ugly last resort for handling formats
    where multi-channel assignments aren't properly defined
    in this case, a from_pcm() method is free to assign the undefined channels
    any way it likes, and is under no obligation to keep them undefined
    when passing back out to to_pcm()
    """

    SPEAKER_TO_MASK = {"front_left": 0x1,
                       "front_right": 0x2,
                       "front_center": 0x4,
                       "low_frequency": 0x8,
                       "back_left": 0x10,
                       "back_right": 0x20,
                       "front_left_of_center": 0x40,
                       "front_right_of_center": 0x80,
                       "back_center": 0x100,
                       "side_left": 0x200,
                       "side_right": 0x400,
                       "top_center": 0x800,
                       "top_front_left": 0x1000,
                       "top_front_center": 0x2000,
                       "top_front_right": 0x4000,
                       "top_back_left": 0x8000,
                       "top_back_center": 0x10000,
                       "top_back_right": 0x20000}

    MASK_TO_SPEAKER = dict(map(reversed, map(list, SPEAKER_TO_MASK.items())))

    from audiotools.text import (MASK_FRONT_LEFT,
                                 MASK_FRONT_RIGHT,
                                 MASK_FRONT_CENTER,
                                 MASK_LFE,
                                 MASK_BACK_LEFT,
                                 MASK_BACK_RIGHT,
                                 MASK_FRONT_RIGHT_OF_CENTER,
                                 MASK_FRONT_LEFT_OF_CENTER,
                                 MASK_BACK_CENTER,
                                 MASK_SIDE_LEFT,
                                 MASK_SIDE_RIGHT,
                                 MASK_TOP_CENTER,
                                 MASK_TOP_FRONT_LEFT,
                                 MASK_TOP_FRONT_CENTER,
                                 MASK_TOP_FRONT_RIGHT,
                                 MASK_TOP_BACK_LEFT,
                                 MASK_TOP_BACK_CENTER,
                                 MASK_TOP_BACK_RIGHT)

    MASK_TO_NAME = {0x1: MASK_FRONT_LEFT,
                    0x2: MASK_FRONT_RIGHT,
                    0x4: MASK_FRONT_CENTER,
                    0x8: MASK_LFE,
                    0x10: MASK_BACK_LEFT,
                    0x20: MASK_BACK_RIGHT,
                    0x40: MASK_FRONT_RIGHT_OF_CENTER,
                    0x80: MASK_FRONT_LEFT_OF_CENTER,
                    0x100: MASK_BACK_CENTER,
                    0x200: MASK_SIDE_LEFT,
                    0x400: MASK_SIDE_RIGHT,
                    0x800: MASK_TOP_CENTER,
                    0x1000: MASK_TOP_FRONT_LEFT,
                    0x2000: MASK_TOP_FRONT_CENTER,
                    0x4000: MASK_TOP_FRONT_RIGHT,
                    0x8000: MASK_TOP_BACK_LEFT,
                    0x10000: MASK_TOP_BACK_CENTER,
                    0x20000: MASK_TOP_BACK_RIGHT}

    def __init__(self, mask):
        """mask should be an integer channel mask value"""

        mask = int(mask)

        for (speaker, speaker_mask) in self.SPEAKER_TO_MASK.items():
            setattr(self, speaker, (mask & speaker_mask) != 0)

    def __unicode__(self):
        return u", ".join([self.MASK_TO_NAME[key] for key in
                          sorted(self.MASK_TO_SPEAKER.keys())
                          if getattr(self, self.MASK_TO_SPEAKER[key])])

    def __repr__(self):
        return "ChannelMask(%s)" % \
            ",".join(["%s=%s" % (field, getattr(self, field))
                      for field in self.SPEAKER_TO_MASK.keys()
                      if (getattr(self, field))])

    def __int__(self):
        import operator
        from functools import reduce

        return reduce(operator.or_,
                      [self.SPEAKER_TO_MASK[field] for field in
                       self.SPEAKER_TO_MASK.keys()
                       if getattr(self, field)],
                      0)

    def __eq__(self, v):
        return int(self) == int(v)

    def __ne__(self, v):
        return int(self) != int(v)

    def __len__(self):
        return sum([1 for field in self.SPEAKER_TO_MASK.keys()
                    if getattr(self, field)])

    def defined(self):
        """returns True if this ChannelMask is defined"""

        return int(self) != 0

    def undefined(self):
        """returns True if this ChannelMask is undefined"""

        return int(self) == 0

    def channels(self):
        """returns a list of speaker strings this mask contains

        returned in the order in which they should appear
        in the PCM stream
        """

        c = []
        for (mask, speaker) in sorted(self.MASK_TO_SPEAKER.items(),
                                      key=lambda pair: pair[0]):
            if (getattr(self, speaker)):
                c.append(speaker)

        return c

    def index(self, channel_name):
        """returns the index of the given channel name within this mask

        for example, given the mask 0xB (fL, fR, LFE, but no fC)
        index("low_frequency") will return 2
        if the channel is not in this mask, raises ValueError"""

        return self.channels().index(channel_name)

    @classmethod
    def from_fields(cls, **fields):
        """given a set of channel arguments, returns a new ChannelMask

        for example:
        >>> ChannelMask.from_fields(front_left=True,front_right=True)
        channelMask(front_right=True,front_left=True)
        """

        mask = cls(0)

        for (key, value) in fields.items():
            if (key in cls.SPEAKER_TO_MASK.keys()):
                setattr(mask, key, bool(value))
            else:
                raise KeyError(key)

        return mask

    @classmethod
    def from_channels(cls, channel_count):
        """given a channel count, returns a new ChannelMask

        this is only valid for channel counts 1 and 2
        all other values trigger a ValueError"""

        if (channel_count == 2):
            return cls(0x3)
        elif (channel_count == 1):
            return cls(0x4)
        else:
            raise ValueError("ambiguous channel assignment")


class PCMReader(object):
    """a class that wraps around a file object and generates pcm.FrameLists"""

    def __init__(self, file,
                 sample_rate, channels, channel_mask, bits_per_sample,
                 process=None, signed=True, big_endian=False):
        """fields are as follows:

        file            - a file-like object with read() and close() methods
        sample_rate     - an integer number of Hz
        channels        - an integer number of channels
        channel_mask    - an integer channel mask value
        bits_per_sample - an integer number of bits per sample
        process         - an optional subprocess object
        signed          - True if the file's samples are signed integers
        big_endian      - True if the file's samples are stored big-endian

        the process, signed and big_endian arguments are optional
        PCMReader-compatible objects need only expose the
        sample_rate, channels, channel_mask and bits_per_sample fields
        along with the read() and close() methods
        """

        self.file = file
        self.sample_rate = sample_rate
        self.channels = channels
        self.channel_mask = channel_mask
        self.bits_per_sample = bits_per_sample
        self.process = process
        self.signed = signed
        self.big_endian = big_endian
        self.bytes_per_frame = self.channels * (self.bits_per_sample // 8)

    def read(self, pcm_frames):
        """try to read the given number of PCM frames from the stream

        this is *not* guaranteed to read exactly that number of frames
        it may return less (at the end of the stream, especially)
        it may return more
        however, it must always return a non-empty FrameList until the
        end of the PCM stream is reached

        may raise IOError if unable to read the input file,
        or ValueError if the input file has some sort of error
        """

        framelist = pcm.FrameList(
            self.file.read(max(pcm_frames, 1) * self.bytes_per_frame),
            self.channels,
            self.bits_per_sample,
            self.big_endian,
            self.signed)
        if (framelist.frames > 0):
            return framelist
        elif (self.process is not None):
            if (self.process.wait() == 0):
                return framelist
            else:
                raise ValueError(u"subprocess exited with error")
        else:
            return framelist

    def close(self):
        """closes the stream for reading

        subsequent calls to read() raise ValueError"""

        self.file.close()


class PCMReaderError(object):
    """a dummy PCMReader which automatically raises ValueError

    this is to be returned by an AudioFile's to_pcm() method
    if some error occurs when initializing a decoder"""

    def __init__(self, error_message,
                 sample_rate, channels, channel_mask, bits_per_sample):
        self.sample_rate = sample_rate
        self.channels = channels
        self.channel_mask = channel_mask
        self.bits_per_sample = bits_per_sample
        self.error_message = error_message

    def read(self, pcm_frames):
        """always raises a ValueError"""

        raise ValueError(self.error_message)

    def close(self):
        """does nothing"""

        pass


def to_pcm_progress(audiofile, progress):
    if (progress is None):
        return audiofile.to_pcm()
    else:
        return PCMReaderProgress(audiofile.to_pcm(),
                                 audiofile.total_frames(),
                                 progress)


class PCMReaderProgress(object):
    def __init__(self, pcmreader, total_frames, progress, current_frames=0):
        """pcmreader is a PCMReader compatible object
        total_frames is the total PCM frames of the stream
        progress(current, total) is a callable function
        current_frames is the current amount of PCM frames in the stream"""

        self.__read__ = pcmreader.read
        self.__close__ = pcmreader.close
        self.sample_rate = pcmreader.sample_rate
        self.channels = pcmreader.channels
        self.channel_mask = pcmreader.channel_mask
        self.bits_per_sample = pcmreader.bits_per_sample
        self.current_frames = current_frames
        self.total_frames = total_frames
        if (callable(progress)):
            self.progress = progress
        else:
            self.progress = lambda current_frames, total_frames: None

    def read(self, pcm_frames):
        frame = self.__read__(pcm_frames)
        self.current_frames += frame.frames
        self.progress(self.current_frames, self.total_frames)
        return frame

    def close(self):
        self.__close__()


class ReorderedPCMReader(object):
    """a PCMReader wrapper which reorders its output channels"""

    def __init__(self, pcmreader, channel_order, channel_mask=None):
        """initialized with a PCMReader and list of channel number integers

        for example, to swap the channels of a stereo stream:
        >>> ReorderedPCMReader(reader,[1,0])

        may raise ValueError if the number of channels specified by
        channel_order doesn't match the given channel mask
        if channel mask is nonzero
        """

        self.pcmreader = pcmreader
        self.sample_rate = pcmreader.sample_rate
        self.channels = len(channel_order)
        if (channel_mask is None):
            self.channel_mask = pcmreader.channel_mask
        else:
            self.channel_mask = channel_mask

        if (((self.channel_mask != 0) and
             (len(ChannelMask(self.channel_mask)) != self.channels))):
            # channel_mask is defined but has a different number of channels
            # than the channel count attribute
            from audiotools.text import ERR_CHANNEL_COUNT_MASK_MISMATCH
            raise ValueError(ERR_CHANNEL_COUNT_MASK_MISMATCH)
        self.bits_per_sample = pcmreader.bits_per_sample
        self.channel_order = channel_order

    def read(self, pcm_frames):
        """try to read a pcm.FrameList with the given number of frames"""

        framelist = self.pcmreader.read(pcm_frames)

        return pcm.from_channels([framelist.channel(channel)
                                  for channel in self.channel_order])

    def close(self):
        """closes the stream"""

        self.pcmreader.close()


def transfer_data(from_function, to_function):
    """sends BUFFER_SIZE strings from from_function to to_function

    this continues until an empty string is returned from from_function"""

    try:
        s = from_function(BUFFER_SIZE)
        while (len(s) > 0):
            to_function(s)
            s = from_function(BUFFER_SIZE)
    except IOError:
        # this usually means a broken pipe, so we can only hope
        # the data reader is closing down correctly
        pass


def transfer_framelist_data(pcmreader, to_function,
                            signed=True, big_endian=False):
    """sends pcm.FrameLists from pcmreader to to_function

    frameLists are converted to strings using the signed and big_endian
    arguments.  This continues until an empty FrameLists is returned
    from pcmreader
    """

    f = pcmreader.read(FRAMELIST_SIZE)
    while (len(f) > 0):
        to_function(f.to_bytes(big_endian, signed))
        f = pcmreader.read(FRAMELIST_SIZE)


def threaded_transfer_framelist_data(pcmreader, to_function,
                                     signed=True, big_endian=False):
    """sends pcm.FrameLists from pcmreader to to_function via threads

    FrameLists are converted to strings using the signed and big_endian
    arguments.  This continues until an empty FrameList is returned
    from pcmreader.  It operates by splitting reading and writing
    into threads in the hopes that an intermittant reader
    will not disrupt the writer
    """

    import threading
    import Queue

    def send_data(pcmreader, queue):
        try:
            s = pcmreader.read(FRAMELIST_SIZE)
            while (len(s) > 0):
                queue.put(s)
                s = pcmreader.read(FRAMELIST_SIZE)
            queue.put(None)
        except (IOError, ValueError):
            queue.put(None)

    data_queue = Queue.Queue(10)
    thread = threading.Thread(target=send_data,
                              args=(pcmreader, data_queue))
    thread.setDaemon(True)
    thread.start()
    s = data_queue.get()
    while (s is not None):
        to_function(s)
        s = data_queue.get()


def pcm_cmp(pcmreader1, pcmreader2):
    """returns True if the PCM data in pcmreader1 equals pcmreader2

    the readers must be closed separately
    """

    if (((pcmreader1.sample_rate != pcmreader2.sample_rate) or
         (pcmreader1.channels != pcmreader2.channels) or
         (pcmreader1.bits_per_sample != pcmreader2.bits_per_sample))):
        return False

    reader1 = BufferedPCMReader(pcmreader1)
    reader2 = BufferedPCMReader(pcmreader2)

    s1 = reader1.read(FRAMELIST_SIZE)
    s2 = reader2.read(FRAMELIST_SIZE)

    while ((len(s1) > 0) and (len(s2) > 0)):
        if (s1 != s2):
            transfer_data(reader1.read, lambda x: x)
            transfer_data(reader2.read, lambda x: x)
            return False
        else:
            s1 = reader1.read(FRAMELIST_SIZE)
            s2 = reader2.read(FRAMELIST_SIZE)

    return True


def pcm_frame_cmp(pcmreader1, pcmreader2):
    """returns the PCM Frame number of the first mismatch

    if the two streams match completely, returns None
    may raise IOError or ValueError if problems occur
    when reading PCM streams"""

    if (((pcmreader1.sample_rate != pcmreader2.sample_rate) or
         (pcmreader1.channels != pcmreader2.channels) or
         (pcmreader1.bits_per_sample != pcmreader2.bits_per_sample))):
        return 0

    if (((pcmreader1.channel_mask != 0) and
         (pcmreader2.channel_mask != 0) and
         (pcmreader1.channel_mask != pcmreader2.channel_mask))):
        return 0

    frame_number = 0
    reader1 = BufferedPCMReader(pcmreader1)
    reader2 = BufferedPCMReader(pcmreader2)

    framelist1 = reader1.read(FRAMELIST_SIZE)
    framelist2 = reader2.read(FRAMELIST_SIZE)

    while ((len(framelist1) > 0) and (len(framelist2) > 0)):
        if (framelist1 != framelist2):
            for i in range(min(framelist1.frames, framelist2.frames)):
                if (framelist1.frame(i) != framelist2.frame(i)):
                    return frame_number + i
            else:
                return frame_number + i
        else:
            frame_number += framelist1.frames
            framelist1 = reader1.read(FRAMELIST_SIZE)
            framelist2 = reader2.read(FRAMELIST_SIZE)
    else:
        if ((len(framelist1) > 0) or (len(framelist2) > 0)):
            return frame_number
        else:
            return None


class PCMCat(object):
    """a PCMReader for concatenating several PCMReaders"""

    def __init__(self, pcmreaders):
        """pcmreaders is a list of PCMReader objects

        all must have the same stream attributes"""

        self.pcmreaders = list(pcmreaders)
        if (len(self.pcmreaders) == 0):
            from audiotools.text import ERR_NO_PCMREADERS
            raise ValueError(ERR_NO_PCMREADERS)

        if (len({r.sample_rate for r in self.pcmreaders}) != 1):
            from audiotools.text import ERR_SAMPLE_RATE_MISMATCH
            raise ValueError(ERR_SAMPLE_RATE_MISMATCH)
        if (len({r.channels for r in self.pcmreaders}) != 1):
            from audiotools.text import ERR_CHANNEL_COUNT_MISMATCH
            raise ValueError(ERR_CHANNEL_COUNT_MISMATCH)
        if (len({r.bits_per_sample for r in self.pcmreaders}) != 1):
            from audiotools.text import ERR_BPS_MISMATCH
            raise ValueError(ERR_BPS_MISMATCH)

        self.__index__ = 0
        reader = self.pcmreaders[self.__index__]
        self.__read__ = reader.read

        self.sample_rate = reader.sample_rate
        self.channels = reader.channels
        self.channel_mask = reader.channel_mask
        self.bits_per_sample = reader.bits_per_sample

    def read(self, pcm_frames):
        """try to read a pcm.FrameList with the given number of frames

        raises ValueError if any of the streams is mismatched"""

        # read a FrameList from the current PCMReader
        framelist = self.__read__(pcm_frames)

        # while the FrameList is empty
        while (len(framelist) == 0):
            # move on to the next PCMReader in the queue, if any
            self.__index__ += 1
            try:
                reader = self.pcmreaders[self.__index__]
                self.__read__ = reader.read

                # and read a FrameList from the new PCMReader
                framelist = self.__read__(pcm_frames)
            except IndexError:
                # if no PCMReaders remain, have all further reads
                # return empty FrameList objects
                # and return an empty FrameList object
                self.read = self.read_finished
                return self.read_finished(pcm_frames)
        else:
            # otherwise, return the filled FrameList
            return framelist

    def read_finished(self, pcm_frames):
        return pcm.from_list([], self.channels, self.bits_per_sample, True)

    def read_closed(self, pcm_frames):
        raise ValueError()

    def close(self):
        """closes the stream for reading"""

        self.read = self.read_closed
        for reader in self.pcmreaders:
            reader.close()


class BufferedPCMReader(object):
    """a PCMReader which reads exact counts of PCM frames"""

    def __init__(self, pcmreader):
        """pcmreader is a regular PCMReader object"""

        self.pcmreader = pcmreader
        self.sample_rate = pcmreader.sample_rate
        self.channels = pcmreader.channels
        self.channel_mask = pcmreader.channel_mask
        self.bits_per_sample = pcmreader.bits_per_sample
        self.buffer = pcm.from_list([],
                                    self.channels,
                                    self.bits_per_sample,
                                    True)

    def close(self):
        """closes the sub-pcmreader and frees our internal buffer"""

        self.pcmreader.close()
        self.read = self.read_closed

    def read(self, pcm_frames):
        """reads the given number of PCM frames

        this may return fewer than the given number
        at the end of a stream
        but will never return more than requested
        """

        # fill our buffer to at least "pcm_frames", possibly more
        while (self.buffer.frames < pcm_frames):
            frame = self.pcmreader.read(FRAMELIST_SIZE)
            if (len(frame)):
                self.buffer += frame
            else:
                break

        # chop off the preceding number of PCM frames and return them
        (output, self.buffer) = self.buffer.split(pcm_frames)

        return output

    def read_closed(self, pcm_frames):
        raise ValueError()


class CounterPCMReader(object):
    """a PCMReader which counts bytes and frames written"""

    def __init__(self, pcmreader):
        self.sample_rate = pcmreader.sample_rate
        self.channels = pcmreader.channels
        self.channel_mask = pcmreader.channel_mask
        self.bits_per_sample = pcmreader.bits_per_sample

        self.__pcmreader__ = pcmreader
        self.frames_written = 0

    def bytes_written(self):
        return (self.frames_written *
                self.channels *
                (self.bits_per_sample // 8))

    def read(self, pcm_frames):
        frame = self.__pcmreader__.read(pcm_frames)
        self.frames_written += frame.frames
        return frame

    def close(self):
        self.__pcmreader__.close()


class LimitedFileReader(object):
    def __init__(self, file, total_bytes):
        self.__file__ = file
        self.__total_bytes__ = total_bytes

    def read(self, x):
        if (self.__total_bytes__ > 0):
            s = self.__file__.read(x)
            if (len(s) <= self.__total_bytes__):
                self.__total_bytes__ -= len(s)
                return s
            else:
                s = s[0:self.__total_bytes__]
                self.__total_bytes__ = 0
                return s
        else:
            return ""

    def close(self):
        self.__file__.close()


class LimitedPCMReader(object):
    def __init__(self, buffered_pcmreader, total_pcm_frames):
        """buffered_pcmreader should be a BufferedPCMReader

        which ensures we won't pull more frames off the reader
        than necessary upon calls to read()"""

        self.pcmreader = buffered_pcmreader
        self.total_pcm_frames = total_pcm_frames
        self.sample_rate = self.pcmreader.sample_rate
        self.channels = self.pcmreader.channels
        self.channel_mask = self.pcmreader.channel_mask
        self.bits_per_sample = self.pcmreader.bits_per_sample

    def read(self, pcm_frames):
        if (self.total_pcm_frames > 0):
            frame = self.pcmreader.read(min(pcm_frames, self.total_pcm_frames))
            self.total_pcm_frames -= frame.frames
            return frame
        else:
            return pcm.FrameList("",
                                 self.channels,
                                 self.bits_per_sample,
                                 False,
                                 True)

    def read_closed(self, pcm_frames):
        raise ValueError()

    def close(self):
        self.read = self.read_closed


def PCMConverter(pcmreader,
                 sample_rate,
                 channels,
                 channel_mask,
                 bits_per_sample):
    """a PCMReader wrapper for converting attributes

    for example, this can be used to alter sample_rate, bits_per_sample,
    channel_mask, channel count, or any combination of those
    attributes.  It resamples, downsamples, etc. to achieve the proper
    output

    may raise ValueError if any of the attributes are unsupported
    or invalid
    """

    if (sample_rate <= 0):
        from audiotools.text import ERR_INVALID_SAMPLE_RATE
        raise ValueError(ERR_INVALID_SAMPLE_RATE)
    elif (channels <= 0):
        from audiotools.text import ERR_INVALID_CHANNEL_COUNT
        raise ValueError(ERR_INVALID_CHANNEL_COUNT)
    elif (bits_per_sample not in (8, 16, 24)):
        from audiotools.text import ERR_INVALID_BITS_PER_SAMPLE
        raise ValueError(ERR_INVALID_BITS_PER_SAMPLE)

    if ((channel_mask != 0) and (len(ChannelMask(channel_mask)) != channels)):
        # channel_mask is defined but has a different number of channels
        # than the channel count attribute
        from audiotools.text import ERR_CHANNEL_COUNT_MASK_MISMATCH
        raise ValueError(ERR_CHANNEL_COUNT_MASK_MISMATCH)

    if (pcmreader.channels > channels):
        if ((channels == 1) and (channel_mask in (0, 0x4))):
            if (pcmreader.channels > 2):
                # reduce channel count through downmixing
                # followed by averaging
                from .pcmconverter import (Averager, Downmixer)
                pcmreader = Averager(Downmixer(pcmreader))
            else:
                # pcmreader.channels == 2
                # so reduce channel count through averaging
                from .pcmconverter import Averager
                pcmreader = Averager(pcmreader)
        elif ((channels == 2) and (channel_mask in (0, 0x3))):
            # reduce channel count through downmixing
            from .pcmconverter import Downmixer
            pcmreader = Downmixer(pcmreader)
        else:
            # unusual channel count/mask combination
            pcmreader = RemaskedPCMReader(pcmreader,
                                          channels,
                                          channel_mask)
    elif (pcmreader.channels < channels):
        # increase channel count by duplicating first channel
        # (this is usually just going from mono to stereo
        #  since there's no way to summon surround channels
        #  out of thin air)
        pcmreader = ReorderedPCMReader(pcmreader,
                                       range(pcmreader.channels) +
                                       [0] * (channels - pcmreader.channels),
                                       channel_mask)

    if (pcmreader.sample_rate != sample_rate):
        # convert sample rate through resampling
        from .pcmconverter import Resampler
        pcmreader = Resampler(pcmreader, sample_rate)

    if (pcmreader.bits_per_sample != bits_per_sample):
        # use bitshifts/dithering to adjust bits-per-sample
        from .pcmconverter import BPSConverter
        pcmreader = BPSConverter(pcmreader, bits_per_sample)

    return pcmreader


def resampled_frame_count(initial_frame_count,
                          initial_sample_rate,
                          new_sample_rate):
    """given an initial PCM frame count, initial sample rate
    and new sample rate, returns the new PCM frame count
    once the stream has been resampled"""

    if (initial_sample_rate == new_sample_rate):
        return initial_frame_count
    else:
        from decimal import (Decimal, ROUND_DOWN)
        new_frame_count = ((Decimal(initial_frame_count) *
                            Decimal(new_sample_rate)) /
                           Decimal(initial_sample_rate))
        return int(new_frame_count.quantize(Decimal("1."),
                                            rounding=ROUND_DOWN))


def calculate_replay_gain(tracks, progress=None):
    """yields (track, track_gain, track_peak, album_gain, album_peak)
    for each AudioFile in the list of tracks

    raises ValueError if a problem occurs during calculation"""

    if (len(tracks) == 0):
        return

    import audiotools.replaygain as replaygain
    from bisect import bisect

    SUPPORTED_RATES = [8000,  11025,  12000,  16000,  18900,  22050, 24000,
                       32000, 37800,  44100,  48000,  56000,  64000, 88200,
                       96000, 112000, 128000, 144000, 176400, 192000]

    target_rate = ([SUPPORTED_RATES[0]] + SUPPORTED_RATES)[
        bisect(SUPPORTED_RATES, most_numerous([track.sample_rate()
                                               for track in tracks]))]

    track_frames = [resampled_frame_count(track.total_frames(),
                                          track.sample_rate(),
                                          target_rate)
                    for track in tracks]
    current_frames = 0
    total_frames = sum(track_frames)

    rg = replaygain.ReplayGain(target_rate)

    gains = []

    for (track, track_frames) in zip(tracks, track_frames):
        pcm = track.to_pcm()

        if (pcm.channels > 2):
            # add a wrapper to cull any channels above 2
            output_channels = 2
            output_channel_mask = 0x3
        else:
            output_channels = pcm.channels
            output_channel_mask = pcm.channel_mask

        if (((pcm.channels != output_channels) or
             (pcm.channel_mask != output_channel_mask) or
             (pcm.sample_rate) != target_rate)):
            pcm = PCMConverter(pcm,
                               target_rate,
                               output_channels,
                               output_channel_mask,
                               pcm.bits_per_sample)

        # finally, perform the gain calculation on the PCMReader
        # and accumulate the title gain
        (track_gain, track_peak) = rg.title_gain(
            PCMReaderProgress(pcm,
                              total_frames,
                              progress,
                              current_frames=current_frames))
        current_frames += track_frames
        gains.append((track, track_gain, track_peak))

    # once everything is calculated, get the album gain
    (album_gain, album_peak) = rg.album_gain()

    # yield a set of accumulated track and album gains
    for (track, track_gain, track_peak) in gains:
        yield (track, track_gain, track_peak, album_gain, album_peak)


def add_replay_gain(tracks, progress=None):
    """given an iterable set of AudioFile objects
    and optional progress function
    calculates the ReplayGain for them and adds it
    via their set_replay_gain method"""

    for (track,
         track_gain,
         track_peak,
         album_gain,
         album_peak) in calculate_replay_gain(tracks, progress):
        track.set_replay_gain(ReplayGain(track_gain=track_gain,
                                         track_peak=track_peak,
                                         album_gain=album_gain,
                                         album_peak=album_peak))


def ignore_sigint():
    """sets the SIGINT signal to SIG_IGN

    some encoder executables require this in order for
    interruptableReader to work correctly since we
    want to catch SIGINT ourselves in that case and perform
    a proper shutdown"""

    import signal

    signal.signal(signal.SIGINT, signal.SIG_IGN)


def make_dirs(destination_path):
    """ensures all directories leading to destination_path are created

    raises OSError if a problem occurs during directory creation
    """

    dirname = os.path.dirname(destination_path)
    if ((dirname != '') and (not os.path.isdir(dirname))):
        os.makedirs(dirname)


class MetaData(object):
    """the base class for storing textual AudioFile metadata

    Fields may be None, indicating they're not present
    in the underlying metadata implementation.

    Changing a field to a new value will update the underlying metadata
    (e.g. vorbiscomment.track_name = u"Foo"
    will set a Vorbis comment's "TITLE" field to "Foo")

    Updating the underlying metadata will change the metadata's fields
    (e.g. setting a Vorbis comment's "TITLE" field to "bar"
    will update vorbiscomment.title_name to u"bar")

    Deleting a field or setting it to None
    will remove it from the underlying metadata
    (e.g. del(vorbiscomment.track_name) will delete the "TITLE" field)
    """

    FIELDS = ("track_name",
              "track_number",
              "track_total",
              "album_name",
              "artist_name",
              "performer_name",
              "composer_name",
              "conductor_name",
              "media",
              "ISRC",
              "catalog",
              "copyright",
              "publisher",
              "year",
              "date",
              "album_number",
              "album_total",
              "comment")

    INTEGER_FIELDS = ("track_number",
                      "track_total",
                      "album_number",
                      "album_total")

    # this is the order fields should be presented to the user
    # to ensure consistency across utilities
    FIELD_ORDER = ("track_name",
                   "artist_name",
                   "album_name",
                   "track_number",
                   "track_total",
                   "album_number",
                   "album_total",
                   "performer_name",
                   "composer_name",
                   "conductor_name",
                   "catalog",
                   "ISRC",
                   "publisher",
                   "media",
                   "year",
                   "date",
                   "copyright",
                   "comment")

    # this is the name fields should use when presented to the user
    # also to ensure constency across utilities
    from audiotools.text import (METADATA_TRACK_NAME,
                                 METADATA_TRACK_NUMBER,
                                 METADATA_TRACK_TOTAL,
                                 METADATA_ALBUM_NAME,
                                 METADATA_ARTIST_NAME,
                                 METADATA_PERFORMER_NAME,
                                 METADATA_COMPOSER_NAME,
                                 METADATA_CONDUCTOR_NAME,
                                 METADATA_MEDIA,
                                 METADATA_ISRC,
                                 METADATA_CATALOG,
                                 METADATA_COPYRIGHT,
                                 METADATA_PUBLISHER,
                                 METADATA_YEAR,
                                 METADATA_DATE,
                                 METADATA_ALBUM_NUMBER,
                                 METADATA_ALBUM_TOTAL,
                                 METADATA_COMMENT)

    FIELD_NAMES = {"track_name": METADATA_TRACK_NAME,
                   "track_number": METADATA_TRACK_NUMBER,
                   "track_total": METADATA_TRACK_TOTAL,
                   "album_name": METADATA_ALBUM_NAME,
                   "artist_name": METADATA_ARTIST_NAME,
                   "performer_name": METADATA_PERFORMER_NAME,
                   "composer_name": METADATA_COMPOSER_NAME,
                   "conductor_name": METADATA_CONDUCTOR_NAME,
                   "media": METADATA_MEDIA,
                   "ISRC": METADATA_ISRC,
                   "catalog": METADATA_CATALOG,
                   "copyright": METADATA_COPYRIGHT,
                   "publisher": METADATA_PUBLISHER,
                   "year": METADATA_YEAR,
                   "date": METADATA_DATE,
                   "album_number": METADATA_ALBUM_NUMBER,
                   "album_total": METADATA_ALBUM_TOTAL,
                   "comment": METADATA_COMMENT}

    def __init__(self,
                 track_name=None,
                 track_number=None,
                 track_total=None,
                 album_name=None,
                 artist_name=None,
                 performer_name=None,
                 composer_name=None,
                 conductor_name=None,
                 media=None,
                 ISRC=None,
                 catalog=None,
                 copyright=None,
                 publisher=None,
                 year=None,
                 date=None,
                 album_number=None,
                 album_total=None,
                 comment=None,
                 images=None):
        """
| field          | type    | meaning                              |
|----------------+---------+--------------------------------------|
| track_name     | unicode | the name of this individual track    |
| track_number   | integer | the number of this track             |
| track_total    | integer | the total number of tracks           |
| album_name     | unicode | the name of this track's album       |
| artist_name    | unicode | the song's original creator/composer |
| performer_name | unicode | the song's performing artist         |
| composer_name  | unicode | the song's composer name             |
| conductor_name | unicode | the song's conductor's name          |
| media          | unicode | the album's media type               |
| ISRC           | unicode | the song's ISRC                      |
| catalog        | unicode | the album's catalog number           |
| copyright      | unicode | the song's copyright information     |
| publisher      | unicode | the album's publisher                |
| year           | unicode | the album's release year             |
| date           | unicode | the original recording date          |
| album_number   | integer | the disc's volume number             |
| album_total    | integer | the total number of discs            |
| comment        | unicode | the track's comment string           |
| images         | list    | list of Image objects                |
|----------------+---------+--------------------------------------|
"""

        # we're avoiding self.foo = foo because
        # __setattr__ might need to be redefined
        # which could lead to unwelcome side-effects
        MetaData.__setattr__(self, "track_name", track_name)
        MetaData.__setattr__(self, "track_number", track_number)
        MetaData.__setattr__(self, "track_total", track_total)
        MetaData.__setattr__(self, "album_name", album_name)
        MetaData.__setattr__(self, "artist_name", artist_name)
        MetaData.__setattr__(self, "performer_name", performer_name)
        MetaData.__setattr__(self, "composer_name", composer_name)
        MetaData.__setattr__(self, "conductor_name", conductor_name)
        MetaData.__setattr__(self, "media", media)
        MetaData.__setattr__(self, "ISRC", ISRC)
        MetaData.__setattr__(self, "catalog", catalog)
        MetaData.__setattr__(self, "copyright", copyright)
        MetaData.__setattr__(self, "publisher", publisher)
        MetaData.__setattr__(self, "year", year)
        MetaData.__setattr__(self, "date", date)
        MetaData.__setattr__(self, "album_number", album_number)
        MetaData.__setattr__(self, "album_total", album_total)
        MetaData.__setattr__(self, "comment", comment)

        if (images is not None):
            MetaData.__setattr__(self, "__images__", list(images))
        else:
            MetaData.__setattr__(self, "__images__", list())

    def __repr__(self):
        fields = ["%s=%s" % (field, repr(getattr(self, field)))
                  for field in MetaData.FIELDS]
        return ("MetaData(%s)" % (
                ",".join(["%s"] * (len(MetaData.FIELDS))))) % tuple(fields)

    def __delattr__(self, field):
        if (field in self.FIELDS):
            MetaData.__setattr__(self, field, None)
        else:
            try:
                object.__delattr__(self, field)
            except KeyError:
                raise AttributeError(field)

    def fields(self):
        """yields an (attr, value) tuple per MetaData field"""

        for attr in self.FIELDS:
            yield (attr, getattr(self, attr))

    def filled_fields(self):
        """yields an (attr, value) tuple per MetaData field
        which is not blank"""

        for (attr, field) in self.fields():
            if (field is not None):
                yield (attr, field)

    def empty_fields(self):
        """yields an (attr, value) tuple per MetaData field
        which is blank"""

        for (attr, field) in self.fields():
            if (field is None):
                yield (attr, field)

    def __unicode__(self):
        table = output_table()

        SEPARATOR = u" : "

        for attr in self.FIELD_ORDER:
            if (attr == "track_number"):
                # combine track number/track total into single field
                track_number = self.track_number
                track_total = self.track_total
                if ((track_number is None) and (track_total is None)):
                    # nothing to display
                    pass
                elif ((track_number is not None) and (track_total is None)):
                    row = table.row()
                    row.add_column(self.FIELD_NAMES[attr], "right")
                    row.add_column(SEPARATOR)
                    row.add_column(unicode(track_number))
                elif ((track_number is None) and (track_total is not None)):
                    row = table.row()
                    row.add_column(self.FIELD_NAMES[attr], "right")
                    row.add_column(SEPARATOR)
                    row.add_column(u"?/%d" % (track_total,))
                else:
                    # neither track_number or track_total is None
                    row = table.row()
                    row.add_column(self.FIELD_NAMES[attr], "right")
                    row.add_column(SEPARATOR)
                    row.add_column(u"%d/%d" % (track_number, track_total))
            elif (attr == "track_total"):
                pass
            elif (attr == "album_number"):
                # combine album number/album total into single field
                album_number = self.album_number
                album_total = self.album_total
                if ((album_number is None) and (album_total is None)):
                    # nothing to display
                    pass
                elif ((album_number is not None) and (album_total is None)):
                    row = table.row()
                    row.add_column(self.FIELD_NAMES[attr], "right")
                    row.add_column(SEPARATOR)
                    row.add_column(unicode(album_number))
                elif ((album_number is None) and (album_total is not None)):
                    row = table.row()
                    row.add_column(self.FIELD_NAMES[attr], "right")
                    row.add_column(SEPARATOR)
                    row.add_column(u"?/%d" % (album_total,))
                else:
                    # neither album_number or album_total is None
                    row = table.row()
                    row.add_column(self.FIELD_NAMES[attr], "right")
                    row.add_column(SEPARATOR)
                    row.add_column(u"%d/%d" % (album_number, album_total))
            elif (attr == "album_total"):
                pass
            elif (getattr(self, attr) is not None):
                row = table.row()
                row.add_column(self.FIELD_NAMES[attr], "right")
                row.add_column(SEPARATOR)
                row.add_column(getattr(self, attr))

        # append image data, if necessary
        from audiotools.text import LAB_PICTURE

        for image in self.images():
            row = table.row()
            row.add_column(LAB_PICTURE, "right")
            row.add_column(SEPARATOR)
            row.add_column(unicode(image))

        return os.linesep.decode('ascii').join(table.format())

    def raw_info(self):
        """returns a Unicode string of low-level MetaData information

        whereas __unicode__ is meant to contain complete information
        at a very high level
        raw_info() should be more developer-specific and with
        very little adjustment or reordering to the data itself
        """

        raise NotImplementedError()

    def __eq__(self, metadata):
        for attr in MetaData.FIELDS:
            if ((not hasattr(metadata, attr)) or (getattr(self, attr) !=
                                                  getattr(metadata, attr))):
                return False
        else:
            return True

    def __ne__(self, metadata):
        return not self.__eq__(metadata)

    @classmethod
    def converted(cls, metadata):
        """converts metadata from another class to this one, if necessary

        takes a MetaData-compatible object (or None)
        and returns a new MetaData subclass with the data fields converted
        or None if metadata is None or conversion isn't possible
        for instance, VorbisComment.converted() returns a VorbisComment
        class.  This way, AudioFiles can offload metadata conversions
        """

        if (metadata is not None):
            fields = {field: getattr(metadata, field)
                      for field in cls.FIELDS}
            fields["images"] = metadata.images()
            return MetaData(**fields)
        else:
            return None

    @classmethod
    def supports_images(cls):
        """returns True if this MetaData class supports embedded images"""

        return True

    def images(self):
        """returns a list of embedded Image objects"""

        # must return a copy of our internal array
        # otherwise this will likely not act as expected when deleting
        return self.__images__[:]

    def front_covers(self):
        """returns a subset of images() which are front covers"""

        return [i for i in self.images() if i.type == FRONT_COVER]

    def back_covers(self):
        """returns a subset of images() which are back covers"""

        return [i for i in self.images() if i.type == BACK_COVER]

    def leaflet_pages(self):
        """returns a subset of images() which are leaflet pages"""

        return [i for i in self.images() if i.type == LEAFLET_PAGE]

    def media_images(self):
        """returns a subset of images() which are media images"""

        return [i for i in self.images() if i.type == MEDIA]

    def other_images(self):
        """returns a subset of images() which are other images"""

        return [i for i in self.images() if i.type == OTHER]

    def add_image(self, image):
        """embeds an Image object in this metadata

        implementations of this method should also affect
        the underlying metadata value
        (e.g. adding a new Image to FlacMetaData should add another
        METADATA_BLOCK_PICTURE block to the metadata)
        """

        if (self.supports_images()):
            self.__images__.append(image)
        else:
            from audiotools.text import ERR_PICTURES_UNSUPPORTED
            raise ValueError(ERR_PICTURES_UNSUPPORTED)

    def delete_image(self, image):
        """deletes an Image object from this metadata

        implementations of this method should also affect
        the underlying metadata value
        (e.g. removing an existing Image from FlacMetaData should
        remove that same METADATA_BLOCK_PICTURE block from the metadata)
        """

        if (self.supports_images()):
            self.__images__.pop(self.__images__.index(image))
        else:
            from audiotools.text import ERR_PICTURES_UNSUPPORTED
            raise ValueError(ERR_PICTURES_UNSUPPORTED)

    def clean(self):
        """returns a (MetaData, fixes_performed) tuple
        where MetaData is an object that's been cleaned of problems
        an fixes_performed is a list of Unicode strings.
        Problems include:

        * Remove leading or trailing whitespace from text fields
        * Remove empty fields
        * Remove leading zeroes from numerical fields
          (except when requested, in the case of ID3v2)
        * Fix incorrectly labeled image metadata fields
        """

        return (MetaData(**{field: getattr(self, field)
                            for field in MetaData.FIELDS}), [])


(FRONT_COVER, BACK_COVER, LEAFLET_PAGE, MEDIA, OTHER) = range(5)


class Image(object):
    """an image data container"""

    def __init__(self, data, mime_type, width, height,
                 color_depth, color_count, description, type):
        """fields are as follows:

        data        - plain string of the actual binary image data
        mime_type   - unicode string of the image's MIME type
        width       - width of image, as integer number of pixels
        height      - height of image, as integer number of pixels
        color_depth - color depth of image (24 for JPEG, 8 for GIF, etc.)
        color_count - number of palette colors, or 0
        description - a unicode string
        type - an integer type whose values are one of:
               FRONT_COVER
               BACK_COVER
               LEAFLET_PAGE
               MEDIA
               OTHER
        """

        self.data = data
        self.mime_type = mime_type
        self.width = width
        self.height = height
        self.color_depth = color_depth
        self.color_count = color_count
        self.description = description
        self.type = type

    def suffix(self):
        """returns the image's recommended suffix as a plain string

        for example, an image with mime_type "image/jpeg" return "jpg"
        """

        return {"image/jpeg": "jpg",
                "image/jpg": "jpg",
                "image/gif": "gif",
                "image/png": "png",
                "image/x-ms-bmp": "bmp",
                "image/tiff": "tiff"}.get(self.mime_type, "bin")

    def type_string(self):
        """returns the image's type as a human readable plain string

        for example, an image of type 0 returns "Front Cover"
        """

        return {FRONT_COVER: "Front Cover",
                BACK_COVER: "Back Cover",
                LEAFLET_PAGE: "Leaflet Page",
                MEDIA: "Media",
                OTHER: "Other"}.get(self.type, "Other")

    def __repr__(self):
        fields = ["%s=%s" % (attr, getattr(self, attr))
                  for attr in ["mime_type",
                               "width",
                               "height",
                               "color_depth",
                               "color_count",
                               "description",
                               "type"]]
        return "Image(%s)" % (",".join(fields))

    def __unicode__(self):
        return u"%s (%d\u00D7%d,'%s')" % \
               (self.type_string(),
                self.width, self.height, self.mime_type)

    @classmethod
    def new(cls, image_data, description, type):
        """builds a new Image object from raw data

        image_data is a plain string of binary image data
        description is a unicode string
        type as an image type integer

        the width, height, color_depth and color_count fields
        are determined by parsing the binary image data
        raises InvalidImage if some error occurs during parsing
        """

        from audiotools.image import image_metrics

        img = image_metrics(image_data)

        return Image(data=image_data,
                     mime_type=img.mime_type,
                     width=img.width,
                     height=img.height,
                     color_depth=img.bits_per_pixel,
                     color_count=img.color_count,
                     description=description,
                     type=type)

    def __eq__(self, image):
        if (image is not None):
            for attr in ["data", "mime_type", "width", "height",
                         "color_depth", "color_count", "description",
                         "type"]:
                if ((not hasattr(image, attr)) or (getattr(self, attr) !=
                                                   getattr(image, attr))):
                    return False
            else:
                return True
        else:
            return False

    def __ne__(self, image):
        return not self.__eq__(image)


class InvalidImage(Exception):
    """raised if an image cannot be parsed correctly"""

    def __init__(self, err):
        self.err = unicode(err)

    def __unicode__(self):
        return self.err


class ReplayGain(object):
    """a container for ReplayGain data"""

    def __init__(self, track_gain, track_peak, album_gain, album_peak):
        """values are:

        track_gain - a dB float value
        track_peak - the highest absolute value PCM sample, as a float
        album_gain - a dB float value
        album_peak - the highest absolute value PCM sample, as a float

        they are also attributes
        """

        self.track_gain = float(track_gain)
        self.track_peak = float(track_peak)
        self.album_gain = float(album_gain)
        self.album_peak = float(album_peak)

    def __repr__(self):
        return "ReplayGain(%s,%s,%s,%s)" % \
            (self.track_gain, self.track_peak,
             self.album_gain, self.album_peak)

    def __eq__(self, rg):
        if (isinstance(rg, ReplayGain)):
            return ((self.track_gain == rg.track_gain) and
                    (self.track_peak == rg.track_peak) and
                    (self.album_gain == rg.album_gain) and
                    (self.album_peak == rg.album_peak))
        else:
            return False

    def __ne__(self, rg):
        return not self.__eq__(rg)


class UnsupportedTracknameField(Exception):
    """raised by AudioFile.track_name()
    if its format string contains unknown fields"""

    def __init__(self, field):
        self.field = field

    def error_msg(self, messenger):
        from audiotools.text import (ERR_UNKNOWN_FIELD,
                                     LAB_SUPPORTED_FIELDS)

        messenger.error(ERR_UNKNOWN_FIELD % (self.field,))
        messenger.info(LAB_SUPPORTED_FIELDS)
        for field in sorted(MetaData.FIELDS +
                            ("album_track_number", "suffix")):
            if (field == 'track_number'):
                messenger.info(u"%(track_number)2.2d")
            else:
                messenger.info(u"%%(%s)s" % (field))

        messenger.info(u"%(basename)s")


class InvalidFilenameFormat(Exception):
    """raised by AudioFile.track_name()
    if its format string contains broken fields"""

    def __unicode__(self):
        from audiotools.text import ERR_INVALID_FILENAME_FORMAT
        return ERR_INVALID_FILENAME_FORMAT


class AudioFile(object):
    """an abstract class representing audio files on disk

    this class should be extended to handle different audio
    file formats"""

    SUFFIX = ""
    NAME = ""
    DESCRIPTION = u""
    DEFAULT_COMPRESSION = ""
    COMPRESSION_MODES = ("",)
    COMPRESSION_DESCRIPTIONS = {}
    BINARIES = tuple()
    BINARY_URLS = {}
    REPLAYGAIN_BINARIES = tuple()

    def __init__(self, filename):
        """filename is a plain string

        raises InvalidFile or subclass if the file is invalid in some way"""

        self.filename = filename

    # AudioFiles support a sorting rich compare
    # which prioritizes album_number, track_number and then filename
    # missing fields sort before non-missing fields
    # use pcm_frame_cmp to compare the contents of two files

    def __sort_key__(self):
        metadata = self.get_metadata()
        return ((metadata.album_number if
                 ((metadata is not None) and
                  (metadata.album_number is not None)) else -sys.maxint - 1),
                (metadata.track_number if
                 ((metadata is not None) and
                  (metadata.track_number is not None)) else -sys.maxint - 1),
                self.filename)

    def __eq__(self, audiofile):
        if (isinstance(audiofile, AudioFile)):
            return (self.__sort_key__() == audiofile.__sort_key__())
        else:
            raise TypeError("cannot compare %s and %s" %
                            (repr(self), repr(audiofile)))

    def __ne__(self, audiofile):
        return not self.__eq__(audiofile)

    def __lt__(self, audiofile):
        if (isinstance(audiofile, AudioFile)):
            return (self.__sort_key__() < audiofile.__sort_key__())
        else:
            raise TypeError("cannot compare %s and %s" %
                            (repr(self), repr(audiofile)))

    def __le__(self, audiofile):
        if (isinstance(audiofile, AudioFile)):
            return (self.__sort_key__() <= audiofile.__sort_key__())
        else:
            raise TypeError("cannot compare %s and %s" %
                            (repr(self), repr(audiofile)))

    def __gt__(self, audiofile):
        if (isinstance(audiofile, AudioFile)):
            return (self.__sort_key__() > audiofile.__sort_key__())
        else:
            raise TypeError("cannot compare %s and %s" %
                            (repr(self), repr(audiofile)))

    def __ge__(self, audiofile):
        if (isinstance(audiofile, AudioFile)):
            return (self.__sort_key__() >= audiofile.__sort_key__())
        else:
            raise TypeError("cannot compare %s and %s" %
                            (repr(self), repr(audiofile)))

    def __gt__(self, audiofile):
        if (isinstance(audiofile, AudioFile)):
            return (self.__sort_key__() > audiofile.__sort_key__())
        else:
            raise TypeError("cannot compare %s and %s" %
                            (repr(self), repr(audiofile)))

    def bits_per_sample(self):
        """returns an integer number of bits-per-sample this track contains"""

        raise NotImplementedError()

    def channels(self):
        """returns an integer number of channels this track contains"""

        raise NotImplementedError()

    def channel_mask(self):
        """returns a ChannelMask object of this track's channel layout"""

        # WARNING - This only returns valid masks for 1 and 2 channel audio
        # anything over 2 channels raises a ValueError
        # since there isn't any standard on what those channels should be.
        # AudioFiles that support more than 2 channels should override
        # this method with one that returns the proper mask.
        return ChannelMask.from_channels(self.channels())

    def lossless(self):
        """returns True if this track's data is stored losslessly"""

        raise NotImplementedError()

    @classmethod
    def supports_metadata(cls):
        """returns True if this audio type supports MetaData"""

        return False

    def update_metadata(self, metadata):
        """takes this track's current MetaData object
        as returned by get_metadata() and sets this track's metadata
        with any fields updated in that object

        raises IOError if unable to write the file
        """

        # this is a sort of low-level implementation
        # which assumes higher-level routines have
        # modified metadata properly

        if (metadata is not None):
            raise NotImplementedError()
        else:
            raise ValueError(ERR_FOREIGN_METADATA)

    def set_metadata(self, metadata):
        """takes a MetaData object and sets this track's metadata

        this metadata includes track name, album name, and so on
        raises IOError if unable to write the file"""

        # this is a higher-level implementation
        # which assumes metadata is from a different audio file
        # or constructed from scratch and converts it accordingly
        # before passing it on to update_metadata()

        pass

    def get_metadata(self):
        """returns a MetaData object, or None

        raises IOError if unable to read the file"""

        return None

    def delete_metadata(self):
        """deletes the track's MetaData

        this removes or unsets tags as necessary in order to remove all data
        raises IOError if unable to write the file"""

        pass

    def total_frames(self):
        """returns the total PCM frames of the track as an integer"""

        raise NotImplementedError()

    def cd_frames(self):
        """returns the total length of the track in CD frames

        each CD frame is 1/75th of a second"""

        try:
            return (self.total_frames() * 75) // self.sample_rate()
        except ZeroDivisionError:
            return 0

    def seconds_length(self):
        """returns the length of the track as a Fraction number of seconds"""

        from fractions import Fraction

        if (self.sample_rate() > 0):
            return Fraction(self.total_frames(), self.sample_rate())
        else:
            # this shouldn't happen, but just in case
            return Fraction(0, 1)

    def sample_rate(self):
        """returns the rate of the track's audio as an integer number of Hz"""

        raise NotImplementedError()

    def to_pcm(self):
        """returns a PCMReader object containing the track's PCM data

        if an error occurs initializing a decoder, this should
        return a PCMReaderError with an appropriate error message"""

        raise NotImplementedError()

    @classmethod
    def from_pcm(cls, filename, pcmreader,
                 compression=None,
                 total_pcm_frames=None):
        """encodes a new file from PCM data

        takes a filename string, PCMReader object
        optional compression level string,
        and optional total_pcm_frames integer
        encodes a new audio file from pcmreader's data
        at the given filename with the specified compression level
        and returns a new AudioFile-compatible object

        specifying total_pcm_frames, when the number is known in advance,
        may allow the encoder to work more efficiently but is never required

        for example, to encode the FlacAudio file "file.flac" from "file.wav"
        at compression level "5":

        >>> flac = FlacAudio.from_pcm("file.flac",
        ...                           WaveAudio("file.wav").to_pcm(),
        ...                           "5")

        may raise EncodingError if some problem occurs when
        encoding the input file.  This includes an error
        in the input stream, a problem writing the output file,
        or even an EncodingError subclass such as
        "UnsupportedBitsPerSample" if the input stream
        is formatted in a way this class is unable to support
        """

        raise NotImplementedError()

    def convert(self, target_path, target_class,
                compression=None, progress=None):
        """encodes a new AudioFile from existing AudioFile

        take a filename string, target class and optional compression string
        encodes a new AudioFile in the target class and returns
        the resulting object
        may raise EncodingError if some problem occurs during encoding"""

        return target_class.from_pcm(
            target_path,
            to_pcm_progress(self, progress),
            compression,
            total_pcm_frames=(self.total_frames() if self.lossless()
                              else None))

    def seekable(self):
        """returns True if the file is seekable

        that is, if its PCMReader has a .seek() method
        and that method supports some sort of fine-grained seeking
        when the PCMReader is working from on-disk files"""

        return False

    @classmethod
    def __unlink__(cls, filename):
        try:
            os.unlink(filename)
        except OSError:
            pass

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
        contains invalid template fields

        raises InvalidFilenameFormat if the format string
        has broken template fields"""

        if (format is None):
            format = FILENAME_FORMAT
        if (suffix is None):
            suffix = cls.SUFFIX
        try:
            if (track_metadata is not None):
                track_number = (track_metadata.track_number
                                if track_metadata.track_number is not None
                                else 0)
                album_number = (track_metadata.album_number
                                if track_metadata.album_number is not None
                                else 0)
                track_total = (track_metadata.track_total
                               if track_metadata.track_total is not None
                               else 0)
                album_total = (track_metadata.album_total
                               if track_metadata.album_total is not None
                               else 0)
            else:
                track_number = 0
                album_number = 0
                track_total = 0
                album_total = 0

            format_dict = {u"track_number": track_number,
                           u"album_number": album_number,
                           u"track_total": track_total,
                           u"album_total": album_total,
                           u"suffix": suffix.decode('ascii')}

            if (album_number == 0):
                format_dict[u"album_track_number"] = u"%2.2d" % (track_number)
            else:
                album_digits = len(str(album_total))

                format_dict[u"album_track_number"] = (
                    u"%%%(album_digits)d.%(album_digits)dd%%2.2d" %
                    {"album_digits": album_digits} %
                    (album_number, track_number))

            if (track_metadata is not None):
                for field in track_metadata.FIELDS:
                    if ((field != "suffix") and (field not in
                                                 MetaData.INTEGER_FIELDS)):
                        if (getattr(track_metadata, field) is not None):
                            format_dict[field.decode('ascii')] = getattr(
                                track_metadata,
                                field).replace(u'/',
                                               u'-').replace(unichr(0),
                                                             u' ')
                        else:
                            format_dict[field.decode('ascii')] = u""
            else:
                for field in MetaData.FIELDS:
                    if (field not in MetaData.INTEGER_FIELDS):
                        format_dict[field.decode('ascii')] = u""

            format_dict[u"basename"] = os.path.splitext(
                os.path.basename(file_path))[0].decode(FS_ENCODING,
                                                       'replace')

            # apply format dictionary and ensure filename isn't absolute
            return (format.decode('utf-8', 'replace') % format_dict).encode(
                FS_ENCODING, 'replace').lstrip(os.sep)
        except KeyError as error:
            raise UnsupportedTracknameField(unicode(error.args[0]))
        except TypeError:
            raise InvalidFilenameFormat()
        except ValueError:
            raise InvalidFilenameFormat()

    @classmethod
    def supports_replay_gain(cls):
        """returns True if this class supports ReplayGain"""

        # implement this in subclass if necessary
        return False

    def get_replay_gain(self):
        """returns a ReplayGain object of our ReplayGain values

        returns None if we have no values

        may raise IOError if unable to read the file"""

        # implement this in subclass if necessary
        return None

    def set_replay_gain(self, replaygain):
        """given a ReplayGain object, sets the track's gain to those values

        may raise IOError if unable to modify the file"""

        # implement this in subclass if necessary
        pass

    def delete_replay_gain(self):
        """removes ReplayGain values from file, if any

        may raise IOError if unable to modify the file"""

        # implement this in subclass if necessary
        pass

    @classmethod
    def supports_cuesheet(self):
        """returns True if the audio format supports embedded Sheet objects"""

        return False

    def set_cuesheet(self, cuesheet):
        """imports cuesheet data from a Sheet object

        Raises IOError if an error occurs setting the cuesheet"""

        pass

    def get_cuesheet(self):
        """returns the embedded Cuesheet-compatible object, or None

        Raises IOError if a problem occurs when reading the file"""

        return None

    def delete_cuesheet(self):
        """deletes embedded Sheet object, if any

        Raises IOError if a problem occurs when updating the file"""

        pass

    def verify(self, progress=None):
        """verifies the current file for correctness

        returns True if the file is okay
        raises an InvalidFile with an error message if there is
        some problem with the file"""

        try:
            total_frames = self.total_frames()
            decoder = self.to_pcm()
            pcm_frame_count = 0
            framelist = decoder.read(FRAMELIST_SIZE)
            while (len(framelist) > 0):
                pcm_frame_count += framelist.frames
                if (progress is not None):
                    progress(pcm_frame_count, total_frames)
                framelist = decoder.read(FRAMELIST_SIZE)
        except (IOError, ValueError) as err:
            raise InvalidFile(str(err))

        try:
            decoder.close()
        except DecodingError as err:
            raise InvalidFile(err.error_message)

        if (self.lossless()):
            if (pcm_frame_count == total_frames):
                return True
            else:
                raise InvalidFile("incorrect PCM frame count")
        else:
            return True

    @classmethod
    def available(cls, system_binaries):
        """returns True if all necessary compenents are available
        to support format"""

        for command in cls.BINARIES:
            if (not system_binaries.can_execute(system_binaries[command])):
                return False
        else:
            return True

    @classmethod
    def missing_components(cls, messenger):
        """given a Messenger object, displays missing binaries or libraries
        needed to support this format and where to get them"""

        binaries = cls.BINARIES
        urls = cls.BINARY_URLS
        format_ = cls.NAME.decode('ascii')

        if (len(binaries) == 0):
            # no binaries, so they can't be missing, so nothing to display
            pass
        elif (len(binaries) == 1):
            # one binary has only a single URL to display
            from audiotools.text import (ERR_PROGRAM_NEEDED,
                                         ERR_PROGRAM_DOWNLOAD_URL,
                                         ERR_PROGRAM_PACKAGE_MANAGER)
            messenger.info(
                ERR_PROGRAM_NEEDED %
                {"program": u"\"%s\"" % (binaries[0].decode('ascii')),
                 "format": format_})
            messenger.info(
                ERR_PROGRAM_DOWNLOAD_URL %
                {"program": binaries[0].decode('ascii'),
                 "url": urls[binaries[0]]})
            messenger.info(ERR_PROGRAM_PACKAGE_MANAGER)
        else:
            # multiple binaries may have one or more URLs to display
            from audiotools.text import (ERR_PROGRAMS_NEEDED,
                                         ERR_PROGRAMS_DOWNLOAD_URL,
                                         ERR_PROGRAM_DOWNLOAD_URL,
                                         ERR_PROGRAM_PACKAGE_MANAGER)
            messenger.info(
                ERR_PROGRAMS_NEEDED %
                {"programs": u", ".join([u"\"%s\"" % (b.decode('ascii'))
                                         for b in binaries]),
                 "format": format_})
            if (len({urls[b] for b in binaries}) == 1):
                # if they all come from one URL (like Vorbis tools)
                # display only that URL
                messenger.info(
                    ERR_PROGRAMS_DOWNLOAD_URL % {"url": urls[binaries[0]]})
            else:
                # otherwise, display the URL for each binary
                for b in binaries:
                    messenger.info(
                        ERR_PROGRAM_DOWNLOAD_URL %
                        {"program": b.decode('ascii'),
                         "url": urls[b]})
            messenger.info(ERR_PROGRAM_PACKAGE_MANAGER)

    def clean(self, output_filename=None):
        """cleans the file of known data and metadata problems

        output_filename is an optional filename of the fixed file
        if present, a new AudioFile is written to that path
        otherwise, only a dry-run is performed and no new file is written

        return list of fixes performed as Unicode strings

        raises IOError if unable to write the file or its metadata
        raises ValueError if the file has errors of some sort
        """

        if (output_filename is None):
            # dry run only
            metadata = self.get_metadata()
            if (metadata is not None):
                (metadata, fixes) = metadata.clean()
                return fixes
            else:
                return []
        else:
            # perform full fix
            input_f = __open__(self.filename, "rb")
            output_f = __open__(output_filename, "wb")
            try:
                transfer_data(input_f.read, output_f.write)
            finally:
                input_f.close()
                output_f.close()

            new_track = open(output_filename)
            metadata = self.get_metadata()
            if (metadata is not None):
                (metadata, fixes) = metadata.clean()
                new_track.set_metadata(metadata)
                return fixes
            else:
                return []


class WaveContainer(AudioFile):
    def has_foreign_wave_chunks(self):
        """returns True if the file has RIFF chunks
        other than 'fmt ' and 'data'
        which must be preserved during conversion"""

        raise NotImplementedError()

    def wave_header_footer(self):
        """returns (header, footer) tuple of strings
        containing all data before and after the PCM stream

        may raise ValueError if there's a problem with
        the header or footer data
        may raise IOError if there's a problem reading
        header or footer data from the file
        """

        raise NotImplementedError()

    @classmethod
    def from_wave(cls, filename, header, pcmreader, footer, compression=None):
        """encodes a new file from wave data

        takes a filename string, header string,
        PCMReader object, footer string
        and optional compression level string
        encodes a new audio file from pcmreader's data
        at the given filename with the specified compression level
        and returns a new WaveAudio object

        header + pcm data + footer should always result
        in the original wave file being restored
        without need for any padding bytes

        may raise EncodingError if some problem occurs when
        encoding the input file"""

        raise NotImplementedError()

    def convert(self, target_path, target_class, compression=None,
                progress=None):
        """encodes a new AudioFile from existing AudioFile

        take a filename string, target class and optional compression string
        encodes a new AudioFile in the target class and returns
        the resulting object
        may raise EncodingError if some problem occurs during encoding"""

        if ((self.has_foreign_wave_chunks() and
             hasattr(target_class, "from_wave") and
             callable(target_class.from_wave))):
            # transfer header and footer when performing PCM conversion
            try:
                (header, footer) = self.wave_header_footer()
            except (ValueError, IOError) as err:
                raise EncodingError(unicode(err))

            return target_class.from_wave(target_path,
                                          header,
                                          to_pcm_progress(self, progress),
                                          footer,
                                          compression)
        else:
            # perform standard PCM conversion instead
            return target_class.from_pcm(
                target_path,
                to_pcm_progress(self, progress),
                compression,
                total_pcm_frames=(self.total_frames() if self.lossless()
                                  else None))


class AiffContainer(AudioFile):
    def has_foreign_aiff_chunks(self):
        """returns True if the file has AIFF chunks
        other than 'COMM' and 'SSND'
        which must be preserved during conversion"""

        raise NotImplementedError()

    def aiff_header_footer(self):
        """returns (header, footer) tuple of strings
        containing all data before and after the PCM stream

        may raise ValueError if there's a problem with
        the header or footer data
        may raise IOError if there's a problem reading
        header or footer data from the file"""

        raise NotImplementedError()

    @classmethod
    def from_aiff(cls, filename, header, pcmreader, footer, compression=None):
        """encodes a new file from AIFF data

        takes a filename string, header string,
        PCMReader object, footer string
        and optional compression level string
        encodes a new audio file from pcmreader's data
        at the given filename with the specified compression level
        and returns a new AiffAudio object

        header + pcm data + footer should always result
        in the original AIFF file being restored
        without need for any padding bytes

        may raise EncodingError if some problem occurs when
        encoding the input file"""

        raise NotImplementedError()

    def convert(self, target_path, target_class, compression=None,
                progress=None):
        """encodes a new AudioFile from existing AudioFile

        take a filename string, target class and optional compression string
        encodes a new AudioFile in the target class and returns
        the resulting object
        may raise EncodingError if some problem occurs during encoding"""

        if ((self.has_foreign_aiff_chunks() and
             hasattr(target_class, "from_aiff") and
             callable(target_class.from_aiff))):
            # transfer header and footer when performing PCM conversion

            try:
                (header, footer) = self.aiff_header_footer()
            except (ValueError, IOError) as err:
                raise EncodingError(unicode(err))

            return target_class.from_aiff(target_path,
                                          header,
                                          to_pcm_progress(self, progress),
                                          footer,
                                          compression)
        else:
            # perform standard PCM conversion instead
            return target_class.from_pcm(
                target_path,
                to_pcm_progress(self, progress),
                compression,
                total_pcm_frames=(self.total_frames() if self.lossless()
                                  else None))


class SheetException(ValueError):
    """a parent exception for CueException and TOCException"""

    pass


def read_sheet(filename):
    """returns Sheet-compatible object from a .cue or .toc file

    may raise a SheetException if the file cannot be parsed correctly"""

    try:
        return read_sheet_string(__open__(filename, "rb").read())
    except IOError:
        from audiotools.text import ERR_CUE_IOERROR
        raise SheetException(ERR_CUE_IOERROR)


def read_sheet_string(sheet_string):
    """given a string of cuesheet data, returns a Sheet-compatible object

    may raise a SheetException if the file cannot be parsed correctly"""

    if ("CD_DA" in sheet_string):
        from audiotools.toc import read_tocfile_string

        return read_tocfile_string(sheet_string)
    else:
        from audiotools.cue import read_cuesheet_string

        return read_cuesheet_string(sheet_string)


class Sheet(object):
    """an object representing a CDDA layout
    such as provided by a .cue or .toc file"""

    def __init__(self, sheet_tracks, metadata=None):
        """sheet_tracks is a list of SheetTrack objects
        metadata is a MetaData object, or None"""

        self.__sheet_tracks__ = sheet_tracks
        self.__metadata__ = metadata

    @classmethod
    def converted(cls, sheet):
        """given a Sheet-compatible object, returns a Sheet"""

        return cls(sheet_tracks=map(SheetTrack.converted, sheet),
                   metadata=sheet.get_metadata())

    def __repr__(self):
        return "Sheet(sheet_tracks=%s, metadata=%s)" % \
            (repr(self.__sheet_tracks__), repr(self.__metadata__))

    def __len__(self):
        return len(self.__sheet_tracks__)

    def __getitem__(self, index):
        return self.__sheet_tracks__[index]

    def __eq__(self, sheet):
        try:
            if (self.get_metadata() != sheet.get_metadata()):
                return False
            if (len(self) != len(sheet)):
                return False
            for (t1, t2) in zip(self, sheet):
                if (t1 != t2):
                    return False
            else:
                return True
        except (AttributeError, TypeError):
            return False

    def track_numbers(self):
        """returns a list of all track numbers in the sheet"""

        return [track.number() for track in self]

    def track(self, track_number):
        """given a track_number (typically starting from 1),
        returns a SheetTrack object or raises KeyError if not found"""

        for track in self:
            if (track_number == track.number()):
                return track
        else:
            raise KeyError(track_number)

    def pre_gap(self):
        """returns the pre-gap of the entire disc
        as a Fraction number of seconds"""

        indexes = self.track(1)
        if ((indexes[0].number() == 0) and (indexes[1].number() == 1)):
            return (indexes[1].offset() - indexes[0].offset())
        else:
            from fractions import Fraction
            return Fraction(0, 1)

    def track_offset(self, track_number):
        """given a track_number (typically starting from 1)
        returns the offset to that track from the start of the stream
        as a Fraction number of seconds

        may raise KeyError if the track is not found"""

        return self.track(track_number).index(1).offset()

    def track_length(self, track_number):
        """given a track_number (typically starting from 1)
        returns the length of the track as a Fraction number of seconds
        or None if the length is to the remainder of the stream
        (typically for the last track in the album)

        may raise KeyError if the track is not found"""

        initial_track = self.track(track_number)
        if ((track_number + 1) in self.track_numbers()):
            next_track = self.track(track_number + 1)
            return (next_track.index(1).offset() -
                    initial_track.index(1).offset())
        else:
            # no next track, so total length is unknown
            return None

    def image_formatted(self):
        """returns True if all tracks are for the same file
        and have ascending index points"""

        initial_filename = None
        previous_index = None
        for track in self:
            if (initial_filename is None):
                initial_filename = track.filename()
            elif (initial_filename != track.filename()):
                return False
            for index in track:
                if (previous_index is None):
                    previous_index = index.offset()
                elif (previous_index >= index.offset()):
                    return False
                else:
                    previous_index = index.offset()
        else:
            return True

    def get_metadata(self):
        """returns MetaData of Sheet, or None
        this metadata often contains information such as catalog number
        or CD-TEXT values"""

        return self.__metadata__


class SheetTrack(object):
    def __init__(self, number,
                 track_indexes,
                 metadata=None,
                 filename="CDImage.wav",
                 is_audio=True,
                 pre_emphasis=False,
                 copy_permitted=False):
        """
| argument       | type         | value                                 |
|----------------+--------------+---------------------------------------|
| number         | int          | track number, starting from 1         |
| track_indexes  | [SheetIndex] | list of SheetIndex objects            |
| metadata       | MetaData     | track's metadata, or None             |
| filename       | str          | track's filename on disc              |
| is_audio       | boolean      | whether track contains audio data     |
| pre_emphasis   | boolean      | whether track has pre-emphasis        |
| copy_permitted | boolean      | whether copying is permitted          |
        """

        self.__number__ = number
        self.__track_indexes__ = list(track_indexes)
        self.__metadata__ = metadata
        self.__filename__ = filename
        self.__is_audio__ = is_audio
        self.__pre_emphasis__ = pre_emphasis
        self.__copy_permitted__ = copy_permitted

    @classmethod
    def converted(cls, sheet_track):
        """Given a SheetTrack-compatible object, returns a SheetTrack"""

        return cls(number=sheet_track.number(),
                   track_indexes=map(SheetIndex.converted, sheet_track),
                   metadata=sheet_track.get_metadata(),
                   filename=sheet_track.filename(),
                   is_audio=sheet_track.is_audio(),
                   pre_emphasis=sheet_track.pre_emphasis(),
                   copy_permitted=sheet_track.copy_permitted())

    def __repr__(self):
        return "SheetTrack(%s)" % \
            ", ".join(["%s=%s" % (attr,
                                  repr(getattr(self, "__" + attr + "__")))
                       for attr in ["number",
                                    "track_indexes",
                                    "metadata",
                                    "filename",
                                    "is_audio",
                                    "pre_emphasis",
                                    "copy_permitted"]])

    def __len__(self):
        return len(self.__track_indexes__)

    def __getitem__(self, i):
        return self.__track_indexes__[i]

    def indexes(self):
        """returns a list of all indexes in the current track"""

        return [index.number() for index in self]

    def index(self, index_number):
        """given an index_number (0 for pre-gap, 1 for track start, etc.)
        returns a SheetIndex object or raises KeyError if not found"""

        for sheet_index in self:
            if (index_number == sheet_index.number()):
                return sheet_index
        else:
            raise KeyError(index_number)

    def __eq__(self, sheet_track):
        try:
            for method in ["number",
                           "is_audio",
                           "pre_emphasis",
                           "copy_permitted"]:
                if (getattr(self, method)() != getattr(sheet_track, method)()):
                    return False

            if (len(self) != len(sheet_track)):
                return False
            for (t1, t2) in zip(self, sheet_track):
                if (t1 != t2):
                    return False
            else:
                return True
        except (AttributeError, TypeError):
            return False

    def __ne__(self, sheet_track):
        return not self.__eq__(sheet_track)

    def number(self):
        """return SheetTrack's number, starting from 1"""

        return self.__number__

    def get_metadata(self):
        """returns SheetTrack's MetaData, or None"""

        return self.__metadata__

    def filename(self):
        """returns SheetTrack's filename as a string"""

        return self.__filename__

    def is_audio(self):
        """returns whether SheetTrack contains audio data"""

        return self.__is_audio__

    def pre_emphasis(self):
        """returns whether SheetTrack has pre-emphasis"""

        return self.__pre_emphasis__

    def copy_permitted(self):
        """returns whether copying is permitted"""

        return self.__copy_permitted__


class SheetIndex(object):
    def __init__(self, number, offset):
        """number is the index number, 0 for pre-gap index

        offset is the offset from the start of the stream
        as a Fraction number of seconds"""

        self.__number__ = number
        self.__offset__ = offset

    @classmethod
    def converted(cls, sheet_index):
        """given a SheetIndex-compatible object, returns a SheetIndex"""

        return cls(number=sheet_index.number(),
                   offset=sheet_index.offset())

    def __repr__(self):
        return "SheetIndex(number=%s, offset=%s)" % \
            (repr(self.__number__), repr(self.__offset__))

    def __eq__(self, sheet_index):
        try:
            return ((self.number() == sheet_index.number()) and
                    (self.offset() == sheet_index.offset()))
        except (TypeError, AttributeError):
            return False

    def __ne__(self, sheet_index):
        return not self.__eq__(sheet_index)

    def number(self):
        return self.__number__

    def offset(self):
        return self.__offset__


def iter_first(iterator):
    """yields a (is_first, item) per item in the iterator

    where is_first indicates whether the item is the first one

    if the iterator has no items, yields (True, None)
    """

    for (i, v) in enumerate(iterator):
        yield ((i == 0), v)


def iter_last(iterator):
    """yields a (is_last, item) per item in the iterator

    where is_last indicates whether the item is the final one

    if the iterator has no items, yields (True, None)
    """

    iterator = iter(iterator)

    try:
        cached_item = iterator.next()
    except StopIteration:
        return

    while (True):
        try:
            next_item = iterator.next()
            yield (False, cached_item)
            cached_item = next_item
        except StopIteration:
            yield (True, cached_item)
            return


def PCMReaderWindow(pcmreader, initial_offset, pcm_frames):
    if (initial_offset == 0):
        return PCMReaderHead(pcmreader, pcm_frames)
    else:
        return PCMReaderHead(PCMReaderDeHead(pcmreader, initial_offset),
                             pcm_frames)


class PCMReaderHead(object):
    """a wrapper around PCMReader for truncating a stream's ending"""

    def __init__(self, pcmreader, pcm_frames):
        """pcmreader is a PCMReader object
        pcm_frames is the total number of PCM frames in the stream

        if pcm_frames is shorter than the pcmreader's stream,
        the stream will be truncated

        if pcm_frames is longer than the pcmreader's stream,
        the stream will be extended with additional empty frames"""

        if (pcm_frames < 0):
            raise ValueError("invalid pcm_frames value")

        self.pcmreader = pcmreader
        self.sample_rate = pcmreader.sample_rate
        self.channels = pcmreader.channels
        self.channel_mask = pcmreader.channel_mask
        self.bits_per_sample = pcmreader.bits_per_sample
        self.pcm_frames = pcm_frames

    def __repr__(self):
        return "PCMReaderHead(%s, %s)" % (repr(self.pcmreader),
                                          self.pcm_frames)

    def read(self, pcm_frames):
        if (self.pcm_frames > 0):
            # data left in window
            # so try to read an additional frame from PCMReader
            frame = self.pcmreader.read(pcm_frames)
            if (frame.frames == 0):
                # no additional data in PCMReader,
                # so return empty frames leftover in window
                # and close window
                frame = pcm.from_list([0] * (self.pcm_frames * self.channels),
                                      self.channels,
                                      self.bits_per_sample,
                                      True)
                self.pcm_frames -= frame.frames
                return frame
            elif (frame.frames <= self.pcm_frames):
                # frame is shorter than remaining window,
                # so shrink window and return frame unaltered
                self.pcm_frames -= frame.frames
                return frame
            else:
                # frame is larger than remaining window,
                # so cut off end of frame
                # close window and return shrunk frame
                frame = frame.split(self.pcm_frames)[0]
                self.pcm_frames -= frame.frames
                return frame
        else:
            # window exhausted, so return empty framelist
            return pcm.FrameList("",
                                 self.channels,
                                 self.bits_per_sample,
                                 True,
                                 True)

    def read_closed(self, pcm_frames):
        raise ValueError()

    def close(self):
        self.pcmreader.close()
        self.read = self.read_closed


class PCMReaderDeHead(object):
    """a wrapper around PCMReader for truncating a stream's beginning"""

    def __init__(self, pcmreader, pcm_frames):
        """pcmreader is a PCMReader object
        pcm_frames is the total number of PCM frames to remove

        if pcm_frames is positive, that amount of frames will be
        removed from the beginning of the stream

        if pcm_frames is negative, the stream will be padded
        with that many PCM frames"""

        self.pcmreader = pcmreader
        self.sample_rate = pcmreader.sample_rate
        self.channels = pcmreader.channels
        self.channel_mask = pcmreader.channel_mask
        self.bits_per_sample = pcmreader.bits_per_sample
        self.pcm_frames = pcm_frames

    def __repr__(self):
        return "PCMReaderDeHead(%s, %s)" % (repr(self.pcmreader),
                                            self.pcm_frames)

    def read(self, pcm_frames):
        if (self.pcm_frames == 0):
            # no truncation or padding, so return framelists as-is
            return self.pcmreader.read(pcm_frames)
        elif (self.pcm_frames > 0):
            # remove PCM frames from beginning of stream
            # until all truncation is accounted for
            while (self.pcm_frames > 0):
                frame = self.pcmreader.read(pcm_frames)
                if (frame.frames == 0):
                    # truncation longer than entire stream
                    # so don't try to truncate it any further
                    self.pcm_frames = 0
                    return frame
                elif (frame.frames <= self.pcm_frames):
                    self.pcm_frames -= frame.frames
                else:
                    (head, tail) = frame.split(self.pcm_frames)
                    self.pcm_frames -= head.frames
                    assert(self.pcm_frames == 0)
                    assert(tail.frames > 0)
                    return tail
            else:
                return self.pcmreader.read(pcm_frames)
        else:
            # pad beginning of stream with empty PCM frames
            frame = pcm.from_list([0] *
                                  (-self.pcm_frames) * self.channels,
                                  self.channels,
                                  self.bits_per_sample,
                                  True)
            assert(frame.frames == -self.pcm_frames)
            self.pcm_frames = 0
            return frame

    def read_closed(self, pcm_frames):
        raise ValueError()

    def close(self):
        self.pcmreader.close()
        self.read = self.read_closed


# returns the value in item_list which occurs most often
def most_numerous(item_list, empty_list=None, all_differ=None):
    """returns the value in the item list which occurs most often
    if list has no items, returns 'empty_list'
    if all items differ, returns 'all_differ'"""

    counts = {}

    if (len(item_list) == 0):
        return empty_list

    for item in item_list:
        counts.setdefault(item, []).append(item)

    (item,
     max_count) = sorted([(item, len(counts[item])) for item in counts.keys()],
                         key=lambda pair: pair[1])[-1]
    if ((max_count < len(item_list)) and (max_count == 1)):
        return all_differ
    else:
        return item


def metadata_lookup(musicbrainz_disc_id,
                    freedb_disc_id,
                    musicbrainz_server="musicbrainz.org",
                    musicbrainz_port=80,
                    freedb_server="us.freedb.org",
                    freedb_port=80,
                    use_musicbrainz=True,
                    use_freedb=True):
    """generates a set of MetaData objects from CD

    first_track_number and last_track_number are positive ints
    offsets is a list of track offsets, in CD frames
    lead_out_offset is the offset of the "lead-out" track, in CD frames
    total_length is the total length of the disc, in CD frames

    returns a metadata[c][t] list of lists
    where 'c' is a possible choice
    and 't' is the MetaData for a given track (starting from 0)

    this will always return at least one choice,
    which may be a list of largely empty MetaData objects
    if no match can be found for the CD
    """

    assert(musicbrainz_disc_id.offsets == freedb_disc_id.offsets)

    matches = []

    # MusicBrainz takes precedence over FreeDB
    if (use_musicbrainz):
        import audiotools.musicbrainz as musicbrainz
        from urllib2 import HTTPError
        from xml.parsers.expat import ExpatError
        try:
            matches.extend(
                musicbrainz.perform_lookup(
                    disc_id=musicbrainz_disc_id,
                    musicbrainz_server=musicbrainz_server,
                    musicbrainz_port=musicbrainz_port))
        except (HTTPError, ExpatError):
            pass

    if (use_freedb):
        import audiotools.freedb as freedb
        from urllib2 import HTTPError
        try:
            matches.extend(
                freedb.perform_lookup(
                    disc_id=freedb_disc_id,
                    freedb_server=freedb_server,
                    freedb_port=freedb_port))
        except (HTTPError, ValueError):
            pass

    if (len(matches) == 0):
        # no matches, so build a set of dummy metadata
        track_count = len(musicbrainz_disc_id.offsets)
        return [[MetaData(track_number=i, track_total=track_count)
                 for i in range(1, track_count + 1)]]
    else:
        return matches


def cddareader_metadata_lookup(cddareader,
                               musicbrainz_server="musicbrainz.org",
                               musicbrainz_port=80,
                               freedb_server="us.freedb.org",
                               freedb_port=80,
                               use_musicbrainz=True,
                               use_freedb=True):
    """given a CDDAReader object
    returns a metadata[c][t] list of lists
    where 'c' is a possible choice
    and 't' is the MetaData for a given track (starting from 0)

    this will always return at least once choice,
    which may be a list of largely empty MetaData objects
    if no match can be found for the CD
    """

    from audiotools.freedb import DiscID as FDiscID
    from audiotools.musicbrainz import DiscID as MDiscID

    return metadata_lookup(
        freedb_disc_id=FDiscID.from_cddareader(cddareader),
        musicbrainz_disc_id=MDiscID.from_cddareader(cddareader),
        musicbrainz_server=musicbrainz_server,
        musicbrainz_port=musicbrainz_port,
        freedb_server=freedb_server,
        freedb_port=freedb_port,
        use_musicbrainz=use_musicbrainz,
        use_freedb=use_freedb)


def track_metadata_lookup(audiofiles,
                          musicbrainz_server="musicbrainz.org",
                          musicbrainz_port=80,
                          freedb_server="us.freedb.org",
                          freedb_port=80,
                          use_musicbrainz=True,
                          use_freedb=True):
    """given a list of AudioFile objects,
    this treats them as a single CD
    and generates a set of MetaData objects pulled from lookup services

    returns a metadata[c][t] list of lists
    where 'c' is a possible choice
    and 't' is the MetaData for a given track (starting from 0)

    this will always return at least one choice,
    which may be a list of largely empty MetaData objects
    if no match can be found for the CD
    """

    from audiotools.freedb import DiscID as FDiscID
    from audiotools.musicbrainz import DiscID as MDiscID

    return metadata_lookup(
        freedb_disc_id=FDiscID.from_tracks(audiofiles),
        musicbrainz_disc_id=MDiscID.from_tracks(audiofiles),
        musicbrainz_server=musicbrainz_server,
        musicbrainz_port=musicbrainz_port,
        freedb_server=freedb_server,
        freedb_port=freedb_port,
        use_musicbrainz=use_musicbrainz,
        use_freedb=use_freedb)


def sheet_metadata_lookup(sheet,
                          total_pcm_frames,
                          sample_rate,
                          musicbrainz_server="musicbrainz.org",
                          musicbrainz_port=80,
                          freedb_server="us.freedb.org",
                          freedb_port=80,
                          use_musicbrainz=True,
                          use_freedb=True):
    """given a Sheet object,
    length of the album in PCM frames
    and sample rate of the disc,

    returns a metadata[c][t] list of lists
    where 'c' is a possible choice
    and 't' is the MetaData for a given track (starting from 0)

    this will always return at least one choice,
    which may be a list of largely empty MetaData objects
    if no match can be found for the CD
    """

    from audiotools.freedb import DiscID as FDiscID
    from audiotools.musicbrainz import DiscID as MDiscID

    return metadata_lookup(
        freedb_disc_id=FDiscID.from_sheet(sheet,
                                          total_pcm_frames,
                                          sample_rate),
        musicbrainz_disc_id=MDiscID.from_sheet(sheet,
                                               total_pcm_frames,
                                               sample_rate),
        musicbrainz_server=musicbrainz_server,
        musicbrainz_port=musicbrainz_port,
        freedb_server=freedb_server,
        freedb_port=freedb_port,
        use_musicbrainz=use_musicbrainz,
        use_freedb=use_freedb)


def accuraterip_lookup(sorted_tracks,
                       accuraterip_server="www.accuraterip.com",
                       accuraterip_port=80):
    """given a list of sorted AudioFile objects
    and optional AccurateRip server and port
    returns a dict of
    {track_number:[(confidence, crc, crc2), ...], ...}
    where track_number starts from 1

    may return a dict of empty lists if no AccurateRip entry is found

    may raise urllib2.HTTPError if an error occurs querying the server
    """

    if (len(sorted_tracks) == 0):
        return {}
    else:
        from audiotools.accuraterip import DiscID, perform_lookup

        return perform_lookup(DiscID.from_tracks(sorted_tracks),
                              accuraterip_server,
                              accuraterip_port)


def accuraterip_sheet_lookup(sheet, total_pcm_frames, sample_rate,
                             accuraterip_server="www.accuraterip.com",
                             accuraterip_port=80):
    """given a Sheet object, total number of PCM frames and sample rate
    returns a dict of
    {track_number:[(confidence, crc, crc2), ...], ...}
    where track_number starts from 1

    may return a dict of empty lists if no AccurateRip entry is found

    may raise urllib2.HTTPError if an error occurs querying the server
    """

    from audiotools.accuraterip import DiscID, perform_lookup

    return perform_lookup(DiscID.from_sheet(sheet,
                                            total_pcm_frames,
                                            sample_rate),
                          accuraterip_server,
                          accuraterip_port)


from audiotools.dvda import DVDAudio
from audiotools.dvda import InvalidDVDA


def output_progress(u, current, total):
    """given a unicode string and current/total integers,
    returns a u'[<current>/<total>]  <string>'  unicode string
    indicating the current progress"""

    if (total > 1):
        return u"[%%%d.d/%%d]  %%s" % (len(str(total))) % (current, total, u)
    else:
        return u


class ExecProgressQueue(object):
    """a class for running multiple jobs in parallel with progress updates"""

    def __init__(self, progress_display):
        """takes a ProgressDisplay object"""

        self.progress_display = progress_display
        self.__displayed_rows__ = {}
        self.__queued_jobs__ = []
        self.__raised_exception__ = None

    def execute(self, function,
                progress_text=None,
                completion_output=None,
                *args, **kwargs):
        """queues the given function and arguments to be run in parallel

        function must have an additional "progress" argument
        not present in "*args" or "**kwargs" which is called
        with (current, total) integer arguments by the function
        on a regular basis to update its progress
        similar to:  function(*args, progress=prog(current, total), **kwargs)

        progress_text should be a unicode string to be displayed while running

        completion_output is either a unicode string,
        or a function which takes the result of the queued function
        and returns a unicode string for display
        once the queued function is complete
        """

        self.__queued_jobs__.append((len(self.__queued_jobs__),
                                     progress_text,
                                     completion_output,
                                     function,
                                     args,
                                     kwargs))

    def run(self, max_processes=1):
        """runs all the queued jobs in parallel"""

        from select import select

        def execute_next_job():
            """pulls the next job from the queue and returns a
            (Process, Array, Connection, progress_text, completed_text) tuple
            where Process is the subprocess
            Array is shared memory of the current progress
            Connection is the listening end of a pipe
            progress_text is unicode to display during progress
            and completed_text is unicode to display when finished"""

            # pull parameters from job queue
            (job_index,
             progress_text,
             completion_output,
             function,
             args,
             kwargs) = self.__queued_jobs__.pop(0)

            # spawn new __ProgressQueueJob__ object
            job = __ProgressQueueJob__.spawn(
                job_index=job_index,
                function=function,
                args=args,
                kwargs=kwargs,
                progress_text=progress_text,
                completion_output=completion_output)

            # add job to progress display, if any text to display
            if (progress_text is not None):
                self.__displayed_rows__[job.job_fd()] = \
                    self.progress_display.add_row(progress_text)

            return job

        # variables for X/Y output display
        # Note that the order a job is inserted into the queue
        # (as captured by its job_index value)
        # may differ from the order in which it is completed.
        total_jobs = len(self.__queued_jobs__)
        completed_job_number = 1

        # a dict of job file descriptors -> __ProgressQueueJob__ objects
        job_pool = {}

        # return values from the executed functions
        results = [None] * total_jobs

        if (total_jobs == 0):
            # nothing to do
            return results

        # populate job pool up to "max_processes" number of jobs
        for i in range(min(max_processes, len(self.__queued_jobs__))):
            job = execute_next_job()
            job_pool[job.job_fd()] = job

        # while the pool still contains running jobs
        try:
            while (len(job_pool) > 0):
                # wait for zero or more jobs to finish (may timeout)
                (rlist,
                 wlist,
                 elist) = select(job_pool.keys(), [], [], 0.25)

                # clear out old display
                self.progress_display.clear_rows()

                for finished_job in [job_pool[fd] for fd in rlist]:
                    job_fd = finished_job.job_fd()

                    (exception, result) = finished_job.result()

                    if (not exception):
                        # job completed successfully

                        # display any output message attached to job
                        completion_output = finished_job.completion_output
                        if (callable(completion_output)):
                            output = completion_output(result)
                        else:
                            output = completion_output

                        if (output is not None):
                            self.progress_display.output_line(
                                output_progress(unicode(output),
                                                completed_job_number,
                                                total_jobs))

                        # attach result to output in the order it was received
                        results[finished_job.job_index] = result
                    else:
                        # job raised an exception

                        # remove all other jobs from queue
                        # then raise exception to caller
                        # once working jobs are finished
                        self.__raised_exception__ = result
                        while (len(self.__queued_jobs__) > 0):
                            self.__queued_jobs__.pop(0)

                    # remove job from pool
                    del(job_pool[job_fd])

                    # remove job from progress display, if present
                    if (job_fd in self.__displayed_rows__):
                        self.__displayed_rows__[job_fd].finish()

                    # add new jobs from the job queue, if any
                    if (len(self.__queued_jobs__) > 0):
                        job = execute_next_job()
                        job_pool[job.job_fd()] = job

                    # updated completed job number for X/Y display
                    completed_job_number += 1

                # update progress rows with progress taken from shared memory
                for job in job_pool.values():
                    if (job.job_fd() in self.__displayed_rows__):
                        self.__displayed_rows__[job.job_fd()].update(
                            job.current(), job.total())

                # display new set of progress rows
                self.progress_display.display_rows()
        except:
            # an exception occurred (perhaps KeyboardInterrupt)
            # so kill any running child jobs
            # clear any progress rows
            self.progress_display.clear_rows()
            # and pass exception to caller
            raise

        # if any jobs have raised an exception,
        # re-raise it in the main process
        if (self.__raised_exception__ is not None):
            raise self.__raised_exception__
        else:
            # otherwise, return results in the order they were queued
            return results


class __ProgressQueueJob__(object):
    """this class is a the parent process end of a running child job"""

    def __init__(self, job_index, process, progress, result_pipe,
                 progress_text, completion_output):
        """job_index is the order this job was inserted into the queue

        process is the Process object of the running child

        progress is an Array object of [current, total] progress status

        result_pipe is a Connection object which will be read for data

        progress_text is unicode to display while the job is in progress

        completion_output is either unicode or a callable function
        to be displayed when the job finishes
        """

        self.job_index = job_index
        self.process = process
        self.progress = progress
        self.result_pipe = result_pipe
        self.progress_text = progress_text
        self.completion_output = completion_output

    def job_fd(self):
        """returns file descriptor of parent-side result pipe"""

        return self.result_pipe.fileno()

    def current(self):
        return self.progress[0]

    def total(self):
        return self.progress[1]

    @classmethod
    def spawn(cls, job_index,
              function, args, kwargs, progress_text, completion_output):
        """spawns a subprocess and returns the parent-side
        __ProgressQueueJob__ object

        job_index is the order this jhob was inserted into the queue

        function is the function to execute

        args is a tuple of positional arguments

        kwargs is a dict of keyword arguments

        progress_text is unicode to display while the job is in progress

        completion_output is either unicode or a callable function
        to be displayed when the job finishes
        """

        def execute_job(function, args, kwargs, progress, result_pipe):
            try:
                result_pipe.send((False, function(*args,
                                                  progress=progress,
                                                  **kwargs)))
            except Exception as exception:
                result_pipe.send((True, exception))

            result_pipe.close()

        from multiprocessing import Process, Array, Pipe

        # construct shared memory array to store progress
        progress = Array("L", [0, 0])

        # construct one-way pipe to collect result
        (parent_conn, child_conn) = Pipe(False)

        # build child job to execute function
        process = Process(target=execute_job,
                          args=(function,
                                args,
                                kwargs,
                                __progress__(progress).update,
                                child_conn))

        # start child job
        process.start()

        # return populated __ProgressQueueJob__ object
        return cls(job_index=job_index,
                   process=process,
                   progress=progress,
                   result_pipe=parent_conn,
                   progress_text=progress_text,
                   completion_output=completion_output)

    def result(self):
        """returns (exception, result) from parent-side pipe
        where exception is True if result is an exception
        or False if it's the result of the called child function"""

        (exception, result) = self.result_pipe.recv()
        self.result_pipe.close()
        self.process.join()
        return (exception, result)


class __progress__(object):
    def __init__(self, memory):
        self.memory = memory

    def update(self, current, total):
        self.memory[0] = current
        self.memory[1] = total


class TemporaryFile(object):
    """a class for staging file rewrites"""

    def __init__(self, original_filename):
        """original_filename is the path of the file
        to be rewritten with new data"""

        from tempfile import mkstemp

        self.__original_filename__ = original_filename
        (dirname, basename) = os.path.split(original_filename)
        (fd, self.__temp_path__) = mkstemp(prefix="." + basename,
                                           dir=dirname)
        self.__temp_file__ = os.fdopen(fd, "wb")

    def __del__(self):
        if (((self.__temp_path__ is not None) and
             os.path.isfile(self.__temp_path__))):
            os.unlink(self.__temp_path__)

    def write(self, data):
        """writes the given data string to the temporary file"""

        self.__temp_file__.write(data)

    def flush(self):
        """flushes pending data to stream"""

        self.__temp_file__.flush()

    def tell(self):
        """returns current file position"""

        return self.__temp_file__.tell()

    def seek(self, offset, whence=None):
        """move to new file position"""

        if (whence is not None):
            self.__temp_file__.seek(offset, whence)
        else:
            self.__temp_file__.seek(offset)

    def close(self):
        """commits all staged changes

        the original file is overwritten, its file mode is preserved
        and the temporary file is closed and deleted"""

        self.__temp_file__.close()
        original_mode = os.stat(self.__original_filename__).st_mode
        try:
            os.rename(self.__temp_path__, self.__original_filename__)
            os.chmod(self.__original_filename__, original_mode)
            self.__temp_path__ = None
        except OSError as err:
            os.unlink(self.__temp_path__)
            raise err


from audiotools.au import AuAudio
from audiotools.wav import WaveAudio
from audiotools.aiff import AiffAudio
from audiotools.flac import FlacAudio
from audiotools.flac import OggFlacAudio
from audiotools.wavpack import WavPackAudio
from audiotools.shn import ShortenAudio
from audiotools.mp3 import MP3Audio
from audiotools.mp3 import MP2Audio
from audiotools.vorbis import VorbisAudio
from audiotools.m4a import M4AAudio
from audiotools.m4a import ALACAudio
from audiotools.opus import OpusAudio
from audiotools.tta import TrueAudio

from audiotools.ape import ApeTag
from audiotools.flac import FlacMetaData
from audiotools.id3 import ID3CommentPair
from audiotools.id3v1 import ID3v1Comment
from audiotools.id3 import ID3v22Comment
from audiotools.id3 import ID3v23Comment
from audiotools.id3 import ID3v24Comment
from audiotools.m4a_atoms import M4A_META_Atom
from audiotools.vorbiscomment import VorbisComment

AVAILABLE_TYPES = (FlacAudio,
                   OggFlacAudio,
                   MP3Audio,
                   MP2Audio,
                   WaveAudio,
                   VorbisAudio,
                   AiffAudio,
                   AuAudio,
                   M4AAudio,
                   ALACAudio,
                   WavPackAudio,
                   ShortenAudio,
                   OpusAudio,
                   TrueAudio)

TYPE_MAP = {track_type.NAME: track_type
            for track_type in AVAILABLE_TYPES
            if track_type.available(BIN)}

DEFAULT_QUALITY = {track_type.NAME:
                   config.get_default("Quality",
                                      track_type.NAME,
                                      track_type.DEFAULT_COMPRESSION)
                   for track_type in AVAILABLE_TYPES
                   if (len(track_type.COMPRESSION_MODES) > 1)}

if (DEFAULT_TYPE not in TYPE_MAP.keys()):
    DEFAULT_TYPE = "wav"
