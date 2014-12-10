import soundcloud, praw, pafy, download, shutil, os, sys
from pydub import AudioSegment

reload(sys)
sys.setdefaultencoding('utf8')
reload(sys)

def fetch(num):
	paths = []

	client = soundcloud.Client(client_id="cd5081c8ae6cd2d6e2e70ecbebce2ab1")

	user_agent = ("The sound scraper bot by /u/thepropterhoc")
	r = praw.Reddit(user_agent=user_agent)
	#r.login()

	subreddit = r.get_subreddit('listentothis')

	files = []

	for thing in subreddit.get_hot(limit=num):
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

	shutil.rmtree('./files/')
	os.mkdir('./files/')

	for f in files:
		shutil.copy(f, './files/')
		paths += ['./files/' + f]
		os.remove(f)

	for f in os.listdir('./files'):
		title, extension = os.path.splitext(f)
		#and not extension == '.ogg' 
		if not extension == '.mp3' and not title.startswith('.') and not extension == '.py':
			endFile = './files/' + title + ".mp3"
			startFile = './files/' + f
			AudioSegment.from_file(startFile).export(endFile, format="mp3")
			os.remove(startFile)
			#audiotools.MP3Audio.from_pcm(endFile, audiotools.open(startFile).to_pcm())

	retval = []

	for f in os.listdir('./files'):
		title, extension = os.path.splitext(f)
		if extension == '.mp3':
			retval += [title + extension]

	return retval