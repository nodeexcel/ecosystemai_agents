from pydantic import BaseModel, Field
from typing import Literal

class Snippet(BaseModel):
    data: str =  Field(max_length=1500)
    data_type: Literal['snippet', 'website', 'files']