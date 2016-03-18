#!/usr/bin/env python3

import configparser

import requests
import os
from datetime import datetime, timedelta

from flask import Flask, Response, abort

class ServiceUnavailableException(Exception):
    """Used for the campus service not functioning correct."""
    pass

class CampusICSFetcher:
    """Fetches the ICS file from Campus."""


    def __init__(self, config_path="default.ini"):
        """Reads in config from config_path (default: default.ini)
        and sets configuration accordingly."""

        # Change working dir to script dir
        abspath = os.path.abspath(__file__)
        dir_name = os.path.dirname(abspath)
        os.chdir(dir_name)

        config_file_locations = [ os.path.join(dir_name, config_path),
                "/etc/campus-ics-feed.ini" ]

        if os.environ.get("CAMPUS_CONFIG_FILE"):
            config_file_locations.append(os.environ.get("CAMPUS_CONFIG_FILE"))

        for cfg_file in config_file_locations:
            if os.path.isfile(cfg_file):
                config = configparser.ConfigParser()
                config.read(cfg_file)
                self.campus_user           = config["Campus"]["Username"]
                self.campus_password       = config["Campus"]["Password"]
                break
        else:
            print("Please provide a configuration file named "
                    + " or ".join(map(lambda x: "'" + str(x) + "'", config_file_locations)) + ".")
            exit()

    def fetch(self):
        """Fetches the ICS file."""

        session = requests.Session()
        data = {"login": "Login", "u": self.campus_user, "p": self.campus_password}
        session.post("https://www.campusoffice.fh-aachen.de/views/campus/search.asp", data=data, timeout = 20)
        start_date  =   (datetime.now() + timedelta(days=-180)).strftime("%d.%m.%Y")
        end_date    =   (datetime.now() + timedelta(days=+180)).strftime("%d.%m.%Y")
        ics_file_response = session.get("https://www.campusoffice.fh-aachen.de/views/"
                "calendar/iCalExport.asp?startdt={}&enddt={}%2023:59:59"
                .format(start_date, end_date), timeout = 20)
        if (ics_file_response.status_code == 200
                and "Content-Disposition" in ics_file_response.headers):
            return ics_file_response.text
        else:
            raise ServiceUnavailableException

app = Flask(__name__)
app.config["PROPAGATE_EXCEPTIONS"] = True
fetcher = CampusICSFetcher()

@app.route("/")
def index():
    """Serves the ICS file."""
    try:
        response = Response(fetcher.fetch())
        response.headers["Content-Type"] = "text/calendar; charset=utf-8"
        response.headers["Content-Disposition"] = "attachment; filename=calendar.ics"
        return response
    except ServiceUnavailableException:
        abort(503)

if __name__ == "__main__":
    #app.debug = True
    app.run()
