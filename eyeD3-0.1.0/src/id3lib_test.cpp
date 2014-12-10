#include <iostream>
#include <id3/tag.h>
#include <id3/misc_support.h>
#include <id3/readers.h>

using namespace std;

int main(int argc, char* argv[]) {
   const ID3_Tag tag(argv[1]);
   bool hasV1 = tag.HasV1Tag();
   bool hasV2 = tag.HasV2Tag();
   if (hasV1) {
      std::cout << "Found id3 v1" << std::endl;
   }
   if (hasV2) {
      std::cout << "Found id3 v2" << std::endl;
   }
   if (!hasV1 && !hasV2) {
      cout << "Found No Tag" << endl;
   }

   ID3_Tag::ConstIterator* iter = tag.CreateIterator();
   const ID3_Frame* frame = NULL;
   while ((frame = iter->GetNext()) != NULL) {
      const char* desc = frame->GetDescription();
      if (!desc) desc = "";
      cout << "=== " << frame->GetTextID() << " (" << desc << "): ";
      ID3_FrameID eFrameID = frame->GetID();
      switch (eFrameID) {
         case ID3FID_ALBUM:
         case ID3FID_BPM:
         case ID3FID_COMPOSER:
         case ID3FID_CONTENTTYPE:
         case ID3FID_COPYRIGHT:
         case ID3FID_DATE:
         case ID3FID_PLAYLISTDELAY:
         case ID3FID_ENCODEDBY:
         case ID3FID_LYRICIST:
         case ID3FID_FILETYPE:
         case ID3FID_TIME:
         case ID3FID_CONTENTGROUP:
         case ID3FID_TITLE:
         case ID3FID_SUBTITLE:
         case ID3FID_INITIALKEY:
         case ID3FID_LANGUAGE:
         case ID3FID_SONGLEN:
         case ID3FID_MEDIATYPE:
         case ID3FID_ORIGALBUM:
         case ID3FID_ORIGFILENAME:
         case ID3FID_ORIGLYRICIST:
         case ID3FID_ORIGARTIST:
         case ID3FID_ORIGYEAR:
         case ID3FID_FILEOWNER:
         case ID3FID_LEADARTIST:
         case ID3FID_BAND:
         case ID3FID_CONDUCTOR:
         case ID3FID_MIXARTIST:
         case ID3FID_PARTINSET:
         case ID3FID_PUBLISHER:
         case ID3FID_TRACKNUM:
         case ID3FID_RECORDINGDATES:
         case ID3FID_NETRADIOSTATION:
         case ID3FID_NETRADIOOWNER:
         case ID3FID_SIZE:
         case ID3FID_ISRC:
         case ID3FID_ENCODERSETTINGS:
         case ID3FID_YEAR: {
            char *sText = ID3_GetString(frame, ID3FN_TEXT);
            cout << sText << endl;
            delete [] sText;
            break;
         }
         case ID3FID_USERTEXT: {
            char *sText = ID3_GetString(frame, ID3FN_TEXT), 
                 *sDesc = ID3_GetString(frame, ID3FN_DESCRIPTION);
            cout << "(" << sDesc << "): " << sText << endl;
            delete [] sText;
            delete [] sDesc;
            break;
         }
         case ID3FID_COMMENT:
         case ID3FID_UNSYNCEDLYRICS: {
            char *sText = ID3_GetString(frame, ID3FN_TEXT), 
                 *sDesc = ID3_GetString(frame, ID3FN_DESCRIPTION), 
                 *sLang = ID3_GetString(frame, ID3FN_LANGUAGE);
            cout << "(" << sDesc << ")[" << sLang << "]: "
                 << sText << endl;
            delete [] sText;
            delete [] sDesc;
            delete [] sLang;
            break;
         }
         case ID3FID_WWWAUDIOFILE:
         case ID3FID_WWWARTIST:
         case ID3FID_WWWAUDIOSOURCE:
         case ID3FID_WWWCOMMERCIALINFO:
         case ID3FID_WWWCOPYRIGHT:
         case ID3FID_WWWPUBLISHER:
         case ID3FID_WWWPAYMENT:
         case ID3FID_WWWRADIOPAGE: {
            char *sURL = ID3_GetString(frame, ID3FN_URL);
            cout << sURL << endl;
            delete [] sURL;
            break;
         }
         case ID3FID_WWWUSER: {
            char *sURL = ID3_GetString(frame, ID3FN_URL),
                 *sDesc = ID3_GetString(frame, ID3FN_DESCRIPTION);
            cout << "(" << sDesc << "): " << sURL << endl;
            delete [] sURL;
            delete [] sDesc;
            break;
         }
         case ID3FID_INVOLVEDPEOPLE: {
            size_t nItems = frame->GetField(ID3FN_TEXT)->GetNumTextItems();
            for (size_t nIndex = 0; nIndex < nItems; nIndex++) {
               char *sPeople = ID3_GetString(frame, ID3FN_TEXT, nIndex);
               cout << sPeople;
               delete [] sPeople;
               if (nIndex + 1 < nItems) {
                  cout << ", ";
               }
            }
            cout << endl;
            break;
         }
         case ID3FID_PICTURE: {
            char *sMimeType = ID3_GetString(frame, ID3FN_MIMETYPE),
                 *sDesc     = ID3_GetString(frame, ID3FN_DESCRIPTION),
                 *sFormat   = ID3_GetString(frame, ID3FN_IMAGEFORMAT);
            size_t nPicType   = frame->GetField(ID3FN_PICTURETYPE)->Get(),
                   nDataSize  = frame->GetField(ID3FN_DATA)->Size();
            cout << "(" << sDesc << ")[" << sFormat << ", "
                 << nPicType << "]: " << sMimeType << ", " << nDataSize
                 << " bytes" << endl;
            delete [] sMimeType;
            delete [] sDesc;
            delete [] sFormat;
            break;
         }
         case ID3FID_GENERALOBJECT: {
            char *sMimeType = ID3_GetString(frame, ID3FN_MIMETYPE), 
                 *sDesc = ID3_GetString(frame, ID3FN_DESCRIPTION), 
                 *sFileName = ID3_GetString(frame, ID3FN_FILENAME);
            size_t nDataSize = frame->GetField(ID3FN_DATA)->Size();
            cout << "(" << sDesc << ")[" 
                 << sFileName << "]: " << sMimeType << ", " << nDataSize
                 << " bytes" << endl;
            delete [] sMimeType;
            delete [] sDesc;
            delete [] sFileName;
            break;
         }
         case ID3FID_UNIQUEFILEID: {
            char *sOwner = ID3_GetString(frame, ID3FN_OWNER);
            size_t nDataSize = frame->GetField(ID3FN_DATA)->Size();
            cout << sOwner << ", " << nDataSize
                 << " bytes" << endl;
            delete [] sOwner;
            break;
         }
         case ID3FID_PLAYCOUNTER: {
            size_t nCounter = frame->GetField(ID3FN_COUNTER)->Get();
            cout << nCounter << endl;
            break;
         }
         case ID3FID_POPULARIMETER: {
            char *sEmail = ID3_GetString(frame, ID3FN_EMAIL);
            size_t nCounter = frame->GetField(ID3FN_COUNTER)->Get(),
                   nRating = frame->GetField(ID3FN_RATING)->Get();
            cout << sEmail << ", counter=" 
                 << nCounter << " rating=" << nRating << endl;
            delete [] sEmail;
            break;
         }
         case ID3FID_CRYPTOREG:
         case ID3FID_GROUPINGREG: {
            char *sOwner = ID3_GetString(frame, ID3FN_OWNER);
            size_t nSymbol = frame->GetField(ID3FN_ID)->Get(),
                   nDataSize = frame->GetField(ID3FN_DATA)->Size();
            cout << "(" << nSymbol << "): " << sOwner
                 << ", " << nDataSize << " bytes" << endl;
            break;
         }
         case ID3FID_SYNCEDLYRICS: {
            char *sDesc = ID3_GetString(frame, ID3FN_DESCRIPTION), 
                 *sLang = ID3_GetString(frame, ID3FN_LANGUAGE);
            size_t nTimestamp = frame->GetField(ID3FN_TIMESTAMPFORMAT)->Get(),
                   nRating = frame->GetField(ID3FN_CONTENTTYPE)->Get();
            const char* format = (2 == nTimestamp) ? "ms" : "frames";
            cout << "(" << sDesc << ")[" << sLang << "]: ";
            switch (nRating) {
               case ID3CT_OTHER:    cout << "Other"; break;
               case ID3CT_LYRICS:   cout << "Lyrics"; break;
               case ID3CT_TEXTTRANSCRIPTION: cout << "Text transcription"; break;
               case ID3CT_MOVEMENT: cout << "Movement/part name"; break;
               case ID3CT_EVENTS:   cout << "Events"; break;
               case ID3CT_CHORD:    cout << "Chord"; break;
               case ID3CT_TRIVIA:   cout << "Trivia/'pop up' information"; break;
            }
            cout << endl;
            ID3_Field* fld = frame->GetField(ID3FN_DATA);
            if (fld) {
               ID3_MemoryReader mr(fld->GetRawBinary(), fld->BinSize());
               while (!mr.atEnd()) {
                  // TODO: Uncomment with next version of id3lib
                  cout << "TODO with next version of id3lib" << endl;
                  //cout << io::readString(mr).c_str();
                  //cout << " [" << io::readBENumber(mr, sizeof(uint32)) << " " 
                  //     << format << "] ";
               }
            }
            cout << endl;
            delete [] sDesc;
            delete [] sLang;
            break;
         }
         case ID3FID_AUDIOCRYPTO:
         case ID3FID_EQUALIZATION:
         case ID3FID_EVENTTIMING:
         case ID3FID_CDID:
         case ID3FID_MPEGLOOKUP:
         case ID3FID_OWNERSHIP:
         case ID3FID_PRIVATE:
         case ID3FID_POSITIONSYNC:
         case ID3FID_BUFFERSIZE:
         case ID3FID_VOLUMEADJ:
         case ID3FID_REVERB:
         case ID3FID_SYNCEDTEMPO:
         case ID3FID_METACRYPTO: {
            cout << " (unimplemented)" << endl;
            break;
         }
         default:
            cout << " frame" << endl;
            break;
      }
   }
   delete iter;

   //cout << "Artist: " << ID3_GetArtist(&tag) << endl;
   //cout << "Album: " << ID3_GetAlbum(&tag) << endl;
   //cout << "Title: " << ID3_GetTitle(&tag) << endl;
   //cout << "Year: " << ID3_GetYear(&tag) << endl;
   //cout << "Track: " << ID3_GetTrack(&tag) << endl;
   //cout << "TrackNum: " << ID3_GetTrackNum(&tag) << endl;
   //cout << "Genre: " << ID3_GetGenre(&tag) << endl;
   //cout << "GenreNum: " << ID3_GetGenreNum(&tag) << endl;

   return 0;
}
