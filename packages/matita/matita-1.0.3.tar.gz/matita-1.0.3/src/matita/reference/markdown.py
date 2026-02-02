class MarkdownTree:

    def __init__(self, raw_txt):
        self.raw = raw_txt
        split = self.raw.split("---\n", 2)
        body = split[2]
        self.front_matter = FrontMatter(split[1])
        self.sections = parse_body(body)
    
    def sections_by_level(self, level):
        """Return all sections at a certain level in a list."""
        section_level = []
        for s in self.sections:
            if s.level == level:
                section_level.append(s)
        return section_level

    def sections_by_title(self, txt):
        """Return sections with txt in the title."""
        sections = []
        for s in self.sections:
            if txt in s.title:
                sections.append(s)
        return sections
        
class FrontMatter:

    def __init__(self, txt):
        self.raw = txt
        self.variables = {}

        txt = txt.split(":")
        splits = [txt[0]]
        for i in range(1, len(txt)):
            splits = splits.copy() + txt[i].rsplit("\n", 1)
        
        for i in range(0, len(splits) - 2, 2):
            key = splits[i]
            value = splits[i+1].lstrip("\n -")
            self.variables[key] = value

class Section:

    def __init__(self, title, paragraphs, level=0):
        self.title = title
        self.paragraphs = paragraphs
        self.level = level

class Paragraph:

    def __init__(self, txt):
        self.txt = txt
        self._table = None
    
    def __str__(self):
        return self.txt

    @property
    def is_table(self):
        # A single line can't be a table
        if "\n" not in self.txt:
            return False
        #If each line of a paragraph starts with '|', it is a table.
        for line in self.txt.splitlines():
            if not line.startswith("|"):
                return False
        return True

    @property
    def table(self):
        if not self._table is None:
            return self._table
        if not self.is_table:
            return None
        self._table = Table(self.txt)
        return self._table

class Table:

    def __init__(self, txt):
        self.txt = txt
        rows = txt.splitlines()
        # Ignore the second line, which only includes dashes
        rows = [rows[0]] + rows[2:]
        rows = [row.split("|")[1:-1] for row in rows]
        rows = [[cell.strip() for cell in row] for row in rows]
        self.rows = rows
    
    def __str__(self):
        return self.txt

def parse_body(txt, level=0):
    """Return a list of sections"""

    txt = "\n" + txt.strip("\n ")
    if "\n#" in txt:
        parsed_body = []
        # I want a single newline at the beginning of the text
        split = txt.split("\n#")
        # If the text starts without a section title, put it in a section at level 0
        if split[0].strip("\n") != "" and level==0:
            title = ""
            paragraphs = split[0].split("\n\n")
            paragraphs = [p.strip("\n ") for p in paragraphs]
            paragraphs = [Paragraph(p) for p in paragraphs]
            parsed_body.append(Section(title, paragraphs, 0))
            split.pop(0)
        for t in split:
            parsed_body += parse_body(t, level+1)
        return parsed_body
    
    # I don't care about empty sections
    if txt.strip("\n ") == "":
        return []

    split = txt.strip("\n ").split("\n", 1)
    title = split[0]
    paragraphs = split[1].split("\n\n")
    paragraphs = [p.strip("\n ") for p in paragraphs]
    paragraphs = [Paragraph(p) for p in paragraphs]
    return [Section(title, paragraphs, level)]
