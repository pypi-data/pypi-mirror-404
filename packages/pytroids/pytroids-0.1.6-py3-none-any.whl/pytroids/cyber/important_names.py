class imp_names:
    def fetch_logged_in_username():
        from getpass import getuser

        return f"{getuser()}"
    def fetch_device_name():
        import socket

        return f"{socket.gethostname()}"
    def fetch_IP():
        import socket

        return f"{socket.gethostbyname(socket.gethostname())}"