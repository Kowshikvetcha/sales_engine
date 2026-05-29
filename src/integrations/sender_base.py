from abc import ABC, abstractmethod

class EmailSender(ABC):
    """
    Abstract interface for email sending implementations.
    Decoupled from specific provider details.
    """
    @abstractmethod
    def send_email(self, to_email: str, subject: str, body: str) -> str:
        """
        Sends an email and returns the message ID.
        Raises an exception if the send fails.
        """
        pass
