class Connection:
    def __init__(self, remote_code, controller_code):
        self.remote_code = remote_code
        self.controller_code = controller_code

class Connections:
    def __init__(self):
        self.connections: list[Connection] = []

    def add(self, new_connection: Connection):
        if self.aspects_exist(new_connection):
            self.connections.append(new_connection)

    def aspects_exist(self, new_connection: Connection):
        new_remote_code = new_connection.remote_code
        new_controller_code = new_connection.controller_code
        for connection in self.connections:
            remote_code = connection.remote_code
            controller_code = connection.controller_code
            if (new_remote_code == remote_code or new_remote_code == controller_code) or (new_controller_code == remote_code or new_controller_code == controller_code):
                raise Exception("Cannot add new connection to connections as an aspect of the connection already exists"
                                f"{new_remote_code=}, {new_controller_code=}, {remote_code=}, {controller_code=}")
        return True

    def remove(self, connection):
        self.connections.remove(connection)

    def remove_connection_associated_with_code(self, code):
        for connection in self.connections:
            remote_code = connection.remote_code
            controller_code = connection.controller_code
            if code == remote_code or code == controller_code:
                self.connections.remove(connection)
                return remote_code if code == remote_code else controller_code  # return the code of the user that was connected to the removed user
        return False

