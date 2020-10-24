from flask import Flask, redirect, render_template, request, send_from_directory
import requests

import datetime
import json
import os

app = Flask(__name__)

API_ROOT = "http://ws.audioscrobbler.com/2.0"
API_KEY = "4c687ee8070a984365972a134b9bf982"

params_country = {"method": "geo.gettopartists", "country": "", "api_key": API_KEY, "format": "json"}
TOP_ARTISTS_KEY = "topartists"
ARTIST_KEY = "artist"
ARTIST_NAME_KEY = "name"
LISTENERS_COUNT_KEY = "listeners"

params_artist = {"method": "artist.gettoptracks", "artist": "", "api_key": API_KEY, "format": "json"}
TOP_TRACK_KEY = "toptracks"
TRACK_KEY = "track"
TRACK_NAME_KEY = "name"
LISTENERS_TRACK_COUNT_KEY = "listeners"


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/", methods=["POST"])
@app.route("/country/<country>", methods=["POST"])
@app.route("/artist/<artist>", methods=["POST"])
def search_submit(country=None, artist=None):
    if "Search country" == request.form["submit_button"]:
        form_country = request.form["country"]
        return redirect(f"/country/{form_country}")
    elif "Search artist" == request.form["submit_button"]:
        form_artist = request.form["artist"]
        return redirect(f"/artist/{form_artist}")


def is_cache_fresh(path):
    time_of_last_change = datetime.datetime.fromtimestamp(os.path.getmtime(path))
    current_time = datetime.datetime.now()
    freshness_limit = datetime.timedelta(hours=24)
    passed_time = current_time - time_of_last_change
    if freshness_limit < passed_time:
        return False
    return True


@app.route("/country/<country>")
def index_country(country):
    if country is None:
        return render_template("index.html")
    params_country["country"] = country
    country_cache_path = os.path.join(os.getcwd(), "app", "cache", "country", f"{country}.json")
    if os.path.exists(country_cache_path) and is_cache_fresh(country_cache_path):
        with open(country_cache_path, "r") as f:
            resp_json = json.loads(f.read())
    else:
        resp = requests.get(API_ROOT, params=params_country)
        resp_json = json.loads(resp.text)
        if TOP_ARTISTS_KEY in resp_json:
            with open(country_cache_path, "w") as f:
                f.write(json.dumps(resp_json))

    if TOP_ARTISTS_KEY not in resp_json:
        # no data for this country
        return render_template("index_message.html", country_error_message=f"No data for country: {country}")
    else:
        top_list = []
        for i, artist in enumerate(resp_json[TOP_ARTISTS_KEY][ARTIST_KEY]):
            top_list.append(
                {
                    "place": f"{i + 1}",
                    "name": f"{artist[ARTIST_NAME_KEY]}",
                    "listeners": f"{artist[LISTENERS_COUNT_KEY]}"
                }
            )
        return render_template("index_country.html", country=country, top_list=top_list)


@app.route("/artist/<artist>")
def index_artist(artist):
    if artist is None:
        return render_template("index.html")
    params_artist["artist"] = artist
    artist_cache_path = os.path.join(os.getcwd(), "app", "cache", "artist", f"{artist}.json")
    if os.path.exists(artist_cache_path) and is_cache_fresh(artist_cache_path):
        with open(artist_cache_path, "r") as f:
            resp_json = json.loads(f.read())
    else:
        resp = requests.get(API_ROOT, params=params_artist)
        resp_json = json.loads(resp.text)
        if (
                TOP_TRACK_KEY in resp_json and TRACK_KEY in resp_json[TOP_TRACK_KEY]
                and len(resp_json[TOP_TRACK_KEY][TRACK_KEY]) > 0
        ):
            with open(artist_cache_path, "w") as f:
                f.write(json.dumps(resp_json))

    if (
            TOP_TRACK_KEY not in resp_json or TRACK_KEY not in resp_json[TOP_TRACK_KEY]
            or not 0 < len(resp_json[TOP_TRACK_KEY][TRACK_KEY])
    ):
        # no such artist
        return render_template("index_message.html", artist_error_message=f"No data for artist: {artist}")
    else:
        top_list = []
        for i, track in enumerate(resp_json[TOP_TRACK_KEY][TRACK_KEY]):
            top_list.append(
                {
                    "place": f"{i + 1}",
                    "track": f"{track[TRACK_NAME_KEY]}",
                    "listeners": f"{track[LISTENERS_TRACK_COUNT_KEY]}"
                }
            )
        return render_template("index_artist.html", artist=artist, top_list=top_list)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, "static"), "favicon.ico",
                               mimetype="image/vnd.microsoft.icon")


if '__main__' == __name__:
    app.run(threaded=True, port=5000)
