import soundcloud, praw, pafy, download, shutil, os, audiotools
from pydub import AudioSegment

paths = []

client = soundcloud.Client(client_id="cd5081c8ae6cd2d6e2e70ecbebce2ab1")

user_agent = ("The sound scraper bot by /u/thepropterhoc")
r = praw.Reddit(user_agent=user_agent)
#r.login()

subreddit = r.get_subreddit('listentothis')

files = []

"""
for thing in subreddit.get_hot(limit=20):
	if thing.domain == 'youtube.com':
		video = pafy.new(thing.url)
		bestaudio = video.getbestaudio()
		retval = bestaudio.download()
		files += [str(retval)]
	elif thing.domain == 'soundcloud.com':
		track = client.get('/resolve', url=thing.url)
		downloader = download.SoundCloudDownload(thing.url)
		downloader.downloadSongs()
		files += downloader.fileList
		"""
		

for f in files:
	shutil.copy(f, './files/')
	paths += ['./files/' + f]
	os.remove(f)

for f in os.listdir('./files'):
	title, extension = os.path.splitext(f)
	#and not extension == '.ogg' 
	if not extension == '.m4a' and not extension == '.mp3' and not title.startswith('.') and not extension == '.py':
		endFile = './files/' + title + ".mp3"
		startFile = './files/' + f
		AudioSegment.from_file(startFile).export(endFile, format="mp3")
		#audiotools.MP3Audio.from_pcm(endFile, audiotools.open(startFile).to_pcm())

with open('manifest.txt', 'w') as f:
	for writeMe in files:
		f.write(writeMe + '\n')