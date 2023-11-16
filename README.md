# temp-cs19-conversions
This is a small program repurposed from an old project of mine, which was initially used for graphing messages, watch history, and other time-related data over time, e.g. from Discord, Google, Facebook, etc. It demonstrates how rudimentary graphing of such data can reveal patterns in a user's schedule, by graphing data over time (**id_grapher.py**) or generating an "hours of the day-time" graph to highlight daily patterns (**id_daily_grapher.py**).

Some (fake!) ID swipes data is provided as **"swipes_fake.txt"** - you can drag an drop the file onto either of the Python files to input the data and run the program. You can also input your own data, but do note that:
1) you can't seem to get the time information from the data download itself, so you might have to copy/scrape off the my.brown.edu website;
2) you might have to pad the days and months with zeroes (e.g. 01/05/2023 instead of the default 1/5/2023), because the website uses an inconvenient-as-hell date format.
