import os, unicodedata
import config
import helpers

def findAssests(metadata, paths, type, part = None):
  root_file = getRootFile(helpers.unicodize(part.file)) if part else None

  # We start by building a dictionary of files to their absolute paths. We also need to know
  # the number of media files that are actually present, in case the found local media asset 
  # is limited to a single instance per media file.
  path_files = {}
  total_media_files = 0
  for path in paths:
    path = helpers.unicodize(path)
    for file_path in os.listdir(path):

      # When using os.listdir with a unicode path, it will always return a string using the
      # NFD form. However, we internally are using the form NFC and therefore need to convert
      # it to allow correct regex / comparisons to be performed.
      file_path = unicodedata.normalize('NFC', file_path)
      if os.path.isfile(os.path.join(path, file_path)):
        path_files[file_path.lower()] = os.path.join(path, file_path)

      # If we've found an actual media file, we should record it.
      (root, ext) = os.path.splitext(file_path)
      if ext.lower()[1:] in config.VIDEO_EXTS:
        total_media_files += 1

  Log('Looking for %s media (%s) in %d paths (root file: %s) with %d media files.', type, metadata.title, len(paths), root_file, total_media_files)
  Log('Paths: %s', ", ".join([ unicode(p) for p in paths ]))

  # Figure out what regexs to use.
  search_tuples = []
  if type == 'season':
    search_tuples += [['season-?%s[-a-z]?' % metadata.index, metadata.posters, config.IMAGE_EXTS, False]]
    search_tuples += [['season-?%s-banner[-a-z]?' % metadata.index, metadata.banners, config.IMAGE_EXTS, False]]
  elif type == 'show':
    search_tuples += [['(show|poster|folder)-?[0-9]?', metadata.posters, config.IMAGE_EXTS, False]]
    search_tuples += [['banner-?[0-9]?', metadata.banners, config.IMAGE_EXTS, False]]
    search_tuples += [['(fanart|art|background|backdrop)-?[0-9]?', metadata.art, config.IMAGE_EXTS, False]]
    search_tuples += [['theme-?[0-9]?', metadata.themes, config.AUDIO_EXTS, False]]
  elif type == 'episode':
    search_tuples += [[re.escape(root_file) + '-?[0-9]?', metadata.thumbs, config.IMAGE_EXTS, False]]
  elif type == 'movie':
    search_tuples += [['(poster|default|cover|movie|folder|' + re.escape(root_file) + ')-?[0-9]?', metadata.posters, config.IMAGE_EXTS, True]]
    search_tuples += [['(fanart|art|background|backdrop|' + re.escape(root_file) + '-fanart' + ')-?[0-9]?', metadata.art, config.IMAGE_EXTS, True]]

  for (pattern, media_list, extensions, limited) in search_tuples:
    valid_keys = []
    
    for file_path in path_files:
      for ext in extensions:
        if re.match('%s.%s' % (pattern, ext), file_path, re.IGNORECASE):

          # Use a pattern if it's unlimited, or if there's only one media file.
          if (limited and total_media_files == 1) or (not limited) or (file_path.find(root_file.lower()) == 0):

            # Read data and hash it.
            data = Core.storage.load(path_files[file_path])
            media_hash = hashlib.md5(data).hexdigest()
      
            # See if we need to add it.
            valid_keys.append(media_hash)
            if media_hash not in media_list:
              media_list[media_hash] = Proxy.Media(data)
              Log('  Local asset added: %s (%s)', path_files[file_path], media_hash)
          else:
            Log('Skipping file %s because there are %d media files.', file_path, total_media_files)
              
    Log('Found %d valid things for pattern %s (ext: %s)', len(valid_keys), pattern, str(extensions))
    media_list.validate_keys(valid_keys)

def getRootFile(filename):
  path = os.path.dirname(filename)
  if 'video_ts' == helpers.splitPath(path.lower())[-1]:
    path = '/'.join(helpers.splitPath(path)[:-1])
  basename = os.path.basename(filename)
  (root_file, ext) = os.path.splitext(basename)
  return root_file