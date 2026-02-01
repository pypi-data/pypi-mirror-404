"""
Utility for safe function calls with standardized error logging.
"""

def safe_call(fn, logger, msg_template: str, *, exc_info: bool = False):
    """
    Execute fn(), logging any exception using msg_template.

    Parameters
    ----------
    fn : callable
        Zero-argument function to execute.
    logger : logging.Logger
        Logger to use for error reporting.
    msg_template : str
        Message template to log on error. Use '{e}' as placeholder for the exception.
    exc_info : bool
        If True, includes traceback in log.

    Returns
    -------
    The result of fn(), or None if an exception occurred.
    """
    try:
        return fn()
    except Exception as e:
        logger.error(msg_template.format(e=e), exc_info=exc_info)
        return None