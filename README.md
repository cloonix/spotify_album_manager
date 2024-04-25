# Spotify album manager

This Python script(s) is mainly for learning and fun. It was created using OpenAi's GPT4.

I don't like the way Spotify manages my favourite albums (and songs). Also, I thought I would lose my collection if Spotify shut down or locked me out for some reason. So this Python application was born. Nothing that an Excel file couldn't solve, but it was fun.

If anyone stumbles across this repository, they're invited to use and improve the application. I welcome pull requests and feedback.

## Setup

Clone the repository and install the requirements:

```
pip install -r requirements.txt
``` 

Getting your personal Spotify API credentials from https://developer.spotify.com and put it in a `.env` file:

```
cp .env_sample .env
vi .env
``` 

Execute the script:

```
python spotify.py
```

## Features

- Adding an album by entering the Spotify URL and one or multiple tags (separated by commas)
- Browse albums by artist or tag
- Delete albums
- Create a backup of the sqlite database
- Loading one of the last 3 backups