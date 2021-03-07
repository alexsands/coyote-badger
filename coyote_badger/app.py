import os

from colorama import init
from flask import Flask
from flask import request
from flask import render_template
from flask import redirect
from flask import url_for
from flask import send_file
from flask import after_this_request
from flask_bootstrap import Bootstrap

from coyote_badger.config import SOURCES_TEMPLATE_FILE
from coyote_badger.project import Project
from coyote_badger.source import Kind
from coyote_badger.source import Result
from coyote_badger.source import Source
from coyote_badger.puller import Puller
from coyote_badger.converter import create_sources_template

init()

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
Bootstrap(app)

citations = None
puller = Puller()


def SuccessResponse(message=None):
    return {
        'error': False,
        'message': message or '',
    }


def ErrorResponse(message=None):
    return {
        'error': True,
        'message': message or '',
    }


@app.route('/', methods=['GET', 'POST'])
def index():
    '''Main homepage.

    The homepage template that asks for login details,
    and the completed template.

    GET: renders a template with all the past projects
    POST: creates a new project with the supplied name and source file
    '''
    projects = Project.get_projects()
    if request.method == 'GET':
        return render_template('index.html.j2', projects=projects)
    elif request.method == 'POST':
        name = request.form.get('name', '').strip()
        xls_file = request.files.get('file')

        # Check for name
        if not name:
            return render_template(
                'index.html.j2',
                projects=projects, error='Missing or invalid project name.')
        if name in projects:
            return render_template(
                'index.html.j2',
                projects=projects, error='This project name already exists.')

        # Check for source template file
        if not xls_file:
            return render_template(
                'index.html.j2',
                projects=projects, error='Missing or invalid template file.')

        # Try to make the project
        try:
            Project(name, xls_file)
        except Exception as e:
            return render_template(
                'index.html.j2',
                projects=projects,
                error='Failed to create your project. {}'.format(str(e)))

        # Everything worked, go to the /sources page for the project
        return redirect(url_for('sources', project_name=name))


@app.route('/about', methods=['GET'])
def about():
    '''About page.

    A route describing Coyote Badger and how it is used.

    GET: renders the about page
    '''
    return render_template('about.html.j2')


@app.route('/download-sources-template', methods=['GET'])
def download_sources_template():
    '''A download link for the Sources.xlsx template.

    GET: sends the template file
    '''
    return send_file(SOURCES_TEMPLATE_FILE, as_attachment=True)


@app.route('/convert', methods=['GET', 'POST'])
def convert():
    '''Create sources template page.

    Page that lets you upload an article/note and download
    a sheet of the sources.

    GET: renders the create sources template page
    POST: makes the sources template page from a form submission
    '''
    if request.method == 'GET':
        return render_template('convert.html.j2')
    elif request.method == 'POST':
        doc_file = request.files.get('file')

        # Check for article/note file
        if not doc_file:
            return render_template(
                'convert.html.j2',
                error='Missing article/note file.')

        try:
            project = create_sources_template(doc_file)

            @after_this_request
            def remove_temp_file(response):
                project.delete()
                return response
        except Exception as e:
            return render_template(
                'convert.html.j2',
                error='Your file could not be converted. {}'.format(str(e)))
        else:
            input_filename = os.path.splitext(doc_file.filename)[0]
            return send_file(
                project.sources_file,
                as_attachment=True,
                attachment_filename='{}_Sources.xlsx'.format(input_filename))


@app.route('/login', methods=['GET', 'POST'])
def login():
    '''Login page.

    The login page that asks the user for the credentials
    to Hein and Westlaw.

    GET: renders the login page
    POST: attempts login and redirects if successful; shows error if not
    '''
    if request.method == 'GET':
        return render_template('login.html.j2')
    elif request.method == 'POST':
        project_name = request.args.get('project')
        hein_username = request.form.get('hein_username')
        hein_password = request.form.get('hein_password')
        westlaw_username = request.form.get('westlaw_username')
        westlaw_password = request.form.get('westlaw_password')
        ssrn_username = request.form.get('ssrn_username')
        ssrn_password = request.form.get('ssrn_password')

        # Check for Hein credentials
        if not hein_username or not hein_password:
            return render_template(
                'login.html.j2',
                error='Missing Hein username or password.')

        # Check for Westlaw credentials
        if not westlaw_username or not westlaw_password:
            return render_template(
                'login.html.j2',
                error='Missing Westlaw username or password.')

        # Check for SSRN credentials
        if not ssrn_username or not ssrn_password:
            return render_template(
                'login.html.j2',
                error='Missing SSRN username or password.')

        # Check that log in was successful
        try:
            puller.login(
                hein_username, hein_password,
                westlaw_username, westlaw_password,
                ssrn_username, ssrn_password)
        except Exception as e:
            return render_template(
                'login.html.j2',
                error='{} Check your username and password.'.format(str(e)))

        # Redirect the user back to the project or home screen
        if project_name:
            return redirect(url_for('sources', project_name=project_name))
        return redirect(url_for('index'))


@app.route('/sources/<string:project_name>', methods=['GET', 'POST'])
def sources(project_name):
    '''Sources page.

    The sources page that shows the list of citations
    and the option to download PDFs. Checks for errors
    on the provided logins and template file.

    GET: loads the project's sources and renders a template
    POST: saves new source data from the UI to a project
    '''
    project = Project.get_project(project_name)
    if request.method == 'GET':
        if not project:
            return redirect(url_for('index'))
        return render_template(
            'sources.html.j2',
            Kind=Kind,
            Result=Result,
            project_name=project_name,
            sources=[s.to_json() for s in project.get_sources()])
    elif request.method == 'POST':
        sources = [Source.from_json(source) for source in request.json]
        project.save_sources(sources)
        return SuccessResponse()


@app.route('/pull', methods=['GET', 'POST'])
def pull():
    '''Endpoint to crawl the source provided.

    Takes data about the source and citation as input, and goes out
    on the internet to search for it using the puller.

    GET: gets whether or not the user is logged in and can start a pull
    POST: starts the pull of a source (assumes user is logged in)
    '''
    if request.method == 'GET':
        if not puller.all_authenticated:
            return ErrorResponse('Not authenticated to all sources.')
        return SuccessResponse()
    elif request.method == 'POST':
        project_name = request.json.get('project_name')
        index = request.json.get('index')

        if not project_name:
            return ErrorResponse('Missing required project name.')
        if not index:
            return ErrorResponse('Missing required index.')

        project = Project.get_project(project_name)
        source = project.get_source(index)
        source.result = puller.pull(source, project)
        project.save_source(index, source)
        return {
            'error': False,
            'result': source.result.value,
        }


if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=False)
