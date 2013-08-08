import urllib2
import re
import sys
import os

UG = "undergraduate"
PG = "postgraduate"

CURRENT_YEAR = "2013"

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
    return scrape_list("https://www.handbook.unsw.edu.au/vbook%d/brCoursesBySubjectArea.jsp?studyArea=%s&StudyLevel=%s" % (CURRENT_YEAR, area, level))

def scrape_everything(level=UG):
    url = "http://www.handbook.unsw.edu.au/vbook%d/brCoursesBySubjectArea.jsp?StudyLevel=%s&descr=A" % (CURRENT_YEAR, level)
    print "Reading area list"
    data = urllib2.urlopen(url).read()
    codes = re.findall(r">([A-Z]{4}): .*?</A></TD>", data)
    print codes
    for code in codes:
        for course in scrape_area(code, level):
            scrape(course, level)

def scrape(course, level=UG):
    url = "http://www.handbook.unsw.edu.au/%s/courses/%d/%s.html" % (CURRENT_YEAR, level, course)
    filename = "courses/%s.html" % course
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
