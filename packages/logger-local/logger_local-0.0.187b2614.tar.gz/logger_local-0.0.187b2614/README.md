<<<<<<< HEAD
# logger-local-python-package 

# TODO
TODO Add OpenTelemetry support

TODO Importing logger-local is broken when using version 0.0.82, but works with 0.0.81 . I was able to get it working locally by changing the index files in the generated node_modules folder for logger-local. The folder structure for logger-local is logger-local/dist/src/<files> instead of <package_name>/dist/<files>, which the rest of the packages use.

TODO send logs to VectorDb


# Initialize

Run this command in the root directory of your project :

    pip install -U logger-local

# Import

import instance from the package:

`from logger_local.LoggerLocal import Logger`

## Set up the minimum severity for all components or a specific component

You can set up `LOGGER_MINIMUM_SEVERITY: Info` or `LOGGER_MINIMUM_SEVERITY: 0` in you operating system or `.env`<br>
You can create `.logger.json` file, specifying the level of message you want to see for each component_id and the path to that
file in `LOGGER_CONFIGURATION_JSON_PATH`<br>
`.logger.json` format:

```json
{
  "component_id": {
    LoggerOutput: minimum_severity,
    // LoggerOutput is one of: "Console", "Logz.io", "MySQLDatabase"

    // for example:
    "1": {
      "Console": 501,
      "Logz.io": 502
    },
    "2": {
      "Logz.io": 502
    },
    "3": {
      "MySQLDatabase": "Info"
    },
    "Logger Python": {
      // you can also use the component name
      "Console": "Error",
      "Logz.io": 502
    },
    "default": {
      "Console": "Info",
      "Logz.io": 502
    }
  }
}
```

Set LOGGER_IS_WRITE_TO_SQL=T/F env var to override the above MySQLDatabase.

<br>

If the logs are ugly, try adding `LOGGER_COLORS_IN_LOGS=False` to your `.env` file.

# Usage

Note that you must have a .env file with the environment name and logz.io token.
`ENVIRONMENT_NAME=...`
`LOGZIO_TOKEN=...`

Logger 1st parameter should be a string, opposed to object which are structured fields we want to send to the logger
record.

## Using with Meta class:

```py
from logger_local.MetaLogger import MetaLogger
from logger_local.LoggerComponentEnum import LoggerComponentEnum

# Please ask your mentor/Team Lead for the component id<br>
# Please use the CONST enum from logger_local\LoggerComponentEnum.py<br>

your_logger_object = {
    'component_id': YOUR_COMPONENT_ID,
    'component_name': YOUR_COMPONENT_NAME,
    'component_category': LoggerComponentEnum.ComponentCategory.Code,
    "developer_email_address": YOUR_CIRCLES_EMAIL
}


# you can use the logger object in the class, and you don't have to expicitly create it, or call logger.start/end/exception
# use `logger = ...` here if you need it inside a static method
class YourClass(metaclass=MetaLogger, object=your_logger_object):
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def some_func(self, arg1):
        # start/end/error/exception will be called automatically
        self.logger.info("whatever", object={"test": 1 / arg1})
```

## Wrap a single function:

```py
from logger_local.MetaLogger import log_function_decorator

logger = Logger.create_logger(object=your_logger_object)


@log_function_decorator(logger)
def whatever(): pass  # no need to use logger start/end/ wrap everything inside try-except
```

## Wrap a module:

Sometimes your functions are not inside a class, for example, in utils/test files.
In such case, add at the end of the file:
`module_wrapper(logger)`  (import from `logger_local.MetaLogger`)

## General tip for using the wrappers:

- Use one return statement per function when possible (you can still `return None` or `return` for cleaner code)
  Also, always return a variable and not a statement (`return x` vs `return 3` or `return x+1`)

## Using with abstract class:

When using an abstract class, use ABCMetaLogger to avoid conflicts with MetaLogger.

```py
from abc import ABC
from logger_local.MetaLogger import ABCMetaLogger


class AbstractClass(ABC, metaclass=ABCMetaLogger):
    pass
```

## Using with logger object:

```py
from logger_local.LoggerLocal import Logger

YOUR_COMPONENT_ID = 1
YOUR_COMPONENT_NAME = "Some component name"

logger_code_init = {
    'component_id': YOUR_COMPONENT_ID,
    'component_name': YOUR_COMPONENT_NAME,
    'component_category': LoggerComponentEnum.ComponentCategory.Code,
    'developer_email_address': 'xxx.y@circ.zone'
}
logger = Logger.create_logger(object=logger_code_init)

SOME_METHOD = "some_method_or_function_name"
logger.start(SOME_METHOD, object={'arg1': arg1})

logger.start(SOME_METHOD, all_parameters)
logger.debug(...)
logger.info(...)
logger.error(...)
logger.critical(...)
logger.exception(" ....", object=exception)
# Send to logger.end all the return values / results
logger.end(SOME_METHOD, object={'result': result})
```

### In case of Tests (i.e. Unit-Tests)<br>

Please add logger.init(), logger.error() and logger.critical() to the Tests with all the fields below, so we can
monitor failing tests from central location.<br>
<br>
This is an example, please use the right values<br>

```py
YOUR_COMPONENT_NAME = 'your-package/tests/your_test.py'
object_unit_test_init = {
    'component_id': YOUR_COMPONENT_ID,
    'component_name': YOUR_COMPONENT_NAME,
    'component_category': LoggerComponentEnum.ComponentCategory.Unit_Test.value,
    'testing_framework': LoggerComponentEnum.testingFramework.Python_Unittest.value,
    'developer_email_address': 'xxx.y@circ.zone'
}
```

#### In each method<br>

```py
def some_test(self):
    YOUR_TEST_METHOD = "some_test"
    logger.start(YOUR_TEST_METHOD, object=all_parameters)
    logger.debug(...)
    logger.info(...)
    logger.error(...)
    logger.critical(...)
    logger.exception(" ....", object=exception)
    logger.end(YOUR_TEST_METHOD, {"result": result})
    return result
```

## logcal_loger.start()

Send the logger all the parameters of the  method/function<br>

```py
def func(aaa, bbb):
    logger.start("Hi", {
        'aaa': aaa,
        'bbb': bbb
    })
```

## Others

You can add any field value you want to any of the methods<br?

```py
logger.info("Hi", {
    'xxx': xxx_value,
    'yyy': yyy_value
})
```

## logger.end()

The general structure of a logger.end() calls

```py
result = .....
logger.end("....", {'result': result})
return result
```

You can insert log into DB with 2 different approaches:<br>

1. Writing a message :<br>
   ```py
   logger.info("your-message")
   logger.error("your-message")
   logger.warning("your-message")
   logger.debug("your-message")
   logger.verbose("your-message")
   logger.start("your-message")
   logger.end("your-message")
   logger.Init("your-message")
   logger.exception("your-message")
   ```

2. Writing an object (Dictionary):

   In case you have more properties to insert into the database,

   You can create a Dictionary object that contains the appropriate fields from the table and send it as a parameter.
   You can use logger.init if you want to save the fields for a few log actions. at the end please use
   clean_variables() function to clear those fields

   The dictionary's keys should be the same as the table's column names, and the values should be of the same type as
   the table's column types.

   ```py
        object_to_insert = {
            'user_id': 1,
            'profile_id': 1,
            'activity': 'logged in the system',
            'payload': 'your-message',
        }

        logger.info(object=object_to_insert)
   ```

   None of the fields above is mandatory. <br>

3. Writing both object and message:  
   just use both former approaches together as you can watch in here: <br>
   `logger.info("your-message",object=object_to_insert)`

Please add to `requirements.txt`<br>
replace the x with the latest version in pypi.org/project/logger-local<br>
`logger-local>=0.0.x` <br>
<br>
Please include at least two Logger calls in each method:<br>

```py
object1 = {arg1: arg1_value, arg2: arg2_value}
logger.start(object=object1)
# ...
object2 = {"return_value": return_value}
logger.end(object=object2)
return return_value
```

If you catch any exceptions, please use:

```py
try:
# ...
except Exception as exception:
    logger.error(object=exception)  # or object={"exception": exception, "whatever": whatever}
    raise exception
```

# Versions
0.0.175 We changed hagging.logs to support Python 3.13.3 so we can use dateime.UTC in criteria-local-python-package (which uses logger-local-python-package)
=======
# Logger Local Python Package

## TODOs

TODO Add support to honeycomb.io using our api-management-local-python-package direct method.<br>
>>>>>>> 9b3108c3fc9b883c4888f2979db2f7d1ee8ef559
