class Remote:
    def __init__(self, hostname=None, code=None, res_width=None, res_height=None):
        self._hostname = hostname
        self._code = code
        self._res_width = res_width
        self._res_height = res_height

    @property
    def hostname(self):
        return self._hostname

    @hostname.setter
    def hostname(self, value):
        self._hostname = value

    @property
    def code(self):
        return self._code

    @code.setter
    def code(self,value):
        self._code = value

    @property
    def res_width(self):
        return self._res_width

    @res_width.setter
    def res_width(self, value):
        self._res_width = value

    @property
    def res_height(self):
        return self._res_height

    @res_height.setter
    def res_height(self, value):
        self._res_height = value

    def copy_from(self, other):
        if isinstance(other, Remote):
            self.hostname = other.hostname
            self.code = other.code
            self.res_width = other.res_width
            self.res_height = other.res_height

    def __repr__(self):
        return f"{self.hostname}, {self.code}, {self.res_width}, {self.res_height}"

    def __len__(self):
        return 69

