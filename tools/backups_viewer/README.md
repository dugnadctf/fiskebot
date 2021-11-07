# Fiskebot Backups Viewer

This is a web application that can be used to display and search through the exported backups of fiskebot. The application uses Flask to run a web facing interface, and uses JSON to save a state of the current CTFs, this state is reload at a set time threshold. It is a dirty, and as noted below, it should never be public facing.

## NB! This tool should NEVER be run in a public facing environment
The code is dirty, horrible, and should ideally only be ran locally, and at most only be port forwarded through SSH or something similar.

## Installation
Set the `BACKUPS_DIRECTORY` environment variable in either `.env` or pass it into docker-compose, then run:

```
docker-compose up -d
```

After a few seconds, the application will be available on `127.0.0.1:5000`. It has to load, scan, and map all the backups, so launching **might take a bit** (~20 seconds with 150 CTFs).

## Configuration

The layout can be customized, but to get the application working all that is needed is the environment variable `BACKUPS_DIRECTORY`. This variable has to point to where the fiskebot backups (JSON files) are located.

| Name | Default | Comment |
| ---- | ------- | ------- |
| `BACKUPS_DIRECTORY` |  | **Required!** Location of the `backups` directory of fiskebot |
| `STATE_JSON_FILE` | `./state.json` | Location of the state file |
| `IGNORE_NAMES` | `fiskebot` | What names should be excluded from the participant lists. Comma (`,`) separated |
| `PAGE_NAME` | `fiskebot` | Name of the website |
| `PAGE_COLOR` | `#AC0A2B` | Color of the website navigation header |
| `UPDATE_STATE_SECONDS` | `300` | How many seconds before the local state should be reloaded (i.e. scan the backups) |
| `SEARCH_RESULT_COUNT_LIMIT` | `500` | How many results to return when searching |


## Functionality

### Listing CTFs
The application will display information about the exported CTFs. This information includes the date of the CTF, the number of channels, messages, participants, and direct links to the CTF and their challenges (`/ctf/<ctf_id>` and `/ctf/<ctf_id>#<challenge_name>`). 

<img src="https://raw.githubusercontent.com/ekofiskctf/fiskebot/master/tools/backups_viewer/readme_resources/listing_ctfs.png" width="700"/>

### CTF summary
When opening a specific CTF (`/ctf/<ctf_id>`), the tool will list all the challenges (channels) of the CTF, all the chat participants and the number of messages they sent, but also all the messages and channels of the CTF will be displayed below the summary.

In addition, all of the challenges/channels of the CTF are directly linkable (`/ctf/ctf_id>#<challenge_name`), and can be obtained by clicking on the challenge/channel name. The individual messages in the CTF are also directly linkable (`/ctf/<ctf_id>#<message_id>`), this link can be obtained by clicking the timestamp of the message.

<img src="https://raw.githubusercontent.com/ekofiskctf/fiskebot/master/tools/backups_viewer/readme_resources/ctfs_summary.png" width="700"/>

### Search

There is currently very simple search functionallity that searches through all the messages and displays all the matching messages.

<img src="https://raw.githubusercontent.com/ekofiskctf/fiskebot/master/tools/backups_viewer/readme_resources/search.png" width="700"/>

### Rendering and attachments

The tool is capable of rendering markdown and linking attachments, this includes images, files, quotes, code, and other markdown formatting.

<img src="https://raw.githubusercontent.com/ekofiskctf/fiskebot/master/tools/backups_viewer/readme_resources/markdown_quote.png" width="700"/>

<img src="https://raw.githubusercontent.com/ekofiskctf/fiskebot/master/tools/backups_viewer/readme_resources/markdown_code_images.png" width="700"/>

<img src="https://raw.githubusercontent.com/ekofiskctf/fiskebot/master/tools/backups_viewer/readme_resources/attachments.png" width="700"/>

