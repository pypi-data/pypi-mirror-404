class WINDOWS_file_attribs:
    @staticmethod

    def impose_hide_attribute(file: str):
        import subprocess as sb

        try:
            sb.run(
                f'attrib +h "{file}"',
                shell=True, check=True,
            )
        except Exception as err:
            raise err
    def revoke_hide_attribute(file: str):
        import subprocess as sb

        try:
            sb.run(
                f'attrib -h "{file}"',
                shell=True, check=True,
            )
        except Exception as err:
            raise err
    def impose_system_attribute(file: str):
        import subprocess as sb

        try:
            sb.run(
                f'attrib +s "{file}"',
                shell=True, check=True,
            )
        except Exception as err:
            raise err
    def revoke_system_attribute(file: str):
        import subprocess as sb

        try:
            sb.run(
                f'attrib -s "{file}"',
                shell=True, check=True,
            )
        except Exception as err:
            raise err
    def impose_read_only_attribute(file: str):
        import subprocess as sb

        try:
            sb.run(
                f'attrib +r "{file}"',
                shell=True, check=True,
            )
        except Exception as err:
            raise err
    def revoke_read_only_attribute(file: str):
        import subprocess as sb

        try:
            sb.run(
                f'attrib -r "{file}"',
                shell=True, check=True,
            )
        except Exception as err:
            raise err
    def impose_archive_attribute(file: str):
        import subprocess as sb

        try:
            sb.run(
                f'attrib +a "{file}"',
                shell=True, check=True,
            )
        except Exception as err:
            raise err
    def revoke_archive_attribute(file: str):
        import subprocess as sb

        try:
            sb.run(
                f'attrib -a "{file}"',
                shell=True, check=True,
            )
        except Exception as err:
            raise err
    def impose_not_content_indexed_attribute(file: str):
        import subprocess as sb

        try:
            sb.run(
                f'attrib +i "{file}"',
                shell=True, check=True,
            )
        except Exception as err:
            raise err
    def revoke_not_content_indexed_attribute(file: str):
        import subprocess as sb

        try:
            sb.run(
                f'attrib -i "{file}"',
                shell=True, check=True,
            )
        except Exception as err:
            raise err
    def impose_offline_attribute(file: str):
        import subprocess as sb

        try:
            sb.run(
                f'attrib +o "{file}"',
                shell=True, check=True,
            )
        except Exception as err:
            raise err
    def revoke_offline_attribute(file: str):
        import subprocess as sb

        try:
            sb.run(
                f'attrib -o "{file}"',
                shell=True, check=True,
            )
        except Exception as err:
            raise err
    def impose_integrity_attribute(file: str):
        import subprocess as sb

        try:
            sb.run(
                f'attrib +v "{file}"',
                shell=True, check=True,
            )
        except Exception as err:
            raise err
    def revoke_integrity_attribute(file: str):
        import subprocess as sb

        try:
            sb.run(
                f'attrib -v "{file}"',
                shell=True, check=True,
            )
        except Exception as err:
            raise err
    def impose_no_scrub_attribute(file: str):
        import subprocess as sb

        try:
            sb.run(
                f'attrib +x "{file}"',
                shell=True, check=True,
            )
        except Exception as err:
            raise err
    def revoke_no_scrub_attribute(file: str):
        import subprocess as sb

        try:
            sb.run(
                f'attrib -x "{file}"',
                shell=True, check=True,
            )
        except Exception as err:
            raise err
    def impose_pinned_attribute(file: str):
        import subprocess as sb

        try:
            sb.run(
                f'attrib +p "{file}"',
                shell=True, check=True,
            )
        except Exception as err:
            raise err
    def revoke_pinned_attribute(file: str):
        import subprocess as sb

        try:
            sb.run(
                f'attrib -p "{file}"',
                shell=True, check=True,
            )
        except Exception as err:
            raise err
    def impose_unpinned_attribute(file: str):
        import subprocess as sb

        try:
            sb.run(
                f'attrib +u "{file}"',
                shell=True, check=True,
            )
        except Exception as err:
            raise err
    def revoke_unpinned_attribute(file: str):
        import subprocess as sb

        try:
            sb.run(
                f'attrib -u "{file}"',
                shell=True, check=True,
            )
        except Exception as err:
            raise err
    def impose_smr_blob_attribute(file: str):
        import subprocess as sb

        try:
            sb.run(
                f'attrib +b "{file}"',
                shell=True, check=True,
            )
        except Exception as err:
            raise err
    def revoke_smr_blob_attribute(file: str):
        import subprocess as sb

        try:
            sb.run(
                f'attrib -b "{file}"',
                shell=True, check=True,
            )
        except Exception as err:
            raise err