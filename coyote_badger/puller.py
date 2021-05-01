import os
import re
import shutil

from urllib.request import urlretrieve
from fake_useragent import UserAgent
from playwright.sync_api import sync_playwright

from coyote_badger import utils
from coyote_badger.config import PACKAGE_FOLDER
from coyote_badger.source import Kind
from coyote_badger.source import Result


class Puller(object):
    BROWSER_USER_DATA_DIR = os.path.join(PACKAGE_FOLDER, 'usr')
    CHROME_USER_DATA_DIR = os.path.join(BROWSER_USER_DATA_DIR, 'chrome')
    FIREFOX_USER_DATA_DIR = os.path.join(BROWSER_USER_DATA_DIR, 'firefox')
    EXTENSIONS_FOLDER = os.path.join(PACKAGE_FOLDER, 'extensions')

    SLOW_MO = 0.5 * 1000  # 0.5 sec, increase to slow down for debugging

    HEIN_SIGN_IN_URL = 'https://heinonline-org.ezproxy.lib.utexas.edu/HOL/Welcome'
    HEIN_AUTHED_URL = 'https://heinonline-org.ezproxy.lib.utexas.edu/HOL/Welcome'
    HEIN_SEARCH_URL = 'https://heinonline-org.ezproxy.lib.utexas.edu/HOL/Welcome'
    HEIN_BASE_URL = 'https://heinonline-org.ezproxy.lib.utexas.edu/HOL/'

    WESTLAW_SIGN_IN_URL = 'https://lawschool.westlaw.com/redirect/westlaw'
    WESTLAW_AUTHED_URL = 'https://1.next.westlaw.com/Search/Home.html?transitionType=Default&contextData=(sc.Default)'
    WESTLAW_SEARCH_URL = 'https://1.next.westlaw.com/Search/Home.html?transitionType=Default&contextData=(sc.Default)'
    WESTLAW_STATUTES_URL = 'https://1.next.westlaw.com/Browse/Home/StatutesCourtRules?transitionType=Default&contextData=(sc.Default)'
    WESTLAW_CASES_URL = 'https://1.next.westlaw.com/Browse/Home/Cases?transitionType=Default&contextData=(sc.Default)'

    SSRN_SIGN_IN_URL = 'https://hq.ssrn.com/login/pubsigninjoin.cfm'
    SSRN_AUTHED_URL = 'https://hq.ssrn.com/Library/myLibrary.cfm'

    def __init__(self):
        '''Creates a new Puller with Playwright.

        Puller stores the browsers that will be used to pull sources,
        and contains the logic for scraping the websites.
        '''
        ua = UserAgent()
        self.ua_chrome = ua.google
        self.ua_firefox = ua.firefox
        self._playwright = None
        self._chrome = None
        self._firefox = None

    @property
    def playwright(self):
        if not self._playwright:
            self._playwright = sync_playwright().start()
        return self._playwright

    @property
    def chrome(self):
        if not self._chrome:
            if os.path.exists(self.CHROME_USER_DATA_DIR):
                shutil.rmtree(self.CHROME_USER_DATA_DIR)
            os.mkdir(self.CHROME_USER_DATA_DIR)
            self._chrome = self.create_context(
                self.playwright.chromium, self.CHROME_USER_DATA_DIR,
                self.ua_chrome)
        return self._chrome

    @property
    def firefox(self):
        if not self._firefox:
            if os.path.exists(self.FIREFOX_USER_DATA_DIR):
                shutil.rmtree(self.FIREFOX_USER_DATA_DIR)
            os.mkdir(self.FIREFOX_USER_DATA_DIR)
            self._firefox = self.create_context(
                self.playwright.firefox, self.FIREFOX_USER_DATA_DIR,
                self.ua_firefox)
        return self._firefox

    @classmethod
    def clear_user_data(cls):
        if os.path.exists(cls.BROWSER_USER_DATA_DIR):
            shutil.rmtree(cls.BROWSER_USER_DATA_DIR)
        os.mkdir(cls.BROWSER_USER_DATA_DIR)

    @classmethod
    def create_context(cls, browser, usr_dir, user_agent):
        extensions = ','.join([
            os.path.join(cls.EXTENSIONS_FOLDER, 'ublock'),
            os.path.join(cls.EXTENSIONS_FOLDER, 'bypass-paywalls-chrome'),
        ])
        return browser.launch_persistent_context(
            usr_dir,
            headless=False,
            slow_mo=cls.SLOW_MO,
            accept_downloads=True,
            user_agent=user_agent,
            chromium_sandbox=False,
            ignore_default_args=[
                '--enable-automation',
            ],
            args=[
                '--no-default-browser-check',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-extensions-except={}'.format(extensions),
                '--load-extension={}'.format(extensions),
            ],
            viewport={
                'width': 1280,
                'height': 780,
            })

    @classmethod
    def timeout(cls, sec):
        return cls.SLOW_MO + sec * 1000

    @property
    def hein_authenticated(self):
        result = False
        page = self.firefox.new_page()
        try:
            page.goto(self.HEIN_AUTHED_URL, wait_until='networkidle')
            username = page.query_selector('#username')
            password = page.query_selector('#password')
            if not username or not password:
                result = True
        except Exception as e:
            print(str(e))
            result = False
        finally:
            page.close()
        return result

    @property
    def westlaw_authenticated(self):
        result = False
        page = self.firefox.new_page()
        try:
            page.goto(self.WESTLAW_AUTHED_URL, wait_until='networkidle')
            username = page.query_selector('#Username')
            password = page.query_selector('#Password')
            if not username or not password:
                result = True
        except Exception as e:
            print(str(e))
            result = False
        finally:
            page.close()
        return result

    @property
    def ssrn_authenticated(self):
        result = False
        page = self.firefox.new_page()
        try:
            page.goto(self.SSRN_AUTHED_URL, wait_until='networkidle')
            forgot = page.query_selector('a:has-text("Forgot password")')
            if not forgot:
                result = True
        except Exception as e:
            print(str(e))
            result = False
        finally:
            page.close()
        return result

    @property
    def all_authenticated(self):
        return (
            self.hein_authenticated
            and self.westlaw_authenticated
            and self.ssrn_authenticated)

    def login_hein(self, hein_username, hein_password):
        page = self.firefox.new_page()
        try:
            page.goto(self.HEIN_SIGN_IN_URL)
            page.fill('#username', hein_username)
            page.fill('#password', hein_password)
            page.click('input[type="submit"]')
            # Handle Duo push logins that happen inside the Duo iframe
            page.wait_for_selector('#duo_iframe', timeout=self.timeout(10))
            duo_frame = page.frames[1]  # Main frame is 1st, Duo is 2nd
            duo_frame.wait_for_load_state(state='networkidle')
            duo_push_selector = 'button:has-text("Push")'
            duo_push_button = duo_frame.wait_for_selector(duo_push_selector, timeout=self.timeout(10))
            # Click the Duo "Send Me a Push" button if it is enabled
            if duo_push_button.is_enabled():
                duo_push_button.click()
            page.wait_for_selector('#search_area', timeout=self.timeout(60))
        except Exception as e:
            print(str(e))
            raise Exception('Failed to log in to Hein.')
        finally:
            page.close()

    def login_westlaw(self, westlaw_username, westlaw_password):
        page = self.firefox.new_page()
        try:
            page.goto(self.WESTLAW_SIGN_IN_URL)
            page.fill('#Username', westlaw_username)
            page.fill('#Password', westlaw_password)
            page.click('#SignIn')
            page.wait_for_selector('#searchButton')
        except Exception as e:
            print(str(e))
            raise Exception('Failed to log in to Westlaw.')
        finally:
            page.close()
        self._configure_westlaw()

    def login_ssrn(self, ssrn_username, ssrn_password):
        page = self.firefox.new_page()
        try:
            page.goto(self.SSRN_SIGN_IN_URL)
            try:
                # Click the "Accept all cookies" button if it appears
                page.click('#onetrust-accept-btn-handler', timeout=self.timeout(10))
            except Exception as e:
                print(str(e))
                # Just ignore failures because they may remove this
                # button and just allow normal signing in
                pass
            page.fill('input[name="input-email"]', ssrn_username)
            page.fill('input[name="input-pass"]', ssrn_password)
            page.click('#signinBtn')
            page.wait_for_selector('.leftmenuTD', timeout=self.timeout(10))
        except Exception as e:
            print(str(e))
            raise Exception('Failed to log in to SSRN.')
        finally:
            page.close()

    def login(
            self,
            hein_username, hein_password,
            westlaw_username, westlaw_password,
            ssrn_username, ssrn_password):
        '''Logs in to the database services.

        Using the BrowserContext, navigates to the log in urls
        for Westlaw, Hein, etc. and logs in. In some cases,
        it will also wait for the user to accept a Duo/2FA prompt.
        '''
        if not self.all_authenticated:
            self.firefox.close()
            self._firefox = None
        self.login_hein(hein_username, hein_password)
        self.login_westlaw(westlaw_username, westlaw_password)
        self.login_ssrn(ssrn_username, ssrn_password)

    def _configure_westlaw(self):
        '''Configures Westlaw session.

        Makes adjustments to the Westlaw front-end to configure
        it for the session. This sets the jurisdiction to
        "All State & Federal".
        '''
        page = self.firefox.new_page()
        try:
            page.goto(self.WESTLAW_SEARCH_URL)
            page.click('#jurisdictionId')
            page.click('#co_clearSelectedJurisdictionsBtn')
            page.check('#co_state_all')
            page.check('#co_fed_all')
            page.click('#co_jurisdictionSave')
            page.close()
        except Exception as e:
            print(str(e))
        finally:
            page.close()

    def _hein_search(self, page, search_term):
        '''Searches Hein for a search_term.

        :param page: The page to use for search
        :type page: Page
        :param search_term: The search_term to search for
        :type search_term: str
        '''
        page.goto(self.HEIN_SEARCH_URL)
        search_query = 'citation:{}'.format(search_term)
        page.fill('#full_text_terms', search_query)
        page.click('#sendit_full_text:visible i')
        page.wait_for_selector('#page_content')
        if (page.query_selector('#page_content:has-text("No matching results")')
                or page.query_selector('#page_content:has-text("Citation Not Found")')
                or page.query_selector('#page_content:has-text("could not be found.")')):
            raise NotFoundError

    def _westlaw_search(self, page, url, search_term):
        '''Searches Westlaw for a search_term.

        A search for Westlaw that is general across source types
        by allowing you to specify a particular search url (e.g.,
        the appropriate search page for Cases or for Statutes)
        :param page: The page to use for search
        :type page: Page
        :param url: The url to input the search term
        :type url: str
        :param search_term: The search_term to search for
        :type search_term: str
        '''
        page.goto(url)
        page.fill('#searchInputId', search_term)
        page.click('#searchButton')
        try:
            page.wait_for_selector('#co_docHeader #title', timeout=self.timeout(10))
        except Exception as e:
            print(str(e))
            raise NotFoundError

    def _hein_download(self, a_tag, project, filename):
        '''Downloads a Hein source.

        Hein's download functionality is a bit strange with Playwright.
        It doesn't operate like the page.expect_download() normally
        does, so this function takes the href attribute on the download
        button and opens it in a new page, which triggers a download
        properly.
        :param project: The project it belongs to
        :type project: Project
        :param a_tag: The <a> tag of the file to download
        :type a_tag: ElementHandle
        :param filename: The filename to save the result as
        :type filename: str
        :returns: The filepath of the download
        :rtype: {str}
        '''
        new_page = self.firefox.new_page()
        try:
            a_href = a_tag.get_attribute('href')
            with new_page.expect_download(timeout=self.timeout(20)) as download_info:
                new_page.goto(self.HEIN_BASE_URL + a_href)
            download = download_info.value
            download_path = project.save_pull_path(filename, 'pdf')
            download.save_as(download_path)
            download.path()
            utils.remove_first_page(download_path)
        except Exception as e:
            print(str(e))
            return None
        else:
            return download_path
        finally:
            new_page.close()

    def _westlaw_download(self, page, project, filename):
        '''Downloads a Westlaw source.

        Takes the present page on Westlaw and downloads the source,
        either as an Original Image (if it's available) or using the
        download option.

        Note: As of 3/27/2021, it is not possible to download Original
        Image files from Westlaw due to a bug in Chrome
        (https://bugs.chromium.org/p/chromium/issues/detail?id=761295)
        that prevents the browser from being able to load pdf
        content-types in headless mode. As a workaround, we will use
        Firefox in headless mode to grab sources from Hein, Westlaw,
        and SSRN. Unfortunately, Playwright does not support loading
        extensions in Firefox easily
        (https://github.com/microsoft/playwright/issues/2644), so now
        we have to use a mix of Chrome (to load extensions for clean
        website screenshots) and Firefox (to pull Hein, Westlaw, SSRN).
        :param page: The page to use for search
        :type page: Page
        :param project: The project it belongs to
        :type project: Project
        :param filename: The filename to save the result as
        :type filename: str
        :returns: The downloaded filepath
        :rtype: {str}
        '''
        save_filepath = project.save_pull_path(filename, 'pdf')
        # Check to see if the source has an Original Image...
        original_img_link = page.query_selector('a:has-text("Original Image")')
        # ...if it does, download the original image
        if original_img_link:
            a_tag = page.query_selector('a:has-text("​Original Image")')
            page.eval_on_selector('a:has-text("​Original Image")', 'link => link.setAttribute("download", "download")')
            with page.expect_download(timeout=self.timeout(20)) as download_info:
                a_tag.click()
            download = download_info.value
            download.save_as(save_filepath)
            download.path()
        # ...if it does not, use the download button
        else:
            page.click('#deliveryLink1')
            # Set the download preferences
            page.click('#co_deliveryOptionsTab1')
            page.select_option('#co_delivery_format_fulltext', value='Pdf')
            page.click('#co_deliveryOptionsTab2')
            page.uncheck('#coid_chkDdcLayoutCoverPage')
            # Click the final download buttons
            page.click('#co_deliveryDownloadButton')
            with page.expect_download(timeout=self.timeout(20)) as download_info:
                page.click('#coid_deliveryWaitMessage_downloadButton')
            download = download_info.value
            download.save_as(save_filepath)
            download.path()

    def pull(self, source, project):
        '''Pulls a source.

        Runs the playwright browser to attempt to find the source.
        If found, downloads the source. Returns the result of the
        pulling.
        :param source: The source to pull
        :type source: Source
        :param source: The project that the source belows to
        :type source: Project
        :returns: The result of the pull
        :rtype: {Result}
        '''
        result = Result.NO_ATTEMPT

        # ==============================================================
        # BOOK
        # ==============================================================
        # Books pulling shouldn't be attempted.
        # ==============================================================
        if source.kind == Kind.BOOK:
            result = Result.NO_ATTEMPT

        # ==============================================================
        # WEBSITE
        # ==============================================================
        # Websites should get downloaded directly from their URL.
        # ==============================================================
        if source.kind == Kind.WEBSITE:
            page = self.chrome.new_page()
            try:
                page.goto(source.short_cite, wait_until='load')
                # Check if the browser's PDF viewer is open and download
                # the file directly if so
                if page.query_selector('embed[type="application/pdf"]'):
                    pdf_path = project.save_pull_path(source.filename, 'pdf')
                    urlretrieve(source.short_cite, pdf_path)
                # Otherwise, take a full page screenshot of the page
                else:
                    img_path = project.save_pull_path(source.filename, 'png')
                    page.screenshot(full_page=True, path=img_path)
                    utils.img2pdf(img_path)
                    os.remove(img_path)
            except NotFoundError:
                result = Result.NOT_FOUND
            except Exception as e:
                print(str(e))
                result = Result.FAILURE
            else:
                result = Result.SUCCESS
            finally:
                page.close()

        # ==============================================================
        # SSRN
        # ==============================================================
        # SSRN articles should get downloaded from their URL, but using
        # the Download This Paper button on the paper.
        # ==============================================================
        if source.kind == Kind.SSRN:
            page = self.firefox.new_page()
            try:
                page.goto(source.short_cite)
                with page.expect_download(timeout=self.timeout(10)) as download_info:
                    page.click('text=Download This Paper')
                download = download_info.value
                download_path = project.save_pull_path(source.filename, 'pdf')
                download.save_as(download_path)
                download.path()
            except NotFoundError:
                result = Result.NOT_FOUND
            except Exception as e:
                print(str(e))
                result = Result.FAILURE
            else:
                result = Result.SUCCESS
            finally:
                page.close()

        # ==============================================================
        # JOURNAL
        # ==============================================================
        # Journals should get pulled from Hein. This should pull both
        # the full article and the table of contents for its issue. If
        # the article is in the first issue, also download the table
        # of contents for the second issue so pagination can be checked.
        #
        # The Contents sidebar on Hein can be structured a few ways:
        # 1. All of the Table of Contents sections appear at the top,
        #    with the Issues later on (see "119 Harv. L. Rev. 32")
        #    sometimes labeled as "Table of Contents - Issue X" or
        #    "Table of Contents--Issue X" (no set format)
        # 2. The Table of Contents section for the Issue is directly
        #    below its header (see "71 Stan. L. Rev. 1") sometimes
        #    labeled as "Table of Contents" or "Table of Contents -
        #    Issue 1" (no set format)
        # 3. Maybe other ways I haven't seen, but those won't be handled
        # ==============================================================
        if source.kind == Kind.JOURNAL:
            page = self.firefox.new_page()
            try:
                self._hein_search(page, source.short_cite)
                # Create variables that will eventually keep track of
                # the download paths, as well as the issue's Table of
                # Contents format and where it was found
                toc_method = ''  # one of: (top|under|global|'')
                article_path = ''
                toc1_path = ''
                toc2_path = ''
                toc1_li = None
                toc2_li = None
                # ------------------------------------------------------
                # Get the issue information
                # ------------------------------------------------------
                try:
                    page.wait_for_selector('.atocpage.sectionhighlight', timeout=self.timeout(10))
                except Exception:
                    raise NotFoundError
                issue_ul = page.evaluate_handle('''
                    document
                        .querySelector('.atocpage.sectionhighlight')
                        .closest('ul.dropdown-submenu')
                ''').as_element()
                issue_header_li = page.evaluate_handle('''
                    document
                        .querySelector('.atocpage.sectionhighlight')
                        .closest('ul.dropdown-submenu')
                        .parentElement
                        .previousElementSibling
                ''').as_element()
                issue_header_li_text = issue_header_li.inner_text()
                match = re.search('Issue ([0-9]+)', issue_header_li_text)
                issue_number = match.group(1)
                # ------------------------------------------------------
                # Get the article
                # ------------------------------------------------------
                article_li = page.query_selector('.atocpage.sectionhighlight')
                article_print_a = article_li.query_selector('a.contents_print')
                article_path = self._hein_download(
                    article_print_a, project,
                    '{}-article'.format(source.filename))
                # ------------------------------------------------------
                # Get the first Table of Contents
                # ------------------------------------------------------
                # Check if Table of Contents is right below the issue
                # in the sidebar (e.g., "71 Stan. L. Rev. 1")
                toc1_li = issue_ul.query_selector('li:has-text("Table of Contents")')
                if toc1_li:
                    toc_method = 'under'
                # Check if the Table of Contents for the issue is at
                # the top of the sidebar (e.g., "119 Harv. L. Rev. 32")
                if not toc1_li:
                    matching_issue_lis = page.query_selector_all('#contents-show li:has-text("Issue {}")'.format(issue_number))
                    for li in matching_issue_lis:
                        if 'Table of Contents' in li.inner_text():
                            toc1_li = li
                            toc_method = 'top'
                            break
                # Check if there is only one global Table of Contents
                if not toc1_li:
                    toc1_li = page.query_selector('#contents-show li:has-text("Table of Contents")')
                    if toc1_li:
                        toc_method = 'global'
                toc1_print_a = toc1_li.query_selector('a.contents_print')
                toc1_path = self._hein_download(
                    toc1_print_a, project,
                    '{}-toc1'.format(source.filename))
                # ------------------------------------------------------
                # Get the second Table of Contents (if needed)
                # ------------------------------------------------------
                if issue_number == '1':
                    if toc_method == 'under':
                        issue2_ul = page.evaluate_handle('''
                            document
                                .querySelector('.atocpage.sectionhighlight')
                                .closest('ul.dropdown-submenu')
                                .parentElement
                                .nextElementSibling
                                .nextElementSibling
                        ''').as_element()
                        toc2_li = issue2_ul.query_selector('li:has-text("Table of Contents")')
                    elif toc_method == 'top':
                        matching_issue_lis = page.query_selector_all('#contents-show li:has-text("Issue 2")')
                        for li in matching_issue_lis:
                            if 'Table of Contents' in li.inner_text():
                                toc2_li = li
                    elif toc_method == 'global':
                        pass  # do nothing because there was only one TOC
                    toc2_print_a = toc2_li.query_selector('a.contents_print')
                    toc2_path = self._hein_download(
                        toc2_print_a, project,
                        '{}-toc2'.format(source.filename))
                # ------------------------------------------------------
                # Merge and save the PDFs
                # ------------------------------------------------------
                pdfs = []
                if toc1_path:
                    pdfs.append(toc1_path)
                if toc2_path:
                    pdfs.append(toc2_path)
                if article_path:
                    pdfs.append(article_path)
                utils.merge(pdfs, project.save_pull_path(source.filename, 'pdf'))
                for pdf in pdfs:
                    os.remove(pdf)
            except NotFoundError:
                result = Result.NOT_FOUND
            except Exception as e:
                print(str(e))
                result = Result.FAILURE
            else:
                result = Result.SUCCESS
            finally:
                page.close()

        # ==============================================================
        # STATE
        # ==============================================================
        # State statutes should get pulled from Westlaw. Usually these
        # do not have an Original Image, but the search function
        # handles that for us.
        # ==============================================================
        if source.kind == Kind.STATE:
            page = self.firefox.new_page()
            try:
                self._westlaw_search(
                    page, self.WESTLAW_STATUTES_URL, source.short_cite)
                self._westlaw_download(page, project, source.filename)
            except NotFoundError:
                result = Result.NOT_FOUND
            except Exception as e:
                print(str(e))
                result = Result.FAILURE
            else:
                result = Result.SUCCESS
            finally:
                page.close()

        # ==============================================================
        # FEDERAL
        # ==============================================================
        # Federal statutes should get downloaded from Hein using the
        # 2018 U.S. Code edition.
        # ==============================================================
        if source.kind == Kind.FEDERAL:
            page = self.firefox.new_page()
            try:
                self._hein_search(page, source.short_cite)
                try:
                    page.wait_for_selector(
                        '#page_content:has-text("U.S. Code Citation")',
                        timeout=self.timeout(10))
                except Exception as e:
                    print(str(e))
                    raise NotFoundError
                chosen_edition = None
                # Try to find the 2018 Edition
                chosen_edition = page.query_selector('#page_content a:has-text("2018 Edition")')
                # If there isn't 2018, try to find the 2012 Edition
                if not chosen_edition:
                    chosen_edition = page.query_selector('#page_content a:has-text("2012 Edition")')
                # If there isn't 2018 or 2012, use the top match
                if not chosen_edition:
                    chosen_edition = page.query_selector('#page_content a:has-text("Edition")')
                # Open the chosen edition in the current tab and download
                chosen_edition_href = chosen_edition.get_attribute('href')
                chosen_edition_url = self.HEIN_BASE_URL + chosen_edition_href
                page.goto(chosen_edition_url)
                page.wait_for_selector('.atocpage.sectionhighlight')
                section_print_a = page.query_selector('.atocpage.sectionhighlight a.contents_print')
                self._hein_download(
                    section_print_a, project, source.filename)
            except NotFoundError:
                result = Result.NOT_FOUND
            except Exception as e:
                print(str(e))
                result = Result.FAILURE
            else:
                result = Result.SUCCESS
            finally:
                page.close()

        # ==============================================================
        # SCOTUS
        # ==============================================================
        # SCOTUS cases should get downloaded from Hein, but if they
        # aren't found on Hein (i.e. it's not yet available) then
        # attempt Westlaw. Some SCOTUS cases, e.g. "76 S. Ct. 212",
        # won't be found on Hein because it's in a different reporter.
        # ==============================================================
        short_cite_no_space = source.short_cite.replace(' ', '').lower()
        in_other_reporters = 's.ct' in short_cite_no_space
        if source.kind == Kind.SCOTUS and not in_other_reporters:
            page = self.firefox.new_page()
            try:
                self._hein_search(page, source.short_cite)
                try:
                    page.wait_for_selector(
                        'a:has-text("HeinOnline (PDF version)")',
                        timeout=self.timeout(10))
                except Exception as e:
                    print(str(e))
                    raise NotFoundError
                page.click('a:has-text("HeinOnline (PDF version)")')
                page.wait_for_selector('.atocpage.sectionhighlight')
                section_print_a = page.query_selector('.atocpage.sectionhighlight a.contents_print')
                self._hein_download(
                    section_print_a, project, source.filename)
            except NotFoundError:
                result = Result.NOT_FOUND
            except Exception as e:
                print(str(e))
                result = Result.FAILURE
            else:
                result = Result.SUCCESS
            finally:
                page.close()

        # SCOTUS but found in different reporters, e.g.,
        # "76 S. Ct. 212"; fallback to Westlaw for these or any errors
        if (source.kind == Kind.SCOTUS
                and (in_other_reporters or result != Result.SUCCESS)):
            page = self.firefox.new_page()
            try:
                self._westlaw_search(
                    page, self.WESTLAW_CASES_URL, source.short_cite)
                self._westlaw_download(page, project, source.filename)
            except NotFoundError:
                result = Result.NOT_FOUND
            except Exception as e:
                print(str(e))
                result = Result.FAILURE
            else:
                result = Result.SUCCESS
            finally:
                page.close()

        # ==============================================================
        # NON_SCOTUS
        # ==============================================================
        # Non-SCOTUS cases should get downloaded from Westlaw. Usually
        # these have an Original Image, but the search function handles
        # that for us.
        # ==============================================================
        if source.kind == Kind.NON_SCOTUS:
            page = self.firefox.new_page()
            try:
                self._westlaw_search(
                    page, self.WESTLAW_CASES_URL, source.short_cite)
                self._westlaw_download(page, project, source.filename)
            except NotFoundError:
                result = Result.NOT_FOUND
            except Exception as e:
                print(str(e))
                result = Result.FAILURE
            else:
                result = Result.SUCCESS
            finally:
                page.close()

        return result


class NotFoundError(Exception):
    pass


class NoAttemptError(Exception):
    pass
