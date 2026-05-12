"""Generate a self-contained interactive 3D preview HTML using Three.js.

The preview is a single static HTML file with embedded JavaScript that loads
Three.js from a CDN and renders the scene data inline.  Features:

- 3D orbit controls (rotate, zoom, pan)
- Bloom post-processing for emissive objects
- Star field background for depth
- Quasar jet geometry
- Animated LAB pulsing and magnetar flicker
- Object type toggles (filaments, nodes, galaxies, LAB, quasar, BH, magnetar)
- Visual mode selector (beauty, science, lyman_alpha, xray, radio, density, cmb)
- Click metadata inspector with relationship links
- Hover tooltips
- Focus-on-object (double-click)
- Coordinate grid for spatial reference
"""

from __future__ import annotations

import json

from universe.models import SceneRegion


def render_preview_html(scene: SceneRegion) -> str:
    scene_json = scene.model_dump_json()
    modes_json = json.dumps(
        scene.visual_modes
        if scene.visual_modes
        else ["beauty", "science", "lyman_alpha", "xray", "radio", "density", "cmb"]
    )

    return _TEMPLATE.format(
        scene_name=scene.name,
        scene_redshift=scene.redshift,
        scene_size_mpc=scene.size_mpc,
        scene_seed=scene.seed,
        scene_json=scene_json,
        modes_json=modes_json,
    )


_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{scene_name} — universe preview</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ background: #05050a; color: #ccc; font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; overflow: hidden; }}
#container {{ width: 100vw; height: 100vh; }}

/* Sidebar */
#sidebar {{
  position: fixed; top: 0; left: 0; z-index: 10;
  width: 270px; height: 100vh;
  background: rgba(8,8,16,0.94);
  border-right: 1px solid rgba(100,100,255,0.12);
  padding: 18px 16px;
  overflow-y: auto;
  font-size: 13px;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}}
#sidebar h2 {{ font-size: 16px; color: #e8e8f8; margin-bottom: 4px; font-weight: 600; }}
.scene-meta {{ color: #556; font-size: 10.5px; margin-bottom: 14px; line-height: 1.5; }}
#sidebar h3 {{
  font-size: 10px; color: #667; margin: 16px 0 6px;
  text-transform: uppercase; letter-spacing: 0.12em; font-weight: 600;
}}
.toggle-group {{ display: flex; flex-direction: column; gap: 2px; }}
.toggle-row {{
  display: flex; align-items: center; gap: 8px; padding: 3px 4px;
  border-radius: 4px; transition: background 0.15s;
}}
.toggle-row:hover {{ background: rgba(255,255,255,0.03); }}
.toggle-row input[type="checkbox"] {{ accent-color: #66f; width: 13px; height: 13px; cursor: pointer; }}
.toggle-row label {{ cursor: pointer; font-size: 11.5px; color: #aab; }}
.toggle-row .count {{ color: #556; font-size: 10px; margin-left: auto; }}
.color-dot {{ width: 9px; height: 9px; border-radius: 50%; display: inline-block; flex-shrink: 0; box-shadow: 0 0 4px currentColor; }}

/* Mode buttons */
.mode-grid {{ display: flex; flex-wrap: wrap; gap: 4px; }}
.mode-btn {{
  background: rgba(20,20,40,0.8); border: 1px solid rgba(100,100,255,0.15);
  color: #889; padding: 4px 9px; border-radius: 4px; cursor: pointer;
  font-size: 10.5px; transition: all 0.2s; font-family: inherit;
}}
.mode-btn:hover {{ border-color: rgba(100,100,255,0.4); color: #ccf; }}
.mode-btn.active {{ background: rgba(40,40,100,0.6); border-color: #66f; color: #ddf; box-shadow: 0 0 8px rgba(100,100,255,0.15); }}

/* Inspector panel */
#inspector {{
  position: fixed; bottom: 16px; right: 16px; width: 360px; max-height: 55vh;
  background: rgba(8,8,16,0.95);
  border: 1px solid rgba(100,100,255,0.15);
  border-radius: 10px; padding: 18px 16px; overflow-y: auto;
  z-index: 20; font-size: 12px; display: none;
  backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
  box-shadow: 0 8px 32px rgba(0,0,0,0.5);
}}
#inspector h3 {{ font-size: 15px; color: #eef; margin-bottom: 6px; font-weight: 600; }}
#inspector .obj-type {{ font-size: 10.5px; color: #66a; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 8px; }}
#inspector .close-btn {{
  position: absolute; top: 10px; right: 14px; cursor: pointer;
  color: #446; font-size: 18px; line-height: 1; transition: color 0.15s;
}}
#inspector .close-btn:hover {{ color: #ccf; }}
#inspector .desc {{ color: #889; margin: 6px 0 10px; line-height: 1.4; font-size: 11.5px; }}
#inspector .prop {{ margin: 2px 0; display: flex; gap: 6px; }}
#inspector .prop-key {{ color: #557; font-size: 11px; min-width: 90px; flex-shrink: 0; }}
#inspector .prop-val {{ color: #bbc; font-size: 11px; word-break: break-all; }}
#inspector .section-label {{ color: #667; font-size: 10px; text-transform: uppercase; letter-spacing: 0.1em; margin: 12px 0 4px; }}
#inspector .rel {{
  color: #7af; font-size: 11px; margin: 3px 0; cursor: pointer;
  padding: 3px 6px; border-radius: 3px; transition: background 0.15s;
}}
#inspector .rel:hover {{ background: rgba(100,150,255,0.1); }}

/* Tooltip */
#tooltip {{
  position: fixed; pointer-events: none;
  background: rgba(8,8,20,0.92); border: 1px solid rgba(100,100,255,0.2);
  border-radius: 5px; padding: 6px 10px; font-size: 11px; color: #dde;
  z-index: 30; display: none;
  backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.4);
}}

/* Stats bar */
#stats {{
  position: fixed; top: 12px; right: 16px;
  font-size: 10px; color: #334; z-index: 10; pointer-events: none;
  font-family: 'SF Mono', 'Fira Code', monospace;
}}

/* Help hint */
#help {{
  position: fixed; bottom: 12px; left: 290px;
  font-size: 10px; color: #334; z-index: 10; pointer-events: none;
}}
</style>
</head>
<body>
<div id="container"></div>

<div id="sidebar">
  <h2>{scene_name}</h2>
  <div class="scene-meta">
    z = {scene_redshift} · {scene_size_mpc} cMpc<br>
    seed: <code style="color:#668">{scene_seed}</code>
  </div>

  <h3>Objects</h3>
  <div class="toggle-group" id="toggles"></div>

  <h3>Visual Mode</h3>
  <div class="mode-grid" id="modes"></div>

  <h3 style="margin-top:18px;">Controls</h3>
  <div style="font-size:10px;color:#556;line-height:1.7;">
    Orbit: drag · Zoom: scroll · Pan: right-drag<br>
    Click: inspect · Double-click: focus<br>
    Hover: tooltip
  </div>
</div>

<div id="inspector"></div>
<div id="tooltip"></div>
<div id="stats"></div>
<div id="help">click object to inspect · double-click to focus</div>

<script type="importmap">
{{
  "imports": {{
    "three": "https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js",
    "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/"
  }}
}}
</script>
<script type="module">
import * as THREE from 'three';
import {{ OrbitControls }} from 'three/addons/controls/OrbitControls.js';
import {{ EffectComposer }} from 'three/addons/postprocessing/EffectComposer.js';
import {{ RenderPass }} from 'three/addons/postprocessing/RenderPass.js';
import {{ UnrealBloomPass }} from 'three/addons/postprocessing/UnrealBloomPass.js';
import {{ OutputPass }} from 'three/addons/postprocessing/OutputPass.js';

const SD = {scene_json};

// ── Palettes ──────────────────────────────────────────────────────────
const PALETTES = {{
  beauty: {{
    galaxy: '#6688ff', lyman_alpha_blob: '#33ffaa', quasar: '#ffffee',
    black_hole: '#110011', magnetar: '#ff44ff', cosmic_web_node: '#ffaa44',
    void: '#060620', cmb_background: '#110808', filament: '#2a3a5a',
    bg: '#05050c', jet: '#ff5500', ring: '#ff8822',
  }},
  science: {{
    galaxy: '#00aaff', lyman_alpha_blob: '#00ff88', quasar: '#ffff00',
    black_hole: '#ff0000', magnetar: '#ff8800', cosmic_web_node: '#aaaaaa',
    void: '#181818', cmb_background: '#333333', filament: '#555555',
    bg: '#0a0a0a', jet: '#ffff00', ring: '#ff4444',
  }},
  lyman_alpha: {{
    galaxy: '#0a2818', lyman_alpha_blob: '#00ffaa', quasar: '#0a3820',
    black_hole: '#040a04', magnetar: '#082810', cosmic_web_node: '#0a2010',
    void: '#020802', cmb_background: '#020402', filament: '#082808',
    bg: '#010402', jet: '#116633', ring: '#0a2a0a',
  }},
  xray: {{
    galaxy: '#3333aa', lyman_alpha_blob: '#5555cc', quasar: '#aaaaff',
    black_hole: '#eeeeff', magnetar: '#7777ff', cosmic_web_node: '#2a2a55',
    void: '#06061a', cmb_background: '#000011', filament: '#1a1a44',
    bg: '#03030a', jet: '#8888ff', ring: '#aaaaff',
  }},
  radio: {{
    galaxy: '#2a1000', lyman_alpha_blob: '#3a1800', quasar: '#ff6600',
    black_hole: '#882200', magnetar: '#ff4400', cosmic_web_node: '#443300',
    void: '#0a0600', cmb_background: '#080400', filament: '#3a1800',
    bg: '#060300', jet: '#ff8800', ring: '#ff6600',
  }},
  density: {{
    galaxy: '#1a5a1a', lyman_alpha_blob: '#33aa33', quasar: '#66ff66',
    black_hole: '#44ee44', magnetar: '#22bb22', cosmic_web_node: '#88ee33',
    void: '#040a04', cmb_background: '#020602', filament: '#2a5a2a',
    bg: '#020602', jet: '#44ff44', ring: '#66ff66',
  }},
  cmb: {{
    galaxy: '#1a0a08', lyman_alpha_blob: '#2a1210', quasar: '#1a0a08',
    black_hole: '#0a0808', magnetar: '#1a0a08', cosmic_web_node: '#1a0a08',
    void: '#060303', cmb_background: '#ff8844', filament: '#120808',
    bg: '#080404', jet: '#2a1008', ring: '#1a0808',
  }},
}};

let curMode = 'beauty';
let P = PALETTES.beauty;

const TOGGLE_TYPES = [
  {{ key: 'filament',          label: 'Filaments',         dot: '#2a3a5a' }},
  {{ key: 'cosmic_web_node',   label: 'Nodes',             dot: '#ffaa44' }},
  {{ key: 'galaxy',            label: 'Galaxies',          dot: '#6688ff' }},
  {{ key: 'lyman_alpha_blob',  label: 'Lyman-\\u03b1 Blob', dot: '#33ffaa' }},
  {{ key: 'quasar',            label: 'Quasar',            dot: '#ffffee' }},
  {{ key: 'black_hole',        label: 'Black Hole',        dot: '#ff8822' }},
  {{ key: 'magnetar',          label: 'Magnetar',          dot: '#ff44ff' }},
  {{ key: 'void',              label: 'Voids',             dot: '#060620' }},
  {{ key: 'cmb_background',    label: 'CMB',               dot: '#110808' }},
];
const vis = {{}};
TOGGLE_TYPES.forEach(t => vis[t.key] = true);

// Count objects per type for sidebar badges
const typeCounts = {{}};
SD.objects.forEach(o => {{ typeCounts[o.type] = (typeCounts[o.type] || 0) + 1; }});
typeCounts['cosmic_web_node'] = SD.nodes.length;
typeCounts['filament'] = SD.filaments.length;

// ── Renderer ──────────────────────────────────────────────────────────
const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: false }});
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;
document.getElementById('container').appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color('#05050c');

const camera = new THREE.PerspectiveCamera(55, window.innerWidth / window.innerHeight, 0.1, 3000);
camera.position.set(55, 35, 70);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.06;
controls.minDistance = 3;
controls.maxDistance = 600;
controls.autoRotate = false;
controls.autoRotateSpeed = 0.15;

// ── Post-processing (bloom) ──────────────────────────────────────────
const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, camera));
const bloom = new UnrealBloomPass(
  new THREE.Vector2(window.innerWidth, window.innerHeight),
  0.6, 0.5, 0.7
);
composer.addPass(bloom);
composer.addPass(new OutputPass());

// ── Lights ────────────────────────────────────────────────────────────
scene.add(new THREE.AmbientLight(0x181828, 2.0));
const dLight = new THREE.DirectionalLight(0xccccff, 0.4);
dLight.position.set(40, 60, 50);
scene.add(dLight);

// ── Star field ────────────────────────────────────────────────────────
(function makeStars() {{
  const N = 4000;
  const geo = new THREE.BufferGeometry();
  const pos = new Float32Array(N * 3);
  const col = new Float32Array(N * 3);
  for (let i = 0; i < N; i++) {{
    const r = 400 + Math.random() * 600;
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos(2 * Math.random() - 1);
    pos[i*3]   = r * Math.sin(phi) * Math.cos(theta);
    pos[i*3+1] = r * Math.sin(phi) * Math.sin(theta);
    pos[i*3+2] = r * Math.cos(phi);
    const temp = 0.4 + Math.random() * 0.6;
    col[i*3]   = temp;
    col[i*3+1] = temp * (0.85 + Math.random() * 0.15);
    col[i*3+2] = temp * (0.7 + Math.random() * 0.3);
  }}
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  geo.setAttribute('color', new THREE.BufferAttribute(col, 3));
  const mat = new THREE.PointsMaterial({{ size: 0.6, vertexColors: true, transparent: true, opacity: 0.6 }});
  scene.add(new THREE.Points(geo, mat));
}})();

// ── Coordinate grid ───────────────────────────────────────────────────
const gridSize = 80;
const gridHelper = new THREE.GridHelper(gridSize, 8, 0x111133, 0x0a0a22);
gridHelper.position.y = -gridSize / 2;
gridHelper.material.transparent = true;
gridHelper.material.opacity = 0.25;
scene.add(gridHelper);

// ── Build scene objects ───────────────────────────────────────────────
const meshEntries = [];   // {{ mesh, data, type, animFn? }}
const filEntries = [];
const relLines = [];      // relationship visualization lines
let animatedObjects = []; // objects with per-frame animation

const nodeMap = {{}};
SD.nodes.forEach(n => nodeMap[n.id] = n);
const objMap = {{}};
SD.objects.forEach(o => objMap[o.id] = o);

function clearScene() {{
  meshEntries.forEach(e => scene.remove(e.mesh));
  filEntries.forEach(e => scene.remove(e.mesh));
  relLines.forEach(l => scene.remove(l));
  meshEntries.length = 0;
  filEntries.length = 0;
  relLines.length = 0;
  animatedObjects = [];
}}

function buildScene() {{
  clearScene();
  P = PALETTES[curMode] || PALETTES.beauty;
  scene.background = new THREE.Color(P.bg);

  bloom.strength = curMode === 'science' ? 0.2 : 0.6;
  bloom.threshold = curMode === 'science' ? 1.0 : 0.7;

  // ── Nodes ──
  SD.nodes.forEach(node => {{
    const s = 0.5 + node.density * 0.35;
    const geo = new THREE.OctahedronGeometry(s, 1);
    const mat = new THREE.MeshStandardMaterial({{
      color: P.cosmic_web_node, emissive: P.cosmic_web_node,
      emissiveIntensity: 0.4, metalness: 0.3, roughness: 0.6,
      transparent: true, opacity: 0.8,
    }});
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.set(node.position_mpc.x, node.position_mpc.y, node.position_mpc.z);
    scene.add(mesh);
    meshEntries.push({{
      mesh, type: 'cosmic_web_node',
      data: {{ ...node, type: 'cosmic_web_node', name: node.id,
               description: `${{node.node_class}} node — density ${{node.density.toFixed(2)}}` }},
    }});
  }});

  // ── Filaments (tubes with CatmullRom curves) ──
  SD.filaments.forEach(fil => {{
    const sn = nodeMap[fil.start_node_id], en = nodeMap[fil.end_node_id];
    if (!sn || !en) return;
    const pts = [new THREE.Vector3(sn.position_mpc.x, sn.position_mpc.y, sn.position_mpc.z)];
    fil.control_points_mpc.forEach(c => pts.push(new THREE.Vector3(c.x, c.y, c.z)));
    pts.push(new THREE.Vector3(en.position_mpc.x, en.position_mpc.y, en.position_mpc.z));

    const curve = new THREE.CatmullRomCurve3(pts);
    const tGeo = new THREE.TubeGeometry(curve, 32, fil.radius_mpc * 0.25, 6, false);
    const tMat = new THREE.MeshStandardMaterial({{
      color: P.filament, emissive: P.filament,
      emissiveIntensity: 0.12, metalness: 0.1, roughness: 0.8,
      transparent: true, opacity: 0.3, side: THREE.DoubleSide,
    }});
    const mesh = new THREE.Mesh(tGeo, tMat);
    scene.add(mesh);
    filEntries.push({{
      mesh, type: 'filament',
      data: {{ ...fil, type: 'filament', name: fil.id,
               description: `${{fil.start_node_id}} → ${{fil.end_node_id}}, density ${{fil.density.toFixed(2)}}, r=${{fil.radius_mpc.toFixed(2)}} Mpc`,
               relationships: [
                 {{ target_id: fil.start_node_id, relation: 'start_node', description: 'Start node' }},
                 {{ target_id: fil.end_node_id, relation: 'end_node', description: 'End node' }},
               ] }},
    }});
  }});

  // ── Objects ──
  SD.objects.forEach(obj => {{
    const ot = obj.type;
    const col = P[ot] || '#888';
    let mesh;

    switch (ot) {{
      case 'lyman_alpha_blob': {{
        const r = obj.visual.scale * 0.55;
        const geo = new THREE.IcosahedronGeometry(r, 4);
        const mat = new THREE.MeshStandardMaterial({{
          color: col, emissive: col, emissiveIntensity: 0.8,
          transparent: true, opacity: 0.18, side: THREE.DoubleSide,
          wireframe: curMode === 'science',
          metalness: 0.0, roughness: 1.0,
        }});
        mesh = new THREE.Mesh(geo, mat);
        // Inner bright core
        const coreGeo = new THREE.IcosahedronGeometry(r * 0.35, 3);
        const coreMat = new THREE.MeshStandardMaterial({{
          color: col, emissive: col, emissiveIntensity: 1.2,
          transparent: true, opacity: 0.12,
        }});
        const core = new THREE.Mesh(coreGeo, coreMat);
        mesh.add(core);
        // Animate pulsing
        const baseScale = 1.0;
        animatedObjects.push((t) => {{
          const s = baseScale + Math.sin(t * 0.4) * 0.03;
          mesh.scale.set(s, s, s);
          mat.opacity = 0.18 + Math.sin(t * 0.6) * 0.04;
        }});
        break;
      }}
      case 'quasar': {{
        const group = new THREE.Group();
        // Central bright sphere
        const qGeo = new THREE.SphereGeometry(1.0, 24, 24);
        const qMat = new THREE.MeshStandardMaterial({{
          color: col, emissive: col, emissiveIntensity: 2.0,
          metalness: 0.8, roughness: 0.1,
        }});
        group.add(new THREE.Mesh(qGeo, qMat));
        // Point light
        const qLight = new THREE.PointLight(col, 60, 80);
        group.add(qLight);
        // Jets (two opposing cones)
        const jetLen = Math.min((obj.properties.jet_length_ckpc || 200) * 0.015, 8);
        const jetAngle = (obj.properties.jet_opening_angle_deg || 15) * Math.PI / 180;
        const jetR = Math.tan(jetAngle) * jetLen * 0.5;
        const jCol = P.jet || '#ff5500';
        for (let sign = -1; sign <= 1; sign += 2) {{
          const jGeo = new THREE.ConeGeometry(jetR, jetLen, 12, 1, true);
          const jMat = new THREE.MeshStandardMaterial({{
            color: jCol, emissive: jCol, emissiveIntensity: 1.5,
            transparent: true, opacity: 0.45, side: THREE.DoubleSide,
          }});
          const jet = new THREE.Mesh(jGeo, jMat);
          jet.position.y = sign * jetLen * 0.5;
          if (sign < 0) jet.rotation.x = Math.PI;
          group.add(jet);
        }}
        mesh = group;
        animatedObjects.push((t) => {{
          qLight.intensity = 60 + Math.sin(t * 2.5) * 15;
        }});
        break;
      }}
      case 'black_hole': {{
        const group = new THREE.Group();
        // Dark sphere
        const bhGeo = new THREE.SphereGeometry(0.6, 24, 24);
        const bhMat = new THREE.MeshStandardMaterial({{
          color: '#000000', emissive: P.black_hole, emissiveIntensity: 0.15,
          metalness: 1.0, roughness: 0.0,
        }});
        group.add(new THREE.Mesh(bhGeo, bhMat));
        // Accretion disk (torus)
        const rCol = P.ring || '#ff8822';
        const ringGeo = new THREE.TorusGeometry(2.0, 0.18, 12, 48);
        const ringMat = new THREE.MeshStandardMaterial({{
          color: rCol, emissive: rCol, emissiveIntensity: 1.2,
          transparent: true, opacity: 0.65, side: THREE.DoubleSide,
        }});
        const ring = new THREE.Mesh(ringGeo, ringMat);
        ring.rotation.x = Math.PI * 0.42;
        group.add(ring);
        // Outer faint ring
        const ring2Geo = new THREE.TorusGeometry(3.0, 0.08, 8, 48);
        const ring2Mat = new THREE.MeshStandardMaterial({{
          color: rCol, emissive: rCol, emissiveIntensity: 0.5,
          transparent: true, opacity: 0.25,
        }});
        const ring2 = new THREE.Mesh(ring2Geo, ring2Mat);
        ring2.rotation.x = Math.PI * 0.42;
        group.add(ring2);
        mesh = group;
        animatedObjects.push((t) => {{
          ring.rotation.z = t * 0.15;
          ring2.rotation.z = -t * 0.08;
        }});
        break;
      }}
      case 'magnetar': {{
        const mGeo = new THREE.OctahedronGeometry(0.35, 0);
        const mMat = new THREE.MeshStandardMaterial({{
          color: col, emissive: col, emissiveIntensity: 1.5,
          metalness: 0.5, roughness: 0.3,
        }});
        mesh = new THREE.Mesh(mGeo, mMat);
        // Magnetic field lines (wireframe rings)
        for (let i = 0; i < 2; i++) {{
          const fGeo = new THREE.TorusGeometry(0.8, 0.02, 4, 24);
          const fMat = new THREE.MeshBasicMaterial({{ color: col, transparent: true, opacity: 0.3 }});
          const f = new THREE.Mesh(fGeo, fMat);
          f.rotation.x = Math.PI * 0.5 * i;
          f.rotation.z = Math.PI * 0.3 * i;
          mesh.add(f);
        }}
        animatedObjects.push((t) => {{
          mMat.emissiveIntensity = 1.5 + Math.sin(t * 8) * 0.8;
          mesh.rotation.y = t * 0.5;
        }});
        break;
      }}
      case 'galaxy': {{
        const gs = 0.12 + obj.visual.scale * 0.1;
        const geo = new THREE.SphereGeometry(gs, 8, 8);
        const mat = new THREE.MeshStandardMaterial({{
          color: col, emissive: col, emissiveIntensity: 0.5,
          transparent: true, opacity: 0.85, metalness: 0.2, roughness: 0.7,
        }});
        mesh = new THREE.Mesh(geo, mat);
        break;
      }}
      case 'void': {{
        const vs = obj.visual.scale * 0.45;
        const geo = new THREE.IcosahedronGeometry(vs, 1);
        const mat = new THREE.MeshBasicMaterial({{
          color: col, transparent: true, opacity: 0.04, wireframe: true,
        }});
        mesh = new THREE.Mesh(geo, mat);
        break;
      }}
      case 'cmb_background': {{
        const geo = new THREE.IcosahedronGeometry(250, 2);
        const mat = new THREE.MeshBasicMaterial({{
          color: col, transparent: true,
          opacity: curMode === 'cmb' ? 0.12 : 0.02,
          side: THREE.BackSide, wireframe: curMode !== 'cmb',
        }});
        mesh = new THREE.Mesh(geo, mat);
        break;
      }}
      default: {{
        const geo = new THREE.SphereGeometry(0.4, 8, 8);
        const mat = new THREE.MeshStandardMaterial({{ color: col }});
        mesh = new THREE.Mesh(geo, mat);
      }}
    }}

    if (mesh.isGroup) {{
      mesh.position.set(obj.position_mpc.x, obj.position_mpc.y, obj.position_mpc.z);
    }} else {{
      mesh.position.set(obj.position_mpc.x, obj.position_mpc.y, obj.position_mpc.z);
    }}
    scene.add(mesh);
    meshEntries.push({{ mesh, data: obj, type: ot }});
  }});

  applyVis();
}}

function applyVis() {{
  meshEntries.forEach(e => {{
    if (e.mesh.isGroup) {{
      e.mesh.visible = !!vis[e.type];
    }} else {{
      e.mesh.visible = !!vis[e.type];
    }}
  }});
  filEntries.forEach(e => {{ e.mesh.visible = !!vis['filament']; }});
}}

buildScene();

// ── Sidebar: Toggles ──────────────────────────────────────────────────
const togEl = document.getElementById('toggles');
TOGGLE_TYPES.forEach(t => {{
  const row = document.createElement('div');
  row.className = 'toggle-row';

  const cb = document.createElement('input');
  cb.type = 'checkbox'; cb.checked = true; cb.id = 'tog-' + t.key;
  cb.addEventListener('change', () => {{ vis[t.key] = cb.checked; applyVis(); }});

  const dot = document.createElement('span');
  dot.className = 'color-dot'; dot.style.background = t.dot; dot.style.color = t.dot;

  const lbl = document.createElement('label');
  lbl.htmlFor = cb.id; lbl.textContent = t.label;

  const cnt = document.createElement('span');
  cnt.className = 'count'; cnt.textContent = typeCounts[t.key] || 0;

  row.append(cb, dot, lbl, cnt);
  togEl.appendChild(row);
}});

// ── Sidebar: Mode buttons ─────────────────────────────────────────────
const modesEl = document.getElementById('modes');
const MODE_LIST = {modes_json};
MODE_LIST.forEach(mode => {{
  const btn = document.createElement('button');
  btn.className = 'mode-btn' + (mode === curMode ? ' active' : '');
  btn.textContent = mode.replace(/_/g, ' ');
  btn.addEventListener('click', () => {{
    curMode = mode;
    document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    buildScene();
  }});
  modesEl.appendChild(btn);
}});

// ── Raycaster ─────────────────────────────────────────────────────────
const ray = new THREE.Raycaster();
const mouse = new THREE.Vector2();
const tooltip = document.getElementById('tooltip');
const inspector = document.getElementById('inspector');

function allVisible() {{
  return [...meshEntries, ...filEntries].filter(e => e.mesh.visible);
}}

function rayTargets() {{
  const targets = [];
  allVisible().forEach(e => {{
    if (e.mesh.isGroup) {{
      e.mesh.traverse(child => {{ if (child.isMesh) targets.push({{ mesh: child, entry: e }}); }});
    }} else {{
      targets.push({{ mesh: e.mesh, entry: e }});
    }}
  }});
  return targets;
}}

function hitTest(e) {{
  mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
  mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
  ray.setFromCamera(mouse, camera);
  const targets = rayTargets();
  const hits = ray.intersectObjects(targets.map(t => t.mesh));
  if (hits.length > 0) {{
    const target = targets.find(t => t.mesh === hits[0].object);
    return target ? target.entry : null;
  }}
  return null;
}}

renderer.domElement.addEventListener('mousemove', (e) => {{
  const entry = hitTest(e);
  if (entry) {{
    tooltip.style.display = 'block';
    tooltip.style.left = (e.clientX + 14) + 'px';
    tooltip.style.top = (e.clientY + 14) + 'px';
    const d = entry.data;
    tooltip.textContent = `${{d.name || d.id}} (${{d.type}})`;
    renderer.domElement.style.cursor = 'pointer';
  }} else {{
    tooltip.style.display = 'none';
    renderer.domElement.style.cursor = 'default';
  }}
}});

renderer.domElement.addEventListener('click', (e) => {{
  const entry = hitTest(e);
  if (entry) showInspector(entry.data);
}});

renderer.domElement.addEventListener('dblclick', (e) => {{
  const entry = hitTest(e);
  if (entry) {{
    const p = entry.data.position_mpc;
    if (p) {{
      controls.target.set(p.x, p.y, p.z);
      camera.position.set(p.x + 12, p.y + 8, p.z + 12);
      controls.update();
    }}
  }}
}});

// ── Relationship lines ────────────────────────────────────────────────
function showRelLines(data) {{
  relLines.forEach(l => scene.remove(l));
  relLines.length = 0;
  if (!data.relationships || !data.position_mpc) return;
  data.relationships.forEach(r => {{
    let targetPos = null;
    const tObj = objMap[r.target_id];
    if (tObj && tObj.position_mpc) {{
      targetPos = new THREE.Vector3(tObj.position_mpc.x, tObj.position_mpc.y, tObj.position_mpc.z);
    }}
    const tNode = nodeMap[r.target_id];
    if (!targetPos && tNode && tNode.position_mpc) {{
      targetPos = new THREE.Vector3(tNode.position_mpc.x, tNode.position_mpc.y, tNode.position_mpc.z);
    }}
    if (!targetPos) return;
    const from = new THREE.Vector3(data.position_mpc.x, data.position_mpc.y, data.position_mpc.z);
    const geo = new THREE.BufferGeometry().setFromPoints([from, targetPos]);
    const mat = new THREE.LineBasicMaterial({{ color: 0x6688ff, transparent: true, opacity: 0.5 }});
    const line = new THREE.Line(geo, mat);
    scene.add(line);
    relLines.push(line);
  }});
}}

// ── Inspector panel ───────────────────────────────────────────────────
function showInspector(data) {{
  showRelLines(data);
  let h = `<span class="close-btn" onclick="document.getElementById('inspector').style.display='none'">&times;</span>`;
  h += `<h3>${{data.name || data.id}}</h3>`;
  h += `<div class="obj-type">${{data.type}}</div>`;
  if (data.description) h += `<div class="desc">${{data.description}}</div>`;

  if (data.position_mpc) {{
    const p = data.position_mpc;
    h += `<div class="prop"><span class="prop-key">position</span><span class="prop-val">(${{p.x.toFixed(2)}}, ${{p.y.toFixed(2)}}, ${{p.z.toFixed(2)}}) cMpc</span></div>`;
  }}
  if (data.redshift !== undefined && data.redshift !== null) {{
    h += `<div class="prop"><span class="prop-key">redshift</span><span class="prop-val">z = ${{typeof data.redshift === 'number' ? data.redshift.toFixed(4) : data.redshift}}</span></div>`;
  }}
  if (data.density !== undefined) {{
    h += `<div class="prop"><span class="prop-key">density</span><span class="prop-val">${{data.density}}</span></div>`;
  }}
  if (data.node_class) {{
    h += `<div class="prop"><span class="prop-key">class</span><span class="prop-val">${{data.node_class}}</span></div>`;
  }}

  // Type-specific properties
  if (data.properties) {{
    h += `<div class="section-label">Properties</div>`;
    Object.entries(data.properties).forEach(([k, v]) => {{
      h += `<div class="prop"><span class="prop-key">${{k.replace(/_/g, ' ')}}</span><span class="prop-val">${{v}}</span></div>`;
    }});
  }}

  // Relationships
  if (data.relationships && data.relationships.length > 0) {{
    h += `<div class="section-label">Relationships</div>`;
    data.relationships.forEach(r => {{
      h += `<div class="rel" data-target="${{r.target_id}}">→ <strong>${{r.relation}}</strong>: ${{r.target_id}} <span style="color:#446">— ${{r.description}}</span></div>`;
    }});
  }}

  // Filament node links
  if (data.start_node_id) {{
    h += `<div class="section-label">Connected Nodes</div>`;
    h += `<div class="rel" data-target="${{data.start_node_id}}">→ start: ${{data.start_node_id}}</div>`;
    h += `<div class="rel" data-target="${{data.end_node_id}}">→ end: ${{data.end_node_id}}</div>`;
  }}

  inspector.innerHTML = h;
  inspector.style.display = 'block';

  // Clickable relationships — navigate to target
  inspector.querySelectorAll('.rel[data-target]').forEach(el => {{
    el.addEventListener('click', () => {{
      const tid = el.dataset.target;
      const tgt = objMap[tid] || SD.nodes.find(n => n.id === tid);
      if (tgt) {{
        const tData = tgt.position_mpc ? {{ ...tgt, type: tgt.type || 'cosmic_web_node', name: tgt.name || tgt.id }} : null;
        if (tData) {{
          showInspector(tData);
          controls.target.set(tData.position_mpc.x, tData.position_mpc.y, tData.position_mpc.z);
        }}
      }}
    }});
  }});
}}

// ── Stats ─────────────────────────────────────────────────────────────
document.getElementById('stats').textContent =
  `${{SD.objects.length}} obj · ${{SD.nodes.length}} nodes · ${{SD.filaments.length}} fil · z=${{SD.redshift}}`;

// ── Resize ────────────────────────────────────────────────────────────
window.addEventListener('resize', () => {{
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
  composer.setSize(window.innerWidth, window.innerHeight);
}});

// ── Animation loop ────────────────────────────────────────────────────
const clock = new THREE.Clock();
function animate() {{
  requestAnimationFrame(animate);
  const t = clock.getElapsedTime();
  animatedObjects.forEach(fn => fn(t));
  controls.update();
  composer.render();
}}
animate();
</script>
</body>
</html>"""
