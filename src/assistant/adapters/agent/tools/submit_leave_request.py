"""L'outil qui agit : déposer une demande de congé. Fictif, il n'écrit dans aucun système."""

from itertools import count

from langchain.tools import tool
from langchain_core.tools import BaseTool

TOOL_NAME = "submit_leave_request"


def submit_leave_request_tool() -> BaseTool:
    request_numbers = count(1)

    @tool(TOOL_NAME, parse_docstring=True)
    def submit_leave_request(start_date: str, end_date: str) -> str:
        """Submit a leave request for the user. Use it only when the user asks to submit or book leave.

        Args:
            start_date: First day of leave, in YYYY-MM-DD format.
            end_date: Last day of leave, in YYYY-MM-DD format.
        """
        return f"Leave request LEAVE-{next(request_numbers)} submitted, from {start_date} to {end_date}."

    return submit_leave_request
