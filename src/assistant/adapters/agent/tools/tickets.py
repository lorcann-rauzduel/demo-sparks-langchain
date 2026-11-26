"""Les outils de la base métier : lire un ticket, en lecture seule."""

from langchain.tools import tool
from langchain_core.tools import BaseTool

from assistant.adapters.tickets.sqlite_tickets import SqliteTickets


def get_ticket_status_tool(tickets: SqliteTickets) -> BaseTool:
    @tool(parse_docstring=True)
    def get_ticket_status(ticket_id: int) -> str:
        """Return the title, status and priority of a support ticket. Use it for any question about a ticket.

        Args:
            ticket_id: The ticket number given by the user.
        """
        return tickets.status(ticket_id) or f"No ticket {ticket_id}."

    return get_ticket_status


CLOSE_TICKET = "close_ticket"


def close_ticket_tool(tickets: SqliteTickets) -> BaseTool:
    @tool(CLOSE_TICKET, parse_docstring=True)
    def close_ticket(ticket_id: int) -> str:
        """Close a support ticket. Use it only when the user explicitly asks to close a ticket.

        Args:
            ticket_id: The ticket number given by the user.
        """
        return f"Ticket {ticket_id} closed." if tickets.close(ticket_id) else f"No ticket {ticket_id}."

    return close_ticket
