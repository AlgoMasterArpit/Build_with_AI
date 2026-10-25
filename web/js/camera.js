const CONSTRAINTS = {
  audio: false,
  video: {
    facingMode: { ideal: "environment" },
    width: { ideal: 3840 },
    height: { ideal: 2160 },
  },
};

export class CameraError extends Error {
  /** @param {"blocked"|"missing"|"unavailable"} kind @param {string} message */
  constructor(kind, message) {
    super(message);
    this.kind = kind;
  }
}

/** @param {HTMLVideoElement} video */
export async function openCamera(video) {
  if (!navigator.mediaDevices?.getUserMedia) {
    throw new CameraError("unavailable", "Is browser mein camera nahi chal raha. Chrome mein kholo.");
  }
  let stream;
  try {
    stream = await navigator.mediaDevices.getUserMedia(CONSTRAINTS);
  } catch (error) {
    const name = /** @type {DOMException} */ (error).name;
    if (name === "NotAllowedError" || name === "SecurityError") {
      throw new CameraError("blocked", "Camera band hai.");
    }
    if (name === "NotFoundError" || name === "OverconstrainedError") {
      throw new CameraError("missing", "Is phone pe camera nahi mila.");
    }
    throw new CameraError("unavailable", "Camera khul nahi paaya. Dobara try karo.");
  }
  video.srcObject = stream;
  video.setAttribute("playsinline", "");
  video.muted = true;
  await video.play();
  return stream;
}

/** @param {MediaStream|null|undefined} stream */
export function closeCamera(stream) {
  stream?.getTracks().forEach((track) => track.stop());
}

/**
 * Full sensor resolution through ImageCapture where Chrome supports it,
 * otherwise the largest video frame the stream gives us.
 * @param {MediaStream} stream @param {HTMLVideoElement} video
 * @returns {Promise<Blob>}
 */
export async function capturePhoto(stream, video) {
  const [track] = stream.getVideoTracks();
  if ("ImageCapture" in window && track) {
    try {
      // @ts-ignore ImageCapture is Chrome-only
      const capture = new ImageCapture(track);
      const caps = await capture.getPhotoCapabilities().catch(() => null);
      const settings = caps?.imageWidth?.max ? { imageWidth: caps.imageWidth.max } : {};
      const blob = await capture.takePhoto(settings);
      if (blob?.size) return blob;
    } catch {
      // fall through to a video frame
    }
  }
  const canvas = document.createElement("canvas");
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  canvas.getContext("2d")?.drawImage(video, 0, 0);
  return new Promise((resolve, reject) =>
    canvas.toBlob((blob) => (blob ? resolve(blob) : reject(new Error("capture failed"))), "image/jpeg", 0.92));
}
