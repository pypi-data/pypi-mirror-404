from enum import StrEnum

CORE_EXPRESSIONS = {
    "ABS": {
        "name": "ABS()",
        "description": "Arithmetic absolute value. If the value is a string, it will be converted to a number.",
        "examples": [
            {"syntax": 'ABS("-3.14")', "returns": 3.14},
            {"syntax": "ABS(-2.718)", "returns": 2.718},
        ],
        "returns": "Number",
    },
    "ACCOUNTID": {
        "name": "ACCOUNTID()",
        "description": "The current account ID",
        "examples": [{"syntax": "ACCOUNTID()", "returns": "UUID"}],
        "returns": "UUID",
    },
    "ADDRESS_TO_LATLNG": {
        "name": "ADDRESS_TO_LATLNG()",
        "description": "Converts an address to latitude and longitude. A point is a tuple with 2 values: latitude and longitude.",
        "examples": [
            {
                "syntax": 'ADDRESS_TO_LATLNG("1600 Amphitheatre Parkway, Mountain View, CA 94043")',
                "returns": "(37.4223878,-122.0841877)",
            }
        ],
        "returns": "Point",
    },
    "AND": {
        "name": "AND()",
        "description": "Returns a YesNo expression",
        "examples": [
            {"syntax": "AND(TRUE, TRUE)", "returns": "Yes"},
            {"syntax": "AND(TRUE, FALSE)", "returns": "No"},
            {"syntax": "AND(FALSE, TRUE)", "returns": "No"},
            {"syntax": "AND(FALSE, FALSE)", "returns": "No"},
        ],
        "returns": "YesNo",
    },
    "ANY": {
        "name": "ANY()",
        "description": "Returns a random choice from a list",
        "examples": [
            {
                "syntax": 'ANY(["a", "b", "c"])',
                "returns": "a random value - a, b, or c",
            },
            {
                "syntax": "ANY([1, 2, 3])",
                "returns": "a random value - 1, 2, or 3",
            },
        ],
        "returns": "Any",
    },
    "AVERAGE": {
        "name": "AVERAGE()",
        "description": "Returns mean of a list",
        "examples": [
            {"syntax": "AVERAGE([1, 2, 3])", "returns": 2},
            {"syntax": "AVERAGE([3.14, 2.71, 1.41])", "returns": 2.42},
        ],
        "returns": "Number",
        "aliases": ["MEAN", "AVG"],
    },
    "BASE_URL": {
        "name": "BASE_URL()",
        "description": "Returns the base URL of the app",
        "examples": [
            {"syntax": "BASE_URL()", "returns": "https://www.appsheet.com/"}
        ],
        "returns": "Text",
    },
    "BOOLEAN": {
        "name": "BOOLEAN() or BOOL()",
        "description": "Converts a value to a boolean",
        "examples": [
            {"syntax": 'BOOLEAN("true")', "returns": "Yes"},
            {"syntax": 'BOOLEAN("false")', "returns": "No"},
            {"syntax": "BOOLEAN(1)", "returns": "Yes"},
            {"syntax": "BOOLEAN(0)", "returns": "No"},
        ],
        "returns": "YesNo",
        "aliases": ["BOOL"],
    },
    "CEILING": {
        "name": "CEILING()",
        "description": "Returns the smallest integer greater than or equal to a number",
        "examples": [
            {"syntax": "CEILING(3.14)", "returns": 4},
            {"syntax": "CEILING(-3.14)", "returns": -3},
        ],
        "returns": "Number",
    },
    "CONCAT": {
        "name": "CONCAT()",
        "description": "Concatenates two or more text strings",
        "examples": [
            {
                "syntax": 'CONCAT("Hello", " ", "World")',
                "returns": "Hello World",
            },
            {
                "syntax": 'CONCAT("Hello", " ", "World", "!")',
                "returns": "Hello World!",
            },
        ],
        "returns": "Text",
    },
    "CONCAT_WS": {
        "name": "CONCAT_WS()",
        "description": "Concatenates two or more text strings with a separator",
        "examples": [
            {
                "syntax": 'CONCAT_WS(" ", "Hello", "World")',
                "returns": "Hello World",
            },
            {
                "syntax": 'CONCAT_WS(" ", "Hello", "World", "!")',
                "returns": "Hello World !",
            },
        ],
        "returns": "Text",
    },
    "CONCATENATE": {
        "name": "CONCATENATE()",
        "description": "Concatenates two or more text strings",
        "examples": [
            {
                "syntax": 'CONCATENATE("Hello", " ", "World")',
                "returns": "Hello World",
            },
            {
                "syntax": 'CONCATENATE("Hello", " ", "World", "!")',
                "returns": "Hello World!",
            },
        ],
        "returns": "Text",
    },
    "CONTAINS": {
        "name": "CONTAINS()",
        "description": "Returns a YesNo expression",
        "examples": [
            {"syntax": 'CONTAINS("Hello World", "World")', "returns": "Yes"},
            {"syntax": 'CONTAINS("Hello World", "World!")', "returns": "No"},
        ],
        "returns": "YesNo",
    },
    "CONTEXT": {
        "name": "CONTEXT()",
        "description": "Returns current context",
        "examples": [
            {"syntax": "CONTEXT('application')", "returns": "my-app"},
            {"syntax": "CONTEXT('solution')", "returns": "my-solution"},
            {"syntax": "CONTEXT('page')", "returns": "my-page"},
            {"syntax": "CONTEXT('view')", "returns": "my-view"},
            {"syntax": "CONTEXT('view-type')", "returns": "list-view"},
            {"syntax": "CONTEXT('object')", "returns": "my-object"},
            {"syntax": "CONTEXT('Bot')", "returns": "False"},
            {
                "syntax": "CONTEXT('Browser')",
                "returns": "Chrome/Safari/Firefox",
            },
            {"syntax": "CONTEXT('DeviceType')", "returns": "Mobile/Web"},
            {
                "syntax": "CONTEXT('Device')",
                "returns": "Uid of the device from cookie",
            },
            {"syntax": "CONTEXT('OS')", "returns": "iOS/Linux/Windows"},
        ],
        "returns": "Text",
    },
    "COUNT": {
        "name": "COUNT()",
        "description": "Returns the number of items in an iterable. If the argument is a table name, it will return the number of rows.",
        "examples": [
            {"syntax": "COUNT([1, 2, 3])", "returns": 3},
            {"syntax": "COUNT([3.14, 2.71, 1.41])", "returns": 3},
            {"syntax": 'COUNT_DB("table_name")', "returns": "Number"},
        ],
        "returns": "Number",
    },
    "CURRENTAPP": {
        "name": "CURRENTAPP()",
        "description": "The ID of the active application",
        "examples": [{"syntax": "CURRENTAPP()", "returns": "UUID"}],
        "returns": "UUID",
    },
    "DATE": {
        "name": "DATE()",
        "description": "Returns a date from a string",
        "examples": [
            {"syntax": 'DATE("2020-01-01")', "returns": "2020-01-01"},
            {"syntax": 'DATE("2020-01-01 00:00:00")', "returns": "2020-01-01"},
        ],
        "returns": "Date",
    },
    "DATEADD": {
        "name": "DATEADD()",
        "description": "Adds a number of days",
        "examples": [
            {"syntax": 'DATEADD("2020-01-01", 1)', "returns": "2020-01-02"},
            {"syntax": 'DATEADD("2020-01-01", -1)', "returns": "2019-12-31"},
        ],
        "returns": "Date",
    },
    "DATEDIFF": {
        "name": "DATEDIFF()",
        "description": 'Returns the number of days between two dates. DATEDIFF("2020-01-01", "2020-12-31") returns 365',
        "examples": [
            {"syntax": 'DATEDIFF("2020-01-01", "2020-12-31")', "returns": 365},
            {"syntax": 'DATEDIFF("2020-12-31", "2020-01-01")', "returns": -365},
            {"syntax": "DATEDIFF(DATE('[[end_date]]'), DATE('[[start_date]]'))", "returns": "Number that represents the difference in days between the end date and start date"},
        ],
        "returns": "Number",
    },
    "DAY": {
        "name": "DAY()",
        "description": "Returns the day of the month",
        "examples": [
            {"syntax": 'DAY("2020-01-01")', "returns": 1},
            {"syntax": 'DAY("2020-12-31")', "returns": 31},
        ],
        "returns": "Number",
    },
    "DLP_SSN": {
        "name": "DLP_SSN()",
        "description": "Returns a de-identified SSN",
        "examples": [
            {"syntax": 'DLP_SSN("123-45-6789")', "returns": "123-XX-XXXX"}
        ],
        "returns": "Text",
    },
    "ENCODEURL": {
        "name": "ENCODEURL()",
        "description": "Returns a URL encoded string",
        "examples": [
            {
                "syntax": 'ENCODEURL("https://www.google.com/search?q=hello world")',
                "returns": "https%3A%2F%2Fwww.google.com%2Fsearch%3Fq%3Dhello+world",
            }
        ],
        "returns": "Text",
    },
    "ENDSWITH": {
        "name": "ENDSWITH()",
        "description": "Returns a YesNo expression",
        "examples": [
            {"syntax": 'ENDSWITH("Hello World", "World")', "returns": "Yes"},
            {"syntax": 'ENDSWITH("Hello World", "World!")', "returns": "No"},
        ],
        "returns": "YesNo",
    },
    "EOMONTH": {
        "name": "EOMONTH()",
        "description": "Returns the last day of the month",
        "examples": [
            {"syntax": 'EOMONTH("2020-01-01")', "returns": "2020-01-31"},
            {"syntax": 'EOMONTH("2020-12-31")', "returns": "2020-12-31"},
        ],
        "returns": "Date",
    },
    "EOWEEK": {
        "name": "EOWEEK()",
        "description": "Returns the last day of the week",
        "examples": [
            {"syntax": 'EOWEEK("2020-01-01")', "returns": "2020-01-05"},
            {"syntax": 'EOWEEK("2020-12-31")', "returns": "2021-01-02"},
        ],
        "returns": "Date",
    },
    "EXISTS": {
        "name": "EXISTS()",
        "description": "Returns a YesNo expression",
        "examples": [
            {"syntax": 'EXISTS("users", "id", 1)', "returns": "Yes"},
            {"syntax": 'EXISTS("users", "id", 999)', "returns": "No"},
        ],
        "returns": "YesNo",
    },
    "EXTRACTDATES": {
        "name": "EXTRACTDATES()",
        "description": "Returns a list of dates from a string",
        "examples": [
            {
                "syntax": 'EXTRACTDATES("2020-01-01, 2020-01-03")',
                "returns": ["2020-01-01", "2020-01-03"],
            }
        ],
        "returns": "List",
    },
    "EXTRACTEMAILS": {
        "name": "EXTRACTEMAILS()",
        "description": "Returns a list of emails from a string",
        "examples": [
            {
                "syntax": 'EXTRACTEMAILS("admin@example.com hello@example.com")',
                "returns": ["admin.example.com", "hello@example.com"],
            }
        ],
        "returns": "List",
    },
    "EXTRACTNUMBERS": {
        "name": "EXTRACTNUMBERS()",
        "description": "Returns a list of numbers from a string",
        "examples": [
            {"syntax": 'EXTRACTNUMBERS("1 2 3")', "returns": [1, 2, 3]}
        ],
        "returns": "List",
    },
    "EXTRACTPHONES": {
        "name": "EXTRACTPHONES()",
        "description": "Returns a list of phone numbers from a string",
        "examples": [
            {
                "syntax": 'EXTRACTPHONES("123-456-7890")',
                "returns": ["123-456-7890"],
            }
        ],
        "returns": "List",
    },
    "EXTRACTURLS": {
        "name": "EXTRACTURLS()",
        "description": "Returns a list of URLs from a string",
        "examples": [
            {
                "syntax": 'EXTRACTURLS("https://www.google.com")',
                "returns": ["https://www.google.com"],
            },
            {
                "syntax": 'EXTRACTURLS("https://www.google.com https://www.example.com")',
                "returns": [
                    "https://www.google.com",
                    "https://www.example.com",
                ],
            },
        ],
        "returns": "List",
    },
    "FIND": {
        "name": "FIND()",
        "description": "Returns the position of a substring. Returns -1 if not found.",
        "examples": [
            {"syntax": 'FIND("needle", "needle in haystack")', "returns": 0},
            {"syntax": 'FIND("rock", "in haystack")', "returns": -1},
        ],
        "returns": "Number",
    },
    "FLOAT": {
        "name": "FLOAT()",
        "description": "Converts a value to float",
        "examples": [
            {"syntax": 'FLOAT("3.14")', "returns": 3.14},
            {"syntax": "FLOAT(3)", "returns": 3.0},
        ],
        "returns": "Number",
    },
    "FLOOR": {
        "name": "FLOOR()",
        "description": "Returns the largest integer less than or equal to a number",
        "examples": [
            {"syntax": "FLOOR(1.1)", "returns": 1},
            {"syntax": "FLOOR(1.9)", "returns": 1},
        ],
        "returns": "Number",
    },
    "FORMAT_DATETIME": {
        "name": "FORMAT_DATETIME() ",
        "description": "FORMAT_DATETIME(value, format,default_timezone[optional],ignore_timezone[optional]) Returns Datetime based on the input input",
        "examples": [
            {
                "syntax": 'FORMAT_DATETIME(Sat, 15 Jun 2024 00:00:00 GMT,"%Y-%m-%d %H:%M:%S")',
                "returns": "2024-05-20 05:07:51",
            },
            {
                "syntax": 'FORMAT_DATETIME(2024-06-13 12:28:47,"%Y-%m-%d")',
                "returns": "2024-06-15",
            },
            {
                "syntax": 'FORMAT_DATETIME(2024-06-13 12:28:47,"%d-%m-%Y %H:%M:%S")',
                "returns": "20-05-2024 05:07:51",
            },
        ],
        "returns": "Text",
    },
    "FORMAT_NUMBER": {
        "name": "FORMAT_NUMBER()",
        "description": "Returns a formatted number",
        "examples": [
            {
                "syntax": 'FORMAT_NUMBER("32", "{:08.0f}")',
                "returns": "00000032",
            },
            {
                "syntax": 'FORMAT_NUMBER(1234567.89, "{:10.2f}")',
                "returns": "1,234,567.89",
            },
            {
                "syntax": 'FORMAT_NUMBER(1234567.89, "{:10.2e}")',
                "returns": "1.23e+06",
            },
            {
                "syntax": 'FORMAT_NUMBER(1234567.89, "{:10.2g}")',
                "returns": "1.2e+06",
            },
            {"syntax": '=FORMAT_NUMBER(.99, "{:7.2%}")', "returns": " 99.00%"},
        ],
        "returns": "Text",
    },
    "FORMAT_TIME": {
        "name": "FORMAT_TIME()",
        "description": "FORMAT_TIME(Value,Military Time, Ignore Seconds, Default timezone('optional)) Returns Time  based on the input ",
        "examples": [
            {
                "syntax": "FORMAT_TIME('05:44:18',True,True,'America/Denver')",
                "returns": "05:44",
            },
            {
                "syntax": 'FORMAT_TIME("05:44:18 AM",False,True,"Pacific/Saipan")", "returns": "03:44 PM"}',
                "returns": "1. AppSheet 2. Bubble",
            },
        ],
        "returns": "Text",
    },
    "GENERATE_CHILD_RECORDS": {
        "name": "GENERATE_CHILD_RECORDS()",
        "description": "GENERATE_CHILD_RECORDS(table, record ID, prompt, number of records, enhance prompt) Generates child records based on the input prompt and table. The number of records and optimise prompt is optional.",
        "examples": [
            {
                "syntax": 'GENERATE_CHILD_RECORDS("superheros", "72570e47-2dc6-477d-97e7-c7b410ddc487" ,"Add details for 3 superheroes from Marvel", 3, True)',
                "returns": "List of record IDs",
            }
        ],
        "returns": "List",
    },
    "GENERATE_IMAGE": {
        "name": "GENERATE_IMAGE()",
        "description": "Returns a generated Image based on the input prompt",
        "examples": [
            {
                "syntax": 'GENERATE_IMAGE("Cute Dog playing football ","512x512",1)',
                "returns": "Image",
            }
        ],
        "returns": "Image",
    },
    "GENERATE_RECORDS": {
        "name": "GENERATE_RECORDS()",
        "description": "GENERATE_RECORDS(table, prompt, number of records, enhance prompt) Generates records based on the input prompt and table. The number of records and optimise prompt is optional.",
        "examples": [
            {
                "syntax": 'GENERATE_RECORDS("superheros", "Add details for 3 superheroes from Marvel", 3, True)',
                "returns": "List of record IDs",
            }
        ],
        "returns": "List",
    },
    "GENERATE_SIGNED_URL": {
        "name": "GENERATE_SIGNED_URL()",
        "description": "GENERATE_SIGNED_URL(url, [expiration=3600]) Returns a signed URL from GCS.",
        "examples": [
            {
                "syntax": 'GENERATE_SIGNED_URL("bucket-name/example.png")',
                "returns": "signed URL",
            }
        ],
        "returns": "Text",
    },
    "GENERATE_TEXT": {
        "name": "GENERATE_TEXT()",
        "description": "GENERATE_TEXT(prompt, context, datasource) Returns a generated text based on the input prompt. Pass a datastore path to be used for grounding.",
        "examples": [
            {
                "syntax": 'GENERATE_TEXT("Give me a name for a blog website")',
                "returns": "Blogger's Home",
            },
            {
                "syntax": 'GENERATE_TEXT("Give two names for a tech product, list them in numbers")',
                "returns": "1. AppSheet 2. Bubble",
            },
        ],
        "returns": "Text",
    },
    "GENERATE_TEXT_WITH_IMAGE": {
        "name": "GENERATE_TEXT_WITH_IMAGE()",
        "description": "Returns a generated text with an image prompt and text prompt. Pass a datastore path to be used for grounding.",
        "examples": [
            {
                "syntax": 'GENERATE_TEXT_WITH_IMAGE("image.jpg","Describe the image")',
                "returns": "Text",
            }
        ],
        "returns": "Text",
    },
    "GET": {
        "name": "GET()",
        "description": "Returns a value from a dictionary or a list",
        "examples": [{"syntax": "GET([1,7,8],0)", "returns": "1"}],
        "returns": "Any",
    },
    "HAS_PERMISSION": {
        "name": "HAS_PERMISSION()",
        "description": "Returns a YesNo expression",
        "examples": [
            {"syntax": 'HAS_PERMISSION("send_mail")', "returns": "Yes"},
            {"syntax": 'HAS_PERMISSION("cases.create")', "returns": "No"},
            {
                "syntax": 'HAS_PERMISSION("cases.case_number.read")',
                "returns": "No",
            },
        ],
        "returns": "YesNo",
    },
    "HOUR": {
        "name": "HOUR()",
        "description": "Returns the hour",
        "examples": [
            {"syntax": 'HOUR("2020-01-01 12:00:00")', "returns": 12},
            {"syntax": 'HOUR("2020-01-01 00:00:00")', "returns": 0},
        ],
        "returns": "Number",
    },
    "IF": {
        "name": "IF()",
        "description": "Returns one value if a condition is true, and another value if it is false",
        "examples": [
            {"syntax": 'IF(True, "Yes", "No")', "returns": "Yes"},
            {"syntax": 'IF(False, "Yes", "No")', "returns": "No"},
        ],
        "returns": "Any",
    },
    "IFS": {
        "name": "IFS()",
        "description": "Returns one value if a condition is true, and another value if it is false for multiple conditions",
        "examples": [
            {"syntax": 'IFS(True, "Yes", False, "No")', "returns": "Yes"},
            {"syntax": 'IFS(FALSE, "Yes", TRUE, "No")', "returns": "No"},
        ],
        "returns": "Any",
    },
    "IMAGE": {
        "name": "IMAGE()",
        "description": "IMAGE(url). Returns a signed URL from GCS.",
        "examples": [
            {
                "syntax": 'IMAGE("bucket-name/example.png")',
                "returns": "signed URL",
            }
        ],
        "returns": "Text",
    },
    "IN": {
        "name": "IN()",
        "description": "Returns a YesNo expression",
        "examples": [
            {"syntax": 'IN("a", ["a", "b", "c"])', "returns": "Yes"},
            {"syntax": 'IN("d", ["a", "b", "c"])', "returns": "No"},
        ],
        "returns": "YesNo",
    },
    "INDEX": {
        "name": "INDEX()",
        "description": "Returns the value at a specific position in a list. Indexes start at 1.",
        "examples": [
            {"syntax": 'INDEX(["a", "b", "c"], 1)', "returns": "a"},
            {"syntax": 'INDEX(["a", "b", "c"], 2)', "returns": "b"},
            {"syntax": 'INDEX(["a", "b", "c"], 3)', "returns": "c"},
            {"syntax": 'INDEX(["a", "b", "c"], 4)', "returns": ""},
        ],
        "returns": "Number",
    },
    "INT": {
        "name": "INT()",
        "description": "Converts a value to an integer",
        "examples": [
            {"syntax": 'INT("3")', "returns": 3},
            {"syntax": "INT(2.718)", "returns": 2},
        ],
        "returns": "Number",
    },
    "ISBLANK": {
        "name": "ISBLANK()",
        "description": "Returns a YesNo expression",
        "examples": [
            {"syntax": 'ISBLANK("")', "returns": "Yes"},
            {"syntax": 'ISBLANK("a")', "returns": "No"},
        ],
        "returns": "YesNo",
    },
    "ISDATE": {
        "name": "ISDATE()",
        "description": "Returns a YesNo expression",
        "examples": [
            {"syntax": 'ISDATE("2020-01-01")', "returns": "Yes"},
            {"syntax": 'ISDATE("a")', "returns": "No"},
        ],
        "returns": "YesNo",
    },
    "ISNOTBLANK": {
        "name": "ISNOTBLANK()",
        "description": "Returns a YesNo expression",
        "examples": [
            {"syntax": 'ISNOTBLANK("")', "returns": "No"},
            {"syntax": 'ISNOTBLANK("a")', "returns": "Yes"},
        ],
        "returns": "YesNo",
    },
    "ISNULL": {
        "name": "ISNULL()",
        "description": "Returns a YesNo expression, if the value is null or None",
        "examples": [
            {"syntax": "ISNULL(1)", "returns": "No"},
            {"syntax": "ISNULL(0)", "returns": "No"},
            {"syntax": "ISNULL(None)", "returns": "Yes"},
        ],
        "returns": "YesNo",
    },
    "ISNUMBER": {
        "name": "ISNUMBER()",
        "description": "Returns a YesNo expression",
        "examples": [
            {"syntax": "ISNUMBER(1)", "returns": "Yes"},
            {"syntax": 'ISNUMBER("a")', "returns": "No"},
        ],
        "returns": "YesNo",
    },
    "KG_SEARCH": {
        "name": "KG_SEARCH()",
        "description": "KG_SEARCH(query, [limit=10]). Returns a list of entities from Google's Knowledge Graph.",
        "examples": [
            {
                "syntax": 'KG_SEARCH("Barack Obama")',
                "returns": '[{"name": "Barack Obama", "type": "Person", "description": "44th U.S. President", "url": "https://en.wikipedia.org/wiki/Barack_Obama"}]',
            }
        ],
        "returns": "JSON",
    },
    "LATLNG_TO_ADDRESS": {
        "name": "LATLNG_TO_ADDRESS()",
        "description": "LATLNG_TO_ADDRESS(latitude, longitude). Returns an address from a latitude and longitude.",
        "examples": [
            {
                "syntax": "LATLNG_TO_ADDRESS(40.714224, -73.961452)",
                "returns": "277 Bedford Ave, Brooklyn, NY 11211, USA",
            }
        ],
        "returns": "Text",
    },
    "LEFT": {
        "name": "LEFT()",
        "description": "Returns the leftmost characters in a text string",
        "examples": [
            {"syntax": 'LEFT("abc", 1)', "returns": "a"},
            {"syntax": 'LEFT("abc", 2)', "returns": "ab"},
            {"syntax": 'LEFT("abc", 3)', "returns": "abc"},
            {"syntax": 'LEFT("abc", 4)', "returns": "abc"},
        ],
        "returns": "Text",
    },
    "LEN": {
        "name": "LEN()",
        "acts_on": "field",
        "description": "The string length",
        "examples": [
            {"syntax": 'LEN("abc")', "returns": 3},
            {"syntax": 'LEN("a")', "returns": 1},
            {"syntax": 'LEN("")', "returns": 0},
        ],
        "returns": "Number",
    },
    "LIST": {
        "name": "LIST()",
        "description": "Returns a list of values",
        "examples": [
            {"syntax": 'LIST("a", "b", "c")', "returns": ["a", "b", "c"]},
            {"syntax": "LIST(1, 2, 3)", "returns": [1, 2, 3]},
        ],
        "returns": "List",
    },
    "LOOKUP": {
        "name": "LOOKUP()",
        "description": "LOOKUP(value, object, field, return-column). Returns a single value from a table if found.",
        "examples": [
            {
                "syntax": 'LOOKUP("admin@example.com", "users", "email", "name")',
                "returns": "List",
            }
        ],
        "returns": "Any",
    },
    "LOWER": {
        "name": "LOWER()",
        "description": "Lowercase a string",
        "examples": [
            {"syntax": 'LOWER("ABC")', "returns": "abc"},
            {"syntax": 'LOWER("aBc")', "returns": "abc"},
        ],
        "returns": "Text",
    },
    "MARKDOWN_TO_HTML": {
        "name": "MARKDOWN_TO_HTML()",
        "description": "Converts Markdown to HTML",
        "examples": [
            {
                "syntax": 'MARKDOWN_TO_HTML("# Hello")',
                "returns": "<h1>Hello</h1>",
            },
            {
                "syntax": 'MARKDOWN_TO_HTML("## Hello")',
                "returns": "<h2>Hello</h2>",
            },
        ],
        "returns": "Text",
    },
    "MAX": {
        "name": "MAX()",
        "description": "Returns the largest value in a list of numbers",
        "examples": [
            {"syntax": "MAX([1, 2, 3])", "returns": 3},
            {"syntax": "MAX([3, 2, 1])", "returns": 3},
            {"syntax": "MAX([3.14, 2.71])", "returns": 3.14},
        ],
        "returns": "Number",
    },
    "MAXROW": {
        "name": "MAXROW()",
        "description": "Returns the largest row number in a table",
        "examples": [{"syntax": 'MAXROW("table", "field")', "returns": 3}],
        "returns": "Number",
    },
    "MID": {
        "name": "MID(arg, start, length)",
        "description": "Returns a specific number of characters from a text string starting at the position you specify.",
        "examples": [
            {"syntax": 'MID("abc", 1, 1)', "returns": "a"},
            {"syntax": 'MID("abc", 1, 2)', "returns": "ab"},
            {"syntax": 'MID("abc", 1, 3)', "returns": "abc"},
            {"syntax": 'MID("abc", 1, 4)', "returns": "abc"},
        ],
        "returns": "Text",
    },
    "MIN": {
        "name": "MIN()",
        "description": "Returns the smallest value in a list of numbers",
        "examples": [
            {"syntax": "MIN([1, 2, 3])", "returns": 1},
            {"syntax": "MIN([3, 2, 1])", "returns": 1},
            {"syntax": "MIN([3.14, 2.71])", "returns": 2.71},
        ],
        "returns": "Number",
    },
    "MINROW": {
        "name": "MINROW()",
        "description": "Returns the smallest row number in a table",
        "examples": [{"syntax": 'MINROW("table", "field")', "returns": 1}],
        "returns": "Number",
    },
    "MINUTE": {
        "name": "MINUTE()",
        "description": "Returns the minute",
        "examples": [
            {"syntax": 'MINUTE("2020-01-01 12:34:56")', "returns": 34}
        ],
        "returns": "Number",
    },
    "MONTH": {
        "name": "MONTH()",
        "description": "Returns the month",
        "examples": [{"syntax": 'MONTH("2020-01-01 12:34:56")', "returns": 1}],
        "returns": "Number",
    },
    "NLP_SENTIMENT": {
        "name": "NLP_SENTIMENT()",
        "description": "NLP_SENTIMENT(text). Returns a sentiment score from -1 to 1.",
        "examples": [
            {"syntax": 'NLP_SENTIMENT("I love this product")', "returns": 0.9},
            {"syntax": 'NLP_SENTIMENT("I hate this product")', "returns": -0.9},
        ],
        "returns": "Number",
    },
    "NOT": {
        "name": "NOT()",
        "description": "Returns a YesNo expression",
        "examples": [
            {"syntax": "NOT(True)", "returns": "No"},
            {"syntax": "NOT(No)", "returns": "Yes"},
        ],
        "returns": "YesNo",
    },
    "NOW": {
        "name": "NOW(timezone='UTC')",
        "description": "The datetime in %Y-%m-%d %H:%M:%S format. The timezone is optional with a default of UTC. Complete list of timezones can be found at https://en.wikipedia.org/wiki/List_of_tz_database_time_zones",
        "examples": [
            {"syntax": "NOW()", "returns": "2020-12-31 12:34:56"},
            {
                "syntax": 'NOW("America/Denver")',
                "returns": "2020-12-31 07:34:56",
            },
        ],
        "returns": "DateTime",
    },
    "OR": {
        "name": "OR()",
        "description": "Returns a YesNo expression",
        "examples": [
            {"syntax": "OR(True, False)", "returns": "Yes"},
            {"syntax": "OR(Yes, No)", "returns": "Yes"},
            {"syntax": "OR(No, No)", "returns": "No"},
        ],
        "returns": "YesNo",
    },
    "POWER": {
        "name": "POWER()",
        "description": "Returns the result of a number raised to a power",
        "examples": [
            {"syntax": "POWER(2, 3)", "returns": 8},
            {"syntax": "POWER(3, 2)", "returns": 9},
            {"syntax": "POWER(3.14, 2)", "returns": 9.8596},
        ],
        "returns": "Number",
    },
    "PREDICT": {
        "name": "PREDICT()",
        "description": "PREDICT(model, input). Returns a prediction from a model.",
        "examples": [
            {
                "syntax": 'PREDICT("my-model", {"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2})',
                "returns": "setosa",
            }
        ],
        "returns": "Text",
    },
    "RANDBETWEEN": {
        "name": "RANDBETWEEN()",
        "description": "Returns a random number between the two numbers",
        "examples": [{"syntax": "RANDBETWEEN(1, 10)", "returns": 5}],
        "returns": "Number",
    },
    "RE_FIND": {
        "name": "RE_FIND()",
        "description": "Returns the first match of a regular expression",
        "examples": [
            {"syntax": 'RE_FIND("([0-9]+)", "abc123def456")', "returns": "123"},
            {"syntax": 'RE_FIND("([a-z]+)", "abc123def456")', "returns": "abc"},
        ],
        "returns": "Text",
    },
    "RE_FINDALL": {
        "name": "RE_FINDALL()",
        "description": "Returns a list of all matches of a regular expression",
        "examples": [
            {
                "syntax": 'RE_FINDALL("([0-9]+)", "abc123def456")',
                "returns": ["123", "456"],
            },
            {
                "syntax": 'RE_FINDALL("([a-z]+)", "abc123def456")',
                "returns": ["abc", "def"],
            },
        ],
        "returns": "List",
    },
    "RE_MATCH": {
        "name": "RE_MATCH()",
        "description": "Returns the first match of a regular expression at the beginning of a string",
        "examples": [
            {"syntax": 'RE_MATCH("([0-9]+)", "123def456")', "returns": "123"},
            {
                "syntax": 'RE_MATCH("([a-z]+)", "abc123def456")',
                "returns": "abc",
            },
        ],
        "returns": "Text",
    },
    "RE_SEARCH": {
        "name": "RE_SEARCH()",
        "description": "Returns the first match of a regular expression anywhere in a string",
        "examples": [
            {
                "syntax": 'RE_SEARCH("([0-9]+)", "abc123def456")',
                "returns": "123",
            },
            {
                "syntax": 'RE_SEARCH("([a-z]+)", "abc123def456")',
                "returns": "abc",
            },
        ],
        "returns": "Text",
    },
    "RE_SUB": {
        "name": "RE_SUB()",
        "description": "Returns a string with all matches of a regular expression replaced",
        "examples": [
            {
                "syntax": 'RE_SUB("([0-9]+)", "X", "abc123def456")',
                "returns": "abcXdefX",
            },
            {
                "syntax": 'RE_SUB("([a-z]+)", "X", "abc123def456")',
                "returns": "X123X456",
            },
        ],
        "returns": "Text",
    },
    "REF_LABEL": {
        "name": "REF_LABEL()",
        "description": "Get Ref Label of record",
        "examples": [
            {
                "syntax": 'REF_LABEL("permits", "1745c746-aaa5-4ecf-96e7-49392458d42c")',
                "returns": "ON-0017",
            }
        ],
        "returns": "Text",
    },
    "REF_ROWS": {
        "name": "REF_ROWS()",
        "description": "Define related table and column",
        "examples": [
            {
                "syntax": 'REF_ROWS("users", "claim_id")',
                "returns": ["users", "claim_id"],
            }
        ],
        "returns": "Tuple",
    },
    "REMOVE_HTML_TAGS": {
        "name": "REMOVE_HTML_TAGS()",
        "description": "Removes HTML tags from a string",
        "examples": [
            {
                "syntax": 'REMOVE_HTML_TAGS("<h1>Hello</h1>")',
                "returns": "Hello",
            },
            {
                "syntax": 'REMOVE_HTML_TAGS("<p><b>Hello</b></p>")',
                "returns": "Hello",
            },
        ],
        "returns": "Text",
    },
    "RIGHT": {
        "name": "RIGHT()",
        "description": "Returns the rightmost characters from a string",
        "examples": [
            {"syntax": 'RIGHT("abc", 1)', "returns": "c"},
            {"syntax": 'RIGHT("abc", 2)', "returns": "bc"},
            {"syntax": 'RIGHT("abc", 3)', "returns": "abc"},
        ],
        "returns": "Text",
    },
    "ROUND": {
        "name": "ROUND()",
        "description": "Returns a number rounded to a specified number of decimal places",
        "examples": [
            {"syntax": "ROUND(3.14159, 2)", "returns": 3.14},
            {"syntax": "ROUND(3.14159, 3)", "returns": 3.142},
            {"syntax": "ROUND(3.14159, 4)", "returns": 3.1416},
        ],
        "returns": "Number",
    },
    "SECOND": {
        "name": "SECOND()",
        "description": "Returns the second",
        "examples": [
            {"syntax": 'SECOND("2020-01-01 12:34:56")', "returns": 56}
        ],
        "returns": "Number",
    },
    "SELECT": {
        "name": "SELECT()",
        "description": """Returns a list of objects from DB table. Optional second parameter to specify fields. Optional third and foruth parameter to specify filter column and filter value. Optional fifth parameter to specify whether to flatten the list."
                        filters:- Optional parameter to apply multiple filters. It should be a list of tuples. Each tuple should have 2 elements. First element should be the column name and second element should be the value. For example, filters=[("column1", 10), ("column2", 20)] will return rows where column1 = 10 and column2 = 20.
                        order_by:- Optional parameter to specify the column name to sort the results. It should be a string. For example, order_by="column1" will sort the results by column1. If you want to sort in descending order, you can add a "-" in front of the column name. For example, order_by="-column1" will sort the results by column1 in descending order.
                        """,
        "examples": [
            {
                "syntax": 'SELECT("table", "field")',
                "returns": "[{...}, {...}, ...]",
            },
            {
                "syntax": 'SELECT("table", "field,field2")',
                "returns": "[{...}, {...}, ...]",
            },
            {
                "syntax": 'SELECT("table", "field", "filter_column", "filter_value")',
                "returns": "[{...}, {...}, ...]",
            },
            {
                "syntax": 'SELECT("table", "field", "filter_column", "filter_value", True)',
                "returns": "[field, field, ...]",
            },
            {
                "syntax": 'SELECT("table", "*", filters=[("column1", 10), ("column2", 20)])',
                "returns": "[(record1), (record2), ...]",
            },
            {
                "syntax": 'SELECT("table", "*", order_by="column1")',
                "returns": "List of records",
            },
        ],
        "returns": "List",
    },
    "SENDER_EMAIL": {
        "name": "SENDER_EMAIL()",
        "description": "The email sender",
        "examples": [
            {"syntax": "SENDER_EMAIL()", "returns": "Default Email Sender"}
        ],
        "returns": "Email",
    },
    "SENDER_EMAIL_NAME": {
        "name": "SENDER_EMAIL_NAME()",
        "description": "The email sender name",
        "examples": [
            {
                "syntax": "SENDER_EMAIL_NAME()",
                "returns": "Default Email Sender Name",
            }
        ],
        "returns": "Text",
    },
    "SORT": {
        "name": "SORT()",
        "description": "Returns a list of values sorted in ascending order. Optional second boolean parameter to sort in descending order.",
        "examples": [
            {"syntax": "SORT([3, 2, 1])", "returns": [1, 2, 3]},
            {"syntax": "SORT([1, 2, 3], True)", "returns": [3, 2, 1]},
        ],
        "returns": "List",
    },
    "SPEECH_TO_TEXT": {
        "name": "SPEECH_TO_TEXT()",
        "description": "SPEECH_TO_TEXT(object). Returns a text string from a GCS object.",
        "examples": [
            {
                "syntax": 'SPEECH_TO_TEXT("example.mp3")',
                "returns": "Hello World",
            }
        ],
        "returns": "Text",
    },
    "SPLIT": {
        "name": "SPLIT()",
        "description": "Returns a list of substrings from a text string, separated by a delimiter",
        "examples": [
            {
                "syntax": 'SPLIT("Hello World", " ")',
                "returns": ["Hello", "World"],
            }
        ],
        "returns": "List",
    },
    "SQRT": {
        "name": "SQRT()",
        "description": "Returns the square root of a number",
        "examples": [
            {"syntax": "SQRT(4)", "returns": 2},
            {"syntax": "SQRT(9)", "returns": 3},
            {"syntax": "SQRT(9.0)", "returns": 3.0},
        ],
        "returns": "Number",
    },
    "STARTSWITH": {
        "name": "STARTSWITH()",
        "description": "Returns a YesNo expression",
        "examples": [
            {"syntax": 'STARTSWITH("Hello World", "Hello")', "returns": "Yes"},
            {"syntax": 'STARTSWITH("Hello World", "World")', "returns": "No"},
        ],
        "returns": "YesNo",
    },
    "STATIC_MAP": {
        "name": "STATIC_MAP()",
        "description": "STATIC_MAP(latitude, longitude, zoom, width, height, map_type). Returns a static map image from Google Maps. <a href='https://developers.google.com/maps/documentation/maps-static/start'>Maps Documentation</a>. This returns a GCS blob URI. You can use the GENERATE_SIGNED_URL() function to display the image. map_type can be one of the following: roadmap, satellite, terrain, hybrid.",
        "examples": [
            {
                "syntax": "STATIC_MAP(40.714224, -73.961452, 12, 400, 400)",
                "returns": "signed URL",
            },
            {
                "syntax": 'STATIC_MAP(ADDRESS_TO_LATLNG("1616 Federal Blvd, Denver, CO 80204, USA"), None, 12, 400, 400)',
                "returns": "File",
            },
        ],
        "returns": "File",
    },
    "STREET_VIEW": {
        "name": "STREET_VIEW()",
        "description": "STREET_VIEW(latitude, longitude, heading, pitch, fov, width, height). Returns a street view image from Google Maps. <a href='https://developers.google.com/maps/documentation/streetview/overview'>Street View Documentation</a>. This returns a GCS blob URI. You can use the GENERATE_SIGNED_URL() function to display the image.",
        "examples": [
            {
                "syntax": "STREET_VIEW(40.714224, -73.961452, 90, 0, 90, 400, 400)",
                "returns": "signed URL",
            }
        ],
        "returns": "File",
    },
    "SUBSTITUTE": {
        "name": "SUBSTITUTE()",
        "description": "Returns a text string with all occurrences of a substring replaced with another substring",
        "examples": [
            {
                "syntax": 'SUBSTITUTE("Hello World", "World", "Universe")',
                "returns": "Hello Universe",
            }
        ],
        "returns": "Text",
    },
    "SUM": {
        "name": "SUM()",
        "description": "Returns the sum of a list of numbers",
        "examples": [
            {"syntax": "SUM([1, 2, 3])", "returns": 6},
            {"syntax": "SUM([1.1, 2.2, 3.3])", "returns": 6.6},
        ],
        "returns": "Number",
    },
    "SUMMARIZE_DOCUMENT": {
        "name": "SUMMARIZE_DOCUMENT(url)",
        "description": "SUMMARIZE_DOCUMENT(url) Returns a summarized text of the input document. Supports PDF files.",
        "examples": [
            {
                "syntax": "SUMMARIZE_DOCUMENT(url = pdf_url)",
                "returns": "Summarized text of the pdf",
            }
        ],
        "returns": "Text",
    },
    "TEXT": {
        "name": "TEXT()",
        "description": "Returns a text string representation of a value",
        "examples": [
            {"syntax": "TEXT(123)", "returns": "123"},
            {"syntax": "TEXT(123.45)", "returns": "123.45"},
        ],
        "returns": "Text",
    },
    "TEXT_TO_SPEECH": {
        "name": "TEXT_TO_SPEECH()",
        "description": "TEXT_TO_SPEECH(text). Returns a GCS blob URI from a text string. You can use the GENERATE_SIGNED_URL() function to play the audio.",
        "examples": [
            {
                "syntax": 'TEXT_TO_SPEECH("Hello World")',
                "returns": "signed URL",
            },
            {
                "syntax": 'TEXT_TO_SPEECH("Hello World", "FEMALE")',
                "returns": "signed URL",
            },
            {
                "syntax": 'TEXT_TO_SPEECH("Hello World", "MALE")',
                "returns": "signed URL",
            },
            {
                "syntax": 'TEXT_TO_SPEECH("Hello World", "NEUTRAL")',
                "returns": "signed URL",
            },
        ],
        "returns": "File",
    },
    "TIME": {
        "name": "TIME()",
        "description": "Returns the time portion of a datetime",
        "examples": [
            {"syntax": 'TIME("2020-01-01 12:34:56")', "returns": "12:34:56"},
            {"syntax": "TIME(NOW())", "returns": "12:34:56"},
        ],
        "returns": "Time",
    },
    "TIMENOW": {
        "name": "TIMENOW(timezone='UTC')",
        "description": "The time in %H:%M:%S format. Similar to TIME(NOW()). The timezone is optional with a default of UTC. Complete list of timezones can be found at https://en.wikipedia.org/wiki/List_of_tz_database_time_zones",
        "examples": [
            {"syntax": "TIMENOW()", "returns": "12:34:56"},
            {"syntax": 'TIMENOW("America/Denver")', "returns": "07:34:56"},
        ],
        "returns": "Time",
    },
    "TITLE": {
        "name": "TITLE()",
        "description": "Returns a text string in title case",
        "examples": [
            {"syntax": 'TITLE("hello world")', "returns": "Hello World"}
        ],
        "returns": "Text",
    },
    "TODAY": {
        "name": "TODAY(timezone='UTC')",
        "description": "The date in %Y-%m-%d format. The timezone is optional with a default of UTC. Complete list of timezones can be found at https://en.wikipedia.org/wiki/List_of_tz_database_time_zones",
        "examples": [
            {"syntax": "TODAY()", "returns": "2020-01-01"},
            {"syntax": 'TODAY("America/Denver")', "returns": "2019-12-31"},
        ],
        "returns": "Date",
    },
    "TOP": {
        "name": "TOP()",
        "description": "Returns the first n items in a list",
        "examples": [
            {"syntax": "TOP([1, 2, 3], 2)", "returns": [1, 2]},
            {"syntax": "TOP([1, 2, 3], 4)", "returns": [1, 2, 3]},
        ],
        "returns": "List",
    },
    "TOTALHOURS": {
        "name": "TOTALHOURS()",
        "description": "Returns the total number of hours in a time",
        "examples": [
            {"syntax": 'TOTALHOURS("12:34:56")', "returns": 12.582222222222222}
        ],
        "returns": "Number",
    },
    "TOTALMINUTES": {
        "name": "TOTALMINUTES()",
        "description": "Returns the total number of minutes in a time",
        "examples": [
            {"syntax": 'TOTALMINUTES("12:34:56")', "returns": 754.9333333333333}
        ],
        "returns": "Number",
    },
    "TOTALSECONDS": {
        "name": "TOTALSECONDS()",
        "description": "Returns the total number of seconds in a time",
        "examples": [
            {"syntax": 'TOTALSECONDS("12:34:56")', "returns": 45296.0}
        ],
        "returns": "Number",
    },
    "TRANSLATE_DOCUMENT": {
        "name": "TRANSLATE_DOCUMENT()",
        "description": 'TRANSLATE_DOCUMENT("URI", "source_language", "target_language"). Returns a translated document from a GCS URI.',
        "examples": [
            {
                "syntax": 'TRANSLATE_DOCUMENT("gs://bucket-name/file-name", "en", "es")',
                "returns": "GCS URI",
            }
        ],
        "returns": "Text",
    },
    "TRANSLATE_DOCUMENT_BATCH": {
        "name": "TRANSLATE_DOCUMENT_BATCH()",
        "description": 'TRANSLATE_DOCUMENT_BATCH("URI", "source_language", "target_language"). Returns a translated document from a GCS URI.',
        "examples": [
            {
                "syntax": 'TRANSLATE_DOCUMENT_BATCH("gs://bucket-name/file-name", "en", "es")',
                "returns": "GCS URI",
            }
        ],
        "returns": "Text",
    },
    "TRANSLATE_TEXT": {
        "name": "TRANSLATE_TEXT()",
        "description": "TRANSLATE_TEXT(text, [source_language='auto', target_language='en']). Returns a translated string. Similar to the <a href='https://support.google.com/docs/answer/3093331?hl=en'>GOOGLETRANSLATE()</a> function in Google Sheets. ",
        "examples": [
            {"syntax": 'TRANSLATE_TEXT("Hola Amigo")', "returns": "Hi friend"},
            {
                "syntax": 'TRANSLATE_TEXT("Hola Amigo", "es", "en")',
                "returns": "Hi friend",
            },
        ],
        "returns": "Text",
        "aliases": ["GOOGLETRANSLATE"],
    },
    "TRIM": {
        "name": "TRIM()",
        "description": "Returns a text string with whitespace removed from the start and end",
        "examples": [
            {"syntax": 'TRIM(" Hello World ")', "returns": "Hello World"},
            {"syntax": 'TRIM("Hello World")', "returns": "Hello World"},
        ],
        "returns": "Text",
    },
    "UNIQUE": {
        "name": "UNIQUE()",
        "description": "Returns a list of unique values from a list",
        "examples": [
            {"syntax": "UNIQUE([1, 2, 3, 1, 2, 3])", "returns": [1, 2, 3]}
        ],
        "returns": "List",
    },
    "UPPER": {
        "name": "UPPER()",
        "description": "Uppercase a string",
        "examples": [
            {"syntax": 'UPPER("Hello World")', "returns": "HELLO WORLD"}
        ],
        "returns": "Text",
    },
    "URL_TO_PDF": {
        "name": "URL_TO_PDF()",
        "description": "URL_TO_PDF(url). Returns a PDF file from a URL.",
        "examples": [
            {"syntax": 'URL_TO_PDF("https://example.com")', "returns": "URI"},
            {
                "syntax": 'URL_TO_PDF("https://example.com","vendors")',
                "returns": "URI",
            },
        ],
        "returns": "File",
    },
    "USEREMAIL": {
        "name": "USEREMAIL()",
        "description": "Returns the current user's email",
        "examples": [{"syntax": "USEREMAIL()", "returns": "email"}],
        "returns": "Email",
    },
    "USERID": {
        "name": "USERID()",
        "description": "Returns the current user's ID",
        "examples": [{"syntax": "USERID()", "returns": "UUID"}],
        "returns": "UUID",
    },
    "USERLOCALE": {
        "name": "USERLOCALE()",
        "description": "The active locale e.g. en, de, es, zh",
        "examples": [
            {"syntax": "USERLOCALE()", "returns": "en, de, es, fr, or zh"}
        ],
        "returns": "Text",
    },
    "USERNAME": {
        "name": "USERNAME()",
        "description": "Returns the current user's fullname",
        "examples": [{"syntax": "USERNAME()", "returns": "Full Name"}],
        "returns": "Text",
    },
    "USERROLE": {
        "name": "USERROLE()",
        "description": "Returns the current user's role ID",
        "examples": [{"syntax": "USERROLE()", "returns": "UUID"}],
        "returns": "UUID",
    },
    "UTCNOW": {
        "name": "UTCNOW()",
        "description": "The datetime for UTC timezone in %Y-%m-%d %H:%M:%S format",
        "examples": [{"syntax": "UTCNOW()", "returns": "2020-01-01 12:34:56"}],
        "returns": "DateTime",
    },
    "WEEKDAY": {
        "name": "WEEKDAY()",
        "description": "Returns the day of the week for a date",
        "examples": [{"syntax": 'WEEKDAY("2020-01-01")', "returns": 1}],
        "returns": "Number",
    },
    "YEAR": {
        "name": "YEAR()",
        "description": "Returns the year",
        "examples": [{"syntax": 'YEAR("2020-01-01")', "returns": 2020}],
        "returns": "Number",
    },
}


class ReservedObject(StrEnum):
    """Enumeration for reserved object types."""

    # system object types
    Actions = "actions"
    Applications = "applications"
    Breadcrumbs = "breadcrumbs"
    Conditions = "conditions"
    CustomPermissions = "custom_permissions"
    Dashboards = "dashboards"
    DataAccessRoles = "data_access_roles"
    DataMigrations = "data_migrations"
    DataSources = "data_sources"
    DeletedItems = "deleted_items"
    DuplicateRules = "duplicate_rules"
    Feeds = "feeds"
    Fields = "fields"
    FormatRules = "format_rules"
    Integrations = "integrations"
    Links = "links"
    Menus = "menus"
    Navigations = "navigations"
    Objects = "objects"
    PackageComponents = "package_components"
    Packages = "packages"
    Pages = "pages"
    Posts = "posts"
    PermissionSetApplications = "permission_set_applications"
    PermissionSetCustomPermissions = "permission_set_custom_permissions"
    PermissionSetFields = "permission_set_fields"
    PermissionSetTables = "permission_set_tables"
    PermissionSets = "permission_sets"
    Predictions = "predictions"
    QueueMembers = "queue_members"
    QueueObjectSkills = "queue_object_skills"
    QueueObjects = "queue_objects"
    Queues = "queues"
    RolePermissionSets = "role_permission_sets"
    Roles = "roles"
    SharingRules = "sharing_rules"
    SnapappFunctions = "snapapp_functions"
    Solutions = "solutions"
    Templates = "templates"
    Users = "users"
    ViewLinks = "view_links"
    Views = "views"
    WebhookActions = "webhook_actions"
    WorkflowConditions = "workflow_conditions"
    Workflows = "workflows"
    Triggers = "triggers"
    Files = "files"
    Folders = "folders"
    VirtualAgents = "virtual_agents"
    Groundings = "groundings"
    Tools = "tools"
    Conversations = "conversations"
    ConversationMembers = "conversation_members"
    ConversationMessages = "conversation_messages"
    Blueprints = "blueprints"
    BlueprintBundles = "blueprint_bundles"

    # standard object types
    Accounts = "accounts"
    Activities = "activities"
    Alerts = "alerts"
    Attachments = "attachments"
    AuditTrails = "audit_trails"
    Contacts = "contacts"
    ChecklistItems = "checklist_items"
    DocAI_1040 = "docai_1040"
    DocAI_1040c = "docai_1040c"
    DocAI_1040se = "docai_1040se"
    DocAI_1099 = "docai_1099"
    DocAI_Bank_Statement = "docai_bank_statement"
    DocAI_Business_Plan = "docai_business_plan"
    DocAI_Change_of_Station = "docai_change_of_station"
    DocAI_Corps = "docai_corps"
    DocAI_Credit_Statement = "docai_credit_statement"
    DocAI_Diploma = "docai_diploma"
    DocAI_Divorce_Decree = "docai_divorce_decree"
    DocAI_EIN = "docai_ein"
    DocAI_ENL = "docai_enl"
    DocAI_Foreign_Passport = "docai_foreign_passport"
    DocAI_Form_Parser = "docai_form_parser"
    DocAI_Generic_ID = "docai_generic_id"
    DocAI_Lease_Agreement = "docai_lease_agreement"
    DocAI_Letter = "docai_letter"
    DocAI_Marriage_Certificate = "docai_marriage_certificate"
    DocAI_Mortgage_Statement = "docai_mortgage_statement"
    DocAI_NYCID = "docai_nycid"
    DocAI_Offer_Letter = "docai_offer_letter"
    DocAI_Paystub = "docai_paystub"
    DocAI_Property_Tax_Statement = "docai_property_tax_statement"
    DocAI_REC_ID = "docai_rec_id"
    DocAI_US_Driver_License = "docai_us_driver_license"
    DocAI_US_Passport = "docai_us_passport"
    DocAI_Utility_Doc = "docai_utility_doc"
    DocAI_W2 = "docai_w2"
    Favorites = "favorites"
    Households = "households"
    Jobs = "jobs"
    Notes = "notes"
    Tags = "tags"
    Vendors = "vendors"


RESTRICTED_OBJECTS_LIST = [e.value for e in ReservedObject]

DEFAULT_SOLUTION_ID="00000000-0000-0000-0000-000000000000"
DEFAULT_APPLICATION_ID="00000000-0000-0000-0000-000000000000"



