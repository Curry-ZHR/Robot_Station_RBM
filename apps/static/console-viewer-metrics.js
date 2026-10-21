// Browser measurements only: rendered frames and newly applied source samples.
export class ViewerMetrics {
  constructor() { this.reset(); }
  reset() { this.frames = []; this.poses = []; this.source = null; this.stamp = null; this.live = false; }
  rendered(time) {
    this.frames.push(time);
    this.frames = this.frames.filter(t => time - t <= 2000);
  }
  pose(sample, time) {
    const live = sample?.valid === true && typeof sample.observedAt === 'string' && Number.isFinite(Date.parse(sample.observedAt));
    if (!live || sample.source !== this.source) {
      this.poses = []; this.stamp = null;
    }
    this.live = live; this.source = sample?.source ?? null;
    if (!live || this.stamp === sample.observedAt) return;
    // A source clock reset starts a new measurement window.
    if (this.stamp && Date.parse(sample.observedAt) < Date.parse(this.stamp)) this.poses = [];
    this.stamp = sample.observedAt;
    this.poses.push(time);
    this.poses = this.poses.filter(t => time - t <= 6000);
  }
  rate(samples, time, window, staleAfter) {
    const recent = samples.filter(t => time - t <= window);
    if (!recent.length || time - recent.at(-1) > staleAfter) return 0;
    if (recent.length < 2 || recent.at(-1) === recent[0]) return null;
    return (recent.length - 1) * 1000 / (recent.at(-1) - recent[0]);
  }
  read(time) {
    return {
      fps: this.rate(this.frames, time, 2000, 1000),
      poseHz: this.live ? this.rate(this.poses, time, 6000, 5000) : null,
    };
  }
}
