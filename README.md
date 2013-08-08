Pathways, the UNSW course handbook done right
---------------------------------------------

Pathways is a web app that lets you view details about UNSW courses, including timetables, prerequisites and course summaries, in a friendlier manner than the [course handbook](http://www.handbook.unsw.edu.au) and [timetable](http://www.timetable.unsw.edu.au) sites. It still has a long way to go in terms of cleaning up the code and adding in a few more features (I will probably end up rewriting significant chunks of it in the near future), but I've been pressured (_cough_ Goldy _cough_) to release the source, so here it is in all its unpolished glory. The 'official' instance is currently run from my CSE account [here](http://cgi.cse.unsw.edu.au/~gric057/pathways/).

In its current state, Pathways has several components:

* **scraper.py**, a Python program that downloads the HTML from every course page on the aforementioned handbook
* **binder.py**, a Python program that takes in the HTML downloaded by the scraper, parses it (with regex, I'm ashamed to say... see, there's a reason why I didn't want to release the source just yet!), and puts the results into a SQLite database, courses.db
* **server.py**, the web server (duh), written in Python using [Flask](http://flask.pocoo.org/), which responds to requests using the information in courses.db and by downloading (and caching) pages from the UNSW timetable site
* **static/index.html, static/css/main.css, static/js/main.js**, all the front end stuff, making heavy use of Bootstrap and jquery

In an attempt to quickly get Pathways running with CGI (which I needed to get it running on the CSE servers), I also wrote a horrible shell script, **cgiify.sh**, which runs a few of the above files through sed to produce their CGI counterparts, with the primary changes being the different location of static files and the requirement that no debugging stuff be printed to stdout. Yes, there are far better ways to go about doing this (I'm not sure what good practice of CGI with Flask is, as using CGI with Flask in itself doesn't seem to be good practice), this being one of the many reasons why I didn't want to release the source in this state... Regardless, if you want to start up your own instance locally, you shouldn't need to worry about this; just run server.py and let Flask work its magic.

A word of warning for those who actually want to start up their own instances: you **must** first run scraper.py (which will download more than 5000 handbook pages at ~25KB each, totalling ~130MB, be warned!) and **then** binder.py (which will compress all those pages into a SQLite database ~6MB in size), otherwise the server will have no data to work from!

I'll leave the rest of its inner workings for you to figure out (in case I haven't repeated it enough, _it's unpolished_, don't judge me!), so if you have any questions/comments/threats, feel free to contact me on the email I've listed on GitHub or try and hunt me down at the CSE weekly BBQ.

Pathways is made available under the Apache License 2.0. Portions of the timetable display code are based on [Octangles](https://github.com/oliver-c/octangles).