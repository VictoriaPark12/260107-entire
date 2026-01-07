from dataclasses import dataclass
import pandas as pd


@dataclass
class DataSets(object):
    _fname: str = ''  # file name
    _dname: str = ''  # data path
    _sname: str = ''  # save path
    _data: pd.DataFrame = None
    _id: str = ''
    _localdate: str = ''
    _title: str = ''
    _content: str = ''
    _userId: str = ''
    _emotion: str = ''  # label

    @property
    def fname(self) -> str:
        return self._fname

    @fname.setter
    def fname(self, fname):
        self._fname = fname

    @property
    def dname(self) -> str:
        return self._dname

    @dname.setter
    def dname(self, dname):
        self._dname = dname

    @property
    def sname(self) -> str:
        return self._sname

    @sname.setter
    def sname(self, sname):
        self._sname = sname

    @property
    def data(self) -> object:
        return self._data

    @data.setter
    def data(self, data):
        self._data = data

    @property
    def id(self) -> str:
        return self._id

    @id.setter
    def id(self, id):
        self._id = id

    @property
    def localdate(self) -> str:
        return self._localdate

    @localdate.setter
    def localdate(self, localdate):
        self._localdate = localdate

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, title):
        self._title = title

    @property
    def content(self) -> str:
        return self._content

    @content.setter
    def content(self, content):
        self._content = content

    @property
    def userId(self) -> str:
        return self._userId

    @userId.setter
    def userId(self, userId):
        self._userId = userId

    @property
    def emotion(self) -> str:
        return self._emotion

    @emotion.setter
    def emotion(self, emotion):
        self._emotion = emotion

