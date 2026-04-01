from typing import Annotated

from pydantic import StringConstraints

FirstName = Annotated[str, StringConstraints(max_length=150, strip_whitespace=True)]
LastName = Annotated[str, StringConstraints(max_length=150, strip_whitespace=True)]
MiddleName = Annotated[str, StringConstraints(max_length=150, strip_whitespace=True)]
PhoneStr = Annotated[str, StringConstraints(min_length=3, max_length=150)]
PasswordStr = Annotated[str, StringConstraints(min_length=8)]
