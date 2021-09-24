# Coyote Badger

![Coyote Badger Home Screen](./coyote_badger/static/home.png)

#### Table of Contents
1. [Getting Started](#getting-started)
2. [Install](#install)
3. [Run](#run)
4. [Development](#development)
5. [Making or Requesting Changes](#making-or-requesting-changes)
6. [Videos](#videos)
7. [FAQ](#faq)


## Getting Started
Coyote Badger is designed to take a spreadsheet of accurately bluebooked
citations and search for them. Basically, it opens and controls a web
browser in the background to do what an editor would be doing manually.

When it runs, it will pull the sources for a particular project, and output
a list of the sources that were found, along with the actual PDF files
of the sources.

To get started with Coyote Badger, first follow the
[instructions to install](#install) the software, then follow the
[instructions to run](#run) the software. Once Coyote Badger is up and running,
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
docker run -it --rm --name coyotebadger --ipc="host" --shm-size="1gb" --memory="2g" --cpus="2" -v %cd%/_projects:/opt/coyotebadger/_projects -p 5000:5000 coyotebadger:latest
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

First, make sure `pyenv` and `pyenv-virtualenv` are installed on your computer.

Then, in the root of the project, create a virtual environment and install
the project dependencies with:
```sh
pyenv install 3.9.2
pyenv virtualenv 3.9.2 coyote-badger
pyenv activate coyote-badger
pip install -r requirements.txt
git clone --branch=v1.12.0 https://github.com/microsoft/playwright-python.git external/playwright-python-1.12.0
pip install external/playwright-python-1.12.0
python -m playwright install
```

Now (and in the future) you can run the project with:
```sh
pyenv activate coyote-badger
FLASK_ENV=development python -m coyote_badger.app
```

The project is generally structured as follows:
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
increase the `slow_mo` argument to something higher in
`coyote_badger.puller.Puller.create_context()`.

In the event Hein, Westlaw, or SSRN ever changes their website, the logic for
actually pulling sources on the web is in `coyote_badger.puller.Puller.pull()`.
You can also contact me directly, just open an
[issue](https://github.com/alexsands/coyote-badger/issues), and I will get
an email about it. I'll happily take a look and try to help.

**Note:** As of 3/27/2021, it is not possible to download
Original Image files from Westlaw due to
[a bug in Chrome](https://bugs.chromium.org/p/chromium/issues/detail?id=761295)
that prevents the browser from being able to load PDF content-types in
`headless=False` mode. As a workaround, we use Firefox in `headless=False`
mode to grab sources from Hein, Westlaw, and SSRN. Unfortunately, Playwright
[does not support loading extensions in Firefox easily](https://github.com/microsoft/playwright/issues/2644),
so now we have to use a mix of Chrome (to load extensions for clean website
screenshots) and Firefox (to pull Hein, Westlaw, SSRN). Eventually, when either
issue is resolved, the code can be simplified by just using one browser.


## Making or Requesting Changes

If the project stops working as expected, please open up an
[issue](https://github.com/alexsands/coyote-badger/issues) with details on what
is failing. I will get an email about it and happily take a look. If you're
familiar with programming and would like to try fixing it yourself, you can
(1) open a pull request with your fix or (2) just upload the file/changes
you think should be made on the issue itself.


## Videos
- [Starting & Stopping](https://youtu.be/Pzyfdr_b198)
- [Creating a Source Inventory Template](https://youtu.be/p2cW8tUTOHU)
- [Pulling Sources](https://youtu.be/ypmY4Hfn5Rg)


## FAQ
**How do I get notified of issues, changes, or new versions of Coyote Badger?**

First, create a GitHub account. Then, at the top right of the [Coyote Badger
project page](https://github.com/alexsands/coyote-badger) click
`Watch` → `All Activity` to receive emails about issues.


**How do I run Coyote Badger on a Mac with Apple Silicon?**

As of right now, you can use the normal [Mac running instructions](#mac) if
all you need to do is run the Coverter to generate a `Sources.xlsx` file. If
you also need to pull sources, you will have to use the
[Development instructions](#development) and run Coyote Badger in the
foreground. There is an
[open issue](https://github.com/alexsands/coyote-badger/issues/6) in place
to track the progress of fully running Coyote Badger in Docker on Apple Silicon
and this will be possible in a future version.


**When I try to run the application, I get a message about not being
able to connect to the Docker daemon. What do I do?**

Make sure you open the Docker application and click Start before trying
to run Coyote Badger. You may need to do this after you restart your computer
if Docker does not start automatically.


**Everything is installed, it's running, but the actual Coyote Badger
application isn't pulling sources properly. What do I do?**

It's likely that Hein, Westlaw, or SSRN changed their website code and it
broke the automated puller. If you are familiar with programming, you can try
to fix this on your own with the [Development](#development) instructions and
then make an issue/pull request on GitHub. Otherwise, please read the
[Making or Requesting Changes](#making-or-requesting-changes) section.


**Hein login seems to always fail because my Duo isn't working. What do I do?**
The program works by attempting to log you in (using the username and password
you provide) to Hein, Westlaw, and SSRN in the background. To do so, Hein
may use Duo for two-factor authentication when you log in with your university
or organization email address. In order for the program to pass this step, you
must set your Duo two-factor authentication settings to use "Push Notifications"
by default. If you use text message codes the program has no way of entering
the pin while its running in the background (since it can't access your text
messages). You can change this preference to use "Push Notifications" by
default on your organization's Duo settings page. You'll also need to download
the Duo smartphone app.


**Why use `headless=False` with `xvfb` if you can't even see the browser?**

The program uses a few Chrome extensions to block ads and paywalls,
which unfortunately do not work in headless Chrome. The Chrome team does
not presently have this on their radar for development.


**Why is git ignoring some files when I make changes?**

The `_projects/Example` folder is being ignored so that it can be run as a
test set, without pushing new pull results to GitHub on each commit. It's a bit
deceiving though, because this doesn't happen in the `.gitignore` file. Instead,
these files are ignored via:
```sh
git update-index --skip-worktree <file>
```
To show which files are ignored, run:
```sh
git ls-files -v . | grep ^S
```


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
