/**
 * Client-Side Video Frame Extractor (Extracted from autosprite.app / Sloth Studio)
 * 
 * ใช้เทคนิค HTML5 <video> seeking และ HTML5 <canvas> ใน WebKit เพื่อสกัดเฟรมภาพนิ่ง (PNG Data URLs)
 * จากวิดีโอ MP4 โดยตรงบนเครื่อง Mac โดยไม่ต้องพึ่ง FFmpeg หรือ external binary ขนาดใหญ่
 */

async function extractFramesFromVideo(videoUrl) {
    const video = document.createElement("video");
    video.preload = "auto";
    video.src = videoUrl;

    await new Promise((resolve, reject) => {
        video.onloadeddata = () => resolve();
        video.onerror = () => reject(new Error("Failed to load video"));
    });

    if (video.videoWidth < 1 || video.videoHeight < 1) {
        throw new Error("Video has no frames");
    }

    const canvas = document.createElement("canvas");
    // จำกัดขนาดความละเอียดสูงสุดที่ 1024px เพื่อลดการใช้ Memory
    const scale = Math.min(1, 1024 / Math.max(video.videoWidth, video.videoHeight));
    canvas.width = Math.max(1, Math.round(video.videoWidth * scale));
    canvas.height = Math.max(1, Math.round(video.videoHeight * scale));

    const ctx = canvas.getContext("2d");
    if (!ctx) {
        throw new Error("Canvas 2D context unavailable");
    }

    // คำนวณจำนวนเฟรมที่ต้องการสุ่ม (Sample) โดยอิง 24 FPS (จำกัดระหว่าง 8 ถึง 144 เฟรม)
    const frameCount = Math.min(144, Math.max(8, Math.round(video.duration * 24) + 1));
    const frames = [];

    try {
        for (let i = 0; i < frameCount; i++) {
            // คำนวณ Time offset สำหรับแต่ละเฟรม
            const targetTime = 0.001 + (i * Math.max(0, video.duration - 0.002)) / Math.max(1, frameCount - 1);

            await new Promise((resolve, reject) => {
                video.onseeked = () => resolve();
                video.onerror = () => reject(new Error("Video seek failed"));
                video.currentTime = targetTime;
            });

            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            frames.push(canvas.toDataURL("image/png"));
        }

        return {
            frames: frames, // Array of PNG data URLs
            durationMs: Math.round(video.duration * 1000)
        };
    } finally {
        video.removeAttribute("src");
        video.load();
    }
}
