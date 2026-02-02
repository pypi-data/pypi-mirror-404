import logging
import os
import string

from .markdown import MarkdownTree

def page_filename_to_key(filename):
    key = filename.removesuffix(".md")
    # Remove portions of the filename which are not part of the api name
    # e.g. "(Object)" from "Excel.Application(Object)"
    key = key.split("(", 1)[0]
    return key

def camel_to_snake_case(s):
    """anyVariableName -> any_variable_name"""

    snake_s =  "".join(
        [f"_{c.lower()}" if c in string.ascii_uppercase else c for c in s]
    )
    snake_s = snake_s.strip("_")
    return snake_s

class DocPage:

    RESERVED_WORDS = ["and", "class", "from", "import", "property", "or"]

    def __init__(self, markdown_src):
        self.md = markdown_src
        self.md_tree = None
        self.title = None
        self.api_name = None

        self.module_name = None
        self.object_name = None
        self.property_name = None
        self.method_name = None
        
        self.is_object = None
        self.is_collection = None
        self.is_set = None
        self.is_property = None
        self.is_method = None
        self.is_enumeration = None

        self.is_read_only_property = None
        self.has_return_value = None
        self.property_class = None
        self.return_value_class = None

        self.enumeration_values = None

        self.properties = []
        self.parameters = []
        self.methods = []
    
    def process_page(self):
        try:
            self.md_tree  = MarkdownTree(self.md)
        except Exception as e:
            logging.warning("Failed building MarkdownTree, raising an exception.")
            raise(e)
        
        self.title = self.md_tree .front_matter.variables["title"]
        if "api_name" in self.md_tree.front_matter.variables:
            self.api_name = self.md_tree.front_matter.variables["api_name"]
        self.process_title()
        self.process_api_name()

        if self.is_enumeration:
            self.process_enumeration()

        # Retrieve information from the opening paragraph
        # Examples
        # -------------------------------------------
        # A collection of all the **[Worksheet](Excel.Worksheet.md)** objects in the specified or active workbook. Each **Worksheet** object represents a worksheet.
        # Returns a collection of **[ListObject](Excel.ListObject.md)** objects on the worksheet. Read-only **[ListObjects](excel.listobjects.md)** collection.
        # Returns or sets a **String** value that represents the object name.
        # Returns a **[Range](Excel.Range(object).md)** object that represents all the cells on the worksheet (not just the cells that are currently in use).
        # Returns a **Range** object that represents the columns in the specified range.
        # -------------------------------------------
        p = self.md_tree.sections_by_level(1)[0].paragraphs[0].txt
        # Check whether the object is a collection
        self.is_collection = p.startswith("A collection")

        # Get the return type of the property (if any)
        if "Returns" in p:
            property_class = None
            if "**[" in p:
                property_class = p.split("**[", 1)[1].split("]", 1)[0]
            elif "**" in p:
                property_class = p.split("**", 1)[1].split("**", 1)[0]
            if "Returns a collection of" in p and property_class is not None:
                if not property_class.endswith("s"):
                    property_class += "s"
            if property_class is not None:
                if property_class.lower() in ["boolean", "variant", "string", "long", "double", "single", "integer"]:
                    property_class = None
            # If property_class can't be parsed and the property is called `Item`,
            # try to infer the class from the parent object
            if self.property_name is not None:
                if property_class is None and self.property_name.lower() == "item":
                    if self.object_name.endswith("s"):
                        property_class = self.object_name[:-1]
                    elif self.object_name.endswith("Collection"):
                        property_class = self.object_name.removesuffix("Collection")
                    else:
                        logging.warning(f"Unexpected collection name, unable to identify the class of '{self.process_api_name}'.")
            self.property_class = property_class

        # Check whether the property is read only
        if "Returns or sets" in p or "Read/write" in p:
            self.is_read_only_property = False
        else:
            self.is_read_only_property = True

        # Find the parameters of a property.
        # The "Syntax" section should look like this.
        # -------------------------------------------
        # ## Syntax
        # _expression_.**Range** (_Cell1_, _Cell2_)
        # -------------------------------------------
        sections = self.md_tree.sections_by_title("Syntax")
        if len(sections) > 0:
            line = sections[0].paragraphs[0].txt.replace("()", "")
            if "(" in line:
                parameters = line.split("(", 1)[1].split(")", 1)[0]
                parameters = parameters.split(", ")
                parameters = [p.strip(" _`[]*\\").replace("\\_", "_").strip("_ ") for p in parameters]
                for p in parameters:
                    if "," in p:
                        logging.warning(f"Parsing error in '{self.api_name}'. Parameter `{p}` ignored. This is probably due to a formatting error in the source file.")
                        parameters.remove(p)
                    if " " in p:
                        logging.warning(f"Unexpected empty space in parameter '{p}' of '{self.api_name}'. Replacing with `{p.replace(" ", "")}`. This is probably due to a formatting error in the source file.")
                        parameters[parameters.index(p)] = p.replace(" ", "")
                self.parameters = parameters
        
        # Find the return value of a property. The section looks like this:
        # Example
        # -------------------------------------------
        # ## Return value
        # A **[Workbook](Excel.Workbook.md)** object that represents the new workbook.
        # -------------------------------------------
        self.has_return_value = False
        sections = self.md_tree.sections_by_title("Return value")
        if len(sections) > 0:
            self.has_return_value = True
            s = sections[0]
            line = s.paragraphs[0].txt.splitlines()[0]
            if any(word in line.lower() for word in ["nothing", "none", "false"]):
                self.return_value_class = None
            elif "**[" in line:
                self.return_value_class = line.split("**[", 1)[1].split("](")[0]
            elif "**" in line:
                self.return_value_class = line.split("**", 1)[1].split("**", 1)[0]
            elif " " in line.strip():
                logging.warning(f"Unexpected format in 'Return value' section, could not parse '{self.title}': '{line}'")
            else:
                self.return_value_class = line
            if self.return_value_class is not None:
                if self.return_value_class.lower() in ["boolean", "variant", "string", "long", "double", "single", "integer"]:
                    self.return_value_class = None

    def process_title(self):
        if self.title is None:
            self.is_object = None
            self.is_property = None
            self.is_method = None
            self.is_enumeration = None
            return
        else:
            self.is_object = False
            self.is_property = False
            self.is_method = False
            self.is_enumeration = False

        if "object" in self.title:
            self.is_object = True
        elif "property" in self.title:
            self.is_property = True
        elif "method" in self.title:
            self.is_method = True
        elif "enumeration" in self.title:
            self.is_enumeration = True

        try:
            title_split = self.title.split(" ")[0].split(".")
            self.object_name = title_split[0]
            if len(title_split) > 1:
                if title_split[1].lower() != "enumerations":
                    if self.is_property:
                        self.property_name = title_split[1]
                    elif self.is_method:
                        self.method_name = title_split[1]
        except Exception as e:
            logging.error(f"Failed parsing title {self.title}. {e}")

    def process_api_name(self):
        if self.api_name is None:
            return
        api_name_split = self.api_name.split(".")
        self.module_name = api_name_split[0]
    
    def process_enumeration(self):
        """Parse enumeration information. Assumes that the page refers to an enumeration.

        Example: [XlReferenceType enumeration (Excel)](https://learn.microsoft.com/en-gb/office/vba/api/excel.xlreferencetype)
        """

        # Find table paragraph in the first section
        table = None
        for p in self.md_tree.sections_by_level(1)[0].paragraphs:
            if p.is_table:
                try:
                    table = p.table
                except Exception as e:
                    logging.WARNING(f"Failed parsing values table for enumeration {self.api_name}. {e}")
                break
        
        if "Name" not in table.rows[0] or "Value" not in table.rows[0]:
            logging.WARNING(f"Unexpected header for values table for enumeration {self.api_name}.")
            return
        
        self.enumeration_values = {}
        for r in table.rows[1:]:
            key = r[0].strip("*")
            value = r[1]
            if value.lstrip("-").isnumeric():
                if int(value) == float(value):
                    value = int(value)
                else:
                    value = float(value)
            self.enumeration_values[key] = value
    
    def parent_object_key(self):
        if (self.module_name and self.object_name) is None:
            return None
        return ".".join([self.module_name, self.object_name]).lower()
    
    def to_dict(self):
        return {
            "title": self.title,
            "module_name": self.module_name,
            "object_name": self.object_name,
            "property_name": self.property_name,
            "method_name": self.method_name,
            "is_object": self.is_object,
            "is_collection": self.is_collection,
            "is_set": self.is_set,
            "is_method": self.is_method,
            "is_property": self.is_property,
            "is_enumeration": self.is_enumeration,
            "api_name": self.api_name,
            "is_collection": self.is_collection,
            "is_read_only_property": self.is_read_only_property,
            "parent object key": self.parent_object_key(),
            "property_class": self.property_class,
            "return_value_class": self.return_value_class,
            "enumeration_values": self.enumeration_values,
            "properties": [page.title for page in self.properties],
            "parameters": self.parameters,
            "methods": [page.title for page in self.methods],
        }
    
    def to_python(self):
        """Return source code of a python class based on the page"""

        if self.is_enumeration:
            code = []
            code.append(f"# {self.object_name} enumeration")
            for key, value in self.enumeration_values.items():
                if type(value) == str:
                    value = f"\"{value}\""
                code.append(f"{key} = {value}")
            code.append("")
            return "\n".join(code)

        if not self.is_object:
            return None

        code = []
        if self.object_name == "Application":
            code.append(f"class {self.object_name}:")
            code.append(f"")
            code.append(f"    def __init__(self, application=None):")
            code.append(f"        if application is None:")
            code.append(f"            self.com_object = win32com.client.gencache.EnsureDispatch(\"{self.module_name}.Application\")")
            code.append(f"        else:")
            code.append(f"            self.com_object = application")
            code.append(f"")
        else:
            code.append(f"class {self.object_name}:")
            code.append(f"")
            code.append(f"    def __init__(self, {self.object_name.lower()}=None):")
            code.append(f"        self.com_object= {self.object_name.lower()}")
            code.append(f"")

        code += self.to_python_properties()
        code += self.to_python_methods()
        code.append("")
        return "\n".join(code)

    def parameters_code(self):
        """Return code to include parameters as arguments of a property or method"""
        return "=None, ".join(self.parameters) + "=None"

    def to_python_arguments_expansion(self):
        """Return python code to expand arguments for COM calls"""
        return f"        arguments = com_arguments([unwrap(a) for a in [{", ".join(self.parameters)}]])"

    def to_python_property_getter(self):
        """Return python code for getter and setter of the property"""
        if not self.is_property:
            logging.warning(f"Property '{self.title}' ignored when exporting getter for '{self.object_name}', because it is not a property.")
            return []
        
        if self.property_name in self.RESERVED_WORDS:
            logging.warning(f"Property '{self.title}' ignored when exporting getter for '{self.object_name}', because it is a reserved word in Python.")
            return []
        
        code = []
        # Getter method - no arguments
        if len(self.parameters) == 0 or not self.is_read_only_property:
            if self.property_class is not None:
                code.append("    @property")
                code.append(f"    def {self.property_name}(self):")
                code.append(f"        return {self.property_class}(self.com_object.{self.property_name})")
            else:
                code.append("    @property")
                code.append(f"    def {self.property_name}(self):")
                code.append(f"        return self.com_object.{self.property_name}")
            code.append(f"")
        # Getter method - with arguments
        else:
            code.append(f"    def {self.property_name}(self, {self.parameters_code()}):")
            code.append(self.to_python_arguments_expansion())
            if self.property_class is not None:
                code.append(f"        if hasattr(self.com_object, \"Get{self.property_name}\"):")
                code.append(f"            return {self.property_class}(self.com_object.Get{self.property_name}(*arguments))")
                code.append(f"        else:")
                code.append(f"            return {self.property_class}(self.com_object.{self.property_name}(*arguments))")
            else:
                code.append(f"        if hasattr(self.com_object, \"Get{self.property_name}\"):")
                code.append(f"            return self.com_object.Get{self.property_name}(*arguments)")
                code.append(f"        else:")
                code.append(f"            return self.com_object.{self.property_name}(*arguments)")
            code.append(f"")

        return code
        
    def to_python_property_setter(self):
        """Return python code for setter of the property"""
        if not self.is_property:
            logging.info(f"Property '{self.title}' ignored when exporting setter for '{self.object_name}', because it is not a property.")
            return []
        
        # If the property is editable, it must have a setter method.
        code = []
        if not self.is_read_only_property:
            code.append(f"    @{self.property_name}.setter")
            code.append(f"    def {self.property_name}(self, value):")
            code.append(f"        self.com_object.{self.property_name} = value")
            code.append("")

        return code

    def to_python_property_aliases(self):
        """Return python code of lower case aliases if the DocPage is a property"""

        if not self.is_property:
            logging.info(f"Property '{self.title}' ignored when exporting aliases for '{self.api_name}', because it is not a property.")
            return []

        # Don't create lower case alias for reserved words in Python
        # E.g. `Access.BoundObjectFrame.Class`
        if self.property_name.lower() in self.RESERVED_WORDS:
            logging.info(f"Aliases for property '{self.property_name}' of '{self.api_name}' ignored, because it is a reserved word in Python.")
            return []
        
        aliases = []
        if self.property_name != self.property_name.lower():
            aliases.append(self.property_name.lower())
        if self.property_name.lower() != camel_to_snake_case(self.property_name):
            aliases.append(camel_to_snake_case(self.property_name))

        code = []
        for alias in aliases:
            # Getter method
            if len(self.parameters) == 0 or not self.is_read_only_property:
                code.append(f"    @property")
                code.append(f"    def {alias}(self):")
                code.append(f"        \"\"\"Alias for {self.property_name}\"\"\"")
                code.append(f"        return self.{self.property_name}")
            else:
                code.append(f"    def {alias}(self, {self.parameters_code()}):")
                code.append(f"        \"\"\"Alias for {self.property_name}\"\"\"")
                code.append(f"        arguments = [{", ".join(self.parameters)}]")
                code.append(f"        return self.{self.property_name}(*arguments)")
            code.append(f"")

            # Setter method
            if not self.is_read_only_property:
                code.append(f"    @{alias}.setter")
                code.append(f"    def {alias}(self, value):")
                code.append(f"        \"\"\"Alias for {self.property_name}.setter\"\"\"")
                code.append(f"        self.{self.property_name} = value")
                code.append(f"")

        # Add `__call__` method for `item` properties
        if self.property_name.lower() == "item" and len(self.parameters) > 0:
            code.append(f"    def __call__(self, {self.parameters_code()}):")
            code.append(f"        return self.Item({", ".join(self.parameters)})")
            code.append("")

        return code

    def to_python_properties(self):
        """Return python code for all properties of the object"""
        code = []
        for p in self.properties:
            if p.property_name is None:
                logging.info("Property '{}' ignored when exporting '{}', because property_name is None.".format(p.title, self.title))
                continue

            code += p.to_python_property_getter()
            code += p.to_python_property_setter()
            code += p.to_python_property_aliases()

        return code
    
    def to_python_method_function(self, parent_is_collection=False):
        """Return python code for a single method of the object

        Example output for method that returns sets or collections:
        ```python
        def FullSeriesCollection(self, Index=None):
            if Index is None:
                return FullSeriesCollection(self.com_object.FullSeriesCollection(com_arguments([None])[0]))
            else:
                return FullSeriesCollection(self.com_object.FullSeriesCollection(com_arguments([None])[0])).Item(Index)
        ```

        Example output without arguments:
        ```python
        def Refresh(self):
            self.com_object.Refresh()
        ```

        Example output with arguments:
        ```python
        def GetChartElement(self, x=None, y=None, ElementID=None, Arg1=None, Arg2=None):
            arguments = com_arguments([unwrap(a) for a in [x, y, ElementID, Arg1, Arg2]])
            self.com_object.GetChartElement(*arguments)
        ```
        """
        
        if not self.is_method:
            logging.info(f"Method '{self.title}' ignored when exporting for '{self.object_name}', because it is not a method.")
            return []
        
        code = []
        if self.method_name == self.return_value_class \
        and len(self.parameters) == 1:
            code.append(f"    def {self.method_name}(self, Index=None):")
            code.append(f"        if Index is None:")
            code.append(f"            return {self.return_value_class}(self.com_object.{self.method_name}(com_arguments([None])[0]))")
            code.append(f"        else:")
            code.append(f"            return {self.return_value_class}(self.com_object.{self.method_name}(com_arguments([None])[0])).Item(Index)")
            code.append("")
            return code
        
        if len(self.parameters) == 0:
            code.append(f"    def {self.method_name}(self):")
            code_line = f"self.com_object.{self.method_name}()"
        else:
            code.append(f"    def {self.method_name}(self, {self.parameters_code()}):")
            code.append(self.to_python_arguments_expansion())
            code_line = f"self.com_object.{self.method_name}(*arguments)"
        if self.has_return_value:
            if self.return_value_class is not None:
                code_line = f"{self.return_value_class}({code_line})"
            # Certain methods of a collection can only return certain types
            # e.g. `Worksheets.Add`` returns a `Worksheet`
            # `.startswith("Open") is for methods like `Workbooks.OpenText`
            elif parent_is_collection and (self.method_name == "Add" or self.method_name.startswith("Open")):
                code_line = f"{self.object_name[:-1]}({code_line})"
        code_line = "return " + code_line
        code_line = " "*8 + code_line
        code.append(code_line)
        code.append("")

        return code

    def to_python_method_function_aliases(self):

        code = []
        if self.method_name.lower() in self.RESERVED_WORDS:
            logging.info(f"Aliases for method '{self.method_name}' of '{self.object_name}' ignored, because it is a reserved word in Python.")
            return code
        
        aliases = []
        if self.method_name != self.method_name.lower():
            aliases.append(self.method_name.lower())
        if self.method_name.lower() != camel_to_snake_case(self.method_name):
            aliases.append(camel_to_snake_case(self.method_name))

        for alias in aliases:
            if len(self.parameters) == 0:
                code.append(f"    def {alias}(self):")
                code.append(f"        \"\"\"Alias for {self.method_name}\"\"\"")
                code.append(f"        return self.{self.method_name}()")
            else:
                code.append(f"    def {alias}(self, {self.parameters_code()}):")
                code.append(f"        \"\"\"Alias for {self.method_name}\"\"\"")
                code.append(f"        arguments = [{", ".join(self.parameters)}]")
                code.append(f"        return self.{self.method_name}(*arguments)")
            code.append("")
        
        # Add `__call__` method for `item` methods
        if self.method_name.lower() == "item" and len(self.parameters) > 0:
            code.append(f"    def __call__(self, {self.parameters_code()}):")
            code.append(f"        return self.Item({", ".join(self.parameters)})")
            code.append("")

        return code
    
    def to_python_methods(self):
        """Return python code for all methods of the object"""
        code = []
        for m in self.methods:
            code += m.to_python_method_function(parent_is_collection=self.is_collection)
            code += m.to_python_method_function_aliases()
        return code

class VbaDocs:

    def __init__(self):
        self.pages = dict()

    def read_directory(self, path):
        with os.scandir(path) as it:
            for entry in it:
                if entry.is_file():
                    print(f"Parsing {entry.name}...")
                    page_key = page_filename_to_key(entry.name).lower()
                    if page_key in ["word.break", "word.global"]:
                        logging.info("Ignoring page '{}', because it conflicts with a Python keyword.".format(entry.name))
                    elif page_key in ["access.report.circle", "access.report.line"]:
                        logging.info("Ignoring page '{}', because non-scalar arguments are not implemented.".format(entry.name))
                    elif "-" in page_key:
                        logging.info("Ignoring page '{}', because the object name includes a dash.".format(entry.name))
                    else:
                        self.pages[page_key] = DocPage(open(entry, "rt", encoding="utf8").read())
    
    def process_pages(self):
        pages_to_remove = []
        for page_key, page in self.pages.items():
            try:
                page.process_page()
                # Remove pages without `api_name`
                if page.api_name is None:
                    logging.warning(f"Attribute `api_name` not found for {page_key}, ignoring.")
                    pages_to_remove.append(page_key)
            except Exception as e:
                logging.error(f"Failed processing page: '{page_key}'. {e}")
        for key in pages_to_remove:
            del self.pages[key]
        # Populate properties and methods of objects
        for page_key, page in self.pages.items():
            parent_object_key = page.parent_object_key()
            if parent_object_key is not None:
                if page.is_property:
                    if parent_object_key in self.pages:
                        self.pages[parent_object_key].properties.append(page)
                    else:
                        logging.warning(f"Parent object '{parent_object_key}' for property '{page_key}' not found.")
                elif page.is_method:
                    if parent_object_key in self.pages:
                        self.pages[parent_object_key].methods.append(page)
                    else:
                        logging.warning(f"Parent object '{parent_object_key}' for method '{page_key}' not found.")
            else:
                if page.is_property or page.is_method:
                    logging.warning(f"Page'{page_key}' is a property or method, but the key of the parent object of is None.")
        
        # Find sets
        # In this context, a set is an object similar to a collection.
        # A set allows to retrieve part of the items of a collection.
        # E.g. Excel.FullSeriesCollection is a set, Excel.SeriesCollection is a collection.
        # All Series in Excel.SeriesCollection are in Excel.FullSeriesCollection, but not vice versa.
        # [FullSeriesCollection object (Excel)](https://learn.microsoft.com/en-gb/office/vba/api/Excel.FullSeriesCollection)
        # [SeriesCollection object (Excel)](https://learn.microsoft.com/en-gb/office/vba/api/excel.seriescollection)
        for page_key, page in self.pages.items():
            page.is_set = False
            if page.is_collection:
                continue
            has_item_method = False
            has_add_method = False
            for m in page.methods:
                if m.method_name is None:
                    logging.warning(f"{m.api_name} is supposed to be a method, but has no method name. Title {m.title}")
                    continue
                if m.method_name.lower() == "item":
                    has_item_method = True
                if m.method_name.lower() == "add":
                    has_add_method = True
            if has_item_method and not has_add_method:
                page.is_set = True

        # Remove invalid class types
        for page in self.pages.values():
            if page.property_class is not None:
                property_class_key = f"{page.module_name}.{page.property_class}".lower()
                if property_class_key not in self.pages:
                    logging.warning(f"Removing 'property_class' from {page.api_name}. Class '{page.property_class}' not found.")
                    page.property_class = None
                elif self.pages[property_class_key].is_enumeration:
                    logging.info(f"Removing 'property_class' from {page.api_name}. '{page.property_class}' is an enumeration.")
                    page.property_class = None
                    
            if page.return_value_class is not None:
                if f"{page.module_name}.{page.return_value_class}".lower() not in self.pages:
                    logging.warning(f"Removing 'return_value_class' from {page.api_name}. Class '{page.return_value_class}' not found.")
                    page.return_value_class = None

        self.apply_manual_adjustments()
    
    def to_dict(self):
        dictionaries = [page.to_dict() for page in self.pages.values()]
        keys_and_values = zip(self.pages.keys(), dictionaries)
        return {key: value for key, value in keys_and_values}

    def apply_manual_adjustments(self):
        # Add parameters for Cell properties, whose parameters are not properly imported
        for p in self.pages.values():
            if p.property_name == "Cells" and len(p.parameters) == 0:
                p.parameters = ["RowIndex", "ColumnIndex"]

    def to_python(self, application):
        code = [
            "from . import com_arguments, unwrap",
            "from .office import *",
            "",
            "import win32com.client",
            "",]
        for page_key, page in self.pages.items():
            if page.module_name is None:
                continue
            if page.module_name.lower() != application.lower():
                continue

            try:
                page_code = page.to_python()
            except Exception as e:
                logging.warning(f"Can't export '{page_key}' to python code. {e}")
            else:
                if page_code is not None:
                    code.append(page_code)
        return "\n".join(code)
    
    def apply_manual_adjustments(self):
        # Add parameters for Cell properties, whose parameters are not properly imported
        for p in self.pages.values():
            if p.property_name == "Cells" and len(p.parameters) == 0:
                p.parameters = ["RowIndex", "ColumnIndex"]
