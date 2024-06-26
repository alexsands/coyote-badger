import os
import uuid
from threading import Timer

import requests
import segment.analytics as analytics
from colorama import init
from flask import (
    Flask,
    after_this_request,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from flask_bootstrap import Bootstrap
from packaging import version

from coyote_badger.config import (
    PORT,
    REPO,
    SEGMENT_WRITE_KEY,
    SOURCES_TEMPLATE_FILE,
    VERSION,
)
from coyote_badger.converter import create_sources_template
from coyote_badger.project import Project
from coyote_badger.puller import Puller
from coyote_badger.source import Kind, Result, Source

analytics.write_key = SEGMENT_WRITE_KEY
anonymous_id = str(uuid.uuid4())

init()

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
Bootstrap(app)

citations = None
puller = Puller()
puller.clear_user_data()

ART_MESSAGE = r"""








   ______    ___   ____  ____   ___    _________  ________
 .' ___  | .'   `.|_  _||_  _|.'   `. |  _   _  ||_   __  |
/ .'   \_|/  .-.  \ \ \  / / /  .-.  \|_/ | | \_|  | |_ \_|
| |       | |   | |  \ \/ /  | |   | |    | |      |  _| _
\ `.___.'\\  `-'  /  _|  |_  \  `-'  /   _| |_    _| |__/ |
 `.____ .' `.___.'  |______|  `.___.'   |_____|  |________|
 ______        _       ______      ______  ________  _______
|_   _ \      / \     |_   _ `.  .' ___  ||_   __  ||_   __ \
  | |_) |    / _ \      | | `. \/ .'   \_|  | |_ \_|  | |__) |
  |  __'.   / ___ \     | |  | || |   ____  |  _| _   |  __ /
 _| |__) |_/ /   \ \_  _| |_.' /\ `.___]  |_| |__/ | _| |  \ \_
|_______/|____| |____||______.'  `._____.'|________||____| |___|
"""
UPDATE_MESSAGE = rf"""
===================================================================
                        UPDATE AVAILABLE
There is a new version of Coyote Badger available! Please make sure
you update to the latest version if you're experiencing issues. For
information on how to update, see this link:
https://github.com/{REPO}#update
===================================================================
"""
READY_MESSAGE = rf"""
Coyote Badger is ready to use!
Open your browser to http://localhost:{PORT} to get started.
"""


def SuccessResponse(message=None):
    return {
        "error": False,
        "message": message or "",
    }


def ErrorResponse(message=None):
    return {
        "error": True,
        "message": message or "",
    }


def has_updates():
    response = requests.get(f"https://api.github.com/repos/{REPO}/releases/latest")
    latest_tag = response.json().get("tag_name")
    if version.parse(VERSION) < version.parse(latest_tag):
        return True


def welcome():
    print(ART_MESSAGE)
    if has_updates():
        print(UPDATE_MESSAGE)
    print(READY_MESSAGE)


@app.route("/", methods=["GET", "POST"])
def index():
    """Main homepage.

    The homepage template that asks for login details,
    and the completed template.

    GET: renders a template with all the past projects
    POST: creates a new project with the supplied name and source file
    """
    projects = Project.get_projects()
    if request.method == "GET":
        analytics.page(
            anonymous_id=anonymous_id,
            name="Home",
            context={
                "page": {
                    "url": request.path,
                    "title": "Home",
                },
            },
        )
        return render_template("index.html.j2", projects=projects)
    elif request.method == "POST":
        name = request.form.get("name", "").strip()
        xls_file = request.files.get("file")

        # Check for name
        if not name:
            return render_template(
                "index.html.j2",
                projects=projects,
                error="Missing or invalid project name.",
            )
        if name in projects:
            return render_template(
                "index.html.j2",
                projects=projects,
                error="This project name already exists.",
            )

        # Check for source template file
        if not xls_file:
            return render_template(
                "index.html.j2",
                projects=projects,
                error="Missing or invalid template file.",
            )

        # Try to make the project
        try:
            Project(name, xls_file)
        except Exception as e:
            return render_template(
                "index.html.j2",
                projects=projects,
                error=f"Failed to create your project. {str(e)}",
            )

        # Everything worked, go to the /sources page for the project
        return redirect(url_for("sources", project_name=name))


@app.route("/about", methods=["GET"])
def about():
    """About page.

    A route describing Coyote Badger and how it is used.

    GET: renders the about page
    """
    analytics.page(
        anonymous_id=anonymous_id,
        name="About",
        context={
            "page": {
                "url": request.path,
            },
        },
    )
    return render_template("about.html.j2")


@app.route("/download-sources-template", methods=["GET"])
def download_sources_template():
    """A download link for the Sources.xlsx template.

    GET: sends the template file
    """
    return send_file(SOURCES_TEMPLATE_FILE, as_attachment=True)


@app.route("/convert", methods=["GET", "POST"])
def convert():
    """Create sources template page.

    Page that lets you upload an article/note and download
    a sheet of the sources.

    GET: renders the create sources template page
    POST: makes the sources template page from a form submission
    """
    if request.method == "GET":
        analytics.page(
            anonymous_id=anonymous_id,
            name="Convert",
            context={
                "page": {
                    "url": request.path,
                    "title": "Convert",
                },
            },
        )
        return render_template("convert.html.j2")
    elif request.method == "POST":
        doc_file = request.files.get("file")

        # Check for article/note file
        if not doc_file:
            return render_template(
                "convert.html.j2", error="Missing article/note file."
            )

        try:
            project, sources = create_sources_template(doc_file)

            @after_this_request
            def remove_temp_file(response):
                project.delete()
                return response

        except Exception as e:
            analytics.track(
                anonymous_id=anonymous_id,
                event="Source Conversion Failed",
                properties={
                    "message": str(e),
                },
            )
            return render_template(
                "convert.html.j2",
                error=f"Your file could not be converted. {str(e)}",
            )
        else:
            input_filename = os.path.splitext(doc_file.filename)[0]
            analytics.track(
                anonymous_id=anonymous_id,
                event="Source Conversion Succeeded",
                properties={
                    "count": len(sources),
                },
            )
            return send_file(
                project.sources_file,
                as_attachment=True,
                attachment_filename=f"{input_filename}_Sources.xlsx",
            )


@app.route("/login", methods=["GET", "POST"])
def login():
    """Login page.

    The login page that asks the user for the credentials
    to Hein and Westlaw.

    GET: renders the login page
    POST: attempts login and redirects if successful; shows error if not
    """
    if request.method == "GET":
        analytics.page(
            anonymous_id=anonymous_id,
            name="Login",
            context={
                "page": {
                    "url": request.path,
                    "title": "Login",
                },
            },
        )
        return render_template("login.html.j2")
    elif request.method == "POST":
        project_name = request.args.get("project")
        hein_username = request.form.get("hein_username")
        hein_password = request.form.get("hein_password")
        westlaw_username = request.form.get("westlaw_username")
        westlaw_password = request.form.get("westlaw_password")
        ssrn_username = request.form.get("ssrn_username")
        ssrn_password = request.form.get("ssrn_password")

        # Check for Hein credentials
        if not hein_username or not hein_password:
            return render_template(
                "login.html.j2", error="Missing Hein username or password."
            )

        # Check for Westlaw credentials
        if not westlaw_username or not westlaw_password:
            return render_template(
                "login.html.j2", error="Missing Westlaw username or password."
            )

        # Check for SSRN credentials
        if not ssrn_username or not ssrn_password:
            return render_template(
                "login.html.j2", error="Missing SSRN username or password."
            )

        # Check that log in was successful
        try:
            puller.login(
                hein_username,
                hein_password,
                westlaw_username,
                westlaw_password,
                ssrn_username,
                ssrn_password,
            )
        except Exception as e:
            analytics.track(
                anonymous_id=anonymous_id,
                event="Login Failed",
                properties={
                    "message": str(e),
                },
            )
            return render_template(
                "login.html.j2",
                error=f"{str(e)} Check your username and password.",
            )

        analytics.track(anonymous_id=anonymous_id, event="Login Succeeded")
        # Redirect the user back to the project or home screen
        if project_name:
            return redirect(url_for("sources", project_name=project_name))
        return redirect(url_for("index"))


@app.route("/sources/<string:project_name>", methods=["GET", "POST"])
def sources(project_name):
    """Sources page.

    The sources page that shows the list of citations
    and the option to download PDFs. Checks for errors
    on the provided logins and template file.

    GET: loads the project's sources and renders a template
    POST: saves new source data from the UI to a project
    """
    project = Project.get_project(project_name)
    if request.method == "GET":
        if not project:
            return redirect(url_for("index"))
        analytics.page(
            anonymous_id=anonymous_id,
            name="Sources",
            context={
                "page": {
                    "url": request.path,
                    "title": "Sources",
                },
            },
        )
        return render_template(
            "sources.html.j2",
            Kind=Kind,
            Result=Result,
            project_name=project_name,
            sources=[s.to_json() for s in project.get_sources()],
        )
    elif request.method == "POST":
        sources = [Source.from_json(source) for source in request.json]
        project.save_sources(sources)
        return SuccessResponse()


@app.route("/pull", methods=["GET", "POST"])
def pull():
    """Endpoint to crawl the source provided.

    Takes data about the source and citation as input, and goes out
    on the internet to search for it using the puller.

    GET: gets whether or not the user is logged in and can start a pull
    POST: starts the pull of a source (assumes user is logged in)
    """
    if request.method == "GET":
        if not puller.all_authenticated:
            return ErrorResponse("Not authenticated to all sources.")
        return SuccessResponse()
    elif request.method == "POST":
        project_name = request.json.get("project_name")
        index = request.json.get("index")

        if not project_name:
            return ErrorResponse("Missing required project name.")
        if not index:
            return ErrorResponse("Missing required index.")

        project = Project.get_project(project_name)
        source = project.get_source(index)
        source.result = puller.pull(source, project)
        project.save_source(index, source)
        analytics.track(
            anonymous_id=anonymous_id,
            event="Source Pulled",
            properties={
                "source": source.to_json(),
            },
        )
        return {
            "error": False,
            "result": source.result.value,
        }


if __name__ == "__main__":
    t = Timer(3, welcome)
    t.start()
    app.run(host="0.0.0.0", port=PORT, threaded=False, use_reloader=False)
    analytics.track(anonymous_id=anonymous_id, event="Application Started")
