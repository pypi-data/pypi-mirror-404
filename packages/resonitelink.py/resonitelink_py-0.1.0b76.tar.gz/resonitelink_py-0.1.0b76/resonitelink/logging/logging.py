from typing import Any, Union
import logging
import sys
import os


__all__ = (
    'CustomFormatter',
    'CustomColourFormatter',
    'get_handler',
    'setup_logging'
)


class CustomFormatter(logging.Formatter):
    """
    Custom logging formatter without support for ANSI colour codes.

    Notes
    -----
    Logging format used is 'YYYY-mm-dd HH:MM:SS [<level>] <name>: <message>'
    Will print formatted exception using default formatting underneath the message, 
    prefixing two spaces before each line, with an additional newline at the end.
    If the extra-dictionary is present and contains a 'raw_msg' key with a string value, 
    it will be printed underneath the message formatted similarly to stacktraces,
    also prefixing two spaces before each line, with an additional newline at the end.

    """
    def __init__(self):
        """
        Constructor, calling super constructur of logging.Formatter class,
        passing the custom logging configuration as parameters.

        See Also
        --------
        logging.Formatter.__init__

        """
        super().__init__(
            '%(asctime)s [%(levelname)-8s] %(name)s: %(message)s',
            '%Y-%m-%d %H:%M:%S',
            style='%'
        )

    def format(self, record : logging.LogRecord):
        """
        Overrides format method from logging.Formatter and implements custom formatting logic as
        described in class docstring.

        Parameters
        ----------
        record : logging.LogRecord
            LogRecord instance containing the logging information to format.

        Returns
        -------
        str
            The formatted logging information as text.

        See Also
        --------
        logging.Formatter.format

        """
        exc_text = None
        if record.exc_info:
            exc_text = super().formatException(record.exc_info)
            exc_text = '  ' + '  '.join(exc_text.splitlines(True)) # Indent error text
            exc_text = exc_text + '\n' # Empty line after stacktrace
        
        raw_text = None
        if hasattr(record, 'raw_msg'):
            raw_text = record.raw_msg # type: ignore
            raw_text = '  ' + '  '.join(raw_text.splitlines(True)) # Indent raw text
            raw_text = '\n' + raw_text + '\n' # Empty line after raw text

        original_exc_text = record.exc_text
        original_msg = record.msg
        try:
            if exc_text: record.exc_text = exc_text # Set exc_text property to print formatted stacktrace
            if raw_text: record.msg += raw_text # Append additional raw text
            return super().format(record) # Format modified record state
        
        finally:
            # Restore original record state
            record.exc_text = original_exc_text
            record.msg = original_msg


class CustomColourFormatter(logging.Formatter):
    """
    Custom logging formatter with support for ANSI colour codes.

    Notes
    -----
    Logging format used is 'YYYY-mm-dd HH:MM:SS [<level>] <name>: <message>'
    Will print formatted exception using default formatting underneath the message, 
    prefixing two spaces before each line, with an additional newline at the end.
    If the extra-dictionary is present and contains a 'raw_msg' key with a string value, 
    it will be printed underneath the message formatted similarly to stacktraces,
    also prefixing two spaces before each line, with an additional newline at the end.

    The following ANSI colour codes are used to decorate the elements of the log messages:
        Timestamp and punctuation: '\\x1b[30;2m' (black text, dim)
        Log levels:
            NOTSET   (0) : '\\x1b[30;1m' (black text, bold)
            DEBUG    (10): '\\x1b[35;1m' (magenta text, bold)
            INFO     (20): '\\x1b[37;1m' (white text, bold)
            WARNING  (30): '\\x1b[33;1m' (yellow text, bold)
            ERROR    (40): '\\x1b[31;1m' (red text, bold)
            CRITICAL (50): '\\x1b[41;1m' (red background, bold)
        Logger name:    '\\x1b[34m' (blue text)
        Exception text: '\\x1b[31m' (red text)
        Log message:     default colour / no custom formatting

    ANSI codes are a bit weird to decipher if you're unfamiliar with them, so here's a refresher
    It starts off with a format like \\x1b[###m where ### is a semicolon separated list of commands
    The important ones here relate to colour.
    30-37 are black, red, green, yellow, blue, magenta, cyan and white in that order
    40-47 are the same except for the background
    90-97 are the same but "bright" foreground
    100-107 are the same as the bright ones but for the background.
    1 means bold, 2 means dim, 0 means reset, and 4 means underline.

    References
    ----------
    This class was taken from https://github.com/Rapptz/discord.py/blob/master/discord/utils.py and modified.
    
    Original License:

    The MIT License (MIT)

    Copyright (c) 2015-present Rapptz

    Permission is hereby granted, free of charge, to any person obtaining a
    copy of this software and associated documentation files (the "Software"),
    to deal in the Software without restriction, including without limitation
    the rights to use, copy, modify, merge, publish, distribute, sublicense,
    and/or sell copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
    OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
    DEALINGS IN THE SOFTWARE.

    """
    def __init__(self):
        """
        Constructor, creating a formatter for each logging level using the specified ANSI colour codes.

        See Also
        --------
        logging.Formatter.__init__

        """
        c_levels = [
            (logging.NOTSET,   '\x1b[30;1m'),
            (logging.DEBUG,    '\x1b[35;1m'),
            (logging.INFO,     '\x1b[37;1m'),
            (logging.WARNING,  '\x1b[33;1m'),
            (logging.ERROR,    '\x1b[31;1m'),
            (logging.CRITICAL, '\x1b[41;1m'),
        ]
        c_accent = '\x1b[90m'
        c_name   = '\x1b[34m'
        c_reset  = '\x1b[0m'

        self._formatters = {}
        for level, c_level in c_levels:
            self._formatters[level] = logging.Formatter(
                f"{c_accent}%(asctime)s [{c_reset}{c_level}%(levelname)-8s{c_reset}{c_accent}] " \
                f"{c_reset}{c_name}%(name)s{c_reset}{c_accent}: {c_reset}%(message)s",
                '%Y-%m-%d %H:%M:%S',
                style='%'
            )

    def format(self, record : logging.LogRecord) -> str:
        """
        Overrides format method from logging.Formatter and implements custom formatting logic as
        described in class docstring.

        Parameters
        ----------
        record : logging.LogRecord
            LogRecord instance containing the logging information to format.

        Returns
        -------
        str
            The formatted logging information as text.

        See Also
        --------
        logging.Formatter.format

        """
        formatter = self._formatters.get(record.levelno, self._formatters[logging.DEBUG])
        
        exc_text = None
        if record.exc_info:
            exc_text = formatter.formatException(record.exc_info)
            exc_text = '  ' + '  '.join(exc_text.splitlines(True)) # Indent error text
            exc_text = exc_text + '\n' # Empty line after stacktrace
            exc_text = f'\x1b[31m{exc_text}\x1b[0m' # Add color red
        
        raw_text = None
        if hasattr(record, 'raw_msg'):
            raw_text = record.raw_msg # type: ignore
            raw_text = '  ' + '  '.join(raw_text.splitlines(True)) # Indent raw text
            raw_text = '\n' + raw_text + '\n' # Empty line after raw text
            raw_text = f'\x1b[36m{raw_text}\x1b[0m' # Add color cyan

        original_exc_text = record.exc_text
        original_msg = record.msg
        try:
            if exc_text: record.exc_text = exc_text # Set exc_text property to print formatted stacktrace
            if raw_text: record.msg += raw_text # Append additional raw text

            return formatter.format(record) # Format modified record state
        
        finally:
            # Restore original record state
            record.exc_text = original_exc_text
            record.msg = original_msg


def is_docker() -> bool:
    """
    Determine if the current environment is running in a docker container.

    Returns
    -------
    bool
        Whether or not the current environment is running in a docker container.

    References
    ----------
    This class was taken from https://github.com/Rapptz/discord.py/blob/master/discord/utils.py.
    
    Original License:

    The MIT License (MIT)

    Copyright (c) 2015-present Rapptz

    Permission is hereby granted, free of charge, to any person obtaining a
    copy of this software and associated documentation files (the "Software"),
    to deal in the Software without restriction, including without limitation
    the rights to use, copy, modify, merge, publish, distribute, sublicense,
    and/or sell copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
    OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
    DEALINGS IN THE SOFTWARE.    
    
    """
    path = '/proc/self/cgroup'
    return os.path.exists('/.dockerenv') or (os.path.isfile(path) and any('docker' in line for line in open(path)))


def stream_supports_colour(stream: Any) -> bool:
    """
    Determine if the provided stream supports ANSI color codes.

    Parameters
    ----------
    stream : Any
        The stream the check for color support.

    Returns
    -------
    bool
        Whether or not the stream supports color.

    References
    ----------
    This class was taken from https://github.com/Rapptz/discord.py/blob/master/discord/utils.py.
    
    Original License:

    The MIT License (MIT)

    Copyright (c) 2015-present Rapptz

    Permission is hereby granted, free of charge, to any person obtaining a
    copy of this software and associated documentation files (the "Software"),
    to deal in the Software without restriction, including without limitation
    the rights to use, copy, modify, merge, publish, distribute, sublicense,
    and/or sell copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
    OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
    DEALINGS IN THE SOFTWARE.

    """
    is_a_tty = hasattr(stream, 'isatty') and stream.isatty()

    # Pycharm and Vscode support colour in their inbuilt editors
    if 'PYCHARM_HOSTED' in os.environ or os.environ.get('TERM_PROGRAM') == 'vscode':
        return is_a_tty

    if sys.platform != 'win32':
        # Docker does not consistently have a tty attached to it
        return is_a_tty or is_docker()

    # ANSICON checks for things like ConEmu
    # WT_SESSION checks if this is Windows Terminal
    return is_a_tty and ('ANSICON' in os.environ or 'WT_SESSION' in os.environ)


def get_handler(use_colour_if_supported : bool = True) -> logging.StreamHandler:
    """
    Returns a StreamHandler with a formatter attached.

    If use_colour_if_supported is True and the stream of the handler supports color output,
    a CustomColourFormatter is used. Otherwise default to CustomFormatter.

    Parameters
    ----------
    use_colour_if_supported : bool
        Whether to consider using CustomColourFormatter.

    Returns
    -------
    logging.StreamHandler
        The newly created StreamHandler

    """
    handler = logging.StreamHandler()
    if use_colour_if_supported and stream_supports_colour(handler.stream):
        formatter = CustomColourFormatter()
    else:
        formatter = CustomFormatter()
    handler.setFormatter(formatter)

    return handler


def setup_logging(file_path : Union[str, None] = None, log_level : int = logging.INFO, file_log_level : int = logging.INFO, use_colour_if_supported : bool = True) -> None:
    """
    Function to setup logging configuration. Should only be called once at startup.

    Parameters
    ----------
    file_path : `str` or `None`
        If set, also attaches a logging.FileHandler for the specified file to the root logger.
    log_level : `int`, optional
        Which logging level to use. Defaults to `logging.INFO`.
    file_log_level : `int`, optional
        Which logging level the file handler should use. Defaults to `logging.INFO`.
    use_colour_if_supported : `bool`, optional
        Whether to consider using CustomColourFormatter.

    Info
    ----
    For root logger, sets up a logging handler with either `CustomColourFormatter` as formatter 
    if the logging stream supports ANSI colour codes, or `CustomFormatter` if it doesn't.
    Optionally attaches a `FileHandler` to the root logger, using `CustomFormatter`.
    Sets the logging level of the root logger to `logging.DEFAULT`.
    Lastly, adds a callback for `sys.excepthook` to allow our modified root logger to log
    exceptions on root level using `logging.CRITICAL` as log level.

    """
    root_logger = logging.getLogger()
    if len(root_logger.handlers) > 0:
        # Don't do anything if logging is already configured.
        return

    root_logger.setLevel(log_level)
    root_logger.addHandler(get_handler(use_colour_if_supported))

    if file_path:
        # Also set up file logger
        file_handler = logging.FileHandler(file_path)
        file_handler.setLevel(file_log_level)
        file_handler.setFormatter(CustomFormatter())
        root_logger.addHandler(file_handler)

    # Handle uncaught exceptions with logger as well
    def _handle_uncaught_exception(exc_type : Any, exc_value : Any, exc_traceback : Any) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            root_logger.critical("KeyboardInterrupt received.")
        else:
            root_logger.critical("App has encountered an unhandled exception!", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = _handle_uncaught_exception
