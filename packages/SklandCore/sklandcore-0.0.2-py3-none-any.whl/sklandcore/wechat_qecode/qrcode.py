from pathlib import Path
from urllib.parse import parse_qs, urlparse

import cv2
import numpy as np

# Get the path to the model files
_DETECT_PROTOTXT = str(Path(__file__).parent / "detect.prototxt")
_DETECT_CAFFEMODEL = str(Path(__file__).parent / "detect.caffemodel")
_SR_PROTOTXT = str(Path(__file__).parent / "sr.prototxt")
_SR_CAFFEMODEL = str(Path(__file__).parent / "sr.caffemodel")

# Lazy-loaded detector instance
_detector: cv2.wechat_qrcode.WeChatQRCode | None = None


class QRCodeError(Exception):
    pass


class QRCodeDetectorInitError(QRCodeError):
    pass


class QRCodeNotFoundError(QRCodeError):
    pass


class ScanIdNotFoundError(QRCodeError):
    pass


def _get_detector() -> cv2.wechat_qrcode.WeChatQRCode:
    global _detector

    if _detector is not None:
        return _detector

    for path, name in [
        (_DETECT_PROTOTXT, "detect.prototxt"),
        (_DETECT_CAFFEMODEL, "detect.caffemodel"),
        (_SR_PROTOTXT, "sr.prototxt"),
        (_SR_CAFFEMODEL, "sr.caffemodel"),
    ]:
        if not Path(path).exists():
            raise QRCodeDetectorInitError(f"Model file not found: {name}")

    try:
        _detector = cv2.wechat_qrcode.WeChatQRCode(
            _DETECT_PROTOTXT,
            _DETECT_CAFFEMODEL,
            _SR_PROTOTXT,
            _SR_CAFFEMODEL,
        )
    except Exception as e:
        raise QRCodeDetectorInitError(f"Failed to initialize WeChatQRCode detector: {e}") from e

    return _detector


def _load_image(image: str | bytes | Path | np.ndarray) -> np.ndarray:
    if isinstance(image, np.ndarray):
        return image

    if isinstance(image, str | Path):
        path = Path(image)
        if not path.exists():
            raise QRCodeError(f"Image file not found: {path}")

        img = cv2.imread(str(path))
        if img is None:
            raise QRCodeError(f"Failed to read image: {path}")
        return img

    if isinstance(image, bytes):
        nparr = np.frombuffer(image, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise QRCodeError("Failed to decode image from bytes")
        return img

    raise QRCodeError(f"Unsupported image type: {type(image)}")


def _enhance_image(img: np.ndarray, alpha: float = 1.2, beta: int = 40) -> np.ndarray:
    return cv2.convertScaleAbs(img, alpha=alpha, beta=beta)


def detect_qrcode(image: str | bytes | Path | np.ndarray) -> list[str]:
    detector = _get_detector()
    img = _load_image(image)

    enhanced_img = _enhance_image(img)

    results, _ = detector.detectAndDecode(enhanced_img)

    return [res for res in results if res]


def extract_scan_id(qr_content: str) -> str | None:
    try:
        parsed = urlparse(qr_content)

        if parsed.scheme != "hypergryph":
            return None

        if parsed.netloc != "scan_login":
            return None

        params = parse_qs(parsed.query)
        scan_ids = params.get("scanId", [])

        if scan_ids:
            return scan_ids[0]

        return None
    except Exception:
        return None


def extract_scan_id_from_image(image: str | bytes | Path | np.ndarray) -> str:
    qr_contents = detect_qrcode(image)

    if not qr_contents:
        raise QRCodeNotFoundError("No QR code found in the image")

    for content in qr_contents:
        scan_id = extract_scan_id(content)
        if scan_id:
            return scan_id

    raise ScanIdNotFoundError(f"No valid scanId found in QR code(s). Content: {qr_contents}")
