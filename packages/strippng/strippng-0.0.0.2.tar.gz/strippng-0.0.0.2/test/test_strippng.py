import hashlib
import io
import os
import pytest
import strippng
import typing

@pytest.fixture
def pngfile():
    # https://www.drawio.com/blog/diagram-data-image-formats
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), '5c-marketing-analysis.png'), 'rb') as f:
        yield f

def test_Read(pngfile: typing.BinaryIO):
    # not meaningful, but for sanity
    assert 'd441ed5e24db52f903816f8b298278863fa4a5ab' == hashlib.sha1(pngfile.read()).hexdigest()

def test_StripPNG(pngfile: typing.BinaryIO):
    stripIO = io.BytesIO()
    strippng.StripPNG(pngfile, stripIO)
    stripIO.seek(0)
    assert 'fc24dbb311b1ba558f524e7e5f240eb8f2fd1d8d' == hashlib.sha1(stripIO.read()).hexdigest()
