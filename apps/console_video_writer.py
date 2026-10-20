"""Single-threaded encoder ownership with acknowledged finalization and no deletion."""
from __future__ import annotations

from pathlib import Path
import queue
import threading


class ManagedVideoWriter:
    def __init__(self,output_path,width,height,fps,codec="h264",buffer_size=50):
        self.output_path,self.width,self.height,self.fps=str(output_path),width,height,fps
        self.codec=codec
        self.queue=queue.Queue(maxsize=buffer_size)
        self.error=None
        self.stopping=False
        self.thread=threading.Thread(target=self._encode,daemon=True)
        self.thread.start()

    def _encode(self):
        container=None
        try:
            import av
            while True:
                frame=self.queue.get()
                if frame is None:break
                if container is None:
                    Path(self.output_path).parent.mkdir(parents=True,exist_ok=True)
                    container=av.open(self.output_path,mode="w")
                    stream=container.add_stream(self.codec,rate=self.fps)
                    stream.width=self.width
                    stream.height=self.height
                    stream.pix_fmt="yuv420p"
                    stream.options={"preset":"fast","crf":"23"}
                video=av.VideoFrame.from_ndarray(frame,format="rgb24")
                for packet in stream.encode(video):container.mux(packet)
            if container is not None:
                for packet in stream.encode():container.mux(packet)
        except Exception as exc:self.error=exc
        finally:
            if container is not None:
                try:container.close()
                except Exception as exc:self.error=exc

    def add_frame(self,frame):
        if self.error:raise RuntimeError("视频编码失败："+str(self.error))
        if self.stopping:raise RuntimeError("视频已结束写入")
        if frame.shape!=(self.height,self.width,3):raise ValueError(f"相机图像应为 {self.width}×{self.height} RGB，收到 {frame.shape}")
        try:self.queue.put(frame.copy(),timeout=2)
        except queue.Full as exc:raise RuntimeError("视频编码队列拥塞，停止采集以保留已有数据") from exc

    def stop(self):
        if not self.stopping:
            self.stopping=True
            if self.thread.is_alive():
                try:self.queue.put(None,timeout=5)
                except queue.Full as exc:raise RuntimeError("视频结束队列超时") from exc
        self.thread.join(timeout=30)
        if self.thread.is_alive():raise RuntimeError("视频编码未在期限内结束")
        if self.error:raise RuntimeError("视频编码失败："+str(self.error))
        return self.output_path

    def cancel(self):
        # Preserve partial media for diagnosis. The console never deletes source recordings.
        return self.stop()
