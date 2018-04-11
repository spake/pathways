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

import urllib2
import re
import sys
import os

COURSES_DIR = "courses"

UG = "undergraduate"
PG = "postgraduate"

CURRENT_YEAR = "2017"

COURSE_LIST_RE = re.compile(r'<TD class="(?:evenTableCell)?" align="left">([A-Z]{4}[0-9]{4})</TD>')

def scrape_list(url):
    print "Fetching page data"
    data = urllib2.urlopen(url).read()
    print

    # find courses
    print "Finding course codes"
    codes = re.findall(COURSE_LIST_RE, data)

    print "Done"
    print
    return codes

def scrape_area(area, level=UG):
    print "Finding all courses for %s" % area
    return scrape_list("https://www.handbook.unsw.edu.au/vbook%s/brCoursesBySubjectArea.jsp?studyArea=%s&StudyLevel=%s" % (CURRENT_YEAR, area, level))

def scrape_everything(level=UG):
    url = "http://www.handbook.unsw.edu.au/vbook%s/brCoursesBySubjectArea.jsp?StudyLevel=%s&descr=A" % (CURRENT_YEAR, level)
    print "Reading area list"
    data = urllib2.urlopen(url).read()
    codes = re.findall(r">([A-Z]{4}): .*?</A></TD>", data)
    print codes
    for code in codes:
        for course in scrape_area(code, level):
            scrape(course, level)

def scrape(course, level=UG):
    url = "http://www.handbook.unsw.edu.au/%s/courses/%s/%s.html" % (level, CURRENT_YEAR, course)
    filename = "%s/%s.html" % (COURSES_DIR, course)
    if os.path.exists(filename):
        print "Skipping", course
        return

    #print "Fetching page data for %s" % course
    print "Fetching", course
    try:
        data = urllib2.urlopen(url).read()
    except Exception as e:
        print "FAILED:", e.message
        return

    #print "Writing to %s" % filename
    try:
        f = open(filename, "w")
        f.write(data)
        f.close()
    except Exception as e:
        print "FAILED:", e.message
        return

    #print "Done"
    #print

if __name__ == "__main__":
    if not os.path.exists(COURSES_DIR):
        os.mkdir(COURSES_DIR)

    scrape_everything(level=UG)
    scrape_everything(level=PG)
    """quit()
    if len(sys.argv) == 2:
        codes = scrape_area(sys.argv[1])
        for code in codes:
            scrape(code)
        print "Whoop, finished!"
    else:
        print "usage: %s <area>" % sys.argv[0]"""
