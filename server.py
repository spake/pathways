#!/usr/bin/python2.7

'''
   Copyright 2013 George Caley

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
'''

from bs4 import BeautifulSoup
import datetime
from flask import Flask, request, send_from_directory, g
import json
import os
import re
import sqlite3
import time
import urllib2

DATABASE_FILENAME = "courses.db"
LOG_FILENAME = "pathways.log"

TIMETABLE_DIR = "timetable"

TIMETABLE_REQUEST_TIMEOUT = 10 # seconds
TIMETABLE_CACHE_TIME = 60*60*6 # 6 hours

CURRENT_YEAR = "2013"

def connect_db():
    return sqlite3.connect(DATABASE_FILENAME)

# logs the current flask request
def log_request():
    f = open(LOG_FILENAME, "a")

    url = request.url
    user_agent = request.user_agent
    remote_addr = request.remote_addr
    now = datetime.datetime.now()

    values = [now, remote_addr, user_agent, url]
    values = map(str, values)
    values = "\t".join(values)

    f.write(values+"\n")
    f.close()

# stupid function for cgi replacement stuff
def dummy_print():
    pass

# fetches the timetable file for the given course
# returns the HTML data if successful, empty string if HTTP 404 (to prevent retries),
# None if any other HTTP error (likely their site is broken, or connection problems)
def fetch_timetable_course(code):
    print "Fetching fresh timetable for", code
    try:
        u = urllib2.urlopen("http://www.timetable.unsw.edu.au/%s/%s.html" % (CURRENT_YEAR, code), timeout=TIMETABLE_REQUEST_TIMEOUT)
        data = u.read()
    except urllib2.HTTPError as e:
        if e.code == 404:
            print "Got 404"
            data = ""
        else:
            print "Misc error:", e.code
            data = None
    except urllib2.URLError as e:
        print "Timeout/other error!"
        raise e
    return data

# returns a tuple of (timetable_data, time)
# where timetable_data is the HTML data for the timetable file,
# and time is the timestamp for the data
# loads from cache if data exists and is less than TIMETABLE_CACHE_TIME seconds old
def get_timetable_course_data(code):
    # check if it's been cached
    filename = "%s/%s.html" % (TIMETABLE_DIR, code)
    if os.path.exists(filename):
        mtime = os.path.getmtime(filename)
        # ensure it is not too old
        if time.time() - mtime <= TIMETABLE_CACHE_TIME:
            return (open(filename, "r").read(), mtime)
        else:
            print "Timetable for", code, "is too old"
    else:
        print "Timetable for", code, "doesn't exist"

    data = fetch_timetable_course(code)
    if data is not None:
        f = open(filename, "w")
        f.write(data)
        f.close()

    return (data, time.time())

# does what it says on the tin
def day_to_index(day):
    indexes = {
        "Mon": 0,
        "Tue": 1,
        "Wed": 2,
        "Thu": 3,
        "Fri": 4,
        "Sat": 5,
        "Sun": 6
    }
    return indexes[day]

# returns a tuple of (timetable_data, time)
# timetable_data is the timetable data for the given course, as a dictionary
# time is the timestamp for the data
def get_timetable_course_schedule(code):
    data, mtime = get_timetable_course_data(code)

    timetable = {}

    # now find some interesting information about the course
    schedule_summary = re.findall(r'<td class="data" colspan="5"><a href="#(.*?)">(.*?)</a></td>.*?</tr>.*?<tr>.*?<td class="data">&nbsp;</td>.*?<td class="data">.*?<table width="100%" cellspacing="0">.*?<tr>.*?<td class="data" width="25%">&nbsp;</td>.*?<td class="data">(.*?)</td>.*?</tr>.*?</table>.*?</td>.*?<td class="data">(.*?)</td>.*?<td class="data">(.*?)</td>.*?<td class="data"><font color="red">(.*?)</font></td>', data, re.DOTALL)
    
    for _, period_name, period_code, contact, census_date, notes in schedule_summary:
        if period_code not in timetable:
            timetable[period_code] = {
                "name": period_name,
                "contact": contact,
                "classes": []
            }

    ROW_RE = re.compile(r'<tr class="row(?:High|Low)light">(.*?)</tr>')
    DATA_RE = re.compile(r'<td class="data">(.*?)</td>')

    soup = BeautifulSoup(data)

    for period in soup.find_all("td", {"class": "sectionSubHeading"}):
        data = period.parent.parent.next_sibling#.next_sibling
        for row in data.find_all("tr", {"class": re.compile("row(High|Low)light")}):
            info = map(lambda node: node.text, row.find_all("td", {"class": "data"}))

            name = info[0]
            
            status = info[4] # Open, Full, On Hold
            size, capacity = map(int, re.match(r"(\d+)/(\d+)", info[5]).groups())
            period = info[1]
            code = info[3]
            classCode = info[2]

            if period not in ("T1","T2"):
                continue

            times = info[6].replace("\n", "")
            times = re.split(r"\(.*?\), ", times)
            for time in times:
                match = re.match(r"^\s*(\w+)\s+(\d{2}):(\d{2})\s+-\s+(\d{2}):(\d{2}).*", time)
                if not match:
                    continue

                start = int(match.group(2))
                finish = int(match.group(4))

                start_minute = int(match.group(3))
                finish_minute = int(match.group(5))

                day = match.group(1)

                if start_minute != 0 or finish_minute != 0:
                    print "wtf"
                    print info

                # add thing
                day_index = day_to_index(day)
                details = {
                    "startHour": start,
                    "finishHour": finish,
                    "size": size,
                    "capacity": capacity,
                    "day": day_index,
                    "status": status,
                    "name": name,
                    "code": code,
                    "classCode": classCode
                }
                timetable[period]["classes"].append(details)

    return (timetable, mtime)

# loads details about a given course from the database
# set detailed to True or False depending on how much detail you want...
def get_course_details(code, detailed=False):
    cur = g.db.cursor()

    if detailed:
        cols = ["code", "name", "description", "prerequisites", "corequisites", "exclusions", "gened", "outline", "uoc"]
    else:
        cols = ["code", "name"]

    result = cur.execute("SELECT %s FROM courses WHERE code = ?" % ", ".join(cols), (code,)).fetchone()
    if not result:
        # create placeholder result
        d = {}
        d["code"] = code
        d["exists"] = False
    else:
        # create tuples
        d = {}
        for i in xrange(len(cols)):
            d[cols[i]] = result[i]
        d["exists"] = True

        if detailed:
            # add timetable stuff
            schedule, mtime = get_timetable_course_schedule(code)

            if "T1" in schedule:
                d["s1"] = schedule["T1"]
            if "T2" in schedule:
                d["s2"] = schedule["T2"]
            d["timetableLastUpdated"] = mtime

    return d

# ~~~~~~~~~~~~
# FLASK STUFF!
# ~~~~~~~~~~~~

app = Flask(__name__)

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    if hasattr(g, "db"):
        g.db.close()

@app.route("/tree/<code>")
def tree(code):
    cur = g.db.cursor()

    log_request()

    above = list()
    below = list()
    
    try:
        centre = get_course_details(code, detailed=True)
    except Exception as e:
        print e
        return json.dumps({"error": True})

    for above_code, type in cur.execute("SELECT source, type FROM relationships WHERE destination = ?", (code,)).fetchall():
    	if type != "exclusion":
            details = get_course_details(above_code)
            details["type"] = type
            above.append(details)

    for below_code, type in cur.execute("SELECT destination, type FROM relationships WHERE source = ?", (code,)).fetchall():
    	if type != "exclusion":
            details = get_course_details(below_code)
            details["type"] = type
            below.append(details)

    return json.dumps({"centre": centre, "above": above, "below": below, "error": False})

@app.route("/all-courses")
def all_courses():
    cur = g.db.cursor()

    courses = list()

    result = cur.execute("SELECT code, name FROM courses ORDER BY code ASC")

    for code, name in result:
        courses.append({"label": name + " - " + code, "value": code})

    return json.dumps(courses)

@app.route("/all-courses-names")
def all_courses():
    cur = g.db.cursor()

    courses = list()

    result = cur.execute("SELECT code, name FROM courses ORDER BY code ASC")

    for code, name in result:
        courses.append(name + " - " + code)

    return json.dumps(courses)

@app.route("/all-courses-reverse")
def all_courses():
    cur = g.db.cursor()

    courses = dict()

    result = cur.execute("SELECT code, name FROM courses ORDER BY code ASC")

    for code, name in result:
        key = name + " - " + code
        courses[key] = code

    return json.dumps(courses)

@app.route("/all-gened")
def all_gened():
    cur = g.db.cursor()

    courses = list()

    result = cur.execute("SELECT code, name FROM courses WHERE gened = 1 ORDER BY code ASC")

    for code, name in result:
        courses.append({"label": name + " - " + code, "value": code})

    return json.dumps(courses)

@app.route("/")
def static_from_root():
    return send_from_directory(app.static_folder, "index.html")

if __name__ == "__main__":
    app.run(debug=True)
