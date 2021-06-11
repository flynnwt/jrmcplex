# read jrmc mp3 tags and transfer rating to plex
# could also pick up custom tags from jrmc and add as collection, etc. plex info
#
# search() doesn't work for special chars - urlencode?  hacked 'fix'
# work? https://forums.plex.tv/t/tip-how-to-create-an-autoplaylist-with-random-sort/472823

# setup
# 1. running this code on windoze
# 2. windoze accesses jrmc/plex mp3 files at winPath/...
# 3. plex (synology) accesses mp3 files at plexPath/...
# 4. set plexURL/plexToken; get token by going to an item in plex then '...' to 'get info' then 'view xml' and get from url

# run
# recursive scan paths starting with 'g'; only print fails (no rating, no match), don't change plex rating if it exists, map to 1/3/5 stars
#  python app.py -q -3 "Shared/Media/Music/Rock/g*" 


# * Config ************************************************
# *** Secrets
plexURL = 'https://plex.secret.xyz'
plexToken = 'jennyjenny8675309'   
winPath = '//shareme'
plexPath = '/volumeme'
# *** Defaults
logFile = './results.txt'
writeLog = True
override = False
starMap135 = False
noUpdate = False
updateMsg = 100
searchHack = True
# *********************************************************

import sys
import os
import argparse
from datetime import datetime
from glob import glob
from id3parse import ID3, ID3PopularimeterFrame

# https://python-plexapi.readthedocs.io/en/latest/introduction.html
from plexapi.server import PlexServer

# command line

parser = argparse.ArgumentParser(description='Update Plex ratings from JRMC tags.')

parser.add_argument('path', help='path to recurse (not including winPath/plexPath')

parser.add_argument('-u', dest='plexURL', default=plexURL, help='plex server url')
parser.add_argument('-t', dest='plexToken', default=plexToken, help='plex server token')

parser.add_argument('-w', dest='winPath', default=winPath, help='windoze path prefix')
parser.add_argument('-p', dest='plexPath', default=plexPath, help='plex server path prefix')

parser.add_argument('-l', dest='logFile', default=logFile, help='log output file')
parser.add_argument('-L', dest='writeLog', default=writeLog, action='store_false', help='disable write to log file')

parser.add_argument('-o', dest='override', action='store_true', default=override, help='overwrite plex rating if it exists')
parser.add_argument('-3', dest='starMap135', action='store_true', default=starMap135, help='map rating 1:5 to 1,3,5')
parser.add_argument('-n', dest='noUpdate', action='store_true', default=noUpdate, help='do not update the rating in plex')
parser.add_argument('--hack', dest='searchHack', action='store_false', default=searchHack, help='disable broadening plex search when special chars in title')

parser.add_argument('-U', dest='updateMsg', default=updateMsg, help='print processing message every n files')
parser.add_argument('--qtag', dest='quietTagerror', action='store_true', default=False, help='do not print info for tag errors')
parser.add_argument('--qexist', dest='quietExist', action='store_true', default=False, help='do not print info if skipping because of existing rating')
parser.add_argument('--qset', dest='quietSet', action='store_true', default=False, help='do not print info if rating is set')
parser.add_argument('-q', dest='quiet', action='store_true', default=False, help='--qtag --qexist --qset')

args = parser.parse_args()

top = args.path

plexURL = args.plexURL
plexToken = args.plexToken

winPath = args.winPath
plexPath = args.plexPath

logFile = args.logFile
writeLog = args.writeLog
logF = None

override = args.override
starMap135 = args.starMap135  
noUpdate = args.noUpdate
searchHack = args.searchHack

updateMsg = args.updateMsg
quietTagerror = args.quietTagerror or args.quiet
quietExist = args.quietExist or args.quiet
quietSet = args.quietSet or args.quiet

# stuff

class NoMatchError(Exception):
   pass

class NoMatchFilenameError(Exception):
   pass

class TagError(Exception):
   pass

class RatingExistsError(Exception):
   pass

class JRMCInfo:
   
   def __init__(self):
      self.title = None
      self.artist = None
      self.rating = None
   
   def __repr__(self):
      return 'title: \'{}\' artist: \'{}\' rating: {}'.format(self.title, self.artist, self.rating)

def log(s):
   s = '[{}] {}'.format(datetime.now(), s) if s.strip() != '' else ''
   print(s)
   if writeLog:
      logF.write('{}\n'.format(s))

# convert tag value to stars
def jrmcStars(r):
   if r == 1:
      return 1
   elif r == 64:
      return 2 if not starMap135 else 1
   elif r == 128:
      return 3
   elif r == 192:
      return 4 if not starMap134 else 5
   elif r == 255:
      return 5
   else:
      raise ValueError('Bad rating value in JRMC POPM tag.')

# get some JRMC ID3v2.4 tags from file
def getJRMCInfo(fn):
   id3 = ID3.from_file(fn)
   rc = JRMCInfo()

   try:
      rc.title = id3.find_frame_by_name('TIT2').text    
      rc.artist = id3.find_frame_by_name('TPE1').text   
      rc.rating = jrmcStars(id3.find_frame_by_name('POPM').rating)
   except:
      raise TagError()

   return rc

# Plex Rating is 0.0-10.0, each star is 2.0
def setPlexRating(fn, title, artist, rating, override=False):
   # this fixes no results if single-quote in title; also see it for others.  isn't it urlencoded for query?
   if searchHack:
      badChars = ["'", '"', '.', '[', ']', '-', '(', ')', '&', '?']
      for c in badChars:
         if title.find(c) != -1:
            title = title[0:title.find(c)]
            break 
   p = plex.library.search(title=title, artist=artist)
   if len(p) == 0:
      raise NoMatchError('No title/artist matches in Plex.')
   for i in range(len(p)):
      if p[i].type == 'track' and p[i].listType == 'audio':
         #log(p[i].artist().title, p[i].title, p[i].ratingKey, p[i].guid, p[i].type, p[i].locations, p[i].userRating, p[i].updatedAt, p[i].listType)
         for j in range(len(p[i].locations)):
            if fn == p[i].locations[j]:
               if p[i].userRating == None or override:
                  if not noUpdate:
                      p[i].rate(rating*2.0)      
                  return True
               else:
                  raise RatingExistsError('Rating is already set in Plex database.')
               break   
   raise NoMatchFilenameError('Found title/artist but no filename match.')

def header(jrmcFile, plexFile, jrmcInfo, msg=None, skip=False):
   if not skip:
      log('')
      log('* jrmc: {}'.format(jrmcFile))
      log('* plex: {}'.format(plexFile))      
      log('* tags: {}'.format(jrmcInfo))   
      if msg is not None:
         log('* ' + str(msg))


# do something

if writeLog:
   logF = open(logFile,'w')

log('Args: {}'.format(','.join(sys.argv[1:])))
log('')

plex = PlexServer(plexURL, plexToken)

total = 0
existed = 0
unrated = 0
tagErrors = 0
fnErrors = 0
taErrors = 0

stars = 6 * [0]

search = os.path.join(winPath, top, '**/*.mp3').replace('\\','/')  
files = glob(search, recursive=True)
log('Found {} mp3 files in \'{}\'.'.format(len(files), search))
log('')

if len(files) == 0:
   log('Done.')
   quit()

for f in files:

   total += 1
   if total % updateMsg == 0:
      log('\nProcessed {}/{}.'.format(total, len(files)))
   jrmcFile = f.replace('\\','/')
   plexFile = plexPath + f.replace(winPath, '').replace('\\','/')  

   try:
      jrmcInfo = getJRMCInfo(f)
   except TagError:
      tagErrors += 1
      header(jrmcFile, plexFile, '', 'Tag error.', quietTagerror)  
      continue
   except Exception as e:
      header(jrmcFile, plexFile, jrmcInfo)
      log(e)
      quit()      

   if jrmcInfo.rating is not None:
      try:
         stars[jrmcInfo.rating] += 1
         setPlexRating(plexFile, jrmcInfo.title, jrmcInfo.artist, jrmcInfo.rating, override=override)
         msg = 'Set rating to ' + str(jrmcInfo.rating) + '.'
         header(jrmcFile, plexFile, jrmcInfo, msg, quietSet)       
      except RatingExistsError:
         existed += 1
         header(jrmcFile, plexFile, jrmcInfo, 'Exists.', quietExist)
      except NoMatchError:
         taErrors += 1
         header(jrmcFile, plexFile, jrmcInfo, 'No title/artist match.')
      except NoMatchFilenameError:
         fnErrors += 1
         header(jrmcFile, plexFile, jrmcInfo, 'No filename match.')
      except Exception as e:
         header(jrmcFile, plexFile, jrmcInfo)
         log(e)
         quit()
   else:
      unrated += 1

log('')
log('Done.')
log('')
log('Total:      {}'.format(total))
log('Tag Errors: {}'.format(tagErrors))
log('FN Errors:  {}'.format(fnErrors))
log('TA Errors:  {}'.format(taErrors))
log('Unrated:    {}'.format(unrated))
if not override:
   log('Existed:    {}'.format(existed))
log('Changed:    {}'.format(total - tagErrors - fnErrors - taErrors - unrated - existed))
log('')
log('Stars: 1:{} 2:{} 3:{} 4:{} 5:{}'.format(stars[1], stars[2], stars[3], stars[4], stars[5]))

if noUpdate:
   log('\n*** Test Mode - no ratings were written! ***')
