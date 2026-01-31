from PIL import Image
from pathlib import PurePath
from bs4 import UnicodeDammit
from .matrix_methods import *

STREAM_BLOCK_SIZE_RANGE = (24, 633)
DEFAULT_STREAM_BLOCK_SIZE = 63

class MessageStreamer:

    acceptableFileExtensionForText = [".txt"]
    acceptableFileExtensionForImage = [".jpg"]
    acceptableEncodings = ["ascii", "utf_8","utf-8"]

    def __init__(self, filePath, streamBlockSize = DEFAULT_STREAM_BLOCK_SIZE,readMode = "rb"):
        """
        class is to "stream" data from .a file source, (image = jpg file)|(text = 'literal'|'csv'), set `readMode` to "r" for reading csv files
        """
        assert readMode in ["rb","r"]
        self.filePath = PurePath(filePath)
        self.rm = readMode
        self.file_to_msg_alphabet()
        self.openedFile = None
        self.open_file()
        assert streamBlockSize >= STREAM_BLOCK_SIZE_RANGE[0] and streamBlockSize <= STREAM_BLOCK_SIZE_RANGE[1], "stream block size inaccurate"
        self.streamBlockSize = streamBlockSize
        self.blockData = []

    def file_to_msg_alphabet(self):
        if self.filePath.suffix in MessageStreamer.acceptableFileExtensionForImage:
            self.messageAlphabet = MessageAlphabet.pixelColor
            self.mav = "pic"
        elif self.filePath.suffix in MessageStreamer.acceptableFileExtensionForText:
            self.messageAlphabet = MessageAlphabet.alphanumeric
            self.mav = "tex"
        else:
            raise ValueError("file {} is invalid message".format(self.filePath))

    def open_file(self):
        if self.mav == "pic":
            self.openedFile = Image.open(str(self.filePath))
            self.loadedPic = self.openedFile.load() # CAUTION: loads entire image into memory
            self.streamIndex = (0,0)
        else:
            self.check_valid_text_file_encoding()
            self.openedFile = open(str(self.filePath),self.rm)
            self.streamIndex = 0

        return

    def check_valid_text_file_encoding(self):
        if self.mav != "tex": return

        with open(str(self.filePath), 'rb') as fi:
            content = fi.read(10 ** 5)
            suggestion = UnicodeDammit(content)
            self.textEncoding = suggestion.original_encoding
            assert self.textEncoding in MessageStreamer.acceptableEncodings, "text encoding {} is wrong".format(self.textEncoding)

    def stream_block(self):
        """
        :return: block of data, terminate stream, finished stream
        :rtype: list,bool,bool
        """

        self.blockData = []
        c = 0
        if self.mav == "tex":
            while c < self.streamBlockSize:

                # case: "rb"
                if self.rm == "rb":
                    b = self.openedFile.read(1)
                # case: "r"
                else:
                    b = self.openedFile.readline()
                    b = string_to_vector(b, castFunc = cr)

                if len(b) == 0:
                    break
                self.streamIndex += 1
                self.blockData.append(b)
                c += 1
        else:

            # x then y
            def next_index(i):
                i1,i2 = (i[0] + 1, i[1])

                if i1 >= self.openedFile.size[0]:
                    i1, i2 = 0, i2 + 1

                if i2 >= self.openedFile.size[1]:
                    return None, False

                return (i1,i2), True

            sz = self.openedFile.size
            while c < self.streamBlockSize:
                # read pixel
                v = self.loadedPic[self.streamIndex[0], self.streamIndex[1]]
                self.streamIndex, stat = next_index(self.streamIndex)
                if not stat: break
                self.blockData.append(v)
                c += 1
        return

    def stream(self):

        if type(self.openedFile) == type(None):
            return False
        self.stream_block()

        if len(self.blockData) == 0:
            self.end_stream()
            return False
        return True

    def end_stream(self):
        if type(self.openedFile) == type(None):
            return
        self.openedFile.close()
        self.openedFile = None

class MessageAlphabet:

    alphanumeric = [(32, 127)]
    pixelColor = [(0, 256), (0, 256), (0, 256)]
