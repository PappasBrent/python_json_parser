# Python JSON Parser

A simple JSON parser written in Python in for educational purposes.
I think JSON is a fun language to write a parser for because of its simplicity.

## Prerequisites
- [Python 3](https://www.python.org/downloads/)

## Usage
1. Clone/download the project repo to your machine
2. Move the `python_json_parser` directory into your project directory
3. Import the module at the top of your file:

    `import python_json_parser`

4. Call the `load_json_string` and pass a JSON string to
it to convert the JSON string into a Python object:
    ```
    json_string = '''
    {
        "first name":"Arthur",
        "last name": "Dent",
        "age":42,
        "interests": [
            "flying",
            "sandwich making"
        ]
    }
    '''
    result = python_json_parser.load_json_string(json_string)
    ```

# License
Distributed under the MIT License. See LICENSE for more information.

# Contact
Please visit my [website](https://pappasbrent.com) for ways of contacting me.

# References
- [JSON.org](https://www.json.org/json-en.html) for the JSON schema
- [_Compilers: Principles, Techniques, and Tools_](https://en.wikipedia.org/wiki/Compilers:_Principles,_Techniques,_and_Tools)
for an introduction to lexical analysis and parsing