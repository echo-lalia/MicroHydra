"""
Naive tool for extracting zip files.

Current limitations:
- Only supports the DEFLATE compression method
- ZIP must include directories (not just imply the directory from the file name)
- ZIP64 not supported
- Central directory is completely ignored
  (therefore all the required data must be in the local headers)

"""

import deflate
import os

_LOCAL_HEADER_SIGN = const(b'PK\x03\x04')
_CENTRAL_HEADER_SIGN = const(b'PK\x01\x02')

class ZipExtractor:
    def __init__(self, zip_path):
        # small arrays of various sizes are used to easily read
        # attributes of various lengths
        self.array_4 = bytearray(4)
        self.array_2 = bytearray(2)
        self.array_1 = bytearray(1)

        self.zip_path = zip_path


    @staticmethod
    def _arr2int(array):
        return int.from_bytes(bytes(array), 'little')


    @staticmethod
    def _arr2str(array):
        return bytes(array).decode("utf-8")


    def _extract_next_file(self, file, out_path, wbits):
        """
        Naively extract files from zip one-by-one, ignoring the "central directory".
        """
        # Start by scanning local header for needed info

        # First bytes should mark a local header
        file.readinto(self.array_4) # (byte 4)
        if self.array_4 != _LOCAL_HEADER_SIGN:
            if self.array_4 == _CENTRAL_HEADER_SIGN:
                return # no more local file data
            print("WARNING: ZipExtractor didn't find expected file header!")

        
        # seek to compression method
        file.seek(4, 1) # (byte 8)
        file.readinto(self.array_2)
        compression_method = self._arr2int(self.array_2) # (byte 10)
        
        # skip to uncompressed size
        file.seek(12, 1) # (byte 22)
        file.readinto(self.array_4) # (byte 26)
        uncompressed_size = self._arr2int(self.array_4)

        # read name and extra data length
        file.readinto(self.array_2) # (byte 28)
        name_len = self._arr2int(self.array_2)
        
        file.readinto(self.array_2) # (byte 30)
        ext_len = self._arr2int(self.array_2)

        # read name (variable size) into new array
        name_arr = bytearray(name_len)
        file.readinto(name_arr) # (byte 30 + n)
        name = self._arr2str(name_arr)
        
        # seek past extra data
        file.seek(ext_len, 1) # (byte 30+n+m)

        # find full output file path
        full_path = '/'.join([out_path, name])
        
        # Make directory if thats what this is
        if uncompressed_size == 0 and name.endswith('/'):
            try:
                # trailing slash must be removed
                print(f"Making {full_path}")
                os.mkdir(full_path[:-1])
            except:
                pass # directory might exist already

        # if this has a name and a valid compression method,
        # it should be a valid file
        elif name and (compression_method in (0, 8)):
            print(f"Writing {full_path}")
            # deflate and write file
            with deflate.DeflateIO(file, deflate.RAW, wbits) as d:
                with open(full_path, 'wb') as output_file:
                    remaining_bytes = uncompressed_size + 1

                    while remaining_bytes > 0:
                        to_read = min(128, remaining_bytes)
                        
                        output_file.write(d.read(to_read))
                        
                        remaining_bytes -= to_read

        # get next file:
        self._extract_next_file(file, out_path, wbits)


    def extract(self, out_path, wbits=14):
        with open(self.zip_path, "rb") as f:
            self._extract_next_file(f, out_path, wbits)
