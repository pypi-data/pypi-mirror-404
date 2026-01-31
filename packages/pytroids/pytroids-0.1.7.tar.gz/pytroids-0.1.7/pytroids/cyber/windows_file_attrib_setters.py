class WINDOWS_file_attribs:
    def impose_hide_attribute(file: str):
        import subprocess as sb

        try:
            sb.run(
                f"attrib +h {file}",
                shell=True,
            )
        except Exception as err:
            raise err
    def revoke_hide_attribute(file: str):
        import subprocess as sb

        try:
            sb.run(
                f"attrib -h {file}",
                shell=True,
            )
        except Exception as err:
            raise err
    def impose_system_attribute(file: str):
        import subprocess as sb

        try:
            sb.run(
                f"attrib +s {file}",
                shell=True,
            )
        except Exception as err:
            raise err
    def revoke_system_attribute(file: str):
        import subprocess as sb

        try:
            sb.run(
                f"attrib -s {file}",
                shell=True,
            )
        except Exception as err:
            raise err
    def impose_read_only_attribute(file: str):
        import subprocess as sb

        try:
            sb.run(
                f"attrib +r {file}",
                shell=True,
            )
        except Exception as err:
            raise err
    def revoke_read_only_attribute(file: str):
        import subprocess as sb

        try:
            sb.run(
                f"attrib -r {file}",
                shell=True,
            )
        except Exception as err:
            raise err