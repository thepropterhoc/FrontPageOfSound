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

import re, os, string;
import config;
from ID3v2Frame import *;
from binfuncs import *;

version = config.version;

class ID3_Tag:

   def __init__(self):
      self.encoding = '\x00';
      self.frames = [];
      self.majorVersion = None;
      self.minorVersion = None;
      self.revVersion = None;
      self.unsync = 0;
      self.extended = 0;
      self.footer = None;
      self.tagSize = 0;
      self.paddingSize = 0;
      self.iterIndex = None;

   # Returns an read-only iterator for all ID3v2 frames.
   def __iter__(self):
      if len(self.frames):
         self.iterIndex = 0;
      else:
         self.iterIndex = None;
      return self;

   def next(self):
      if self.iterIndex == None or self.iterIndex == len(self.frames):
         raise StopIteration;
      frm = self.frames[self.iterIndex];
      self.iterIndex += 1;
      return frm;

   # Returns true when an ID3 tag is read from fileName.
   # Converts all ID3v1 data into ID3v2 frames.
   # May throw IOError
   def link(self, fileName):
      self.frames = [];
      if self.__loadV2Tag(fileName) or self.__loadV1Tag(fileName):
            return 1;
        
      return 0;

   #######################################################################
   # Returns false when an ID3 v1 tag is not present, or contains no data.
   def __loadV1Tag(self, fileName):
      fh = open(fileName, 'rb')

      # Seek to the end of the file where all ID3v1 tags are written.
      fh.seek(0, 2)
      if fh.tell() > 127:
         fh.seek(-128, 2)
         id3tag = fh.read(128)
         if id3tag[0:3] == 'TAG':
            self.majorVersion = 1;
            self.revVersion = 0;
            title = re.sub('\x00+$', '', id3tag[3:33].strip())
            if title:
               self.setTitle(title);

            artist = re.sub('\x00+$', '', id3tag[33:63].strip())
            if artist:
               self.setArtist(artist);

            album = re.sub('\x00+$', '', id3tag[63:93].strip())
            if album:
               self.setAlbum(album);

            year = re.sub('\x00+$', '', id3tag[93:97].strip())
            if year and int(year):
               self.setYear(year);

            comment = re.sub('\x00+$', '', id3tag[97:127].strip())
            if comment:
               # Parse track number (added to ID3v1.1) if present in
               # comment field.
               if comment[28:29] == '\x00':
                  track = ord(comment[29:30])
                  comment = re.sub('\x00+$', '', comment[0:28].rstrip())
                  self.setTrackNum((track, None));
                  self.minorVersion = 1;
               else:
                  track = None
                  self.minorVersion = 0;
               # TODO
               #self.setComment(comment);

            genre = ord(id3tag[127:128])
            if genre:
               self.setGenre(genre);


      fh.close()
      return len(self.frames);

   #######################################################################
   # Returns false when an ID3 v2 tag is not present, or contains 0 frames.
   # May throw IOError
   def __loadV2Tag(self, fileName):
      fh = open(fileName, 'rb');

      # All IV3v2 tags must start with the three bytes "ID3"
      id = fh.read(3);
      if id != "ID3":
         fh.close();
         return 0;

      # The next 2 bytes are the minor and revision versions.
      version = fh.read(2);
      self.majorVersion = 2;
      self.minorVersion = ord(version[0]);
      self.revVersion = ord(version[1]);

      # The first 4 bits of the next byte are flags.
      (self.unsync,
       self.extended,
       self.experimental,
       self.footer,
       None,
       None,
       None,
       None) = byte2bin(fh.read(1), 8);

      # The size of the optional extended header, frames, and padding
      # ager unsynchronization.
      self.tagSize = bin2dec(byte2bin(fh.read(4), 7));

      # Read the extended header if present.
      # TODO
      if self.extended:
         print("DEBUG: extended header.");

      # Read frames
      sizeLeft = self.tagSize;
      while sizeLeft > 0:
         frameid = fh.read(4);
         if frameid != '\x00\x00\x00\x00':
           # Frame size corresponds to the size of the data segment after
           # encryption, compression, and unzynchronization.
           framesize = bin2dec(byte2bin(fh.read(4), 7));
	  
           flags = fh.read(2);
           flags = byte2bin(flags, 8);

           # Frame data.
           data = fh.read(framesize);
           frm = createFrame(frameid, data, flags);

           self.frames.append(frm);
           sizeLeft -= (framesize + 10);
         else:
            self.paddingSize = sizeLeft;
            break;

      fh.close();
      if len(self.frames) > 0:
         return 1;
      else:
         return 0;
         
   def getFrame(self, frameId):
      for f in self.frames:
         if f.id == frameId:
            return f;
      return None;
         
   def removeFrame(self, frameId):
      i = 0;
      while i < len(self.frames):
         if self.frames[i].id == frameId:
            del self.frames[i];
            return 1;
         i += 1;
      return 0;

   # Use with care, very low-level wrt data (i.e. encoding bytes and UserText
   # description)
   def setTextFrame(self, frameId, data, flags = ID3v2Frame.nullFlags):
      if not re.compile("T.+.+.+").match(frameId):
         # TODO: Exceptions
         return 0;

      if frameId == USERTEXT_FID:
         userText = 1;
      else:
         userText = 0;

      f = self.getFrame(frameId);
      if f:
         if userText:
            f.set(data, flags);
         else:
            f.set(frameId, data, flags);
      else:
         if userText:
            self.frames.append(UserTextInfo(data, flags));
         else:
            self.frames.append(TextInfo(frameId, data, flags));
      return 1;

   def getArtistFrame(self):
      for fid in ARTIST_FIDs:
         f = self.getFrame(fid);
         if f:
            return f;
      return None; 

   def getArtist(self):
      f = self.getArtistFrame();
      if f:
         return f.value;
      else:
         return None;

   def setArtist(self, a):
      self.setTextFrame(ARTIST_FIDs[0], self.encoding + a);
 

   def getAlbumFrame(self):
      f = self.getFrame(ALBUM_FID);
      if f:
         return f;
      return None; 

   def getAlbum(self):
      f = self.getAlbumFrame();
      if f:
         return f.value;
      else:
         return None;

   def setAlbum(self, a):
      self.setTextFrame(ALBUM_FID, self.encoding + a);


   def getTitleFrame(self):
      f = self.getFrame(TITLE_FID);
      if f:
         return f;
      return None; 

   def getTitle(self):
      f = self.getTitleFrame();
      if f:
         return f.value;
      else:
         return None;

   def setTitle(self, t):
      self.setTextFrame(TITLE_FID, self.encoding + t);
 

   def getYearFrame(self):
      f = self.getFrame(YEAR_FID);
      if f:
         return f;
      return None; 

   def getYear(self):
      f = self.getYearFrame();
      if f:
         return f.value;
      else:
         return None;

   def setYear(self, y):
      self.setTextFrame(YEAR_FID, self.encoding + y);


   def getGenreFrame(self):
      f = self.getFrame(GENRE_FID);
      if f:
         return f;
      return None; 

   def getGenre(self):
      f = self.getGenreFrame();
      if f:
         return f.value;
      else:
         return None;

   def setGenre(self, g):
      self.setTextFrame(GENRE_FID, self.encoding + str(g));


   def getTrackNumFrame(self):
      f = self.getFrame(TRACKNUM_FID);
      if f:
         return f;
      return None; 

   # Returns a tuple with the first value containing the track number and the
   # second the total number of tracks.  One or both of these values may be None
   # depending on what is available in the tag. 
   def getTrackNum(self):
      f = self.getTrackNumFrame();
      if f:
         n = string.split(f.value, '/');
         if len(n) == 2:
            return (n[0], n[1]);
         else:
            return (n[0], None);
      else:
         return (None, None);

   # Accepts a tuple with the first value containing the track number and the
   # second the total number of tracks.  One or both of these values may be None.
   def setTrackNum(self, n):
      if n[0] != None and n[1] != None:
         s = str(n[0]) + "/" + str(n[1]);
      elif n[0] != None and n[1] == None:
         s = str(n[0]);
      else:
         s = None;

      if s:
         self.setTextFrame(TRACKNUM_FID, self.encoding + s);
      else:
         self.removeFrame(TRACKNUM_FID);

   # Test ID3 major version.
   def isID3v1Tag(self):
      return self.majorVersion == 1;
   def isID3v2Tag(self):
      return self.majorVersion == 2;

   def getVersion(self):
      v = str(self.majorVersion) + "." + str(self.minorVersion);
      if self.revVersion:
         v += "." + str(self.revVersion);
      return v;

#######################################################################
# ID3 genres as defined by the v1.1 spec with WinAmp extensions.
genres = ['Blues',
          'Classic Rock',
	  'Country',
          'Dance',
	  'Disco',
	  'Funk',
          'Grunge',
	  'Hip-Hop',
	  'Jazz',
          'Metal',
	  'New Age',
	  'Oldies',
          'Other',
	  'Pop',
	  'R&B',
          'Rap',
	  'Reggae',
	  'Rock',
          'Techno',
	  'Industrial',
	  'Alternative',
          'Ska',
	  'Death Metal',
	  'Pranks',
          'Soundtrack',
	  'Euro-Techno',
	  'Ambient',
          'Trip-Hop',
	  'Vocal',
	  'Jazz+Funk',
          'Fusion',
	  'Trance',
	  'Classical',
          'Instrumental',
	  'Acid',
	  'House',
          'Game',
	  'Sound Clip',
	  'Gospel',
          'Noise',
	  'AlternRock',
	  'Bass',
          'Soul',
	  'Punk',
	  'Space',
          'Meditative',
	  'Instrumental Pop',
	  'Instrumental Rock',
          'Ethnic',
	  'Gothic',
	  'Darkwave',
          'Techno-Industrial',
	  'Electronic',
	  'Pop-Folk',
          'Eurodance',
	  'Dream',
	  'Southern Rock',
          'Comedy',
	  'Cult',
	  'Gangsta Rap',
          'Top 40',
	  'Christian Rap',
	  'Pop / Funk',
          'Jungle',
	  'Native American',
	  'Cabaret',
          'New Wave',
	  'Psychedelic',
	  'Rave',
          'Showtunes',
	  'Trailer',
	  'Lo-Fi',
          'Tribal',
	  'Acid Punk',
	  'Acid Jazz',
          'Polka',
	  'Retro',
	  'Musical',
          'Rock & Roll',
	  'Hard Rock',
	  'Folk',
          'Folk-Rock',
	  'National Folk',
	  'Swing',
          'Fast  Fusion',
	  'Bebob',
	  'Latin',
          'Revival',
	  'Celtic',
	  'Bluegrass',
          'Avantgarde',
	  'Gothic Rock',
	  'Progressive Rock',
          'Psychedelic Rock',
	  'Symphonic Rock',
	  'Slow Rock',
          'Big Band',
	  'Chorus',
	  'Easy Listening',
          'Acoustic',
	  'Humour',
	  'Speech',
          'Chanson',
	  'Opera',
	  'Chamber Music',
          'Sonata',
	  'Symphony',
	  'Booty Bass',
          'Primus',
	  'Porn Groove',
	  'Satire',
          'Slow Jam',
	  'Club',
	  'Tango',
          'Samba',
	  'Folklore',
	  'Ballad',
          'Power Ballad',
	  'Rhythmic Soul',
	  'Freestyle',
          'Duet',
	  'Punk Rock',
	  'Drum Solo',
          'A Cappella',
	  'Euro-House',
	  'Dance Hall',
          'Goa',
	  'Drum & Bass',
	  'Club-House',
          'Hardcore',
	  'Terror',
	  'Indie',
          'BritPop',
	  'Negerpunk',
	  'Polsk Punk',
          'Beat',
	  'Christian Gangsta Rap',
	  'Heavy Metal',
          'Black Metal',
	  'Crossover',
	  'Contemporary Christian',
          'Christian Rock',
	  'Merengue',
	  'Salsa',
          'Thrash Metal',
	  'Anime',
	  'JPop',
          'Synthpop'
         ];


nullFlags = ID3v2Frame.nullFlags;

