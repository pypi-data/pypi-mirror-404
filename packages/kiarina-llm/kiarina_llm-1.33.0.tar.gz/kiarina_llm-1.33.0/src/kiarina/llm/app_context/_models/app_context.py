from pydantic import BaseModel

from .._types.fs_name import FSName


class AppContext(BaseModel):
    """
    Application Context
    """

    app_author: FSName
    """
    Application author

    Used in PlatformDirs.
    """

    app_name: FSName
    """
    Application name

    Used in PlatformDirs.
    """
