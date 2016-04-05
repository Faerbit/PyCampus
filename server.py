#!/usr/bin/env python3

import configparser

import requests
import os
from datetime import datetime, timedelta

from flask import Flask, Response, abort, request

def authenticate():
    """ Sends a 401 response that enables basic auth"""
    return Response(
    'Username or password missing', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

app = Flask(__name__)
app.config["PROPAGATE_EXCEPTIONS"] = True

@app.route("/")
def index():
    """Serves the ICS file."""

    # use HTTP basic auth for auth with campus
    auth = request.authorization
    if auth:
        campus_user = request.authorization.username
        campus_password = request.authorization.password
        if not campus_user and campus_password:
            return authenticate()
    else:
        return authenticate()
    session = requests.Session()
    data = {"login": "Login", "u": campus_user, 
            "p": campus_password}
    login_response = session.post("https://www.campusoffice.fh-aachen.de/"
            "views/campus/search.asp", data=data, timeout = 20)
    if "fehlgeschlagen" in login_response.text:
        abort(403)
    start_date  =   (datetime.now() + 
            timedelta(days=-180)).strftime("%d.%m.%Y")
    end_date    =   (datetime.now() 
            + timedelta(days=+180)).strftime("%d.%m.%Y")
    ics_file_response = session.get("https://www.campusoffice.fh-aachen.de/"
            "views/calendar/iCalExport.asp?startdt={}&enddt={}%2023:59:59"
            .format(start_date, end_date), timeout = 20)
    if (ics_file_response.status_code == 200
            and "Content-Disposition" in ics_file_response.headers):
        response = Response(ics_file_response.text)
        response.headers["Content-Type"] = "text/calendar; charset=utf-8"
        response.headers["Content-Disposition"] = ("attachment;"
                " filename=calendar.ics")
        return response
    else:
        abort(503)

if __name__ == "__main__":
    app.debug = True
    app.run()
