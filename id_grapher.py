# additional dependencies: pygame 
import sys
filenames = sys.argv[1:] if len(sys.argv) > 1 else [input("Filename: ")]
import pygame
pygame.init()
from datetime import datetime,timedelta
import re
from os import getcwd
from random import choice,randint

IMG_HEIGHT = 750
GRAPH_TOP = int(1/10 * IMG_HEIGHT)
GRAPH_BOT = IMG_HEIGHT - 2*GRAPH_TOP
font      = pygame.font.SysFont("verdana",8,True)
font_img  = font.render("messages sent", True, (100,100,100))
font_rect = font_img.get_rect()
Y_FONT_GAP  = font_rect.height 						# used for spacing the y-label font and the graph's left
font_rect.midleft = Y_FONT_GAP, (GRAPH_TOP+GRAPH_BOT)//2
Y_LINE_GAP = Y_FONT_GAP*2 + font_rect.width
#Y_LINE_COORDS = (Y_LINE_GAP, GRAPH_TOP), (Y_LINE_GAP, GRAPH_BOT)
user_colour = pygame.Color(0,0,0)
RANDOM_HUE  = False
NO_USER_DISTINCTION = True
MAX_USERS = 0

time_step_input = 2 #int(input("Time division:\n[0] Minutes\t[1] Hours\t[2] Days\t[3] Months\t[4] Years\n"))
time_format = "%m/%d/%Y"
time_read_index = 0

label_resolution = int(input("Time label resolution:\n[0] Minutes\t[1] Hours\t[2] Days\t[3] Months\t[4] Years\n"))
DAYS_TO_ADD_LIST = (1/(24*60),1/24,1,31,366)
LABEL_FORMATS    = ("%M","%H","%d","%b","%Y")
LOG_BASE_FORMAT  = "%m/%d/%Y %I:%M %p"
line_thickness = time_step_input-1 if time_step_input > 1 else 1
dot_thickness  = time_step_input+1 #if time_step_input > 1 else 1

def get_date_xcoord(current_t, start_t, total_t, graph_w):	return int(Y_LINE_GAP + graph_w * (current_t - start_t).total_seconds()/total_t)

def get_date_ycoord(msg_count, max_msgs):					return int(GRAPH_BOT - (GRAPH_BOT - GRAPH_TOP) * msg_count/max_msgs)

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

class MessageCount:
	'''Tallies messages from all users for each date'''
	def __init__(self,init_name=None):
		self.msg_count = {}					# "name" : count
		if init_name: self.add(init_name)	# giving the option to initialise each MessageCount with the first user of the time period

	def add(self,name):
		try:
			self.msg_count[name] += 1
		except KeyError:
			self.msg_count[name] = 1

	def get(self,name):					# in the case a username didnt send any messages in the MessageCount period but still exists in the guild
		try:
			return self.msg_count[name]
		except KeyError:
			return 0

	def get_max(self):
		return max(self.msg_count.values())


if __name__ == "__main__":
	for filename in filenames:
		#start_date = input(f"Start date? 0 to start graphing from the first message.\nRemember to adhere to this format: {time_format}\n")
		#end_date   = input("End date? 0 to graph till the end. Same format!\n")
		start_date,end_date = "0","0"			# to not waste time; disable when control is needed over automation

		if start_date != "0": start_date = datetime.strptime(start_date, time_format)
		if end_date   != "0": end_date   = datetime.strptime(end_date, time_format)

		with open(filename,"r", errors="ignore") as file:
			messages = file.readlines()[::-1]

		time_msg_count = {}				# "message_time" : MessageCount
		username_data = {}				# "username"     : [(hue value,value_value),(prev_coords)]
		msges = 0
		for message in messages:
			message_time   = message.split()[0]
			message_datetime = datetime.strptime(message[:-1], LOG_BASE_FORMAT)
			if start_date != "0" and message_datetime < start_date: continue
			if end_date   != "0" and message_datetime > end_date: continue

			message_author = "Saser"

			if message_author not in username_data.keys(): username_data[message_author] = [(0,0),None]

			try:
				time_msg_count[message_time].add(message_author)
				
			except KeyError:
				time_msg_count[message_time] = MessageCount(message_author)

			msges += 1

		print(msges)

		max_msgs = max( (msgcount.get_max() for msgcount in time_msg_count.values()) )		# used to limit the y-axis's greatest value
		Y_AXIS_LABEL_STEP = int(round(max_msgs,-len(str(max_msgs))+1)/10)
		if Y_AXIS_LABEL_STEP==0: Y_AXIS_LABEL_STEP = 1
		max_msgs = (max_msgs//Y_AXIS_LABEL_STEP * Y_AXIS_LABEL_STEP) + Y_AXIS_LABEL_STEP
		y_axis_divisions = max_msgs//Y_AXIS_LABEL_STEP
		y_axis_px_step   = (GRAPH_BOT - GRAPH_TOP)//y_axis_divisions
		
		number_of_users = len(username_data.keys())
		colours = [360/number_of_users * i for i in range(number_of_users)]
		for index in range(number_of_users):
			random_hue = choice(colours)
			colours.remove(random_hue)
			username_data[tuple(username_data.keys())[index]] = [(random_hue, 55 if index%2 else 100), None] if RANDOM_HUE else [(360/number_of_users * index, 55 if index%2 else 100), None]

		print(tuple(time_msg_count.keys())[0])
		if start_date == "0": start_date = datetime.strptime(tuple(time_msg_count.keys())[0], time_format)
		if end_date   == "0": end_date   = datetime.strptime(tuple(time_msg_count.keys())[-1], time_format)
		total_time = (end_date - start_date).total_seconds()
		print(total_time)

		graph_width = 1000				# could change so that graph_width changes depending on number of time steps
		img_width   = int(1.5 * Y_LINE_GAP + graph_width)
		graph_right = int(img_width - 0.5*Y_LINE_GAP)
		draw_surface = pygame.Surface((img_width,IMG_HEIGHT), flags=pygame.SRCALPHA)
		draw_surface.fill((230,230,230,255))
		scr = pygame.display.set_mode((img_width,IMG_HEIGHT))

		# drawing y axis label fonts and x axis label lines
		current_y_coord = GRAPH_BOT
		for y_label in range(0, max_msgs+1, Y_AXIS_LABEL_STEP):
			percent_fimg = font.render(str(y_label), True, (80,80,80))
			percent_frect= percent_fimg.get_rect()
			percent_frect.midright = Y_LINE_GAP-5, current_y_coord
			draw_surface.blit(percent_fimg, percent_frect)
			pygame.draw.line(draw_surface, (180,180,180,100), (Y_LINE_GAP, current_y_coord), (graph_right, current_y_coord), 1)
			current_y_coord -= y_axis_px_step

		# drawing usernames
		heading_x_step = img_width//(len(username_data.keys())+1)
		current_x_coord = heading_x_step
		min_y = GRAPH_TOP//3
		y_alternate = True
		for username in username_data.keys():
			user_colour.hsva = (username_data[username][0][0], 100, username_data[username][0][1], 100)
			heading_img = font.render(str(username), True, user_colour)
			heading_rect= heading_img.get_rect()
			heading_rect.midtop = current_x_coord, min_y if y_alternate else int(min_y + Y_FONT_GAP*1.2)
			if len(username_data.keys()) > 2: y_alternate = not y_alternate
			draw_surface.blit(heading_img, heading_rect)
			current_x_coord += heading_x_step

		# x axis labelling
		current_y_coord = GRAPH_BOT+5
		for time_mode in range(5):				# 0 = minutes, 1 = hours, 2 = days, 3 = months, 4 = years
			if time_mode < label_resolution: continue
			
			label_time_format = LABEL_FORMATS[time_mode]
			current_date = start_date
			while current_date <= end_date:
				time_to_write = current_date.strftime(label_time_format)
				time_fimg  = font.render(time_to_write, True, (80,80,80))
				time_frect = time_fimg.get_rect()
				time_frect.topleft = get_date_xcoord(current_date, start_date, total_time, graph_width), current_y_coord
				draw_surface.blit(time_fimg, time_frect)

				current_date += timedelta(days=DAYS_TO_ADD_LIST[time_mode])
				current_date = strip_time(current_date,time_mode)

			current_y_coord += int(Y_FONT_GAP*1.2)

		# actual data graphing
		#msgs_graphed = 0
		current_date = start_date
		while current_date <= end_date:
			for user in username_data.keys():
				try:			 count = time_msg_count[current_date.strftime(time_format)].get(user)
				except KeyError: count = 0
				#msgs_graphed += count

				current_coords = (get_date_xcoord(current_date, start_date, total_time, graph_width), get_date_ycoord(count, max_msgs))
				user_colour.hsva = (username_data[user][0][0], 100, username_data[user][0][1], 100)
				pygame.draw.circle(draw_surface, user_colour, current_coords, dot_thickness)
				if username_data[user][1]: pygame.draw.line(draw_surface, user_colour, username_data[user][1], current_coords, line_thickness)

				username_data[user][1] = current_coords

			current_date += timedelta(days=DAYS_TO_ADD_LIST[time_step_input])
			current_date = strip_time(current_date, time_step_input)

			scr.blit(draw_surface,(0,0))
			pygame.display.flip()

		draw_surface.blit(font_img,font_rect)
		pygame.draw.line(draw_surface, (0,0,0), (Y_LINE_GAP, GRAPH_BOT), (graph_right, GRAPH_BOT), 3)
		pygame.draw.line(draw_surface, (0,0,0), (Y_LINE_GAP, GRAPH_BOT), (Y_LINE_GAP, GRAPH_TOP),  3)
		filename = filename.replace(getcwd()+"\\","")[:-4]
		title_img = font.render(filename, True, (30,30,30))
		title_rect = title_img.get_rect()
		title_rect.center = img_width//2, (IMG_HEIGHT + GRAPH_BOT)//2
		draw_surface.blit(title_img,title_rect)
		author_img = font.render("By Sas", True, (255,0,0))
		author_rect= author_img.get_rect()
		author_rect.bottomright = img_width-5, IMG_HEIGHT-5
		draw_surface.blit(author_img,author_rect)			
		scr.blit(draw_surface,(0,0))
		pygame.display.flip()

		pygame.image.save(draw_surface,f"{filename} w{graph_width},h{GRAPH_BOT-GRAPH_TOP} t{time_step_input} l{label_resolution} y{Y_AXIS_LABEL_STEP} {randint(0,9999)}.png")
