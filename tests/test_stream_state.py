from unittest.mock import MagicMock, patch
from btkeepalive.stream import AudioStream


def test_stream_active_status():
    settings = {
        "sample_rate": 44100,
        "volume": 0.02,
        "buffer_seconds": 0.012,
        "keepalive_mode": "continuous",
    }
    audio = AudioStream(lambda: settings)

    # 1. No stream yet
    assert not audio.is_running()

    # Mock OutputStream class
    with patch("btkeepalive.stream.sd.OutputStream") as mock_output_stream_cls:
        mock_stream = MagicMock()
        mock_output_stream_cls.return_value = mock_stream

        # When active is True
        mock_stream.active = True

        audio.start()

        # Stream should be created and started
        mock_output_stream_cls.assert_called_once()
        mock_stream.start.assert_called_once()

        assert audio.is_running() is True

        # If start is called again while active, it should return early
        mock_output_stream_cls.reset_mock()
        mock_stream.start.reset_mock()

        audio.start()
        mock_output_stream_cls.assert_not_called()
        mock_stream.start.assert_not_called()

        # Now make stream inactive
        mock_stream.active = False
        assert audio.is_running() is False

        # Call start again. Since inactive, it should cleanup the old stream and start a new one
        mock_output_stream_cls.reset_mock()
        audio.start()

        # Old stream should be stopped and closed
        mock_stream.stop.assert_called_once()
        mock_stream.close.assert_called_once()

        # New stream should be created and started
        mock_output_stream_cls.assert_called_once()
