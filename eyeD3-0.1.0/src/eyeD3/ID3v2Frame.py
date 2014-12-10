#
#  Copyright (C) 2002  Travis Shirk <travis@pobox.com>
#  Copyright (C) 2001  Ryan Finne <ryan@finnie.org>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
__version__ = "$Revision: 1.1 $"

import re, zlib;
from binfuncs import *;

ARTIST_FIDs  = ["TPE1", "TPE2", "TPE3", "TPE4", "TCOM"];
ALBUM_FID    = "TALB";
TITLE_FID    = "TIT2";
YEAR_FID     = "TYER";
COMMENT_FID  = "COMM";
GENRE_FID    = "TCON";
TRACKNUM_FID = "TRCK";
USERTEXT_FID = "TXXX";

class ID3v2Frame:
  id = '';
  compressed = 0;
  dlied = 0;
  encrypted = 0;
  unsynched = 0;
  grouped = 0;
  nullFlags = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];

  def __repr__(self):
    return '<ID3v2Frame.%s (%s)>' % (self.__class__.__name__, self.id)

  def unsynch(self, flags, data):
    (data, subsmade) = re.subn('\xff', '\xff\x00', data)
    if subsmade > 0:
      flags[14] = 1
    else:
      if self.unsynched == 1:
        flags[14] = 1
      else:
        flags[14] = 0
    return (flags, data)

  def deunsynch(self, flags, data):
    if flags[14] == 1:
      data = re.sub('\xff\x00', '\xff', data)
      self.unsynched = 1
    else:
      self.unsynched = 0
    return (flags, data)

  def read_group(self, flags, data):
    if flags[9] == 1:
      grouppos = len(data) - 1
      self.groupid = data[grouppos]
      data = data[0:grouppos]
      self.grouped = 1
    return (flags, data)

  def write_group(self, flags, data):
    if self.grouped == 1:
      data += self.groupid
      flags[9] = 1
      self.dlied = 1
    return (flags, data)

  def decompress(self, flags, data):
    if flags[15] == 1:
      realdata = len(data) - 4
      data = data[0:realdata]
      self.dlied = 1
    if flags[12] == 1:
      data = zlib.decompress(data)
      self.compressed = 1
    return (flags, data)

  def compress(self, flags, data):
    oldframesize = bin2byte(bin2synchsafe(dec2bin(len(data), 28)))
    if self.compressed == 1:
      self.dlied = 1
      flags[12] = 1
      data = zlib.compress(data)
    if self.dlied == 1:
      flags[15] = 1
      data += oldframesize
    return (flags, data)

  def assemble_frame(self, data):
    flags = [0] * 16
    (flags, data) = self.write_group(flags, data)
    (flags, data) = self.compress(flags, data)
    (flags, data) = self.unsynch(flags, data)
    flags = bin2byte(flags)
    framesize = bin2byte(bin2synchsafe(dec2bin(len(data), 28)))
    return self.id + framesize + flags + data

  def disassemble_frame(self, frameId, flags, data):
    (flags, data) = self.deunsynch(flags, data)
    (flags, data) = self.decompress(flags, data)
    (flags, data) = self.read_group(flags, data)
    self.encrypted = flags[13]
    return (frameId, flags, data)

#######################################################################
class TextInfo(ID3v2Frame):

   def __init__(self, frameId, data, flags = ID3v2Frame.nullFlags):
      self.encoding = '\x00';
      self.value = '';

      self.set(frameId, data, flags);

   def set(self, frameId, data, flags = ID3v2Frame.nullFlags):
      (self.id, None, data) = self.disassemble_frame(frameId, flags, data);
      self.encoding = data[0];
      self.value = data[1:];

   def __repr__(self):
      return '<ID3v2Frame.%s (%s): %s>' % (self.__class__.__name__, self.id,
                                         self.value)

   def dump(self):
      data = self.encoding + self.value
      return self.assemble_frame(data)

#######################################################################
class UserTextInfo(ID3v2Frame):

  def __init__(self, data, flags = ID3v2Frame.nullFlags):
     self.id = "TXXX";
     self.encoding = '';
     self.description = '';
     self.value = '';

     self.set(data, flags);

  def set(self, data, flags = ID3v2Frame.nullFlags):
     (None, None, data) = self.disassemble_frame(self.id, flags, data);
     self.encoding = data[0];
     (self.description, self.value) = data[1:].split('\x00', 1);

  def dump(self):
     data = self.encoding + self.description + '\x00' + self.value;
     return self.assemble_frame(data);

#######################################################################
class URL(ID3v2Frame):
  url = ''

  def __init__(self, frameId, data, flags = ID3v2Frame.nullFlags):
    (self.id, flags, data) = self.disassemble_frame(frameId, flags, data);
    self.url = data;

  def dump(self):
    data = self.url;
    return self.assemble_frame(data);

#######################################################################
class UserURL(ID3v2Frame):
  description = ''
  url = ''

  def __init__(self, data, flags = ID3v2Frame.nullFlags):
    self.id = "WXXX";
    (None, flags, data) = self.disassemble_frame(self.id, flags, data);
    self.encoding = data[0];
    (self.description, self.url) = data[1:].split('\x00', 1);

  def dump(self):
    data = self.encoding + self.description + '\x00' + self.url
    return self.assemble_frame(data)

#######################################################################
class Comment(ID3v2Frame):
  encoding = '';
  language = '';
  description = '';
  comment = '';

  def __init__(self, data, flags = ID3v2Frame.nullFlags):
     self.id = "COMM";
     (None, flags, data) = self.disassemble_frame(self.id, flags, data);
     self.encoding = data[0];
     self.language = data[1:4];
     (self.description, self.comment) = data[4:].split('\x00', 1);

  def __repr__(self):
    return '<ID3v2Frame.%s (%s): %s>' % (self.__class__.__name__, self.id,
                                         self.comment)

  def dump(self):
    data = self.encoding + self.language + self.description + '\x00' +\
           self.comment;
    return self.assemble_frame(data);

#######################################################################
class Unknown(ID3v2Frame):
  data = '';

  def __init__(self, frameId, flags, data):
    (self.id, flags, data) = self.disassemble_frame(frameId, flags, data);
    self.data = data;

  def dump(self):
    return self.assemble_frame(self.data)

#######################################################################
class MusicCDIdentifier(ID3v2Frame):
  data = '';

  def __init__(self, data, flags = ID3v2Frame.nullFlags):
    self.id = "MCDI";
    (None, flags, data) = self.disassemble_frame(self.id, flags, data);
    self.toc = data;

  def dump(self):
    data = self.data
    return self.assemble_frame(data)

#######################################################################
# Create and return the appropriate frame.
# Exceptions: ....
def createFrame(frameId, data, flags = ID3v2Frame.nullFlags):
   f = None
   if frameId[0] == 'T':
      if frameId == 'TXXX':
         f = UserTextInfo(data, flags);
      else:
         f = TextInfo(frameId, data, flags);
   elif frameId[0] == 'C':
      if frameId == 'COMM':
         f = Comment(data, flags);
      else:
         pass;
   elif frameId[0] == 'W':
      if frameId == 'WXXX':
         f = UserURL(data, flags);
      else:
         f = URL(frameId, data, flags);
   elif frameId == 'MCDI':
      f = MusicCDIdentifier(data, flags);

   if f == None:
     f = Unknown(frameId, data, flags);

   return f;
