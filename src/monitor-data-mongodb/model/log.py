from datetime import datetime, timezone
from typing import Annotated, Optional

from bson import ObjectId as _ObjectId

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, model_validator
from pydantic.functional_validators import AfterValidator


def check_object_id(value: str) -> str:
    if not _ObjectId.is_valid(value):
        raise ValueError('Invalid ObjectId')
    return value


def is_less_than(a: datetime):
    """
    check is datetime less than now
    :param a: datetime to check
    :return: boolean
    """
    if a.utcoffset() is None:
        if a < datetime.now():
            return True
    else:
        if a < datetime.now(timezone.utc):
            return True
    return False


class LogNoValidation(BaseModel):
    """
    Skip validation to improve performance
    Used when
    1. the log record is returned from mongodb which should be validated
    2. going to return the json as response
    """
    _id: Annotated[str, AfterValidator(check_object_id)]
    log_id: str
    user_id: str
    tool_id: str
    start_dt: datetime
    end_dt: Optional[datetime] = None
    create_dt: Optional[datetime] = None
    update_dt: Optional[datetime] = None
    is_delete: bool = False
    delete_dt: Optional[datetime] = None

    def to_json(self, exclude=None):
        if exclude is None:
            exclude = ['is_delete', 'delete_dt', 'create_dt', 'update_dt']
        return jsonable_encoder(self, exclude_none=True, exclude=exclude)

    def to_bson(self):
        data = self.model_dump(by_alias=True, exclude_none=True)
        if data.get("_id") is None:
            data.pop("_id", None)
        return data


class Log(LogNoValidation):
    """
    Used when want to run validation on the object
    """
    @model_validator(mode='before')
    def ensure_start_dt(cls, data):
        if "start_dt" not in data:
            raise ValueError("Start date time should exist")
        if type(data['start_dt']) is str:
            data['start_dt'] = datetime.fromisoformat(data['start_dt'])
        if not is_less_than(data['start_dt']):
            raise ValueError("Start date time is greater than current time")
        if 'end_dt' in data and type(data['end_dt']) is str:
            data['end_dt'] = datetime.fromisoformat(data['end_dt'])
        return data

    @model_validator(mode='after')
    def ensure_end_dt(self) -> 'Log':
        end_dt = self.end_dt
        if end_dt is not None:
            if not is_less_than(self.end_dt):
                raise ValueError("End date time is greater than current time")
            if end_dt < self.start_dt:
                raise ValueError("End time is less than start time")
        return self
