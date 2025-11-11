import shutil
import zipfile


def extract_file_from_zip_archive(
    zip_path,
    output_path,
    condition=lambda zipinfo: True,
    buffer_size=32 * 1024,
):
    """
    Extract a single file from a ZIP archive to the specified path

    `condition` is a callable for filtering the ZipInfo objects in the archive. There
    should be exactly one matching member.
    """
    with zipfile.ZipFile(zip_path) as zf:
        matching = [zipinfo for zipinfo in zf.infolist() if condition(zipinfo)]
        assert len(matching) == 1, f"Expected exactly one matching file: {matching}"
        with output_path.open("wb") as output_file:
            input_file = zf.open(matching[0])
            shutil.copyfileobj(input_file, output_file, buffer_size)
