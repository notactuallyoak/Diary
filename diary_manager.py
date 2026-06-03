# Zlib Compression, binary file I/O, readable file headers

from config import FILE_HEADER
import zlib

class DiaryManager:

    @staticmethod
    def _get_header_bytes():
        return FILE_HEADER.encode('utf-8') + b"\n"

    @staticmethod
    def save_to_file(file_path: str, text_content: str):
        # compress the text
        compressed_bytes = zlib.compress(text_content.encode('utf-8'))

        # glue the readable header and the compressed data together
        final_binary_data = DiaryManager._get_header_bytes() + compressed_bytes

        # write to file
        with open(file_path, 'wb') as f:
            f.write(final_binary_data)

    @staticmethod
    def load_from_file(file_path: str) -> str:
        with open(file_path, 'rb') as f:
            file_data = f.read()

        # get the exact byte-length of the header from config
        header_bytes = DiaryManager._get_header_bytes()
        header_len = len(header_bytes)

        if not file_data.startswith(header_bytes):
            raise ValueError("InvalidFileFormat")

        # slice off the header to get pure compressed bytes
        compressed_bytes = file_data[header_len:]

        try:
            # decompress and decode back to normal plain text
            decompressed_text = zlib.decompress(compressed_bytes).decode('utf-8')
            return decompressed_text
        except zlib.error:
            raise ValueError("CorruptedFile")

    @staticmethod
    def parse_last_timestamp(text: str):
        try:
            lines = text.strip().split('\n')
            for line in reversed(lines):
                cleaned_line = line.strip()
                if cleaned_line.startswith("[") and "]" in cleaned_line and ":" in cleaned_line:
                    potential_timestamp = cleaned_line.split("]")[0][1:].strip()
                    if len(potential_timestamp) == 16:
                        return potential_timestamp
        except Exception:
            pass
        return None