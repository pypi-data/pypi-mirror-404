from pydantic import Field

from common.message.message import Message


class Bool(Message):
    """
    Boolean value message.

    Example:
        ```python
        from common.message import Bool

        msg = Bool(value=True)
        if msg.value:
            print("Value is true")
        ```
    """

    _type = "antioch/bool"
    value: bool = Field(description="Boolean value")


class Int(Message):
    """
    Integer value message.

    Example:
        ```python
        from common.message import Int

        msg = Int(value=42)
        print(f"The answer is {msg.value}")
        ```
    """

    _type = "antioch/int"
    value: int = Field(description="Integer value")


class Float(Message):
    """
    Float value message.

    Example:
        ```python
        from common.message import Float

        msg = Float(value=3.14159)
        print(f"Pi is approximately {msg.value:.2f}")
        ```
    """

    _type = "antioch/float"
    value: float = Field(description="Floating-point value")


class String(Message):
    """
    String value message.

    Example:
        ```python
        from common.message import String

        msg = String(value="Hello, World!")
        print(msg.value)
        ```
    """

    _type = "antioch/string"
    value: str = Field(description="String value")
