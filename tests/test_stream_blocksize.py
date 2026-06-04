def test_blocksize_from_buffer_seconds():
    sr = 44100
    buf_sec = 0.012
    blocksize = max(64, min(8192, int(sr * buf_sec)))
    assert 64 <= blocksize <= 8192
    assert blocksize == 529
