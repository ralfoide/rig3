#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: Template generator

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

import os

#------------------------
_WS = " \t\f"
_EOL = "\r\n"

#------------------------
class Buffer(object):
    """
    A buffer wraps a data string with a "current position" offset.
    All operations advance the offset.
    
    If the offset is 0 and the linesep argument is defined (which defaults
    to os.linesep), then all line separators will be converted to be uniform.
    Set linesep to None if you want to avoid line separator conversion.
    """
    def __init__(self, filename, data, offset=0, linesep=os.linesep):
        self.filename = filename
        self.data = data
        self.offset = offset
        self.lineno = 1
        self.lineoffset = 0
        self.linesep = linesep
        if offset == 0 and linesep:
            self.ConvertLineSep()

    def CurrCol(self):
        return self.offset - self.lineoffset + 1

    def ConvertLineSep(self, linesep=None):
        """
        This method tries to convert all line endings in the buffer to the
        'default' of the given platform.
        
        The buffer is expected to contain line separators consistent with:
        - only \n, aka unix mode
        - only \r, aka MacOS mode
        - only \r\n pairs, aka DOS/Windows mode
        
        If the linesep argument is defined, it redefines the current Buffer's
        linesep. Otherwise the default (as given to the constructor) is used.
        
        The operation happens in-place to the whole data buffer, independant of the
        current offset position. If offset is not 0, it will raise an exception and
        do nothing since it would ruin the current offset (no attempt is made to fix it).
        
        Returns self (the Buffer) so that you can chain commands.
        """
        if self.offset != 0:
            raise RuntimeError("ConvertLineSep will not apply to buffer with offset=%d" %
                               self.offset)
        if linesep is not None:
            self.linesep = linesep
        sep = ""
        if "\r" in self.data:
            sep = "\r"
            if self.data.find("\r\n") != -1:
                sep = "\r\n"
        elif "\n" in self.data:
            sep = "\n"
        if sep and sep != self.linesep:
            self.data = self.data.replace(sep, self.linesep)
        return self

    def EndReached(self):
        """
        Returns true if the end of the buffer has been reached
        """
        return self.offset >= len(self.data)

    def StartsWith(self, word, whitespace=False, consume=False):
        """
        Returns true if the given word is present at the current position
        in the buffer.
        If whitespace is true, some whitespace must be present after the word
        or the end of the buffer must have been reached.
        If consume is True, the content is 'consumed' (i.e. offset is moved to end)
        if found. If whitespace is requested, it also consumes the whitespace.
        
        Line numbers: Since this methods will never pass over a line separator,
        it doesn't touch Buffer.lineno
        
        Returns false if the end of the buffer has been reached or if the
        given word is empty.
        """
        if not word or self.EndReached():
            return False
        end = self.offset + len(word)
        if self.data[self.offset:end] == word:
            found = True
            if whitespace and end < len(self.data):
                found = self.data[end] in _WS
                if consume:
                    consume = False
                    while found and self.data[end] in _WS:
                        end += 1
                        self.offset = end
            if consume:
                self.offset = end
            return found
        return False

    def SkipTo(self, word):
        """
        Advances the buffer up to the first occurence of the given word
        (not included) or to the end of the buffer.
        
        Line numbers: The method returns *everything* between the current position
        and the first occurence of word, including line separators. If linesep is
        defined, these are scanned for when the buffer is consumed and the
        Buffer.lineno is incremeted as necessary.

        Returns whatever has been read in between or an empty string is
        nothing changed (i.e. if the requested word is already at the current
        location or the end had already been reached or the requested word
        is empty.)
        """
        if not word or self.EndReached():
            return ""
        offset = self.offset
        found = self.data.find(word, offset)
        if found == -1:
            self.offset = len(self.data)
        else:
            self.offset = found
        result = self.data[offset:self.offset]
        if self.linesep:
            n = result.count(self.linesep)
            if n > 0:
                self.lineno += n
                self.lineoffset = (self.data.rfind(self.linesep,
                                                   offset,
                                                   self.offset)
                                   + len(self.linesep))
        return result

    def NextWord(self):
        """
        Returns the next word in the buffer and consumes it.
        Returns an empty if the end of the buffer has already been reached.
        
        Words are any sequence of characters separated by spaces or line
        separators, or the [[ and ]] tags markers.
        
        Whitespace at the beginning of the buffer's current position is
        consumed and not returned. Whitespace at the end of the word is left
        intact.
        """
        data = self.data
        initial = offset = self.offset
        len_buf = len(data)
        linesep = self.linesep
        len_sep = len(linesep)
        s = ""
        while offset < len_buf:
            if data[offset:offset + 2] in ["[[", "]]"]:
                if not s:
                    offset += 2
                break
            c = data[offset]
            if c in _WS:
                if not s:
                    offset += 1
                    continue
                else:
                    break
            if c == linesep or (len_sep > 1 and data[offset:offset + len_sep] == linesep):
                if not s:
                    offset += len_sep
                    self.lineno += 1
                    self.lineoffset = offset
                    continue
                else:
                    break
            s += c
            offset += 1
        self.offset = offset
        return s


#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
