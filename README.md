# Coyote Badger

![Coyote Badger Home Screen](./coyote_badger/static/home.png)

#### Table of Contents
1. [Getting Started](#getting-started)
2. [Install](#install)
3. [Run](#run)
4. [Development](#development)
5. [Videos](#videos)
6. [FAQ](#faq)


## Getting Started
Coyote Badger is designed to take a spreadsheet of accurately bluebooked
citations and search for them. Basically, it opens and controls a Chrome
browser in the background to do what an editor would be doing manually.

When it runs, it will pull the sources for a particular project, and output
a list of the sources that were found, along with the actual PDF files
of the sources.

To get started with Coyote Badger, first follow the
[instructions to install](#install) the software, then follow the
[instructions to run](#run) the software. Once Coyote Badger is up an running,
you may find the short [tutorial videos](#videos) helpful to understand
how it works.

## Install
To install Coyote Badger:
1. Install Docker for your operating system by selecting the appropriate
   version [here](https://docs.docker.com/get-docker/) and following the
   installation instructions.
2. Once Docker is installed, you shouldn't have to change any of the default
   preferences, but make sure you have it running (see install instructions).
3. Download the latest "Source code (zip)" of Coyote Badger from
   [here](https://github.com/alexsands/coyote-badger/releases/latest).
   Then unzip the file and move it to somewhere on your computer that you'll
   remember (e.g., `Documents` folder). You can rename the containing folder
   if you'd like.
4. That's it! Now you can [run Coyote Badger](#run).


## Run
To run Coyote Badger, follow the instructions for your particular operating
system:

#### Mac
1. Make sure Docker is started on your computer
2. Navigate to your Coyote Badger folder
3. Right click on the `_start-mac.command` file, then select "Open". Accept
   the warning about the unidentified developer if it asks (you should only
   have to do this step once).
4. A Terminal window will open and you'll see it printing out information. Wait
   until you see `Running on http://0.0.0.0:5000/`.
   Once you see this, you can close the Terminal window. If it's your first
   time running, a lot of stuff will install and this will take
   several minutes (but you shouldn't have to wait this long again!).
5. Open your browser and go to [http://localhost:5000](http://localhost:5000)
6. You should see Coyote Badger!
7. When you're done using the program, right click on the `_stop-mac.command`
   file in the Coyote Badger folder, then select "Open". Accept
   the warning about the unidentified developer if it asks (you should only
   have to do this step once).

#### Windows
1. Navigate to your Coyote Badger folder
2. While holding <kbd>Shift</kbd>, right-click anywhere in the folder window
   and select "Open command window here"
3. Copy and paste the following into Command Prompt and press <kbd>Enter</kbd>
```sh
docker build . -t coyotebadger:latest
docker run -it --rm --name coyotebadger --memory="2g" --cpus="2" --tmpfs /tmp/coyotebadger/chrome -v "$(pwd)"/_projects:/opt/coyotebadger/_projects -p 5000:5000 coyotebadger:latest
```
4. You'll start to see it printing out information. Wait
   until you see `Running on http://0.0.0.0:5000/`. If it's your first
   time running, a lot of stuff will install and this will take
   several minutes (but you shouldn't have to wait this long again!).
5. Open your browser and go to [http://localhost:5000](http://localhost:5000)
6. You should see Coyote Badger!
7. When you're done using the program, go back to the Command Prompt that was
   running and press <kbd>Ctrl</kbd> + <kbd>C</kbd>.


## Development
Coyote Badger uses Flask as the web server and Microsoft Playwright as the
automated browser. To improve or debug Coyote Badger, it's easiest to run
it directly from source with Python, instead of in the Docker container,
because you can view the `headless=False` Chromium browser.

First, create a virtual environment in the root and install the project
dependencies with:
```sh
virtualenv -p python3 venv
source venv/bin/activate
pip3 install -r requirements.txt
```

Then run the project with:
```sh
FLASK_ENV=development python3 -m coyote_badger.app
```

The project is generally structure as follows:
1. `/_projects`: holds the project data and is mounted to the Docker container
   as a volume.
2. `/coyote_badger/extensions`: these are the Chrome extensions that get added
   to the browser instance. They are slightly modified, with the description
   of the changes in the `README.md` in that directory.
3. `/coyote_badger/static`: holds the static files. In this case it's just the
   sources template file `Soruces.xlsx`.
4. `/coyote_badger/templates`: the frontend Jinja files for Flask.
5. `/coyote_badger/usr`: a user data folder for the Chromium browser instance.
6. `/coyote_badger/app.py`: the main routes and app logic for Flask.
7. `/coyote_badger/puller.py`: the main file for the web scraper and pulling
   sources. If Hein, Westlaw, or SSRN ever changes, this is where you should
   start.
8. `/coyote_badger/converter.py`: the main logic for turning an article/note
   Word document into the source inventory Excel sheet.
9. Everything else: these files shouldn't need to change too much in the
   future. The main thing that might break is likely in `puller.py` since
   that's where all the scraping logic happens.

To make it easier to see what is happening with Playwright, you can
uncomment the `slow_mo` argument in `coyote_badger.puller.Puller.context`.

In the event Hein, Westlaw, or SSRN ever changes their website, the logic for
actually pulling sources on the web is in `coyote_badger.puller.Puller.pull()`.
You can also contact me directly, just open an
[issue](https://github.com/alexsands/coyote-badger/issues), and I will get
an email about it. I'll happily take a look and try to help.


## Videos

- [Running and Using Coyote Badger](https://youtu.be/2kK8G_dHtWQ)

## FAQ
**When I try to run the application, I get a message about Docker not
being started. What do I do?**

Make sure you open the Docker application and click Start before trying
to run Coyote Badger. You may need to do this after you restart your computer
if Docker does not start automatically.


**Everything is installed, it's running, but the actual Coyote Badger
application isn't pulling sources properly. What do I do?**

It's likely that Hein, Westlaw, or SSRN changed their website code and it
broke the automated puller. If you are familiar with Python, you can try to
fix this on your own with the [Development](#development) instructions.
Otherwise, you can also contact me directly, just open an
[issue](https://github.com/alexsands/coyote-badger/issues), and I will get
an email about it. I'll happily take a look and try to help.


**Why use `headless=False` with `xvfb` if you can't even see the browser?**

The program uses a few Chrome extensions to block ads and paywalls,
which unfortunately do not work in headless Chrome. The Chrome team does
not presently have this on their radar for development.


**Something else?**

Open up an [issue](https://github.com/alexsands/coyote-badger/issues) with your
question, and I will get an email about it. I'll happily take a look and try
to help.


## Maintenance
This code was written by Alex Sands and Warner Scott. Both authors, as well
the current research editor, have access to this repository and will receive
emails when new issues are submitted. If you'd like to improve this code,
please submit a PR rather than making changes offline. Keep this source
up to date!
