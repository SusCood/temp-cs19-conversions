# additional dependencies: pygame
import sys
filenames = sys.argv[1:] if len(sys.argv) > 1 else [input("Filename: ")]
import pygame
pygame.init()
from datetime import datetime,timedelta
import re
from os import getcwd
from random import randint,choice

# stripped  = reducing precision from the RHS direction (rounding up time) (x-axis)
# truncated = reducing precision from the LHS direction (modulus-ing time) (y-axis)

# MORE TODOS:
# make graphs for specific users and compare

IMG_HEIGHT  = 750
GRAPH_TOP   = int(1/10 * IMG_HEIGHT)
GRAPH_BOT   = IMG_HEIGHT - GRAPH_TOP
GRAPH_HEIGHT= GRAPH_BOT - GRAPH_TOP
GRAPH_WIDTH = 1000
LINE_WIDTH  = 10
MSG_LIMIT   = 255000000					# limit of messages that can be tallied per "pixel", to avoid random bursts in messages overshadowing the other messages like in buddhabrot
USER_MIN_VAL= 50
USER_MAX_VAL= 100
BG_COLOUR         = 255,255,255
AXES_LABEL_COLOUR = 50,80,50
GRAPH_DIV_COLOUR  = 200,200,200
AXES_LINE_COLOUR  = 130,130,180
GRAPH_DIV_THICC   = 3
GRAPH_LINE_THICC  = 15
user_colour = pygame.Color(0,0,0)
USER_Y_ALTERNATE = True
ROUND_TRUNCATE   = False
USE_HSV = True
# the stuff I vary to get different graphs:
# - USE_HSV: true gives a more visually pleasing graph, as the lowest frequencies of messages are easily visible too. false is better to identify peaks of frequencies
# - NO_USER_DISTINCTION: whether or not I want different users to have different colours for their data. I only enable this when I whitelist a specific user
# - ROUND_TRUNCATE: ...I was running out of variable names, alright? This rounds the datetimes to a specific precision, making overall trends show up more easily

REARRANGED_USER_HUES = False
RAN_USER_HUE = True
RAN_HUE = True
FIXED_HUE = -1		#-1

y_axis_headers = ("minutes of the hour","hours of the day","days of the week","days of the month","months of the year")
Y_MAX_SEC_LIST = (3600, 3600*24, 3600*24*7, 3600*24*31, 3600*24*366)
Y_LABELS = (tuple((i for i in range(0,60,10))), tuple((i for i in range(0,24,2))), ("Mon","Tue","Wed","Thu","Fri","Sat","Sun"), tuple((i for i in range(1,31,1))), tuple((i for i in range(1,12,1))))
#print("Y-axis scale:")
y_header_index = 1 #int(input( "\t".join( f"({i}) {y_axis_headers[i]}" for i in range(len(y_axis_headers)) ) + "\n") )
#y_header_index = int(input(f"Y-axis scale:\n{ "\t".join( (f"({i}) {y_axis_headers[i]}" for i in range(len(y_axis_headers))) ) }\n"))
axesfont    = pygame.font.SysFont("verdana",12,True)
labelfont   = pygame.font.SysFont("verdana", 8,True)
ylabel_fimg = axesfont.render(y_axis_headers[y_header_index], True, AXES_LABEL_COLOUR)
ylabel_frect= ylabel_fimg.get_rect()
Y_LABEL_GAP = ylabel_frect.height 						# used for spacing the y-label font and the graph's left
Y_AXIS_GAP  = Y_LABEL_GAP*3 + ylabel_frect.width		# 1 * YAG to the left of ylabel font, 2 * YAG to the right (to give space for y-axis number labels)
ylabel_frect.midleft = Y_LABEL_GAP, (GRAPH_TOP+GRAPH_BOT)//2
IMG_WIDTH   = Y_AXIS_GAP + GRAPH_WIDTH + Y_AXIS_GAP

time_step_input = 2 #int(input("Time division:\n[0] Minutes\t[1] Hours\t[2] Days\t[3] Months\t[4] Years\n"))
time_format = "%m/%d/%Y %I:%M %p"
time_read_index = 0

label_resolution = 2 #int(input("X-axis label resolution:\n[0] Minutes\t[1] Hours\t[2] Days\t[3] Months\t[4] Years\n"))
DAYS_TO_ADD_LIST = (1/(24*60),1/24,1,31,366)			# adding xth of a day as the x-axis time step unit
LABEL_FORMATS    = ("%M","%H","%d","%b","%Y")
LOG_BASE_FORMAT  = "%m/%d/%Y %I:%M %p"					# time format in the log; change if time format is different

def get_date_xcoord(current_t, start_t, total_t):	return int(Y_AXIS_GAP + GRAPH_WIDTH * (current_t  - start_t).total_seconds()/total_t)

def get_date_ycoord(truncated_t, y_timemode):		return int(GRAPH_BOT - GRAPH_HEIGHT * truncated_t.total_seconds()/Y_MAX_SEC_LIST[y_timemode])

def strip_time(time,timemode):
	if timemode == 2:
		return datetime(time.year, time.month, time.day)
	elif timemode == 3:
		return datetime(time.year, time.month, 1)
	elif timemode == 4:
		return datetime(time.year, 1, 1)
	elif timemode == 0:
		return datetime(time.year, time.month, time.day, time.hour, time.minute)
	elif timemode == 1:
		return datetime(time.year, time.month, time.day, time.hour)

def truncate_time(dttime,y_timemode):			# returns timedelta of truncated time
	if   y_timemode == 0:
		return dttime - datetime(dttime.year, dttime.month, dttime.day, dttime.hour)		# truncate so that only minutes are left
	elif y_timemode == 1:
		if ROUND_TRUNCATE: dttime = strip_time(dttime,1)
		return dttime - datetime(dttime.year, dttime.month, dttime.day)		# strip_time
	elif y_timemode == 2:		# weeks
		if ROUND_TRUNCATE: dttime = strip_time(dttime,2) #2)
		return (dttime- datetime(dttime.year, dttime.month, dttime.day)) + timedelta(days=dttime.weekday())
	elif y_timemode == 3:
		if ROUND_TRUNCATE: dttime = strip_time(dttime,2) #2)
		return dttime - datetime(dttime.year, dttime.month, 1) #+ timedelta(days=1)
	elif y_timemode == 4:
		if ROUND_TRUNCATE: dttime = strip_time(dttime,3) #2) #3)
		return dttime - datetime(dttime.year, 1, 1) #+ timedelta(days=31.4375)

class MessageCount:
	'''Tallies messages for each user at each pixel FOR A PARTICULAR X TIME DIVISION'''
	def __init__(self):
		self.msg_count = {}			# "name" : count_dict; count_dict = y_coord : count
		self.max_msgs = 0

	def add(self,name,dttime):
		time = truncate_time(dttime,  y_header_index)
		y_coord = get_date_ycoord(time,y_header_index)

		if name not in self.msg_count.keys():
			self.msg_count[name] = {}
		if y_coord not in self.msg_count[name].keys():
			self.msg_count[name][y_coord] = 0

		if self.msg_count[name][y_coord] < MSG_LIMIT:
			self.msg_count[name][y_coord] += 1
			if self.msg_count[name][y_coord] > self.max_msgs:
				self.max_msgs = self.msg_count[name][y_coord]

scr = pygame.display.set_mode((IMG_WIDTH,IMG_HEIGHT))
# can't blit anything before this, since screen needs to be cleared after each file
for filename in filenames:
	#start_date = input(f"Start date? 0 to start graphing from the first message.\nRemember to adhere to this format: {time_format}\n")
	#end_date   = input("End date? 0 to graph till the end. Same format!\n")
	start_date,end_date = "0","0"			# to not waste time; disable when control is needed over automation
	if start_date != "0": start_date = datetime.strptime(start_date,time_format)
	if end_date   != "0": end_date   = datetime.strptime(end_date,  time_format)

	with open(filename,"r", errors="ignore") as file:
		messages = file.readlines()[::-1]
	filename = filename.replace(getcwd()+"\\","")[:-4]
	filename = filename if len(sys.argv) > 1 else filename[:-4]

	pygame.display.set_caption(filename)
	scr.fill(BG_COLOUR)

	time_msg_count = {}				# "stripped message_time" : MessageCount
	username_data  = {}				# "username"              : (hue_value,value_value); value will be used only for the username legend
	for message in messages:
		message_time   = message[:-1]		# stripped time text
		message_datetime = datetime.strptime(message[:-1], LOG_BASE_FORMAT)		# true time
		if start_date != "0" and message_datetime < start_date: continue
		if end_date   != "0" and message_datetime > end_date:   continue

		message_author = "Sase"

		if message_author not in username_data.keys(): username_data[message_author] = (0,0)
		
		if message_time not in time_msg_count.keys():  time_msg_count[message_time]  = MessageCount()

		time_msg_count[message_time].add(message_author,message_datetime)

	if start_date == "0": start_date = datetime.strptime(tuple(time_msg_count.keys())[0],  time_format)
	if end_date   == "0": end_date   = datetime.strptime(tuple(time_msg_count.keys())[-1], time_format)
	total_time = (end_date - start_date).total_seconds()
	line_length = int((DAYS_TO_ADD_LIST[time_step_input]*24*3600)/total_time * GRAPH_WIDTH)

	number_of_users = len(username_data.keys())
	colours = [360/number_of_users * i for i in range(number_of_users)]
	for index in range(number_of_users):
		user_val = USER_MIN_VAL if index%2 else USER_MAX_VAL
		if RAN_USER_HUE:
			hue = randint(0,360)
		elif REARRANGED_USER_HUES:
			hue = choice(colours)
			colours.remove(random_hue)
		else:
			hue = 360/number_of_users * index
		username_data[tuple(username_data.keys())[index]] = (hue, user_val)

	y_label_list = Y_LABELS[y_header_index]
	y_step = int(GRAPH_HEIGHT/len(y_label_list))
	current_y = GRAPH_BOT
	for i in range(len(y_label_list)):
		y_fimg = labelfont.render(str(y_label_list[i]), True, AXES_LABEL_COLOUR)
		y_frect= y_fimg.get_rect()
		y_frect.midright = Y_AXIS_GAP-5, current_y
		scr.blit(y_fimg, y_frect)
		pygame.draw.line(scr, GRAPH_DIV_COLOUR, (Y_AXIS_GAP, current_y), (GRAPH_WIDTH+Y_AXIS_GAP, current_y), GRAPH_DIV_THICC)
		current_y -= y_step
	
	heading_x_step = IMG_WIDTH//(len(username_data.keys())+1)
	current_x_coord = heading_x_step
	min_y = GRAPH_TOP//3
	for username in username_data.keys():
		user_colour.hsva = (username_data[username][0] if FIXED_HUE==-1 else FIXED_HUE, 100, username_data[username][1], 100)
		heading_img = axesfont.render(str(username), True, user_colour)
		heading_rect= heading_img.get_rect()
		heading_rect.midtop = current_x_coord, min_y if USER_Y_ALTERNATE else int(min_y + Y_LABEL_GAP*1.2)
		if len(username_data.keys()) > 2: USER_Y_ALTERNATE = not USER_Y_ALTERNATE
		scr.blit(heading_img, heading_rect)
		current_x_coord += heading_x_step

	username_data = {"Sase":(randint(0,360) if RAN_HUE else 0,100)}

	# x axis labelling
	current_y_coord = GRAPH_BOT + GRAPH_LINE_THICC//2 + 3
	for time_mode in range(5):				# 0 = minutes, 1 = hours, 2 = days, 3 = months, 4 = years
		if time_mode < label_resolution: continue
		
		label_time_format = LABEL_FORMATS[time_mode]
		current_date = start_date
		while current_date <= end_date:
			current_x_coord = get_date_xcoord(current_date, start_date, total_time)
			time_to_write = current_date.strftime(label_time_format)
			time_fimg  = labelfont.render(time_to_write, True, AXES_LABEL_COLOUR)
			time_frect = time_fimg.get_rect()
			time_frect.midtop = current_x_coord, current_y_coord
			scr.blit(time_fimg, time_frect)
			pygame.draw.line(scr, GRAPH_DIV_COLOUR, (current_x_coord, GRAPH_BOT), (current_x_coord, GRAPH_TOP), GRAPH_DIV_THICC)

			current_date += timedelta(days=DAYS_TO_ADD_LIST[time_mode])
			current_date = strip_time(current_date,time_mode)
		current_y_coord += int(Y_LABEL_GAP*1.2)

	pygame.draw.line(scr, AXES_LINE_COLOUR, (Y_AXIS_GAP, GRAPH_BOT), (GRAPH_WIDTH+Y_AXIS_GAP, GRAPH_BOT), 3)
	pygame.draw.line(scr, AXES_LINE_COLOUR, (Y_AXIS_GAP, GRAPH_BOT), (Y_AXIS_GAP, GRAPH_TOP),             3)
	scr.blit(ylabel_fimg,ylabel_frect)
	user_colour.hsva = randint(0,360), 100, 100, 100
	title_img = axesfont.render(filename, True, user_colour)
	title_rect= title_img.get_rect()
	title_rect.center = IMG_WIDTH//2, GRAPH_BOT + int(2/3 * (IMG_HEIGHT - GRAPH_BOT))
	author_img = axesfont.render("By Sas", True, (255,0,0))
	author_rect= author_img.get_rect()
	author_rect.bottomright = IMG_WIDTH-5, IMG_HEIGHT-5
	scr.blit(author_img,author_rect)
	scr.blit(title_img,title_rect)

	# actual data graphing
	for message_time in time_msg_count.keys():
		message_dttime = datetime.strptime(message_time,time_format)
		current_x_coord = get_date_xcoord(message_dttime, start_date, total_time)

		for username in username_data.keys():
			if username not in time_msg_count[message_time].msg_count.keys():
				continue

			for y_coord in time_msg_count[message_time].msg_count[username].keys():
				if USE_HSV:
					user_colour.hsva = username_data[username][0] if FIXED_HUE==-1 else FIXED_HUE, 100, 100 - time_msg_count[message_time].msg_count[username][y_coord]/time_msg_count[message_time].max_msgs * 100, 100
				else:
					user_colour.hsla = username_data[username][0], 100, 100 - time_msg_count[message_time].msg_count[username][y_coord]/time_msg_count[message_time].max_msgs * 100, 100
				pygame.draw.line(scr, user_colour, (current_x_coord,y_coord), (current_x_coord+line_length,y_coord), GRAPH_LINE_THICC)

		pygame.display.flip()

	pygame.image.save(scr,f"truncstand {filename} w{GRAPH_WIDTH},h{GRAPH_HEIGHT} t{time_step_input} l{label_resolution} y{y_header_index} r{ROUND_TRUNCATE} {randint(0,9999)}.png")