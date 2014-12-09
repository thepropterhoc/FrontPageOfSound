import pygame, os

for f in os.listdir('./'):
	print f

for f in [x for x in os.listdir('./') if x.endswith('.mp3')]:
	print f
	pygame.mixer.init()
	pygame.mixer.music.load(f)
	pygame.mixer.music.play()
	next = raw_input()
	while (next != "next"):
		next = raw_input()
	pygame.mixer.music.stop()