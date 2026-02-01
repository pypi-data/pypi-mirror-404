from collections.abc import Callable
from functools import partial
from pathlib import Path
import time

import requests

from tinesight._api import TinesightApiMixin


class TinesightClient(TinesightApiMixin):
    """
    Client for invoking the Tinesight API from a device.

    To use this class, a device must be registered with a signed certificate using the
    `TinesightRegistrar`.

    Examples:
        >>> result = TinesightClient(my_key_path, my_cert_path).classify(my_image_bytes)
        >>> print(result.json)
        >>> {'class': 'deer', 'probability': 0.98}

    """

    @property
    def _mtls_post(self) -> Callable:
        """Private wrapper for making invoking requests with a certa"""
        return partial(requests.post, cert=(self.cert_path, self.key_path))

    def _is_raspberry_pi(self) -> bool:
        """Check if running on a Raspberry Pi"""
        try:
            with open("/proc/device-tree/model", "r") as f:
                model = f.read()
                return "Raspberry Pi" in model
        except FileNotFoundError:
            return False

    def __init__(self, x509_key_path: Path | str, x509_cert_path: Path | str):
        self.key_path: str = str(x509_key_path)
        self.cert_path: str = str(x509_cert_path)

    def classify(self, image: str | Path | bytes) -> requests.Response:
        """Invokes the classification model for the specified image

        Args:
            image: Can be a file path (str or Path) or raw image bytes

        Returns:
            requests.Response containing classification results
        """
        classification_url = self.tenant_base_api_uri + "/classify/v1"

        if isinstance(image, bytes):
            image_bytes = image
            file_name = "frame.jpg"
        else:
            if isinstance(image, str):
                image = Path(image)
            with open(image, "rb") as fp:
                image_bytes = fp.read()
            file_name = image.name

        return self._mtls_post(classification_url, files={"file": (file_name, image_bytes)})

    def classify_video_stream(
        self,
        video_source: str | int = 0,
        frame_skip: int = 10,
        probability_threshold: float = 0.55,
        window_name: str = "Tinesight Classification",
    ) -> None:
        """
        Continuously classify frames from a video stream and display results.

        Captures video from a source (camera, RTSP stream, etc.), classifies frames
        at regular intervals, and displays the video with classification annotations.
        Press Ctrl+C to stop.

        Args:
            video_source: Video source - can be device index (0 for default camera),
                         RTSP URL (e.g., "rtsp://192.168.1.100:8554/stream"),
                         or HTTP stream URL
            frame_skip: Classify every Nth frame (default: 10). Higher values = faster but less frequent updates
            probability_threshold: Minimum confidence threshold to display classification (default: 0.55)
            window_name: Name of the display window

        Examples:
            >>> client = TinesightClient(key_path, cert_path)
            >>> # Local camera
            >>> client.classify_video_stream(0)
            >>> # Raspberry Pi RTSP stream
            >>> client.classify_video_stream("rtsp://raspberrypi.local:8554/stream")
            >>> # With custom threshold
            >>> client.classify_video_stream(0, probability_threshold=0.75)
        """
        try:
            import cv2
        except ImportError:
            raise ImportError(
                "OpenCV is required for video streaming. Install with: pip install opencv-python"
            )

        # Check if we should use picamera2 (Raspberry Pi with CSI camera)
        use_picamera2 = False
        picam2 = None

        if isinstance(video_source, int) and self._is_raspberry_pi():
            try:
                from picamera2 import Picamera2

                use_picamera2 = True
                print("Detected Raspberry Pi - using picamera2 for CSI camera")
            except ImportError:
                print("picamera2 not available, falling back to OpenCV")

        # Initialize camera
        if use_picamera2:
            picam2 = Picamera2()
            config = picam2.create_preview_configuration(
                main={"size": (640, 480), "format": "RGB888"}
            )
            picam2.configure(config)
            picam2.start()
            print("Starting picamera2 stream")
        else:
            cap = cv2.VideoCapture(video_source)
            if not cap.isOpened():
                raise RuntimeError(f"Could not open video source: {video_source}")
            print(f"Starting video stream from: {video_source}")

        print(f"Classifying every {frame_skip} frames")
        print("Press Ctrl+C to stop")

        frame_count = 0
        last_classification = None
        last_probability = None
        fps_start = time.time()
        fps_frame_count = 0
        current_fps = 0
        last_latency = 0

        try:
            while True:
                # Capture frame based on camera type
                if use_picamera2:
                    try:
                        frame = picam2.capture_array()
                        # picamera2 returns RGB, convert to BGR for OpenCV
                        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                        ret = True
                    except Exception as e:
                        print(f"Failed to capture frame from picamera2: {e}")
                        ret = False
                else:
                    ret, frame = cap.read()

                if not ret:
                    print("Failed to read frame, attempting to reconnect...")
                    if use_picamera2:
                        picam2.stop()
                        time.sleep(1)
                        picam2.start()
                    else:
                        cap.release()
                        time.sleep(1)
                        cap = cv2.VideoCapture(video_source)
                    continue

                # Calculate FPS
                fps_frame_count += 1
                if time.time() - fps_start >= 1.0:
                    current_fps = int(fps_frame_count / (time.time() - fps_start))
                    fps_frame_count = 0
                    fps_start = time.time()

                # Classify every Nth frame
                if frame_count % frame_skip == 0:
                    # Encode frame as JPEG
                    _, buffer = cv2.imencode(".jpg", frame)
                    image_bytes = buffer.tobytes()

                    # Classify with timing
                    classify_start = time.time()
                    try:
                        response = self.classify(image_bytes)
                        last_latency = int((time.time() - classify_start) * 1000)  # ms

                        if response.status_code == 200:
                            result = response.json()
                            last_classification = result.get("class", "Unknown")
                            last_probability = result.get("probability", 0.0)
                        else:
                            last_classification = f"Error: {response.status_code}"
                            last_probability = None
                    except Exception as e:
                        last_classification = f"Error: {str(e)}"
                        last_probability = None
                        last_latency = int((time.time() - classify_start) * 1000)

                # Draw annotations on frame
                height, width = frame.shape[:2]

                # Semi-transparent overlay for text background
                overlay = frame.copy()
                cv2.rectangle(overlay, (10, 10), (width - 10, 120), (0, 0, 0), -1)
                frame = cv2.addWeighted(overlay, 0.6, frame, 0.4, 0)

                # Display classification results only if above threshold
                y_offset = 40
                if (
                    last_classification
                    and last_probability is not None
                    and last_probability >= probability_threshold
                ):
                    cv2.putText(
                        frame,
                        f"Class: {last_classification}",
                        (20, y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 0),
                        2,
                    )
                    y_offset += 30
                    cv2.putText(
                        frame,
                        f"Confidence: {last_probability:.2%}",
                        (20, y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 0),
                        2,
                    )
                elif last_classification and last_probability is not None:
                    # Show low confidence indicator
                    cv2.putText(
                        frame,
                        f"Low confidence ({last_probability:.2%})",
                        (20, y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (100, 100, 100),
                        2,
                    )
                    y_offset += 30

                # Display metrics
                y_offset += 30
                cv2.putText(
                    frame,
                    f"FPS: {current_fps:.1f} | Latency: {last_latency:.0f}ms",
                    (20, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    2,
                )

                # Show frame
                cv2.imshow(window_name, frame)

                # Check for ESC key or window close
                if cv2.waitKey(1) & 0xFF == 27:
                    break

                frame_count += 1

        except KeyboardInterrupt:
            print("\nStopping video stream...")
        finally:
            if use_picamera2 and picam2:
                picam2.stop()
            elif not use_picamera2:
                cap.release()
            cv2.destroyAllWindows()
