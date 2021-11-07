import collections
import json
import os
import time
from datetime import datetime
from pathlib import Path
from pprint import pprint

import markdown
from flask import Flask, abort, jsonify, render_template, request

# =============================================================================
# WARNING!
# =============================================================================
# This is a dirty app to make the backups searchable, DO NOT make this public facing.

# For future use
API_URL_PREFIX = "/api/v1"

# For displaying dates and times
DATE_FORMAT = "%d.%m.%Y"
DATETIME_FORMAT = "%d.%m.%Y %H:%M:%S"

# Absolute path to the JSON state file
STATE_JSON_FILE = Path(os.getenv("STATE_JSON_FILE", "state.json"))

# Names to ignore when calculating participants
IGNORE_NAMES = os.getenv("IGNORE_NAMES", "fiskebot").split(",")

# Page name
PAGE_NAME = os.getenv("PAGE_NAME", "fiskebot")

# Search ratio, threshold before including a result into the results. Lower will include more results
# TODO: not used currently
FUZZY_SEARCH_THRESHOLD = int(os.getenv("FUZZY_SEARCH_THRESHOLD", 70))

# Max count of how many messages that should be included in search results
SEARCH_RESULT_COUNT_LIMIT = int(os.getenv("SEARCH_RESULT_COUNT_LIMIT", 500))

# Color used for mainly the navbar
PAGE_COLOR = os.getenv("PAGE_COLOR", "#AC0A2B")

if not bool(os.getenv("IS_DOCKER", False)):
    # Absolute path to the fiskebot JSON export/backup files
    BACKUPS_DIRECTORY = os.getenv("BACKUPS_DIRECTORY")
    if not BACKUPS_DIRECTORY:
        print("Environment variable 'BACKUPS_DIRECTORY' is not defined")
        exit(1)
else:
    # We are running in a container, let's use the hardcoded path
    BACKUPS_DIRECTORY = "/code/fiskebot/backups"

BACKUPS_DIRECTORY = Path(BACKUPS_DIRECTORY)

# Seconds between forcing a state update, instead of having to read the file every single time
UPDATE_STATE_SECONDS = int(os.getenv("UPDATE_STATE_SECONDS", 300))

DEFAULT_STATE = {
    "last_updated": None,
    "ctf_list": {},
    "users": {},
    "parsed_backup_files": [],
}


def parse_backup_file(backup_file):
    with open(backup_file) as fd:
        backup = json.load(fd)
    if "channels" not in backup:
        print(f"JSON file {backup_file} does not have 'channels', ignoring it")
        return None

    channels = backup["channels"]
    message_count = 0

    """
    Sometimes the main channel isn't the first channel in the backup.
    We therefore have to look through all the channels and sort by the channel IDs to find the oldest channel.
    NB! There is an edge case where the main channel does not have any messages.
    In that case we cannot correctly determine the main channel.
    """
    main_channel = None
    current_id = None
    for channel in channels:
        if len(channel["messages"]) == 0:
            continue

        message_count += len(channel["messages"])

        channel_id = channel["messages"][0]["id"]

        if not current_id or current_id > channel_id:
            main_channel = channel
            current_id = channel_id

    ctf_name = main_channel["name"]

    # We don't have an exact start day of the CTF, let's assume the first message is the start date
    ctf_date = datetime.fromisoformat(main_channel["messages"][0]["created_at"])
    ctf = {
        # Use the first message in the main channel as the ID for the CTF
        "id": str(main_channel["messages"][0]["id"]),
        "name": ctf_name,
        "message_count": message_count,
        "timestamp": ctf_date.timestamp(),
        # For easier printing
        "formatted_date": ctf_date.strftime(DATE_FORMAT),
        "topic": main_channel["topic"],
        "challenges": [],
        "participants": {},
    }

    participants = {}
    for channel in channels:
        challenge = {
            # Remove the prefix from the challenge channel
            "name": channel["name"].replace(ctf["name"] + "-", ""),
            "messages": [],
        }
        # Let's only extract the information we need from the messages
        for message in channel["messages"]:
            attachments = []
            for attachment in message["attachments"]:
                attachments.append(
                    {"filename": attachment["filename"], "url": attachment["url"]}
                )

            content = message["content"]
            is_safe = True
            if "`" in content or ">" in content:
                # Only attempt to parse as markdown if the content has backticks or is a quote
                content = markdown.markdown(content, extensions=["fenced_code"])
                is_safe = False

            # str because json doesn't like ints as keys
            user_id = str(message["author"]["id"])

            challenge["messages"].append(
                {
                    "id": message["id"],
                    "user_id": user_id,
                    "content": content,
                    # Don't parse the dates for now
                    "date": message["created_at"],
                    "attachments": attachments,
                    "is_safe": is_safe,
                }
            )

            if not message["author"]["avatar"]:
                # Default avatar
                avatar_url = "/static/img/default_avatar.png"
            else:
                avatar_url = f"https://cdn.discordapp.com/avatars/{ message['author']['id'] }/{ message['author']['avatar'] }.png?size=40"

            if user_id not in participants:
                participants[user_id] = {
                    "name": message["author"]["user"],
                    "avatar_url": avatar_url,
                    "message_count": 0,
                }
            participants[user_id]["message_count"] += 1

        ctf["challenges"].append(challenge)

    ctf["participants"] = participants
    return ctf


def scan_ctfs(state, reload=False):
    ctfs = {}
    for backup_file in BACKUPS_DIRECTORY.glob("*.json"):
        if backup_file in state["parsed_backup_files"] and not reload:
            # We already have this CTF loaded, ignore it if we don't force a reload
            continue
        parsed_ctf = parse_backup_file(backup_file)
        if (
            parsed_ctf
            and parsed_ctf["id"] not in ctfs
            or parsed_ctf["message_count"] > ctfs[parsed_ctf["id"]]["message_count"]
        ):
            # We might have multiple backup files for the SAME ctf, only use the one with the most messages
            ctfs[parsed_ctf["id"]] = parsed_ctf
        if backup_file not in state["parsed_backup_files"]:
            state["parsed_backup_files"].append(backup_file.name)

    # Now do a quick dirty sort based on the CTF timestamps
    ctfs = dict(
        sorted(ctfs.items(), key=lambda item: item[1]["timestamp"], reverse=True)
    )
    return ctfs


def load_state(reload=False):
    if not STATE_JSON_FILE.exists():
        state = DEFAULT_STATE
    else:
        with open(STATE_JSON_FILE) as fd:
            state = json.load(fd)

    if reload:
        print("Reloading state, this will take a while...")
        state["ctf_list"] = scan_ctfs(state, reload=reload)
        """
        Make sure we fetch the latest avatar of each user as that is most likely the current avatar of the user.
        Base this on the ID of each CTF and pick the last one.
        """
        users_state = {}
        # Map the participants/users
        users = state["users"] if "users" in state else {}
        for ctf in state["ctf_list"].values():
            for user_id, user in ctf["participants"].items():
                if user_id not in users_state or int(users_state[user_id]) < int(
                    ctf["id"]
                ):
                    if user["name"] == "UnblvR":
                        if user_id in users_state:
                            print(users_state[user_id], ctf["id"])
                    users_state[user_id] = ctf["id"]
                    users[user_id] = user
        state["users"] = users

    print(f"Loaded state, {len(state['ctf_list'])} CTFs")
    return save_state(state)


def save_state(state):
    state["last_updated"] = time.time()
    with open(STATE_JSON_FILE, "w") as fd:
        json.dump(state, fd)
    print("Saved state")
    return state


def check_state(state, reload=False):
    if (
        not state["last_updated"]
        or time.time() > state["last_updated"] + UPDATE_STATE_SECONDS
    ):
        # Load the state and scan CTFs again
        state = load_state(reload=reload)
    return state


app = Flask(__name__)
# Force a scan at startup
state = load_state(reload=True)


@app.route("/state.json")
def state_file():
    # Could be a middleware
    force_reload = request.args.get("force_reload", False)
    global state
    state = check_state(state, reload=force_reload is not False)
    return jsonify(state)


@app.route("/")
def ctf_list():
    global state
    state = check_state(state)
    """
    # Dirty mutation to remove the channels
    ctf_list = state["ctf_list"].copy()
    for ctf_id, data in ctf_list.items():
        ctf_list.pop("challenges", None)
    """
    return render_template(
        "ctf_list.html",
        page_name=PAGE_NAME,
        page_color=PAGE_COLOR,
        ignore_names=IGNORE_NAMES,
        users=state["users"],
        ctf_list=state["ctf_list"],
    )


@app.route("/search")
def search():
    # DIRTY!!! should ideally get this into a db instead of a huge JSON "state"
    search_string = request.args.get("search", None)
    fuzzy_threshold = request.args.get("fuzzy_threshold", None)
    if not search_string:
        return abort(400)
    if fuzzy_threshold and fuzzy_threshold.isdigit():
        fuzzy_threshold = int(fuzzy_threshold)
    else:
        fuzzy_threshold = FUZZY_SEARCH_THRESHOLD

    global state
    state = check_state(state)

    # Let's group the results by CTF
    search_results = {}
    search_result_count = 0
    for ctf_id, ctf in state["ctf_list"].items():
        challenges_matched = {}
        for challenge in ctf["challenges"]:
            messages_matched = []
            for message in challenge["messages"]:
                # TODO: implement fuzzy searching
                """
                if ratio > fuzzy_threshold:
                ratio = fuzz.ratio(search_string, message["content"])
                """
                for attachment in message["attachments"]:
                    if search_string.lower() in attachment["filename"].lower():
                        messages_matched.append(message)
                        search_result_count += 1
                if search_string.lower() in message["content"].lower():
                    messages_matched.append(message)
                    search_result_count += 1

            if len(messages_matched) > 0:
                challenges_matched[challenge["name"]] = messages_matched

        if len(challenges_matched) > 0:
            search_results[ctf_id] = {
                "name": ctf["name"],
                "challenges": challenges_matched,
            }

        if search_result_count > SEARCH_RESULT_COUNT_LIMIT:
            # Limit reached!
            break

    return render_template(
        "search.html",
        page_name=PAGE_NAME,
        page_color=PAGE_COLOR,
        users=state["users"],
        search_results=search_results,
    )


@app.route("/ctf/<ctf_id>")
def ctf_view(ctf_id):
    global state
    state = check_state(state)
    if ctf_id not in state["ctf_list"]:
        abort(404)
    return render_template(
        "ctf.html",
        page_name=PAGE_NAME,
        page_color=PAGE_COLOR,
        ignore_names=IGNORE_NAMES,
        users=state["users"],
        ctf=state["ctf_list"][ctf_id],
    )


@app.route(f"{API_URL_PREFIX}/function/force_state_reload/")
def api_ctf_list():
    global state
    state = check_state(state)
    return jsonify(list(state["ctf_list"].keys()))


@app.route(f"{API_URL_PREFIX}/ctf/<ctf_id>/")
def api_ctf(ctf_id):
    global state
    state = check_state(state)
    if ctf_id not in state["ctf_list"]:
        abort(404)

    return jsonify(state["ctf_list"][ctf_id])
