# JRMCPlex

## Code Example to read JRMC tags and update Plex user

Created to start trying to use Plex as main audio server; first need the ratings! Then good stuff can hopefully be added for *reallysmartlists*.

Read JRMC tags from mp3 files and update Plex user rating.  Could be extended to create collections, etc.

In my setup, the code is run on Windoze host accessing the mp3 files on a Synology NAS, which is running Plex using the same files in its music library.  

#### Setup/Running

1. windoze host accesses jrmc/plex mp3 files at winPath/...
2. Plex accesses mp3 files at plexPath/...
3. set plexURL/plexToken; get token by going to an item in plex then '...' to 'get info' then 'view xml' and get from url
4. run on windoze host, which parses file tags, tries to find a Plex match, then sets Plex rating if successful

To recursively apply for directories starting with 'g' and change from 5 stars to 1/3/5 stars (abysmal, OK, rocks):

```
python app.py -q -3 "Shared/Media/Music/Rock/g*" 
```

I ran 22085 files in 4 hours.



#### Problems

1. Plex search doesn't work with special chars.  This also appears to be a problem even in manual filters.  Didn't check if there's a solution or different way.  The code hack truncates the search title if special char exists.

These match:

```
Artist Title contains guns
Artist Title contains guns roses
Artist Title contains guns n roses
```

This don't:

```
Artist Title contains guns n' roses
```


