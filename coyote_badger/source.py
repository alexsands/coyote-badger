import re
from enum import Enum

from urlextract import URLExtract

from coyote_badger.utils import clean_filename

extractor = URLExtract()


class Header(Enum):
    fn_num = "FN#"
    long_cite = "Citation"
    short_cite = "Short Cite"
    filename = "Filename"
    library = "Library"
    has_book = "Book Available?"
    result = "Source Puller Result"
    kind = "Source Type"


class Kind(Enum):
    BOOK = "Book"
    WEBSITE = "Website"
    SSRN = "SSRN"
    JOURNAL = "Journal"
    STATE = "State Statute"
    FEDERAL = "Federal Statute"
    SCOTUS = "SCOTUS Case"
    NON_SCOTUS = "Non-SCOTUS Case"
    UNKNOWN = "Unknown"


class Result(Enum):
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    SUCCESS = "Success"
    NO_ATTEMPT = "No Attempt"
    NOT_FOUND = "Not Found"
    FAILURE = "Failure"


class Source(object):
    def __init__(
        self,
        fn_num=None,
        long_cite=None,
        short_cite=None,
        filename=None,
        library=None,
        has_book=None,
        kind=None,
        result=None,
    ):
        # Public properties that are used in the Source sheet
        self.fn_num = fn_num
        self.long_cite = long_cite or ""
        self.short_cite = short_cite or ""
        self.filename = clean_filename(filename or "")
        self.library = library or ""
        self.has_book = has_book or ""
        self.kind = kind
        self.result = result
        # Hidden properties that are not shown in the Source sheet
        self._is_westlaw_reporter = self.infer_westlaw_reporter()

    @property
    def kind(self):
        return self._kind

    @kind.setter
    def kind(self, value):
        if isinstance(value, Kind):
            self._kind = value
        else:
            try:
                self._kind = Kind(value)
            except ValueError:
                self._kind = self.infer_kind()

    @property
    def result(self):
        return self._result

    @result.setter
    def result(self, value):
        if isinstance(value, Result):
            self._result = value
        else:
            try:
                self._result = Result(value)
            except ValueError:
                self._result = Result.NOT_STARTED

    def infer_kind(self):
        """Predicts the source's type.

        Given what we have about the citation (it's long cite,
        short cite, book availability, etc.), this function predicts
        what type of source it is.
        :returns: The kind of the source
        :rtype: {Kind}
        """
        long_cite_lower = self.long_cite.lower()
        long_cite_no_periods = self.long_cite.replace(".", "")

        # If we already have it marked as a book, use that.
        if self.has_book or self.library:
            return Kind.BOOK

        # If it contains a URL, mark it as a website. Even if it's
        # something else, the puller will be able to download the
        # source at the URL if it thinks it is a website.
        if extractor.has_urls(self.long_cite):
            url = extractor.find_urls(self.long_cite)[0]
            if "ssrn.com" in url:
                return Kind.SSRN
            else:
                return Kind.WEBSITE

        # If somewhere in the citation we find "## U.S. ##",
        # "## U.S. at ##" or "## S.Ct. ##" (along with minor variations
        # of those forms), it is most likely a SCOTUS case.
        if (
            re.search("[0-9]+ [sS] ?[cC][tT] [0-9]+", long_cite_no_periods)
            or re.search("[0-9]+ U ?S [0-9]+", long_cite_no_periods)
            or re.search("[0-9]+ U ?S at [0-9]+", long_cite_no_periods)
        ):
            return Kind.SCOTUS

        # If somewhere in the citation we find " v. " or "In re" and it
        # wasn't a SCOTUS case, it is most likely a non-SCOTUS case.
        if " v. " in long_cite_lower or "in re " in long_cite_lower:
            return Kind.NON_SCOTUS

        # If somewhere in the citation we find a "## USC ##" format
        # (along with minor variations of that form), it is most likely
        # a federal statute.
        if " u.s.c. " in long_cite_lower or " u.s. code " in long_cite_lower:
            return Kind.FEDERAL
        if re.search("[0-9]+ (.{4,8}) [0-9]+", long_cite_no_periods):
            match = re.search("[0-9]+ (.{4,8}) [0-9]+", long_cite_no_periods)
            if "usc" in match.group(1).lower():
                return Kind.FEDERAL

        # If somewhere in the citation we find a "Stat." or a "§", it
        # is most likely a state statute since we didn't already pick
        # up on the federal statute above.
        if " stat. " in long_cite_lower or "§" in self.long_cite:
            return Kind.STATE

        # If somewhere in the citation we find a "## text ##" format
        # where the text between the numbers is at least 7 characters,
        # the citation also has some commas, and it ends with a year,
        # it is most likely a journal.
        if (
            "," in self.long_cite
            and re.search("\\([0-9]{4}\\)", self.long_cite)
            and re.search("[0-9]+ .{7,}? [0-9]+", self.long_cite)
        ):
            return Kind.JOURNAL

        # Similar to the test for journals, if it has commas and ends
        # in a year but DOESN'T have the "## text ##" format, it might
        # be a book. Since we can't pull books anyways, let's just mark
        # these as Unknown.
        if (
            "," in self.long_cite
            and re.search("\\([0-9]{4}\\)", self.long_cite)
            and not re.search("[0-9]+ .+? [0-9]+", self.long_cite)
        ):
            # return Kind.BOOK
            return Kind.UNKNOWN

        # For everything else, return Unknown so that the puller
        # does not waste its time.
        return Kind.UNKNOWN

    def infer_westlaw_reporter(self):
        """Predicts whether or not the source is from the
        Westlaw Reporter.

        Given the short cite, this function predicts if the short cite
        matches the Westlaw Reporter format (i.e., YYYY WL XX..XXX)
        :returns: Whether or not it is from WL reporter
        :rtype: {boolean}
        """
        short_cite_no_periods = self.short_cite.replace(".", "")
        if re.search("[0-9]{4} WL [0-9]+", short_cite_no_periods):
            return True

    @staticmethod
    def from_json(data):
        """Creates a source from front-end json.

        This method should be used to create a source whenever
        the input data comes from the list of sources on the
        front-end.
        :param data: The json data of the source row
        :type data: dict
        :returns: The created source object
        :rtype: {Source}
        """
        return Source(
            long_cite=data.get(Header.long_cite.name),
            short_cite=data.get(Header.short_cite.name),
            filename=data.get(Header.filename.name),
            kind=data.get(Header.kind.name, Kind.UNKNOWN.value),
            result=data.get(Header.result.name, Result.FAILURE.value),
        )

    def to_json(self):
        """Creates the json response for a source.

        This method converts a source into a json-serializable
        response for the front-end to display.
        :returns: A json-serializable representation of a source
        :rtype: {dict}
        """
        data = {}
        data[Header.long_cite.name] = self.long_cite
        data[Header.short_cite.name] = self.short_cite
        data[Header.filename.name] = self.filename
        data[Header.kind.name] = self.kind.value
        data[Header.result.name] = self.result.value
        return data
