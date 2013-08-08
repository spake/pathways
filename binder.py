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

import codecs
import os
import re
import sqlite3

# woo regular expressions
PREREQS_RE = re.compile(r"Pre-?req(?:uisites?)?:(.*?)(?:</p>|;)")
EXCLUSIONS_RE = re.compile(r"((?:Excluded|Exclusion|Exclusions|(?:and )?Excludes)[: ](.*?))(?:</p>|<br />)", re.IGNORECASE)
COREQS_RE = re.compile(r"Co-?requisite:(.*?)</p>", re.IGNORECASE)
NAME_RE = re.compile(r"<title>UNSW Handbook Course - (.*?) - [A-Z]{4}[0-9]{4}</title>", re.DOTALL)
DESC_RE = re.compile(r"<!-- Start Course Description -->(.*?)<!-- End Course description -->", re.DOTALL | re.IGNORECASE)
GENED_RE = re.compile(r"Available for General Education:")
OUTLINE_RE = re.compile(r"Course Outline:.*?<a .*?href=[\"'](.*?)[\"']")
UOC_RE = re.compile(r"Units of Credit:.*?([0-9]+)")

COURSE_RE = re.compile(r"[A-Z]{4}[0-9]{4}", re.IGNORECASE)
BR_RE = re.compile(r"<br ?/?>", re.IGNORECASE)
TAG_RE = re.compile(r"</?.*?>")

TYPE_PREREQUISITE = "prerequisite"
TYPE_COREQUISITE = "corequisite"
TYPE_EXCLUSION = "exclusion"

DATABASE_FILENAME = "courses.db"
COURSE_DIR = "courses"

if os.path.exists(DATABASE_FILENAME):
    print "Deleting existing database"
    os.unlink(DATABASE_FILENAME)

print "Creating new database"
conn = sqlite3.connect(DATABASE_FILENAME)
cur = conn.cursor()

print "Creating tables"
cur.execute("CREATE TABLE courses (code text primary key, name text, description text, prerequisites text, corequisites text, exclusions text, gened integer, outline text, uoc integer)")
cur.execute("CREATE TABLE relationships (source text, destination text, type text)")

print "Loading course list"
print

filenames = os.listdir(COURSE_DIR)

i = 0
for filename in filenames:
    i += 1
    code = filename.rstrip(".html")
    print "Reading %s (%d/%d)" % (code, i, len(filenames))

    # open with unicode support
    f = codecs.open("%s/%s" % (COURSE_DIR, filename), encoding="utf-8", mode="r")
    data = f.read()
    f.close()

    # strip &nbsp;'s and <strong> tags
    data = data.replace("&nbsp;", " ")
    data = data.replace("<strong>", "")
    data = data.replace("</strong>", "")

    # find name
    match = re.search(NAME_RE, data)
    if match:
        name = match.group(1).strip().replace("\n", "")
        print "Found name:", name
    else:
        name = None
        print "Couldn't find name"
        print "Fatal error!"
        quit()

    # find exclusions. all of them.
    exclusions = ""
    exclusions_list = []
    while True:
        match = re.search(EXCLUSIONS_RE, data)
        if match:
            exclusions = match.group(2).strip()
            print "Found exclusions:", exclusions
            data = data.replace(match.group(1), "")
            exclusions_list = re.findall(COURSE_RE, exclusions)
            print "Exclusions list:", exclusions_list
        else:
            #exclusions = None
            #exclusions_list = []
            #print "Couldn't find exclusions"
            break

    # find corequisites
    match = re.search(COREQS_RE, data)
    if match:
        coreqs = match.group(1).strip()
        print "Found corequisites:", coreqs
        data = data.replace(match.group(0), "")
        coreqs_list = map(unicode.upper, re.findall(COURSE_RE, coreqs))
        print "Corequisites list:", coreqs_list
    else:
        coreqs = None
        coreqs_list = []
        print "Couldn't find corequisites"

    # find prerequisites
    match = re.search(PREREQS_RE, data)
    if match:
        prereqs = match.group(1).strip()
        print "Found prerequisites:", prereqs
        data = data.replace(match.group(0), "")
        prereqs_list = map(unicode.upper, re.findall(COURSE_RE, prereqs))
        print "Prerequisites list:", prereqs_list
    else:
        prereqs = None
        prereqs_list = []
        print "Couldn't find prerequisites"

    # find description
    match = re.search(DESC_RE, data)
    if match:
        desc = match.group(1).strip()
        # change <br>'s
        #desc = re.sub(BR_RE, "\n", desc)
        # strip tags
        #desc = re.sub(TAG_RE, "", desc)
        #print "Found description:", desc
        print "Found description"
    else:
        desc = None
        print "Couldn't find description"

    # find general education statement
    match = re.search(GENED_RE, data)
    if match:
        gened = 1
    else:
        gened = 0

    # find course outline
    match = re.search(OUTLINE_RE, data)
    if match:
        outline = match.group(1).strip()
        print "Found course outline:", outline
    else:
        outline = None
        print "Couldn't find course outline"

    # find uoc
    match = re.search(UOC_RE, data)
    if match:
        uoc = match.group(1).strip()
        try:
            uoc = int(uoc)
            print "Found UoC:", uoc
        except:
            print "UoC was not an integer: '%s'" % uoc
            uoc = None
    else:
        uoc = None
        print "Couldn't find UoC"

    print "Writing to database"
    cur.execute("INSERT INTO courses (code, name, description, prerequisites, corequisites, exclusions, gened, outline, uoc) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (code, name, desc, prereqs, coreqs, exclusions, gened, outline, uoc))
    for prereq in prereqs_list:
        cur.execute("INSERT INTO relationships (source, destination, type) VALUES (?, ?, ?)", (code, prereq, TYPE_PREREQUISITE))
    for coreq in coreqs_list:
        cur.execute("INSERT INTO relationships (source, destination, type) VALUES (?, ?, ?)", (code, coreq, TYPE_COREQUISITE))
    for exclusion in exclusions_list:
        cur.execute("INSERT INTO relationships (source, destination, type) VALUES (?, ?, ?)", (code, exclusion, TYPE_EXCLUSION))
    print

conn.commit()
conn.close()
