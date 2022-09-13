import re
from tempfile import NamedTemporaryFile

from docx2python import docx2python
from openpyxl import load_workbook
from urlextract import URLExtract

from coyote_badger.config import (
    CONVERTER_FOLDER_PREFIX,
    PROJECTS_FOLDER,
    SOURCES_TEMPLATE_FILE,
)
from coyote_badger.project import Project
from coyote_badger.source import Kind, Source
from coyote_badger.utils import clean_string

extractor = URLExtract()


def create_sources_template(doc_file):
    docx = docx2python(doc_file)

    # Gather all the sources, removing duplicate citations
    sources = []
    seen = {}
    footnote_count = 0
    for footnote in docx.footnotes[0][0][0]:
        # Ignore blank footnotes
        if not footnote:
            continue

        # Ignore the footnote metadata
        if footnote.startswith("footnote"):
            continue

        # Now we are looking at actual citation footnotes
        footnote_count += 1
        clean_footnote = footnote.strip(".")  # remove leading/trailing "."
        citations = clean_footnote.split(";")  # split at each citation
        for citation_count, citation in enumerate(citations):
            # Format the FN# to two digits so that 3.04 appears before 3.11
            fn_num = float("{}.{:0=2d}".format(footnote_count, citation_count))
            long_cite = citation

            # ----------------------------------------------------------
            # Clean the long_cite
            # ----------------------------------------------------------
            # Remove any double spaces or weird spacing
            long_cite = clean_string(long_cite)
            long_cite = " ".join(long_cite.split())

            # Remove any commentary that happens in parentheses at
            # the end of a citation. Avoid commentary that has a nested
            # parenthesis because this indicates we might be picking up
            # a year and removing that too, e.g.:
            # ... 374 (2006) ([I]ssues concerning police intent) would
            # remove (2006) if we don't check nested parens.
            if re.search("\\([^\\(]{12,}?\\)$", long_cite):
                long_cite = re.sub("(\\([^\\(]{12,}?\\)$)", "", long_cite)

            # Strip any new whitespace again after cleaning
            long_cite = long_cite.strip()

            # Create the source so we can use it's Kind prediction
            source = Source(fn_num=fn_num, long_cite=long_cite)

            # ----------------------------------------------------------
            # Skip/ignore the duplicate citations
            # ----------------------------------------------------------
            # The obvious case where we've already seen this exactly
            if long_cite in seen:
                continue

            # The case where the citation is just "Id." or a variant
            if long_cite.lower() == "id." or long_cite.lower() == "id":
                continue

            # The case where the citation is just "See id" or a variant
            if long_cite.lower() == "see id." or long_cite.lower() == "see id":
                continue

            # The case where a citation is in the format "Id. at 813"
            if re.search("^[iI][dD].? at [0-9]+[-–—]?[0-9]+.?$", long_cite):
                continue

            # ----------------------------------------------------------
            # Try to predict the short_cite, now that we have a Kind
            # ----------------------------------------------------------
            # Predict short_cite for websites
            if source.kind == Kind.WEBSITE or source.kind == Kind.SSRN:
                if extractor.has_urls(long_cite):
                    source.short_cite = extractor.find_urls(long_cite)[0]

            # Predict short_cite for SCOTUS cases
            if source.kind == Kind.SCOTUS:
                match = re.search("([0-9]+ .{3,}? [0-9]+)", long_cite)
                source.short_cite = match.group(1)

            # Predict short_cite for journals
            if source.kind == Kind.JOURNAL:
                match = re.search("([0-9]+ .{7,}? [0-9]+)", long_cite)
                source.short_cite = match.group(1)

            # For anything else, just leave short_cite blank because
            # there are weird edge cases that aren't worth it. The
            # accuracy needs to be really high, otherwise people gloss
            # over the predicted short_cite without closely checking it.
            # Better to leave blank and have people fill these manually.

            sources.append(source)
            seen[long_cite] = True

    # Create the template file from the sources
    with NamedTemporaryFile(
        dir=PROJECTS_FOLDER, prefix=CONVERTER_FOLDER_PREFIX
    ) as temp_file:
        temp_name = temp_file.name
    project = Project(temp_name, load_workbook(SOURCES_TEMPLATE_FILE))
    project.save_sources(sources)
    return project, sources
