
def stringify_exception(exception: Exception) -> str:
    """Convert an exception to a string information."""
    exception_type = type(exception).__name__
    message = str(exception)
    a_traceback = exception.__traceback__
    file_name = a_traceback.tb_frame.f_code.co_filename if a_traceback else None
    line_number = a_traceback.tb_lineno if a_traceback else None
    function_name = a_traceback.tb_frame.f_code.co_name if a_traceback else None
    return (
        f"{exception_type}: {message}\n"
        f"  File \"{file_name}\", line {line_number}, in {function_name}"
    )
