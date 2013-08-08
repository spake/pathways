var courses = null;
var coursesReverse = null;
var courseNames = null;
var courseCodes = null;

function generateCourseBox(course, index, totalCourses, isRight) {
    var parent = $("<div class=\"course-box-parent\" />");
    var box = $("<div class=\"course-box\" />");
    box.text(course["code"]);

    box.click(function(e) {
        if (course["exists"]) {
            // kill course details box
            $("#course-details-box").hide();

            // position the activity indicator
            var target = $(e.target);
            var pos = target.offset();
            $("#activity-indicator").animate({
                left: pos.left + target.width() + 32,
                top: pos.top + 10
            }, 0);

            var code = course["code"];
            window.location.hash = code;
        }
    });
    box.mouseover(function (e) {
        $("#course-details-box").show();
        var hoverText;

        if (course["exists"]) {
            hoverText = course["name"];
            if (course["type"] == "corequisite") {
                hoverText += " (corequisite)";
            }
        } else {
            hoverText = "(Course not found)";
        }

        $("#course-details-box").text(hoverText);
    });
    box.mousemove(function (e) {
        $("#course-details-box").animate({
            left: e.pageX + 5,
            top: e.pageY + 5
        }, 0);
    });
    box.mouseout(function (e) {
        $("#course-details-box").hide();
    });
    parent.append(box);
    return parent;
}

function arrayEquals(a,b) {
    if (a.length != b.length) return false;

    for (var i = 0; i < a.length; i++) {
        //if (a[i] != b[i]) return false;
        if (a[i]["code"] != b[i]["code"]) return false;
    }

    return true;
}

function loadCourseGraph(course) {
    // show loading indicator
    $("#activity-overlay").show();

    time = new Date().getTime();
    $.getJSON("/tree/" + course + "?" + time, null, function(data, textStatus, jqXHR) {
        // hide activity indicator
        //$("#activity-indicator").hide();
        $("#activity-overlay").hide();

        if (data["error"]) {
            $("#error-message").text("Looks like there was a server error while trying to load that course. Sorry about that :(");
            $("#error-message-container").show();
            return;
        }

        var centre = data["centre"]; // middle, i.e. current course
        var above = data["above"]; // current course is a prerequisite for...
        var below = data["below"]; // current course has prerequisites...

        // ensure that the centre course actually exists
        if (!centre["exists"]) {
            $("#error-message").text("Doesn't look like " + centre["code"] + " is a valid course code!");
            $("#error-message-container").show();
            return;
        }

        // change document title
        document.title = "Pathways - " + centre["code"];

        // clear errors
        $("#error-message-container").hide();

        var classTreeDiv = $("#class-tree");
        var classTreeParentDiv = $("#class-tree-parent");

        var treeTotal;
        if (above.length > below.length) {
            treeTotal = above.length;
        } else {
            treeTotal = below.length;
        }
        var treeMiddle = (treeTotal-1)/2;

        var treeMiddleY = classTreeDiv.height()/2;

        // add course boxes
        var treeLeft = $("#class-tree-left");
        var treeMid = $("#class-tree-mid");
        var treeRight = $("#class-tree-right");

        treeLeft.empty();
        treeMid.empty();
        treeRight.empty();

        for (i in above) {
            var course = above[i];
            treeRight.append(generateCourseBox(course, i, treeTotal, true));
        }

        var mainCourseBox = generateCourseBox(centre);
        treeMid.append(mainCourseBox);

        for (i in below) {
            var course = below[i];
            treeLeft.append(generateCourseBox(course, i, treeTotal, false));
        }

        // add course details
        var processCourseCodes = function(raw) {
            if (raw) {
                raw = raw.replace(/([A-Z]{4}[0-9]{4})/g, "<a href='#$1'>$1</a>");
                raw = raw.replace(/(([A-Z]{4}[0-9])###)/g, "<a href='javascript:searchCourse(\"$2\")'>$1</a>");
                return raw;
            } else {
                return "(nil)";
            }
        };

        $("#course-details-header").text(centre["name"] + " - " + centre["code"]);
        $("#course-details-header-outline").attr("href", centre["outline"]);
        $("#course-details-header-handbook").attr("href", "http://www.handbook.unsw.edu.au/undergraduate/courses/current/" + centre["code"] + ".html");
        $("#course-details-header-timetable").attr("href", "http://www.timetable.unsw.edu.au/current/" + centre["code"] + ".html");
        $("#course-details-header-google").attr("href", "http://www.google.com.au/search?q=" + centre["code"] + "+UNSW");

        $("#course-details-uoc").text(centre["uoc"]);

        $("#course-details-description").html(centre["description"].replace(/(<br ?\/?>)+/g, "<br/>"));

        $("#course-details-prerequisites").html(processCourseCodes(centre["prerequisites"]));
        $("#course-details-corequisites").html(processCourseCodes(centre["corequisites"]));
        $("#course-details-exclusions").html(processCourseCodes(centre["exclusions"]));

        if (centre["prerequisites"]) {
            $("#course-details-prerequisites-parent").show();
        } else {
            $("#course-details-prerequisites-parent").hide();
        }
        if (centre["corequisites"]) {
            $("#course-details-corequisites-parent").show();
        } else {
            $("#course-details-corequisites-parent").hide();
        }
        if (centre["exclusions"]) {
            $("#course-details-exclusions-parent").show();
        } else {
            $("#course-details-exclusions-parent").hide();
        }

        // woo code reuse
        var addTimetableDetails = function(div, periodCode, periodCode2) {
            if (centre[periodCode]) {
                var baseTimetableURL = "http://www.timetable.unsw.edu.au/current/" + centre["code"] + ".html#";
                //div.text("Yes; Contact: " + centre[periodCode]["contact"]);
                div.empty();
                div.append($("<a/>")
                    .attr("class", "affirmative")
                    .attr("href", baseTimetableURL + periodCode2 + "S")
                    .attr("target", "_blank")
                    .text("Yes"));
                div.removeClass("negative");
                div.addClass("affirmative");
                $("#course-details-" + periodCode + "-button").show();

                // calculate class stuff
                var minHour = -1;
                var maxHour = -1;
                for (i in centre[periodCode]["classes"]) {
                    var classDetails = centre[periodCode]["classes"][i];
                    var start = classDetails["startHour"];
                    var finish = classDetails["finishHour"];
                    if (start < minHour || minHour == -1) {
                        minHour = start;
                    }
                    if (finish > maxHour || maxHour == -1) {
                        maxHour = finish;
                    }
                }

                var timetableSpan = $("#course-details-timetable-" + periodCode);
                var timetableTable = $("<table/>");
                timetableTable.addClass("table");
                timetableTable.addClass("table-bordered");

                var days = [
                    "Monday",
                    "Tuesday",
                    "Wednesday",
                    "Thursday",
                    "Friday"
                ];

                var unusedColours = [
                    "colour7",
                    "colour6",
                    "colour5",
                    "colour4",
                    "colour3",
                    "colour2",
                    "colour1"
                ];
                var usedColours = {};

                var headerRow = $("<tr/>");
                headerRow.append($("<td/>").addClass("timetable-header-side"));
                for (i in days) {
                    var cell = $("<td/>");
                    cell.text(days[i]);
                    cell.addClass("timetable-header");
                    headerRow.append(cell);
                }
                timetableTable.append(headerRow);

                // stealing some stuff from octangles here
                var table = new Array(24);
                for (var i = 0; i < 24; i++) {
                    table[i] = new Array(5);
                    for (var j = 0; j < 5; j++) {
                        table[i][j] = [];
                    }
                }

                for (var i in centre[periodCode]["classes"]) {
                    var classDetails = centre[periodCode]["classes"][i];
                    var start = classDetails["startHour"];
                    var finish = classDetails["finishHour"];
                    var day = classDetails["day"];
                    for (var hour = start; hour < finish; hour++) {
                        table[hour][day].push(classDetails);
                    }
                }

                for (hour = minHour; hour < maxHour; hour++) {
                    var timetableRow = $("<tr/>");
                    var cell = $("<td/>");
                    cell.html(hour + ":00" + "<br/><br/>");
                    cell.addClass("timetable-side");
                    timetableRow.append(cell);

                    for (day = 0; day < 5; day++) {
                        var cell = $("<td/>");

                        if (table[hour][day] === "") {
                            continue;
                        }

                        var rowspan = 1;
                        if (table[hour][day].length >= 1) {
                            for (var later = hour+1; later < maxHour; later++) {
                                if (!arrayEquals(table[hour][day], table[later][day])) {
                                    break;
                                }
                                rowspan++;
                                table[later][day] = "";
                            }

                            cell.addClass("timetable-cell");
                            cell.addClass("colour1");

                            cell.attr("rowspan", rowspan);

                            var codes = {};
                            var names = [];
                            var plainCodes = [];
                            for (i in table[hour][day]) {
                                var classDetails = table[hour][day][i];
                                var name = classDetails["name"];
                                var code = classDetails["code"];
                                var classCode = classDetails["classCode"];
                                var size = classDetails["size"];
                                var capacity = classDetails["capacity"];
                                var status = classDetails["status"];
                                
                                var description = status + ": " + size + "/" + capacity;
                                var codeWithDesc = [code, description, periodCode2 + "-" + classCode];

                                /*if ($.inArray(codeWithDesc, codes) == -1) {
                                    codes.push(codeWithDesc);
                                }*/
                                codes[code] = codeWithDesc;
                                if ($.inArray(name, names) == -1) {
                                    names.push(name);
                                }
                                if ($.inArray(code, plainCodes) == -1) {
                                    plainCodes.push(code);
                                }
                            }

                            var matchName = names[0];
                            if (matchName.indexOf("Lecture") != -1) {
                                matchName += plainCodes[0];
                            }
                            if (!(matchName in usedColours)) {
                                var colour = unusedColours.pop();
                                usedColours[matchName] = colour;
                            }
                            cell.addClass(usedColours[matchName]);

                            // crazy stupid logic here on 4 hours of sleep
                            // make lecture come first for colouring purposes
                            names.sort(function (a, b) {
                                if (a.indexOf("Lecture") != -1) {
                                    return -1;
                                } else if (b.indexOf("Lecture") != -1) {
                                    return 1;
                                }
                                return (a > b);
                            });

                            var codesHTML = [];
                            for (i in codes) {
                                var code = codes[i];
                                codesHTML.push("<a class=\"timetable-tooltip\" data-toggle=\"tooltip\" title=\"" + code[1] + "\" href=\"" + baseTimetableURL + code[2] +"\" target=\"_blank\">" + code[0] + "</a>");
                            }
                            cell.html(names.join(", ") + "<br/>" + "<span class=\"codes\">" + codesHTML.join(", ") + "</span>");
                        }

                        timetableRow.append(cell);
                    }
                    timetableTable.append(timetableRow);
                }

                timetableSpan.empty();

                // append disclaimer
                timetableDisclaimer = $("<span/>");
                timetableDisclaimer.addClass("timetable-disclaimer");
                var timetableLastUpdatedTimestamp = centre["timetableLastUpdated"];
                var timetableLastUpdated = new Date(timetableLastUpdatedTimestamp*1000);
                var timetableLastUpdatedString = moment(timetableLastUpdated).format("DD/MM/YYYY, h:mm A")
                timetableDisclaimer.text("Last updated " + timetableLastUpdatedString);
                timetableSpan.append(timetableDisclaimer);

                // append table
                timetableSpan.append(timetableTable);

                $("a.timetable-tooltip").tooltip({
                    placement: "bottom"
                });
            } else {
                div.text("No");
                div.removeClass("affirmative");
                div.addClass("negative");
                $("#course-details-" + periodCode + "-button").hide();
            }
        };

        if ($("#course-details-timetable-s1").is(".in")) {
            $("#course-details-timetable-s1").collapse("hide");
        }
        if ($("#course-details-timetable-s2").is(".in")) {
            $("#course-details-timetable-s2").collapse("hide");
        }
 
        addTimetableDetails($("#course-details-s1"), "s1", "S1");
        addTimetableDetails($("#course-details-s2"), "s2", "S2");

        $("#course-details-gened").text(centre["gened"] ? "Yes" : "No");

        // unhide content
        $("#pathways-welcome").hide();
        $("#pathways-content").show();

        // set up canvas
        var canvas = document.getElementById("canvas");
        var context = canvas.getContext("2d");

        var width = classTreeDiv.width();
        var height = classTreeDiv.height();

        $("#canvas").width(width);
        $("#canvas").height(height);

        if (window.devicePixelRatio == 2) {
            canvas.setAttribute("width", width*2);
            canvas.setAttribute("height", height*2);
            context.scale(2, 2);
        } else {
            canvas.setAttribute("width", width);
            canvas.setAttribute("height", height);
        }

        var corequisiteColour = "#ff4500";
        var normalColour = "#000000";

        // draw right arrows
        var total = above.length;
        var middle = (total-1)/2;
        var arrowLeft = 400;
        var arrowRight = 600;
        var arrowMid = (arrowLeft+arrowRight)/2;
        var courseBoxHeight = 38;
        var courseBoxGap = 5;
        var yOffsetCount = treeTotal - total;
        var yOffset = yOffsetCount > 0 ? (courseBoxHeight * yOffsetCount + courseBoxGap * (yOffsetCount - 1)) / 2 : 0;

        for (i = 0; i < total; i++) {
            var x1 = arrowLeft;
            var y1 = yOffset + courseBoxHeight*(middle + 0.5) + courseBoxGap*middle;
            var x2 = arrowRight;
            var y2 = yOffset + courseBoxHeight*(i + 0.5) + courseBoxGap*i;
            var colour = (above[i]["type"] == "corequisite" ? corequisiteColour : normalColour);
            drawArrow(context, x1, y1, x2, y2, colour);
        }

        // draw left arrows
        total = below.length;
        middle = (total-1)/2;
        arrowLeft = 100;
        arrowRight = 300;
        arrowMid = (arrowLeft+arrowRight)/2;
        yOffsetCount = treeTotal - total;
        yOffset = yOffsetCount > 0 ? (courseBoxHeight * yOffsetCount + courseBoxGap * (yOffsetCount - 1)) / 2 : 0;

        for (i = 0; i < total; i++) {
            var x1 = arrowLeft;
            var y1 = yOffset + courseBoxHeight*(i + 0.5) + courseBoxGap*i;
            var x2 = arrowRight;
            var y2 = yOffset + courseBoxHeight*(middle + 0.5) + courseBoxGap*middle;
            var colour = (below[i]["type"] == "corequisite" ? corequisiteColour : normalColour);
            drawArrow(context, x1, y1, x2, y2, colour);
        }
    });
}

function searchCourse(query) {
    $("#course-selector2").focus();
    $("#course-selector2").val(query);
    $("#course-selector2").typeahead("lookup");
}

function loadAllCourses() {
    time = new Date().getTime();

    $("#activity-overlay").show();

    $.getJSON("/all-courses-reverse" + "?" + time, null, function(data, textStatus, jqXHR) {
        coursesReverse = data;
        courseNames = $.map(coursesReverse, function(value, key) {
            return key;
        });
        courseCodes = $.map(coursesReverse, function(value, key) {
            return value;
        });

        $("#course-selector2").typeahead({
            source: courseNames,
            items: 50,
            minLength: 0
        });

        $("#course-selector2").on("change", function(e) {
            var value = $("#course-selector2").val();
            var code = null;

            code = coursesReverse[value];

            if (code) {
                window.location.hash = code;

                // unfocus
                $("#course-selector2").blur();
            }
        });

        $("#course-selector2").on("focus", function(e) {
            $("#course-selector2").select();
        });
        $("#course-selector2").mouseup(function (e) {
            e.preventDefault();
        });

        loadAllGened();
    });
}

function loadAllGened() {
    time = new Date().getTime();
    $.getJSON("/all-gened" + "?" + time, null, function(data, textStatus, jqXHR) {
        // add each to the selector
        for (i in data) {
            var course = data[i];
            $("#gened-dropdown").append($("<li/>").append($("<a/>").text(course["label"]).attr("href", "#" + course["value"])));
        }

        $("#activity-overlay").hide();

        // update hash
        updateHash();
    });
}

var ARROWHEADWIDTH = 10;
var ARROWHEADHEIGHT = 10;
function drawArrow(context, x1, y1, x2, y2, colour) {
    // draw bezier curve
    context.beginPath();

    // endpoints p0 and p3, control points p1 and p2
    var p0X = x1;
    var p0Y = y1;
    var p1X = (x1+x2)/2;
    var p1Y = y1;
    var p2X = (x1+x2)/2;
    var p2Y = y2;
    var p3X = x2;
    var p3Y = y2;

    context.moveTo(p0X, p0Y);
    context.bezierCurveTo(p1X, p1Y, p2X, p2Y, p3X, p3Y);

    context.strokeStyle = colour;
    context.lineWidth = 1;
    context.stroke();

    // calculate the gradient of the tangent at the end of the curve
    // differentiating bezier curves, whoop
    var t = 0.97;
    var dx = -3*Math.pow(t-1, 2)*p0X + 3*(3*t-1)*(t-1)*p1X + 3*t*(2-3*t)*p2X + 3*Math.pow(t, 2)*p3X;
    var dy = -3*Math.pow(t-1, 2)*p0Y + 3*(3*t-1)*(t-1)*p1Y + 3*t*(2-3*t)*p2Y + 3*Math.pow(t, 2)*p3Y;

    // draw arrowhead using some fancy trig
    var lineAngle = Math.atan2(dy, dx);
    var arrowheadAngle = Math.atan(ARROWHEADHEIGHT / (2*ARROWHEADWIDTH));
    var length = Math.sqrt((1/4)*ARROWHEADHEIGHT*ARROWHEADHEIGHT + ARROWHEADWIDTH*ARROWHEADWIDTH);

    var p1X = x2;
    var p1Y = y2;
    var p2X = x2 - length*Math.cos(lineAngle - arrowheadAngle);
    var p2Y = y2 - length*Math.sin(lineAngle - arrowheadAngle);
    var p3X = x2 - length*Math.cos(lineAngle + arrowheadAngle);
    var p3Y = y2 - length*Math.sin(lineAngle + arrowheadAngle);

    context.beginPath();
    context.moveTo(p1X, p1Y);
    context.lineTo(p2X, p2Y);
    context.lineTo(p3X, p3Y);
    context.lineTo(p1X, p1Y);
    context.closePath();

    context.fillStyle = colour;

    context.fill();
}

function updateHash() {
    var hash = window.location.hash.slice(1);
    // is the hash blank?
    if (hash == "") {
        $("#pathways-content").hide();
        $("#pathways-welcome").show();
    } else {
        loadCourseGraph(hash);
    }
}

$(window).bind("hashchange", updateHash);

$(document).ready(function() {
    loadAllCourses();
});
