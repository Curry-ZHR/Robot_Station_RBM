import * as THREE from 'three';
import { STLLoader } from './vendor/STLLoader.js';

const geometryCache = new Map();
export class RobotScene {
  constructor(container, profile) {
    this.container = container; this.profile = profile; this.dead = false; this.jointNodes = new Map(); this.materials = [];
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    this.renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 1.6)); this.renderer.setClearColor(0xf1f5fa, 1);
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.domElement.setAttribute('aria-label', 'G1 29 关节参考模型，可拖动旋转、滚轮缩放');
    this.renderer.domElement.setAttribute('role', 'img'); container.append(this.renderer.domElement);
    this.scene = new THREE.Scene(); this.camera = new THREE.PerspectiveCamera(34, 1, .02, 30); this.camera.up.set(0, 0, 1);
    this.target = new THREE.Vector3(0, 0, .83); this.theta = -.72; this.phi = .23; this.distance = 2.9;
    this.scene.add(new THREE.HemisphereLight(0xffffff, 0x8496ae, 2.5));
    const key = new THREE.DirectionalLight(0xffffff, 3.4); key.position.set(3, -2, 5); this.scene.add(key);
    const rim = new THREE.DirectionalLight(0x80b6ff, 1.8); rim.position.set(-2, 2, 2); this.scene.add(rim);
    const grid = new THREE.GridHelper(3.4, 24, 0xb6c9df, 0xdce5ef); grid.rotateX(Math.PI / 2); grid.position.z = -.003; this.scene.add(grid);
    this.robot = new THREE.Group(); this.robot.position.z = .79; this.scene.add(this.robot);
    const links = new Map(profile.links.map(link => [link.name, new THREE.Group()]));
    for (const [name, node] of links) node.name = name;
    this.robot.add(links.get(profile.root_link));
    for (const joint of profile.joints) {
      const node = new THREE.Group(); node.position.fromArray(joint.xyz); node.rotation.set(...joint.rpy, 'ZYX');
      const base = node.quaternion.clone(); links.get(joint.parent)?.add(node); node.add(links.get(joint.child));
      this.jointNodes.set(joint.name, { node, base, axis: new THREE.Vector3(...joint.axis).normalize() });
    }
    this.loading = Promise.all(profile.links.flatMap(link => link.visuals.map(async visual => {
      if (!geometryCache.has(visual.mesh)) geometryCache.set(visual.mesh, new STLLoader().loadAsync(visual.mesh));
      try {
        const geometry = await geometryCache.get(visual.mesh); if (this.dead) return;
        const color = new THREE.Color(...visual.color.slice(0, 3));
        const material = new THREE.MeshStandardMaterial({ color, roughness: .5, metalness: .2 });
        const mesh = new THREE.Mesh(geometry, material); mesh.position.fromArray(visual.xyz); mesh.rotation.set(...visual.rpy, 'ZYX'); mesh.scale.fromArray(visual.scale);
        links.get(link.name).add(mesh); this.materials.push(material);
      } catch { container.dataset.modelError = '部分模型资源未加载'; }
    })));
    this.pointer = null;
    const canvas = this.renderer.domElement;
    canvas.addEventListener('pointerdown', event => { this.pointer = [event.clientX, event.clientY]; canvas.setPointerCapture(event.pointerId); });
    canvas.addEventListener('pointermove', event => {
      if (!this.pointer) return;
      this.theta -= (event.clientX - this.pointer[0]) * .008; this.phi = Math.max(-.08, Math.min(.95, this.phi + (event.clientY - this.pointer[1]) * .005));
      this.pointer = [event.clientX, event.clientY];
    });
    canvas.addEventListener('pointerup', () => { this.pointer = null; }); canvas.addEventListener('pointercancel', () => { this.pointer = null; });
    canvas.addEventListener('wheel', event => { event.preventDefault(); this.distance = Math.max(1.4, Math.min(5, this.distance + event.deltaY * .002)); }, { passive: false });
    this.observer = new ResizeObserver(() => this.resize()); this.observer.observe(container); this.resize();
    let last = 0;
    const render = time => { if (this.dead) return; this.frame = requestAnimationFrame(render); if (time - last < 28) return; last = time;
      this.camera.position.set(this.target.x + this.distance * Math.cos(this.phi) * Math.cos(this.theta), this.target.y + this.distance * Math.cos(this.phi) * Math.sin(this.theta), this.target.z + this.distance * Math.sin(this.phi));
      this.camera.lookAt(this.target); this.renderer.render(this.scene, this.camera); };
    this.frame = requestAnimationFrame(render);
  }
  resize() { if (this.dead) return; const width = Math.max(1, this.container.clientWidth), height = Math.max(1, this.container.clientHeight); this.camera.aspect = width / height; this.camera.updateProjectionMatrix(); this.renderer.setSize(width, height, false); }
  setPose(values) { this.profile.body_joints.forEach((name, index) => { const joint = this.jointNodes.get(name); if (joint) joint.node.quaternion.copy(joint.base).multiply(new THREE.Quaternion().setFromAxisAngle(joint.axis, Number.isFinite(values?.[index]) ? values[index] : 0)); }); }
  resetView() { this.theta = -.72; this.phi = .23; this.distance = 2.9; }
  dispose() { this.dead = true; cancelAnimationFrame(this.frame); this.observer.disconnect(); this.materials.forEach(m => m.dispose()); this.renderer.dispose(); this.renderer.domElement.remove(); }
}
