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

import os, re, requests, sys
from requests.exceptions import HTTPError

COURSES_DIR = "courses"
UG = "undergraduate"
PG = "postgraduate"
CURRENT_YEAR = "2018"
COURSE_LIST_RE = re.compile(r'<TD class="(?:evenTableCell)?" align="left">([A-Z]{4}[0-9]{4})</TD>')

def scrape_list(url):
    
    print("Fetching page data")
    try:
        data = requests.get(url).text
        print("Finding course codes")
        codes = re.findall(COURSE_LIST_RE, data)
        print("Done")
        return codes
    except HTTPError as http_err:
        print("HTTP error")
    except Exception as err:
        print(err)
    return None

def scrape_area(area, level=UG):
    print("Finding all courses for " + str(area))
    return scrape_list("http://legacy.handbook.unsw.edu.au/vbook" + CURRENT_YEAR + "/brCoursesBySubjectArea.jsp?studyArea=" + str(area) + "&StudyLevel=" + str(level))

def scrape_everything(level):
    url = "http://legacy.handbook.unsw.edu.au/vbook%s/brCoursesBySubjectArea.jsp?StudyLevel=%s&descr=A" % (CURRENT_YEAR, level)
    print("Reading area list")
    data = requests.get(url).text
    codes = re.findall(r'>([A-Z]{4}): .*?</A></TD>', data)
    print(codes)
    for code in codes:
        for course in scrape_area(code, level):
            scrape(course, level)

def scrape(course, level=UG):
    url = "http://legacy.handbook.unsw.edu.au/%s/courses/%s/%s.html" % (level, CURRENT_YEAR, course)
    filename = "%s/%s.html" % (COURSES_DIR, course)
    if os.path.exists(filename):
        print("Skipping " + course)
        return
    print("Fetching " + course)
    try:
        data = requests.get(url).text
    except Exception as e:
        print("FAILED: " + e.message)
        return
    with open(filename, "w") as f:
        f.write(data)

if __name__ == "__main__":
    if not os.path.exists(COURSES_DIR):
        os.mkdir(COURSES_DIR)
    scrape_everything(UG)
    scrape_everything(PG)
