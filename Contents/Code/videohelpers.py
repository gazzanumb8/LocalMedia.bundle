import os
import helpers

from mutagen.mp4 import MP4

class VideoHelper(object):
  def __init__(self, filename):
    self.filename = filename

def VideoHelpers(filename):
  filename = helpers.unicodize(filename)
  file = os.path.basename(filename)
  (file, ext) = os.path.splitext(file)

  for cls in [ MP4VideoHelper ]:
    if cls.is_helper_for(ext):
      return cls(filename)
  return None

#####################################################################################################################

class MP4VideoHelper(VideoHelper):
  @classmethod
  def is_helper_for(cls, file_extension):
    return file_extension.lower() in ['.mp4', '.m4v', '.mov']

  def process_metadata(self, metadata, episode = None):

    if episode == None:
      item = metadata
    else:
      item = episode

    Log('Reading MP4 tags')
    try: tags = MP4(self.filename)
    except: 
      Log('An error occurred while attempting to parse the MP4 file: ' + self.filename)
      return

    # Coverart
    try: 
      picture = Proxy.Media(str(tags["covr"][0]))

      # If we're dealing with an actual episode, it uses thumbs rather than posters.
      if episode != None:
        item.thumbs['atom_coverart'] = picture
      else:
        item.posters['atom_coverart'] = picture
    except: pass

    # Title
    try:
      title = tags["\xa9nam"][0]
      item.title = title
    except: pass

    # Sort Title
    try:
      title_sort = tags["sonm"][0]
      item.title_sort = title_sort
    except: pass

    # Summary (long or short)
    try:
      try:
        summary = tags["ldes"][0]
      except:
        summary = tags["desc"][0]
      item.summary = summary
    except: pass

    # Genres
    try:
      if "\xa9gen" in tags:
        genres = tags["\xa9gen"][0]
      else:
        genres = tags["gnre"][0]
      if len(genres) > 0:
        if ':' in genres:
          genre_list = genres.split(':')
        elif ',' in genres:
          genre_list = genres.split(',')
        else:
          genre_list = genres.split('/')
        metadata.genres.clear()
        for genre in genre_list:
          metadata.genres.add(genre.strip())
    except: pass

    # Release Date & Year
    try:
      releaseDate = tags["\xa9day"][0]
      releaseDate = releaseDate.split('T')[0]
      parsedDate = Datetime.ParseDate(releaseDate)
      item.originally_available_at = parsedDate.date()
      item.year = parsedDate.year
    except: pass

    # Content Rating
    try:
      rating = tags["----:com.apple.iTunes:iTunEXTC"][0].split('|')[1]
      if len(rating) > 0:
        item.content_rating = rating
    except: pass

    # Look for iTunes-style metadata, use regular tags otherwise
    try:
      pl = plistlib.readPlistFromString(str(tags["----:com.apple.iTunes:iTunMOVI"][0]))
    except:
      pl = None

    # Directors
    try:
      if pl and 'directors' in pl and pl['directors']:
        item.directors.clear()
        for director in pl['directors']:
          item.directors.add(director['name'])
    except: pass

    # Writers
    try:
      if pl and 'screenwriters' in pl and pl['screenwriters']:
        item.writers.clear()
        for writer in pl['screenwriters']:
          item.writers.add(writer['name'])
    except: pass

    # Cast
    try:
      if pl and 'cast' in pl and pl['cast']:
        item.roles.clear()
        for actor in pl['cast']:
          role = item.roles.new()
          role.actor = actor['name']
      else:
        artists = tags["\xa9ART"][0]
        if len(artists) > 0:
          artist_list = artists.split(',')
          item.roles.clear()
          for artist in artist_list:
            role = item.roles.new()
            role.actor = artist.strip()
    except: pass
  
    # Studio
    try:
      if pl and 'studio' in pl and pl['studio']:
        item.studio = pl['studio']
      else:
        try:
          copyright = tags["cprt"][0]
          if len(copyright) > 0:
            item.studio = copyright
        except: pass
    except: pass

    # Collection
    try:
      albums = tags["\xa9alb"][0]
      if len(albums) > 0:
        album_list = albums.split('/')
        item.collections.clear()
        for album in album_list:
          item.collections.add(album.strip())
    except: pass
