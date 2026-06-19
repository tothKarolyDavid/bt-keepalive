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

        # Call start again. Since inactive, it should cleanup the
        # old stream and start a new one
        mock_output_stream_cls.reset_mock()
        audio.start()

        # Old stream should be stopped and closed
        mock_stream.stop.assert_called_once()
        mock_stream.close.assert_called_once()

        # New stream should be created and started
        mock_output_stream_cls.assert_called_once()


def test_monitor_loop_unexpected_stop():
    settings = {
        "sample_rate": 44100,
        "volume": 0.02,
        "buffer_seconds": 0.012,
        "keepalive_mode": "continuous",
        "playing": True,
    }
    audio = AudioStream(lambda: settings)

    # Mock is_running to return False (unexpectedly stopped)
    audio.is_running = MagicMock(return_value=False)
    audio._recreate_stream = MagicMock(return_value=True)

    # Mock stop_event.wait to run once and then exit
    stop_event = MagicMock()
    stop_event.wait.side_effect = [False, True]

    audio._monitor_loop(stop_event)

    # Should check is_running, see it's False, and trigger _recreate_stream
    audio.is_running.assert_called_once()
    audio._recreate_stream.assert_called_once_with(stop_event)


def test_monitor_loop_paused():
    settings = {
        "sample_rate": 44100,
        "volume": 0.02,
        "buffer_seconds": 0.012,
        "keepalive_mode": "continuous",
        "playing": False,  # Paused by user
    }
    audio = AudioStream(lambda: settings)

    audio.is_running = MagicMock(return_value=False)
    audio._recreate_stream = MagicMock()

    stop_event = MagicMock()
    stop_event.wait.side_effect = [False, True]

    audio._monitor_loop(stop_event)

    # Since playing is False, it should exit immediately without checking
    # running or recreating
    audio.is_running.assert_not_called()
    audio._recreate_stream.assert_not_called()


def test_monitor_loop_device_change():
    settings = {
        "sample_rate": 44100,
        "volume": 0.02,
        "buffer_seconds": 0.012,
        "keepalive_mode": "continuous",
        "playing": True,
    }
    audio = AudioStream(lambda: settings)
    audio.is_running = MagicMock(return_value=True)
    audio._last_device_id = "device_1"

    # Mock get_default_audio_endpoint_id to return a new device
    with patch(
        "btkeepalive.stream.get_default_audio_endpoint_id",
        return_value="device_2",
    ):
        audio._recreate_stream = MagicMock(return_value=True)

        stop_event = MagicMock()
        stop_event.wait.side_effect = [False, True]

        audio._monitor_loop(stop_event)

        # Should detect device change and call _recreate_stream
        audio._recreate_stream.assert_called_once_with(stop_event)


def test_recreate_stream_success():
    settings = {
        "sample_rate": 44100,
        "volume": 0.02,
        "buffer_seconds": 0.012,
        "keepalive_mode": "continuous",
        "playing": True,
    }
    audio = AudioStream(lambda: settings)
    audio.stop = MagicMock()
    audio.start = MagicMock()

    stop_event = MagicMock()

    with patch("btkeepalive.stream.sd") as mock_sd:
        success = audio._recreate_stream(stop_event)

        assert success is True
        audio.stop.assert_called_once()
        mock_sd._terminate.assert_called_once()
        mock_sd._initialize.assert_called_once()
        audio.start.assert_called_once()
        assert audio._last_error_logged is None


def test_recreate_stream_failure():
    settings = {
        "sample_rate": 44100,
        "volume": 0.02,
        "buffer_seconds": 0.012,
        "keepalive_mode": "continuous",
        "playing": True,
    }
    audio = AudioStream(lambda: settings)
    audio.stop = MagicMock()
    audio.start = MagicMock(side_effect=RuntimeError("Some audio error"))

    stop_event = MagicMock()

    with (
        patch("btkeepalive.stream.sd") as mock_sd,
        patch("btkeepalive.stream.log_error") as mock_log_error,
    ):
        success = audio._recreate_stream(stop_event)

        assert success is False
        audio.stop.assert_called_once()
        mock_sd._terminate.assert_called_once()
        mock_sd._initialize.assert_called_once()
        audio.start.assert_called_once()

        # Check that error is logged and stop_event cleared
        mock_log_error.assert_called_once()
        assert audio._last_error_logged == "Some audio error"
        stop_event.clear.assert_called_once()
