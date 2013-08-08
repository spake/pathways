#!/bin/sh
echo "static/js/main.js -> static/js/main.cgi.js"
sed "s:\$\.getJSON(\"/:$.getJSON(\"../cgi-bin/pathways.cgi/:" < static/js/main.js > static/js/main.cgi.js

echo "static/index.html -> static/index.cgi.html"
sed "s/main\.js/main.cgi.js/g;s:/static/::g" < static/index.html > static/index.cgi.html

echo "server.py -> cgiserver.py"
sed "s/^\( *\)print.*$/\1dummy_print()/g" < server.py > cgiserver.py
