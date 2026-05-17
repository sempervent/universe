"""Generate a self-contained playable telescope UI as static HTML.

The output embeds scene data, tech tree, discovery requirements, and
game state as JSON, then implements the game loop client-side in vanilla
JavaScript with localStorage persistence.
"""

from __future__ import annotations

import json
from pathlib import Path

from universe.game.discovery import get_discovery_requirements
from universe.game.milestones import get_default_milestones
from universe.game.models import ResearchState
from universe.game.surveys import get_default_survey_programs
from universe.game.tech_tree import get_default_tech_tree
from universe.models import SceneRegion


def export_telescope_ui(
    scene: SceneRegion,
    state: ResearchState | None = None,
    out_path: str | Path = "data/generated/telescope-ui.html",
) -> Path:
    """Write a playable telescope UI HTML file.

    Returns the path to the written file.
    """
    if state is None:
        state = ResearchState()

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    from universe.game.entity import (
        ENTITY_TYPE_LABELS,
        RANDOM_ENTITY_NAMES,
        get_all_entity_modifiers,
    )
    from universe.game.scenes import campaign_catalog_bundle
    from universe.game.objectives import objectives_for_export
    from universe.game.transients import transients_for_export

    scene_json = scene.model_dump_json()
    state_json = state.model_dump_json()
    tree_json = json.dumps([t.model_dump() for t in get_default_tech_tree()])
    reqs_json = json.dumps([r.model_dump() for r in get_discovery_requirements()])
    random_names_json = json.dumps(RANDOM_ENTITY_NAMES)
    entity_types_json = json.dumps(ENTITY_TYPE_LABELS)
    surveys_json = json.dumps([s.model_dump() for s in get_default_survey_programs()])
    milestones_json = json.dumps([m.model_dump() for m in get_default_milestones()])

    modifiers_json = json.dumps([m.model_dump() for m in get_all_entity_modifiers()])
    catalog_json = json.dumps(campaign_catalog_bundle(state))
    transients_json = json.dumps(transients_for_export())
    objectives_json = json.dumps(objectives_for_export())

    html = _TELESCOPE_HTML.replace("__SCENE_DATA__", scene_json)
    html = html.replace("__STATE_DATA__", state_json)
    html = html.replace("__TECH_TREE__", tree_json)
    html = html.replace("__DISCOVERY_REQS__", reqs_json)
    html = html.replace("__RANDOM_NAMES__", random_names_json)
    html = html.replace("__ENTITY_TYPES__", entity_types_json)
    html = html.replace("__ENTITY_MODIFIERS__", modifiers_json)
    html = html.replace("__SURVEYS_DATA__", surveys_json)
    html = html.replace("__MILESTONES_DATA__", milestones_json)
    html = html.replace("__SCENE_CATALOG__", catalog_json)
    html = html.replace("__TRANSIENTS_DATA__", transients_json)
    html = html.replace("__OBJECTIVES_DATA__", objectives_json)
    html = html.replace("__SCENE_NAME__", scene.name)

    out.write_text(html, encoding="utf-8")
    return out


_TELESCOPE_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__SCENE_NAME__ — Observatory Console</title>
<style>
:root {
  --bg: #060610; --panel: rgba(10,12,24,0.95); --border: rgba(80,90,180,0.15);
  --text: #b0b8d0; --dim: #4a5070; --bright: #d8ddf0; --accent: #6680ff;
  --green: #44cc88; --orange: #ee9944; --red: #ee5555; --cyan: #44dddd;
  --gold: #eebb33; --purple: #aa66ff;
  --font: 'SF Mono', 'Fira Code', 'Consolas', monospace;
  --sans: 'Segoe UI', system-ui, -apple-system, sans-serif;
}
* { margin:0; padding:0; box-sizing:border-box; }
body { background: var(--bg); color: var(--text); font-family: var(--sans); font-size: 13px; height: 100vh; overflow: hidden; }

/* Layout */
#app { display: grid; grid-template-columns: 260px 1fr 320px; grid-template-rows: 48px 1fr 180px; height: 100vh; gap: 1px; }
#header { grid-column: 1/-1; background: var(--panel); border-bottom: 1px solid var(--border); display: flex; align-items: center; padding: 0 18px; gap: 20px; }
#left { grid-row: 2/3; background: var(--panel); border-right: 1px solid var(--border); overflow-y: auto; }
#center { grid-row: 2/3; position: relative; background: #030308; overflow: hidden; }
#right { grid-row: 2/3; background: var(--panel); border-left: 1px solid var(--border); overflow-y: auto; }
#log { grid-column: 1/-1; grid-row: 3/4; background: var(--panel); border-top: 1px solid var(--border); overflow-y: auto; padding: 10px 16px; }

/* Header */
#header h1 { font-size: 14px; color: var(--bright); font-weight: 600; letter-spacing: 0.04em; }
.hstat { font-size: 11px; color: var(--dim); }
.hstat b { color: var(--accent); font-weight: 600; }
.hstat.rp b { color: var(--gold); }
#btn-reset { margin-left: auto; background: rgba(200,60,60,0.15); border: 1px solid rgba(200,60,60,0.25); color: #c44; padding: 4px 12px; border-radius: 4px; cursor: pointer; font-size: 10px; font-family: var(--sans); }
#btn-reset:hover { background: rgba(200,60,60,0.3); }
#btn-export { background: rgba(60,120,200,0.15); border: 1px solid rgba(60,120,200,0.25); color: #68b; padding: 4px 12px; border-radius: 4px; cursor: pointer; font-size: 10px; font-family: var(--sans); margin-left: 6px; }
#btn-export:hover { background: rgba(60,120,200,0.3); }

/* Left panel */
#left { padding: 12px; }
.panel-title { font-size: 10px; color: var(--dim); text-transform: uppercase; letter-spacing: 0.12em; margin: 12px 0 6px; font-weight: 600; }
.panel-title:first-child { margin-top: 0; }

/* Object list */
.obj-row { display: flex; align-items: center; gap: 6px; padding: 5px 6px; border-radius: 4px; cursor: pointer; transition: background 0.12s; font-size: 11.5px; }
.obj-row:hover { background: rgba(100,128,255,0.08); }
.obj-row.selected { background: rgba(100,128,255,0.14); }
.obj-row.undiscovered { opacity: 0.4; font-style: italic; }
.obj-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.obj-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.obj-conf { font-size: 9px; color: var(--dim); font-family: var(--font); }
.conf-high { color: var(--green); }
.conf-mid { color: var(--orange); }
.conf-low { color: var(--red); }

/* Buttons */
.btn { background: rgba(100,128,255,0.12); border: 1px solid rgba(100,128,255,0.2); color: var(--accent); padding: 6px 14px; border-radius: 5px; cursor: pointer; font-size: 11px; font-family: var(--sans); transition: all 0.15s; display: inline-block; text-align: center; }
.btn:hover { background: rgba(100,128,255,0.22); border-color: rgba(100,128,255,0.4); }
.btn:disabled { opacity: 0.3; cursor: default; }
.btn-observe { width: 100%; margin: 8px 0; background: rgba(40,180,100,0.15); border-color: rgba(40,180,100,0.25); color: var(--green); }
.btn-observe:hover { background: rgba(40,180,100,0.25); }
.btn-survey { width: 100%; margin: 0 0 8px; }

/* Center sky map */
#sky-canvas { width: 100%; height: 100%; }

/* Right panel */
#right { padding: 14px; }
.tab-bar { display: flex; gap: 2px; margin-bottom: 10px; }
.tab-btn { flex: 1; padding: 5px 0; text-align: center; font-size: 10px; color: var(--dim); cursor: pointer; border-radius: 4px; transition: all 0.15s; text-transform: uppercase; letter-spacing: 0.06em; }
.tab-btn:hover { color: var(--text); background: rgba(100,128,255,0.06); }
.tab-btn.active { color: var(--accent); background: rgba(100,128,255,0.1); }
.tab-content { display: none; }
.tab-content.active { display: block; }

/* Detail panel */
.detail-name { font-size: 15px; color: var(--bright); font-weight: 600; margin-bottom: 2px; }
.detail-type { font-size: 10px; color: var(--dim); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px; }
.detail-desc { font-size: 11.5px; color: #7880a0; line-height: 1.5; margin-bottom: 10px; }
.detail-row { display: flex; gap: 8px; margin: 2px 0; font-size: 11px; }
.detail-key { color: var(--dim); min-width: 80px; flex-shrink: 0; }
.detail-val { color: var(--text); word-break: break-all; }
.detail-section { font-size: 9px; color: var(--dim); text-transform: uppercase; letter-spacing: 0.1em; margin: 10px 0 4px; }
.signal-tag { display: inline-block; padding: 1px 6px; border-radius: 3px; font-size: 9px; margin: 1px 2px; font-family: var(--font); }
.signal-have { background: rgba(40,180,100,0.15); color: var(--green); border: 1px solid rgba(40,180,100,0.2); }
.signal-need { background: rgba(200,60,60,0.1); color: #a55; border: 1px solid rgba(200,60,60,0.15); }
.signal-opt { background: rgba(100,128,255,0.1); color: var(--accent); border: 1px solid rgba(100,128,255,0.15); }

/* Tech tree */
.tier-card { padding: 8px 10px; margin: 4px 0; border-radius: 5px; border: 1px solid var(--border); font-size: 11px; transition: all 0.15s; }
.tier-card.unlocked { border-color: rgba(40,180,100,0.2); background: rgba(40,180,100,0.04); }
.tier-card.available { border-color: rgba(100,128,255,0.25); background: rgba(100,128,255,0.06); }
.tier-card.locked { opacity: 0.4; }
.tier-card.speculative { border-color: rgba(170,100,255,0.2); }
.tier-card .tier-name { font-weight: 600; color: var(--bright); font-size: 12px; }
.tier-card .tier-meta { color: var(--dim); font-size: 10px; margin-top: 3px; }
.tier-card .tier-signals { margin-top: 4px; }
.tier-card .btn { margin-top: 6px; padding: 4px 10px; font-size: 10px; }
.spec-badge { font-size: 8px; color: var(--purple); border: 1px solid rgba(170,100,255,0.3); padding: 1px 5px; border-radius: 3px; margin-left: 6px; vertical-align: middle; }

/* Log */
#log .panel-title { margin-top: 0; }
.log-entry { font-size: 11px; padding: 2px 0; border-bottom: 1px solid rgba(255,255,255,0.02); font-family: var(--font); }
.log-entry .ts { color: var(--dim); font-size: 9px; margin-right: 8px; }
.log-new { color: var(--green); }
.log-upgrade { color: var(--cyan); }
.log-info { color: var(--dim); }
.log-unlock { color: var(--gold); }

/* Naming modal */
#naming-overlay { position: fixed; inset: 0; background: rgba(2,3,8,0.92); z-index: 1000; display: flex; align-items: center; justify-content: center; }
#naming-modal { background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 36px 40px; max-width: 440px; width: 90%; }
#naming-modal h2 { color: var(--bright); font-size: 18px; margin-bottom: 4px; }
#naming-modal .nm-sub { color: var(--dim); font-size: 11px; margin-bottom: 20px; }
#naming-modal label { display: block; font-size: 10px; color: var(--dim); text-transform: uppercase; letter-spacing: 0.1em; margin: 12px 0 4px; }
#naming-modal input, #naming-modal select { width: 100%; background: rgba(255,255,255,0.04); border: 1px solid var(--border); color: var(--bright); padding: 8px 10px; border-radius: 5px; font-size: 13px; font-family: var(--sans); }
#naming-modal input:focus, #naming-modal select:focus { outline: none; border-color: var(--accent); }
#naming-modal .nm-btns { display: flex; gap: 8px; margin-top: 20px; }
#naming-modal .nm-btns .btn { flex: 1; padding: 10px; font-size: 12px; }
.btn-begin { background: rgba(40,180,100,0.15); border-color: rgba(40,180,100,0.25); color: var(--green); }
.btn-begin:hover { background: rgba(40,180,100,0.3); }
.btn-random { background: rgba(170,100,255,0.12); border-color: rgba(170,100,255,0.2); color: var(--purple); }
.btn-random:hover { background: rgba(170,100,255,0.25); }
</style>
</head>
<body>
<div id="naming-overlay" style="display:none">
  <div id="naming-modal">
    <h2>Establish Your Research Entity</h2>
    <div class="nm-sub">Name the observatory, institute, or research group you represent.</div>
    <label for="nm-name">Entity Name</label>
    <input id="nm-name" type="text" placeholder="e.g. Hydrogen Ghost Institute" maxlength="80" autocomplete="off">
    <label for="nm-type">Entity Type</label>
    <select id="nm-type"></select>
    <label for="nm-motto">Motto <span style="color:var(--dim)">(optional)</span></label>
    <input id="nm-motto" type="text" placeholder='e.g. "Listening for the old light."' maxlength="120" autocomplete="off">
    <div class="nm-btns">
      <button class="btn btn-random" id="nm-random">Random Name</button>
      <button class="btn btn-begin" id="nm-begin">Begin Observing</button>
    </div>
  </div>
</div>
<div id="app">
  <div id="header">
    <h1 id="h-title">Observatory Console</h1>
    <span class="hstat" id="h-telescope"></span>
    <span class="hstat rp" id="h-rp"></span>
    <span class="hstat" id="h-signals"></span>
    <span class="hstat" id="h-discoveries"></span>
    <span class="hstat" id="h-background" style="max-width:280px;white-space:normal;line-height:1.3"></span>
    <span class="hstat" id="h-objective" style="max-width:320px;white-space:normal;line-height:1.3;color:var(--gold)"></span>
    <button id="btn-export" title="Export game state as JSON">Export</button>
    <button id="btn-reset" title="Reset all progress">Reset</button>
  </div>
  <div id="left">
    <div class="panel-title">Observation Controls</div>
    <button class="btn btn-observe" id="btn-observe">Observe Selected</button>
    <button class="btn btn-survey" id="btn-survey">Survey All</button>
    <div class="panel-title">Objects</div>
    <div id="obj-list"></div>
  </div>
  <div id="center">
    <canvas id="sky-canvas"></canvas>
  </div>
  <div id="right">
    <div class="tab-bar">
      <div class="tab-btn active" data-tab="detail">Detail</div>
      <div class="tab-btn" data-tab="tech">Tech</div>
      <div class="tab-btn" data-tab="surveys">Surveys</div>
      <div class="tab-btn" data-tab="milestones">Milestones</div>
      <div class="tab-btn" data-tab="campaign">Campaign</div>
      <div class="tab-btn" data-tab="transients">Transients</div>
      <div class="tab-btn" data-tab="objectives">Objectives</div>
    </div>
    <div id="tab-detail" class="tab-content active"></div>
    <div id="tab-transients" class="tab-content"></div>
    <div id="tab-objectives" class="tab-content"></div>
    <div id="tab-tech" class="tab-content"></div>
    <div id="tab-surveys" class="tab-content"></div>
    <div id="tab-milestones" class="tab-content"></div>
    <div id="tab-campaign" class="tab-content"></div>
  </div>
  <div id="log">
    <div class="panel-title">Discovery Log</div>
    <div id="log-entries"></div>
  </div>
</div>

<script>
// ── Embedded data ─────────────────────────────────────────────────────
const SCENE = __SCENE_DATA__;
const INIT_STATE = __STATE_DATA__;
const TECH_TREE = __TECH_TREE__;
const DISC_REQS = __DISCOVERY_REQS__;
const RANDOM_NAMES = __RANDOM_NAMES__;
const SURVEYS = __SURVEYS_DATA__;
const MILESTONES = __MILESTONES_DATA__;
const SCENE_CATALOG = __SCENE_CATALOG__;
const TRANSIENTS = __TRANSIENTS_DATA__;
const OBJECTIVES = __OBJECTIVES_DATA__;
const ENTITY_TYPES = __ENTITY_TYPES__;
const ENTITY_MODIFIERS = __ENTITY_MODIFIERS__;

const STORAGE_KEY = 'universe_game_state_' + SCENE.id;
const DEFAULT_ENTITY_NAME = 'Unnamed Research Entity';

// ── Safe text helper ──────────────────────────────────────────────────
function esc(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}
function safeText(el, text) { el.textContent = text; }

// ── State management ──────────────────────────────────────────────────
let state = loadState();
let selectedObjId = null;

function ensureEntity() {
  if (!state.research_entity) {
    state.research_entity = { id: '', name: DEFAULT_ENTITY_NAME, entity_type: 'custom', motto: '', founded_turn: 0, description: '', style: '', created_at: '', metadata: {} };
  }
}

function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) { const s = JSON.parse(raw); return s; }
  } catch {}
  return JSON.parse(JSON.stringify(INIT_STATE));
}
function saveState() { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); }

function entityName() {
  ensureEntity();
  return state.research_entity.name || DEFAULT_ENTITY_NAME;
}

function needsNaming() {
  ensureEntity();
  return !state.research_entity.name || state.research_entity.name === DEFAULT_ENTITY_NAME;
}

// ── Tech tree helpers ─────────────────────────────────────────────────
const tierMap = {};
TECH_TREE.forEach(t => tierMap[t.id] = t);

function allSignals() {
  const s = new Set();
  state.unlocked_tiers.forEach(tid => {
    const t = tierMap[tid];
    if (t) t.signal_types.forEach(sig => s.add(sig));
  });
  return s;
}
function bestSens() {
  let b = 0;
  state.unlocked_tiers.forEach(tid => { const t = tierMap[tid]; if (t) b = Math.max(b, t.sensitivity); });
  return b;
}
function bestRes() {
  let b = 99999;
  state.unlocked_tiers.forEach(tid => { const t = tierMap[tid]; if (t) b = Math.min(b, t.resolution_arcsec); });
  return b;
}
function maxDist() {
  let b = 0;
  state.unlocked_tiers.forEach(tid => { const t = tierMap[tid]; if (t) b = Math.max(b, t.max_effective_distance_mpc); });
  return b;
}
function availableUpgrades() {
  const u = new Set(state.unlocked_tiers);
  return TECH_TREE.filter(t => !u.has(t.id) && t.prerequisites.every(p => u.has(p)));
}

// ── Entity background modifiers (mirror universe.game.entity + tech_tree) ──
function getEntityModifier() {
  const t = (state.research_entity || {}).entity_type || 'custom';
  let m = ENTITY_MODIFIERS.find(x => x.entity_type === t);
  if (!m) m = ENTITY_MODIFIERS.find(x => x.entity_type === 'custom');
  return m;
}
function isEarlyOpticalTierId(id) {
  return id === 'ground_optical' || id === 'improved_ground';
}
function isSpaceTrackTier(tier) {
  return tier.tier_index >= 3;
}
function effectiveTierCost(tier) {
  const mod = getEntityModifier();
  let c = tier.research_cost;
  c *= mod.upgrade_cost_multiplier;
  if (isEarlyOpticalTierId(tier.id)) c *= mod.early_optical_upgrade_cost_multiplier;
  if (isSpaceTrackTier(tier)) c *= mod.space_upgrade_cost_multiplier;
  return Math.max(0, Math.round(c));
}
function effectiveSurveyReward(survey) {
  const mod = getEntityModifier();
  let mult = mod.survey_rp_multiplier;
  if (mod.speculative_bonus && survey.speculative) mult *= 1.1;
  return Math.max(0, Math.round(survey.reward_research_points * mult));
}
function effectiveMilestoneReward(m) {
  const mod = getEntityModifier();
  let mult = mod.milestone_rp_multiplier;
  if (mod.speculative_bonus && m.speculative) mult *= 1.1;
  return Math.max(0, Math.round(m.reward_research_points * mult));
}

// ── Discovery engine (JS port) ───────────────────────────────────────
const reqMap = {};
DISC_REQS.forEach(r => reqMap[r.object_type] = r);

function calcConfidence(obj) {
  const req = reqMap[obj.type];
  if (!req) return { confidence: 0, detected: [] };
  const sigs = allSignals();
  const sens = bestSens(), res = bestRes(), md = maxDist();
  if (sens < req.minimum_sensitivity) return { confidence: 0, detected: [] };
  if (res > req.minimum_resolution_arcsec) return { confidence: 0, detected: [] };
  const p = obj.position_mpc;
  const dist = Math.sqrt(p.x*p.x + p.y*p.y + p.z*p.z);
  if (dist > md && dist > 0.0001) return { confidence: 0, detected: [] };

  const required = new Set(req.required_signal_types);
  const optional = new Set(req.optional_signal_types);
  const detReq = [...required].filter(s => sigs.has(s));
  const detOpt = [...optional].filter(s => sigs.has(s));
  const allDet = [...new Set([...detReq, ...detOpt])].sort();

  const sigCov = required.size === 0 ? 1 : detReq.length / required.size;
  const sensFact = Math.min(1, sens / Math.max(req.minimum_sensitivity, 0.01));
  const resFact = Math.min(1, req.minimum_resolution_arcsec / Math.max(res, 0.00001));
  let base = sigCov * Math.min(sensFact, 1) * Math.min(resFact, 1);
  const mmBonus = 0.08 * detOpt.length;
  let conf = Math.min(1, base + mmBonus);
  if (md > 0 && dist > 0.0001) {
    const dr = dist / md;
    if (dr > 0.5) conf *= Math.max(0.3, 1 - (dr - 0.5));
  }
  conf = Math.round(conf * 10000) / 10000;
  if (conf > 0) {
    const mod = getEntityModifier();
    conf = Math.min(1, Math.round((conf + mod.confidence_bonus) * 10000) / 10000);
  }
  return { confidence: conf, detected: allDet };
}

function confLabel(c) {
  if (c < 0.25) return 'not detected';
  if (c < 0.50) return 'signal anomaly';
  if (c < 0.75) return 'candidate';
  if (c < 0.95) return 'confirmed';
  return 'characterized';
}
function confClass(c) {
  if (c >= 0.75) return 'conf-high';
  if (c >= 0.25) return 'conf-mid';
  return 'conf-low';
}

function awardPoints(obj, conf, isNew) {
  const req = reqMap[obj.type];
  const base = req ? req.base_research_points : 5;
  if (conf < 0.25) return 0;
  let pts = Math.floor(base * conf);
  if (isNew) {
    const seenTypes = new Set(Object.values(state.discoveries).map(d => d.object_type));
    if (!seenTypes.has(obj.type)) pts = Math.floor(pts * 1.5);
  }
  pts = Math.max(1, pts);
  const mod = getEntityModifier();
  return Math.max(1, Math.round(pts * mod.discovery_rp_multiplier));
}

let firstDiscoveryCount = 0;
let firstTypesSeen = new Set();

function observeObject(objId) {
  const obj = SCENE.objects.find(o => o.id === objId);
  if (!obj) return null;
  const { confidence, detected } = calcConfidence(obj);
  if (confidence < 0.01) return null;

  const prev = state.discoveries[objId];
  const isNew = !prev;
  const isUpgrade = prev && confidence > prev.confidence + 0.05;
  if (!isNew && !isUpgrade) return null;

  const pts = isNew ? awardPoints(obj, confidence, true) : Math.max(1, Math.floor(awardPoints(obj, confidence, false) / 2));
  const isFirstOfType = isNew && !firstTypesSeen.has(obj.type);
  state.research_points += pts;
  state.discoveries[objId] = {
    object_id: objId, object_type: obj.type,
    confidence, detected_signals: detected,
    research_points_earned: ((prev ? prev.research_points_earned : 0) + pts),
    first_detected_tier: state.active_telescope_tier,
  };
  if (isNew) { firstDiscoveryCount++; firstTypesSeen.add(obj.type); }

  // Survey progress
  const surveyEvent = applySurveyProgress(objId, obj.type, detected, confidence);

  saveState();
  return { obj, confidence, detected, pts, isNew, isUpgrade, isFirstOfType, label: confLabel(confidence), surveyEvent };
}

function observeAll() {
  const results = [];
  SCENE.objects.forEach(o => {
    const r = observeObject(o.id);
    if (r) results.push(r);
  });
  return results;
}

function unlockTier(tierId) {
  const tier = tierMap[tierId];
  if (!tier) return false;
  if (state.unlocked_tiers.includes(tierId)) return false;
  if (!tier.prerequisites.every(p => state.unlocked_tiers.includes(p))) return false;
  const cost = effectiveTierCost(tier);
  if (state.research_points < cost) return false;
  state.research_points -= cost;
  state.unlocked_tiers.push(tierId);
  state.active_telescope_tier = tierId;
  const newSigs = new Set(state.known_signal_types);
  tier.signal_types.forEach(s => newSigs.add(s));
  state.known_signal_types = [...newSigs].sort();
  saveState();
  return true;
}

// ── Surveys (JS port of Python rules) ─────────────────────────────────
const surveyMap = {};
SURVEYS.forEach(s => surveyMap[s.id] = s);

function ensureSurveyMilestoneFields() {
  ensureObjectiveFields();
  if (!state.survey_progress) state.survey_progress = {};
  if (!state.milestones) state.milestones = {};
  if (state.active_survey_id === undefined) state.active_survey_id = null;
  if (typeof state.turn !== 'number') state.turn = 0;
}

function ensureObjectiveFields() {
  if (!state.objectives) state.objectives = {};
  if (!state.active_objective_ids) state.active_objective_ids = [];
  if (!state.campaign) state.campaign = { active_scene_id: 'solar-system', scenes: {} };
  if (!state.transient_events) state.transient_events = {};
}

const SOLAR_DISCOVERY_TYPES_JS = new Set(['star','planet','moon','asteroid','comet','observatory']);
const DEEP_FIELD_TYPES_JS = new Set(['galaxy','quasar','lyman_alpha_blob']);

function objectiveCondition(defn) {
  const tt = defn.trigger_type;
  if (tt === 'entity_named') return !needsNaming();
  if (tt === 'solar_discovery') return Object.values(state.discoveries).some(d => SOLAR_DISCOVERY_TYPES_JS.has(d.object_type));
  if (tt === 'survey_complete') {
    const p = state.survey_progress[defn.required_survey_id];
    return p && p.completed;
  }
  if (tt === 'tier_unlocked') return (state.unlocked_tiers || []).includes(defn.required_tier_id);
  if (tt === 'transient_observed') return Object.values(state.transient_events || {}).some(ts => ts.reward_claimed);
  if (tt === 'campaign_scene_unlocked') {
    const cs = (state.campaign.scenes || {})[defn.required_scene_id];
    return cs && cs.unlocked;
  }
  if (tt === 'campaign_scene_active') {
    return (state.campaign.active_scene_id === defn.required_scene_id) || (SCENE.id === defn.required_scene_id);
  }
  if (tt === 'survey_active_or_complete') {
    return state.active_survey_id === defn.required_survey_id || (state.survey_progress[defn.required_survey_id] && state.survey_progress[defn.required_survey_id].completed);
  }
  if (tt === 'deep_field_discovery') {
    return Object.values(state.discoveries).some(d => DEEP_FIELD_TYPES_JS.has(d.object_type) && d.confidence >= 0.5);
  }
  return false;
}

function evaluateObjectivesJS() {
  ensureObjectiveFields();
  const newly = [];
  let changed = true;
  while (changed) {
    changed = false;
    const sorted = [...OBJECTIVES].sort((a,b) => (a.tutorial_step||0) - (b.tutorial_step||0));
    for (const defn of sorted) {
      const prog = state.objectives[defn.id] || { objective_id: defn.id, status: 'locked', reward_claimed: false };
      if (prog.status === 'completed') continue;
      const canEval = prog.status === 'active' || sorted.every(o => o.tutorial_step >= defn.tutorial_step || (state.objectives[o.id] && state.objectives[o.id].status === 'completed') || o.tutorial_step >= defn.tutorial_step);
      const predsOk = sorted.filter(o => o.tutorial_step < defn.tutorial_step).every(o => state.objectives[o.id] && state.objectives[o.id].status === 'completed');
      if (prog.status !== 'active' && !predsOk) continue;
      if (!objectiveCondition(defn)) continue;
      state.objectives[defn.id] = { ...prog, status: 'completed', completed_turn: state.turn, reward_claimed: true };
      state.active_objective_ids = (state.active_objective_ids || []).filter(id => id !== defn.id);
      (defn.next_objective_ids || []).forEach(nid => {
        if (!state.objectives[nid]) state.objectives[nid] = { objective_id: nid, status: 'locked', reward_claimed: false };
        if (state.objectives[nid].status === 'locked') state.objectives[nid].status = 'active';
        if (!(state.active_objective_ids || []).includes(nid)) state.active_objective_ids.push(nid);
      });
      if (!prog.reward_claimed) state.research_points += defn.reward_research_points || 0;
      newly.push(defn);
      changed = true;
    }
  }
  if (!Object.keys(state.objectives).length && OBJECTIVES.length) {
    const first = OBJECTIVES[0];
    state.objectives[first.id] = { objective_id: first.id, status: 'active', reward_claimed: false };
    state.active_objective_ids = [first.id];
  }
  if (newly.length) saveState();
  return newly;
}

function logObjectives(completed) {
  (completed || []).forEach(o => addLog('Objective: ' + o.title + ' — +' + (o.reward_research_points||0) + ' RP', 'log-unlock'));
}

function scopeMatches(survey) {
  if (survey.scene_scope === 'any') return true;
  if (survey.scene_scope === 'solar_system') return SCENE.id === 'solar-system';
  if (survey.scene_scope === 'deep_field') return SCENE.id !== 'solar-system';
  return false;
}

function surveyStatus(survey) {
  const prog = state.survey_progress[survey.id];
  if (prog && prog.completed) return 'completed';
  if (state.active_survey_id === survey.id) return 'active';
  const tiers = new Set(state.unlocked_tiers);
  const sigs = new Set(state.known_signal_types);
  if (!survey.required_tier_ids.every(t => tiers.has(t))) return 'locked';
  if (!survey.required_signal_types.every(s => sigs.has(s))) return 'locked';
  return 'available';
}

function matchesSurvey(survey, objType, detectedSignals, conf) {
  if (survey.target_object_types && survey.target_object_types.length > 0) {
    if (!survey.target_object_types.includes(objType)) return false;
  } else if (!survey.speculative) {
    return false;
  }
  if (conf < (survey.min_confidence || 0.5)) return false;
  if (!scopeMatches(survey)) return false;
  if (survey.required_signal_types && survey.required_signal_types.length > 0) {
    const det = new Set(detectedSignals);
    if (!survey.required_signal_types.every(s => det.has(s))) return false;
  }
  return true;
}

function applySurveyProgress(objId, objType, detectedSignals, conf) {
  if (!state.active_survey_id) return null;
  const survey = surveyMap[state.active_survey_id];
  if (!survey) return null;
  if (!matchesSurvey(survey, objType, detectedSignals, conf)) return null;

  let prog = state.survey_progress[survey.id];
  if (!prog) {
    prog = { survey_id: survey.id, observations_completed: 0, discoveries_completed: 0, completed: false, claimed_reward: false, discovered_object_ids: [] };
    state.survey_progress[survey.id] = prog;
  }
  if (prog.completed) return null;
  if (prog.discovered_object_ids.includes(objId)) return null;

  const mod = getEntityModifier();
  let delta = 1;
  if (survey.completion_goal >= 8 && (mod.survey_progress_bonus || 0) > 0) {
    delta = 1 + mod.survey_progress_bonus;
  }
  prog.discovered_object_ids.push(objId);
  prog.discoveries_completed = Math.min(survey.completion_goal, prog.discoveries_completed + delta);
  if (prog.discoveries_completed >= survey.completion_goal && !prog.completed) {
    prog.completed = true;
    if (!prog.claimed_reward) {
      const reward = effectiveSurveyReward(survey);
      state.research_points += reward;
      prog.claimed_reward = true;
      return { type: 'completed', survey, reward };
    }
  }
  return { type: 'progress', survey, done: prog.discoveries_completed, goal: survey.completion_goal };
}

function startSurvey(surveyId) {
  const survey = surveyMap[surveyId];
  if (!survey) return false;
  const status = surveyStatus(survey);
  if (status === 'locked' || status === 'completed') return false;
  state.active_survey_id = surveyId;
  if (!state.survey_progress[surveyId]) {
    state.survey_progress[surveyId] = { survey_id: surveyId, observations_completed: 0, discoveries_completed: 0, completed: false, claimed_reward: false, discovered_object_ids: [] };
  }
  saveState();
  return true;
}

function claimSurvey(surveyId) {
  const survey = surveyMap[surveyId];
  if (!survey) return false;
  const prog = state.survey_progress[surveyId];
  if (!prog || !prog.completed || prog.claimed_reward) return false;
  state.research_points += effectiveSurveyReward(survey);
  prog.claimed_reward = true;
  saveState();
  return true;
}

// ── Milestones (JS port) ──────────────────────────────────────────────
const milestoneMap = {};
MILESTONES.forEach(m => milestoneMap[m.id] = m);

const DEFAULT_NAMED = 'Unnamed Research Entity';

function hasDiscovery(typeSet, minConf) {
  return Object.values(state.discoveries).some(d => typeSet.has(d.object_type) && d.confidence >= minConf);
}
function hasSignalInDiscoveries(sig) {
  return Object.values(state.discoveries).some(d => (d.detected_signals || []).includes(sig));
}

function milestoneCondition(id) {
  switch (id) {
    case 'first_light': return state.turn >= 1 || Object.keys(state.discoveries).length > 0;
    case 'named_entity': {
      const n = (state.research_entity || {}).name || '';
      return n && n !== DEFAULT_NAMED;
    }
    case 'first_planet': return hasDiscovery(new Set(['planet']), 0.75);
    case 'first_moon': return hasDiscovery(new Set(['moon']), 0.75);
    case 'first_comet': return hasDiscovery(new Set(['comet']), 0.5);
    case 'first_upgrade': return state.unlocked_tiers.filter(t => t !== 'naked_eye').length >= 1;
    case 'first_deep_field_ready': {
      if (!state.unlocked_tiers.includes('space_optical')) return false;
      const fl = state.survey_progress['local_sky_survey'];
      if (fl && fl.completed) return true;
      const solar = new Set(['star', 'planet', 'moon', 'asteroid', 'comet']);
      return Object.values(state.discoveries).filter(d => solar.has(d.object_type) && d.confidence >= 0.5).length >= 8;
    }
    case 'radio_first_light': return state.known_signal_types.includes('radio') || hasSignalInDiscoveries('radio');
    case 'first_deep_sky_object': return hasDiscovery(new Set(['galaxy', 'quasar', 'lyman_alpha_blob']), 0.5);
    case 'first_black_hole_candidate': return hasDiscovery(new Set(['black_hole']), 0.5);
    case 'first_magnetar': return hasDiscovery(new Set(['magnetar']), 0.75);
    case 'multi_messenger_confirmation':
      return Object.values(state.discoveries).some(d => (d.detected_signals || []).length >= 3 && d.confidence >= 0.75);
    case 'cosmic_web_mapped': return hasDiscovery(new Set(['cosmic_web_filament', 'cosmic_web_node']), 0.75);
    case 'dark_matter_inferred': return hasSignalInDiscoveries('dark_matter_inference');
    case 'now_scope_first_light':
      return hasSignalInDiscoveries('speculative_now_signal') ||
        Object.values(state.discoveries).some(d => d.first_detected_tier === 'now_scope');
    default: return false;
  }
}

function evaluateMilestonesJS() {
  const newly = [];
  MILESTONES.forEach(m => {
    const existing = state.milestones[m.id];
    if (existing && existing.achieved) return;
    if (!milestoneCondition(m.id)) return;
    const rp = effectiveMilestoneReward(m);
    state.milestones[m.id] = {
      milestone_id: m.id,
      achieved: true,
      achieved_at_turn: state.turn,
      reward_claimed: true,
    };
    state.research_points += rp;
    newly.push({ milestone: m, rp });
  });
  if (newly.length > 0) saveState();
  return newly;
}

// ── Object colors ─────────────────────────────────────────────────────
const TYPE_COLORS = {
  star: '#ffffaa', planet: '#88aaff', moon: '#cccccc', asteroid: '#999999',
  comet: '#aaddff', observatory: '#4488ff', galaxy: '#6688ff',
  lyman_alpha_blob: '#33ffaa', quasar: '#ffffee', black_hole: '#ff8822',
  magnetar: '#ff44ff', cosmic_web_node: '#ffaa44', void: '#222244',
  cmb_background: '#331818',
};
function typeColor(t) { return TYPE_COLORS[t] || '#666'; }

// ── Rendering ─────────────────────────────────────────────────────────
const logEl = document.getElementById('log-entries');
let logCount = 0;

function addLog(msg, cls = 'log-info') {
  logCount++;
  const el = document.createElement('div');
  el.className = 'log-entry ' + cls;
  const ts = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  const tsSpan = document.createElement('span');
  tsSpan.className = 'ts';
  tsSpan.textContent = ts;
  el.appendChild(tsSpan);
  el.appendChild(document.createTextNode(' ' + msg));
  logEl.prepend(el);
  if (logEl.children.length > 200) logEl.removeChild(logEl.lastChild);
}

function renderHeader() {
  const t = tierMap[state.active_telescope_tier];
  const titleEl = document.getElementById('h-title');
  safeText(titleEl, entityName());
  document.getElementById('h-telescope').innerHTML = 'Telescope: <b>' + esc(t ? t.name : state.active_telescope_tier) + '</b>';
  document.getElementById('h-rp').innerHTML = 'RP: <b>' + state.research_points + '</b>';
  document.getElementById('h-signals').innerHTML = 'Signals: <b>' + state.known_signal_types.length + '</b>';
  document.getElementById('h-discoveries').innerHTML = 'Discovered: <b>' + Object.keys(state.discoveries).length + '/' + SCENE.objects.length + '</b>';
  const mod = getEntityModifier();
  const hb = document.getElementById('h-background');
  if (hb) hb.innerHTML = 'Background: <b>' + esc(mod.name) + '</b> — <span style="color:var(--dim)">' + esc(mod.description) + '</span>';
  const ho = document.getElementById('h-objective');
  if (ho) {
    const active = (state.active_objective_ids || []).map(id => OBJECTIVES.find(o => o.id === id)).filter(Boolean);
    if (active.length) ho.innerHTML = 'Objective: <b>' + esc(active[0].title) + '</b>';
    else ho.innerHTML = '';
  }
}

function displayName(obj) {
  const disc = state.discoveries[obj.id];
  if (!disc) {
    const { confidence } = calcConfidence(obj);
    if (confidence >= 0.25) return 'Unclassified Source';
    return null;
  }
  if (disc.confidence < 0.5) return 'Signal Anomaly (' + obj.type + '?)';
  if (disc.confidence < 0.75) return obj.name + ' (candidate)';
  return obj.name;
}

function renderObjectList() {
  const el = document.getElementById('obj-list');
  el.innerHTML = '';
  const items = [];
  SCENE.objects.forEach(obj => {
    const disc = state.discoveries[obj.id];
    const { confidence } = calcConfidence(obj);
    const visible = confidence >= 0.01 || disc;
    if (!visible) return;
    items.push({ obj, disc, confidence });
  });
  items.sort((a, b) => {
    const ac = a.disc ? a.disc.confidence : 0;
    const bc = b.disc ? b.disc.confidence : 0;
    return bc - ac || a.obj.name.localeCompare(b.obj.name);
  });
  items.forEach(({ obj, disc, confidence }) => {
    const row = document.createElement('div');
    row.className = 'obj-row' + (!disc ? ' undiscovered' : '') + (obj.id === selectedObjId ? ' selected' : '');
    const c = disc ? disc.confidence : confidence;
    const name = displayName(obj) || '???';
    row.innerHTML = `<span class="obj-dot" style="background:${typeColor(obj.type)};box-shadow:0 0 4px ${typeColor(obj.type)}"></span>` +
      `<span class="obj-name">${esc(name)}</span>` +
      `<span class="obj-conf ${confClass(c)}">${Math.round(c * 100)}%</span>`;
    row.onclick = () => { selectedObjId = obj.id; renderObjectList(); renderDetail(); renderSkyMap(); };
    el.appendChild(row);
  });
}

function renderDetail() {
  const el = document.getElementById('tab-detail');
  if (!selectedObjId) { el.innerHTML = '<div style="color:var(--dim);padding:20px;text-align:center">Select an object to inspect</div>'; return; }
  const obj = SCENE.objects.find(o => o.id === selectedObjId);
  if (!obj) { el.innerHTML = ''; return; }
  const disc = state.discoveries[obj.id];
  const { confidence, detected } = calcConfidence(obj);
  const conf = disc ? disc.confidence : confidence;
  const name = displayName(obj) || '???';
  const req = reqMap[obj.type];
  const sigs = allSignals();

  let h = `<div class="detail-name">${esc(name)}</div>`;
  h += `<div class="detail-type">${esc(obj.type)}</div>`;
  if (conf >= 0.5) h += `<div class="detail-desc">${esc(obj.description)}</div>`;
  h += `<div class="detail-row"><span class="detail-key">confidence</span><span class="detail-val ${confClass(conf)}">${esc(confLabel(conf))} (${Math.round(conf * 100)}%)</span></div>`;
  if (conf >= 0.5 && obj.position_mpc) {
    const p = obj.position_mpc;
    h += `<div class="detail-row"><span class="detail-key">position</span><span class="detail-val">(${p.x.toExponential(2)}, ${p.y.toExponential(2)}, ${p.z.toExponential(2)}) cMpc</span></div>`;
  }
  if (disc) {
    h += `<div class="detail-row"><span class="detail-key">RP earned</span><span class="detail-val" style="color:var(--gold)">${disc.research_points_earned}</span></div>`;
    h += `<div class="detail-row"><span class="detail-key">first seen</span><span class="detail-val">${esc(disc.first_detected_tier)}</span></div>`;
  }

  if (req) {
    h += '<div class="detail-section">Required Signals</div>';
    req.required_signal_types.forEach(s => {
      h += `<span class="signal-tag ${sigs.has(s) ? 'signal-have' : 'signal-need'}">${esc(s.replace(/_/g, ' '))}</span>`;
    });
    if (req.optional_signal_types.length) {
      h += '<div class="detail-section">Optional Signals (boost confidence)</div>';
      req.optional_signal_types.forEach(s => {
        h += `<span class="signal-tag ${sigs.has(s) ? 'signal-have' : 'signal-opt'}">${esc(s.replace(/_/g, ' '))}</span>`;
      });
    }
    h += `<div class="detail-section">Notes</div><div style="font-size:11px;color:var(--dim)">${esc(req.notes)}</div>`;
  }

  if (conf >= 0.75 && obj.properties && Object.keys(obj.properties).length) {
    h += '<div class="detail-section">Properties</div>';
    Object.entries(obj.properties).forEach(([k, v]) => {
      h += `<div class="detail-row"><span class="detail-key">${esc(k.replace(/_/g, ' '))}</span><span class="detail-val">${esc(String(v))}</span></div>`;
    });
  }

  if (conf >= 0.75 && obj.relationships && obj.relationships.length) {
    h += '<div class="detail-section">Relationships</div>';
    obj.relationships.forEach(r => {
      h += `<div style="font-size:11px;color:var(--cyan);margin:2px 0;cursor:pointer" onclick="selectedObjId='${esc(r.target_id)}';renderAll()">→ ${esc(r.relation)}: ${esc(r.target_id)}</div>`;
    });
  }

  el.innerHTML = h;
}

function renderTechTree() {
  const el = document.getElementById('tab-tech');
  let h = '';
  TECH_TREE.forEach(tier => {
    const unlocked = state.unlocked_tiers.includes(tier.id);
    const available = !unlocked && tier.prerequisites.every(p => state.unlocked_tiers.includes(p));
    const cost = effectiveTierCost(tier);
    const canAfford = state.research_points >= cost;
    const active = state.active_telescope_tier === tier.id;
    let cls = 'tier-card';
    if (unlocked) cls += ' unlocked';
    else if (available) cls += ' available';
    else cls += ' locked';
    if (tier.speculative) cls += ' speculative';

    h += `<div class="${cls}">`;
    h += `<span class="tier-name">${esc(tier.name)}</span>`;
    if (tier.speculative) h += '<span class="spec-badge">SPECULATIVE</span>';
    if (active) h += '<span style="font-size:9px;color:var(--green);margin-left:6px">● ACTIVE</span>';
    h += `<div class="tier-meta">`;
    if (!unlocked) h += `Cost: ${cost} RP` + (cost !== tier.research_cost ? ` (base ${tier.research_cost})` : '') + ' · ';
    h += `Res: ${tier.resolution_arcsec}" · Sens: ${tier.sensitivity} · Range: ${tier.max_effective_distance_mpc} Mpc`;
    h += `</div>`;
    h += `<div class="tier-signals">`;
    tier.signal_types.forEach(s => {
      h += `<span class="signal-tag signal-have">${esc(s.replace(/_/g, ' '))}</span>`;
    });
    h += '</div>';
    h += `<div style="font-size:10px;color:var(--dim);margin-top:4px">${esc(tier.description)}</div>`;
    if (unlocked && !active) {
      h += `<button class="btn" onclick="state.active_telescope_tier='${esc(tier.id)}';saveState();renderAll();addLog('Switched to ${esc(tier.name)}','log-info')">Set Active</button>`;
    }
    if (available) {
      if (canAfford) {
        h += `<button class="btn" onclick="doUnlock('${esc(tier.id)}')">Unlock (${cost} RP)</button>`;
      } else {
        h += `<button class="btn" disabled>Need ${cost - state.research_points} more RP</button>`;
      }
    }
    h += '</div>';
  });
  el.innerHTML = h;
}

// ── Sky map ───────────────────────────────────────────────────────────
const canvas = document.getElementById('sky-canvas');
const ctx = canvas.getContext('2d');

function renderSkyMap() {
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.parentElement.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  canvas.style.width = rect.width + 'px';
  canvas.style.height = rect.height + 'px';
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

  const W = rect.width, H = rect.height;
  const cx = W / 2, cy = H / 2;
  const maxR = Math.min(cx, cy) - 30;

  ctx.fillStyle = '#030308';
  ctx.fillRect(0, 0, W, H);

  const rng = mulberry32(42);
  for (let i = 0; i < 200; i++) {
    const x = rng() * W, y = rng() * H;
    const b = 0.1 + rng() * 0.3;
    ctx.fillStyle = `rgba(200,210,240,${b})`;
    ctx.fillRect(x, y, 1, 1);
  }

  ctx.strokeStyle = 'rgba(60,70,130,0.15)';
  ctx.lineWidth = 0.5;
  for (let i = 1; i <= 4; i++) {
    ctx.beginPath();
    ctx.arc(cx, cy, maxR * i / 4, 0, Math.PI * 2);
    ctx.stroke();
  }
  ctx.beginPath();
  ctx.moveTo(cx - maxR, cy); ctx.lineTo(cx + maxR, cy);
  ctx.moveTo(cx, cy - maxR); ctx.lineTo(cx, cy + maxR);
  ctx.stroke();

  const isSolarSystem = SCENE.id === 'solar-system';
  const positions = SCENE.objects.map(o => {
    const p = o.position_mpc;
    return { obj: o, dist: Math.sqrt(p.x*p.x + p.y*p.y + p.z*p.z), x: p.x, z: p.z, y: p.y };
  }).filter(p => p.dist > 0 || p.obj.type === 'observatory');

  let scaleR;
  if (isSolarSystem) {
    const maxD = Math.max(...positions.map(p => p.dist), 1e-15);
    scaleR = d => d <= 0 ? 0 : (Math.log10(d / maxD * 1e6 + 1) / Math.log10(1e6 + 1)) * maxR;
  } else {
    const maxD = Math.max(...positions.map(p => p.dist), 1);
    scaleR = d => (d / maxD) * maxR;
  }

  positions.forEach(({ obj, dist, x, z }) => {
    const disc = state.discoveries[obj.id];
    const { confidence } = calcConfidence(obj);
    const visible = confidence >= 0.01 || disc;
    if (!visible && obj.type !== 'observatory') return;

    const r = scaleR(dist);
    const angle = Math.atan2(z, x);
    const px = cx + r * Math.cos(angle);
    const py = cy - r * Math.sin(angle);

    const col = typeColor(obj.type);
    const conf = disc ? disc.confidence : confidence;
    const alpha = conf < 0.25 ? 0.15 : conf < 0.5 ? 0.35 : conf < 0.75 ? 0.6 : 0.9;
    const sz = obj.type === 'star' ? 6 : obj.type === 'observatory' ? 5 : obj.type === 'planet' ? 4 : 3;

    if (conf >= 0.25) {
      const grad = ctx.createRadialGradient(px, py, 0, px, py, sz * 3);
      grad.addColorStop(0, col + '40');
      grad.addColorStop(1, 'transparent');
      ctx.fillStyle = grad;
      ctx.fillRect(px - sz * 3, py - sz * 3, sz * 6, sz * 6);
    }

    ctx.globalAlpha = alpha;
    ctx.fillStyle = col;
    ctx.beginPath();
    ctx.arc(px, py, sz, 0, Math.PI * 2);
    ctx.fill();
    ctx.globalAlpha = 1;

    if (obj.id === selectedObjId) {
      ctx.strokeStyle = '#6680ff';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.arc(px, py, sz + 4, 0, Math.PI * 2);
      ctx.stroke();
    }

    if (conf >= 0.5) {
      ctx.fillStyle = `rgba(200,210,240,${alpha * 0.7})`;
      ctx.font = '9px ' + getComputedStyle(document.body).fontFamily;
      ctx.fillText(obj.name, px + sz + 4, py + 3);
    }
  });

  ctx.fillStyle = 'rgba(100,110,160,0.4)';
  ctx.font = '9px ' + getComputedStyle(document.body).fontFamily;
  ctx.textAlign = 'center';
  ctx.fillText(isSolarSystem ? 'Earth' : 'Observer', cx, cy + maxR + 18);
  ctx.textAlign = 'start';

  canvas.onclick = (e) => {
    const cr = canvas.getBoundingClientRect();
    const mx = e.clientX - cr.left, my = e.clientY - cr.top;
    let closest = null, closestDist = Infinity;
    positions.forEach(({ obj, dist, x, z }) => {
      const disc2 = state.discoveries[obj.id];
      const { confidence: c2 } = calcConfidence(obj);
      if (c2 < 0.01 && !disc2 && obj.type !== 'observatory') return;
      const r = scaleR(dist);
      const angle = Math.atan2(z, x);
      const px = cx + r * Math.cos(angle);
      const py = cy - r * Math.sin(angle);
      const d = Math.sqrt((mx - px) ** 2 + (my - py) ** 2);
      if (d < 20 && d < closestDist) { closest = obj; closestDist = d; }
    });
    if (closest) { selectedObjId = closest.id; renderAll(); }
  };
}

function mulberry32(a) {
  return function() {
    a |= 0; a = a + 0x6D2B79F5 | 0;
    let t = Math.imul(a ^ a >>> 15, 1 | a);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
}

// ── Actions ───────────────────────────────────────────────────────────
function logSurveyEvent(ev) {
  if (!ev) return;
  if (ev.type === 'completed') {
    addLog('Survey complete: ' + ev.survey.name + ' — +' + ev.reward + ' RP', 'log-unlock');
  } else if (ev.type === 'progress') {
    addLog('  ↳ ' + ev.survey.name + ': ' + ev.done + '/' + ev.goal, 'log-info');
  }
}

function logMilestones(ms) {
  ms.forEach(entry => {
    const m = entry.milestone || entry;
    const rp = entry.rp != null ? entry.rp : effectiveMilestoneReward(m);
    const spec = m.speculative ? ' [SPECULATIVE]' : '';
    addLog('Milestone: ' + m.name + spec + ' — +' + rp + ' RP', 'log-unlock');
  });
}

function doObserve() {
  if (!selectedObjId) { addLog('Select an object first.', 'log-info'); return; }
  state.turn = (state.turn || 0) + 1;
  const r = observeObject(selectedObjId);
  if (!r) {
    addLog('No new data from this observation.', 'log-info');
    const ms = evaluateMilestonesJS();
    logMilestones(ms);
  const ob = evaluateObjectivesJS();
  logObjectives(ob);
    saveState();
    renderAll();
    return;
  }
  const tag = r.isNew ? 'log-new' : 'log-upgrade';
  const label = r.isNew ? 'NEW' : 'UPGRADED';
  let msg = `[${label}] ${r.obj.name} (${r.obj.type}) — ${r.label} ${Math.round(r.confidence * 100)}% — +${r.pts} RP`;
  if (r.isFirstOfType) msg = entityName() + ' confirmed first ' + r.obj.type + ': ' + r.obj.name + ' — +' + r.pts + ' RP';
  addLog(msg, tag);
  logSurveyEvent(r.surveyEvent);
  const ms = evaluateMilestonesJS();
  logMilestones(ms);
  const ob = evaluateObjectivesJS();
  logObjectives(ob);
  saveState();
  renderAll();
}

const _SOLAR_TYPES_JS = new Set(['star', 'planet', 'moon', 'asteroid', 'comet']);
function _followupRpJs(t) {
  if (_SOLAR_TYPES_JS.has(t)) return 1;
  const m = { galaxy: 3, quasar: 4, lyman_alpha_blob: 5, black_hole: 4, magnetar: 4, speculative_anomaly: 5 };
  return m[t] || 3;
}
function applyFollowupPass(primaryIds) {
  if (!state.followup_observation_counts) state.followup_observation_counts = {};
  if (!state.last_observation_tier_by_object) state.last_observation_tier_by_object = {};
  let total = 0;
  const mod = getEntityModifier();
  SCENE.objects.forEach(obj => {
    if (primaryIds.has(obj.id)) {
      state.last_observation_tier_by_object[obj.id] = state.active_telescope_tier;
      return;
    }
    const prev = state.discoveries[obj.id];
    if (!prev || prev.confidence < 0.5) return;
    const count = state.followup_observation_counts[obj.id] || 0;
    const tierChanged = state.last_observation_tier_by_object[obj.id] !== state.active_telescope_tier;
    if (prev.confidence >= 0.95 && !tierChanged) return;
    if (count >= 2 && !tierChanged) return;
    const rp = Math.max(1, Math.min(5, Math.round(_followupRpJs(obj.type) * mod.discovery_rp_multiplier)));
    state.followup_observation_counts[obj.id] = count + 1;
    state.last_observation_tier_by_object[obj.id] = state.active_telescope_tier;
    state.research_points += rp;
    prev.research_points_earned = (prev.research_points_earned || 0) + rp;
    total += rp;
    addLog('Follow-up: ' + obj.name + ' — +' + rp + ' RP (diminishing returns)', 'log-info');
  });
  return total;
}
let _lastGuidanceKey = '';
function showGuidanceHints() {
  const hints = [];
  const solar = SCENE.id === 'solar-system';
  const targets = SCENE.objects.filter(o => _SOLAR_TYPES_JS.has(o.type));
  const done = targets.filter(o => state.discoveries[o.id] && state.discoveries[o.id].confidence >= 0.5).length;
  const exhausted = solar && targets.length && done / targets.length >= 0.8;
  const hasSpace = state.unlocked_tiers.includes('space_optical');
  if (exhausted && hasSpace) hints.push('deep_field_ready');
  if (exhausted && !hasSpace) hints.push('need_upgrade');
  if ((state.consecutive_no_rp_turns || 0) >= 3) hints.push('no_rp');
  const key = hints.join(',');
  if (key && key !== _lastGuidanceKey) {
    _lastGuidanceKey = key;
    if (hints.includes('deep_field_ready')) {
      addLog('Guidance: Local sky mostly catalogued — generate scene-001 for deep-field science.', 'log-unlock');
    } else if (hints.includes('need_upgrade')) {
      addLog('Guidance: Upgrade toward space_optical or finish surveys for more RP.', 'log-info');
    } else if (hints.includes('no_rp')) {
      addLog('Guidance: Try Scene 001, a new survey, or follow-up observations on known targets.', 'log-info');
    }
  }
}

function doSurvey() {
  state.turn = (state.turn || 0) + 1;
  const rpBefore = state.research_points;
  const results = observeAll();
  const primaryIds = new Set(results.map(r => r.obj.id));
  const surveyEvents = [];
  if (results.length === 0) {
    addLog(entityName() + ': Survey complete — no new discoveries.', 'log-info');
  } else {
    let totalPts = 0;
    results.forEach(r => {
      totalPts += r.pts;
      const tag = r.isNew ? 'log-new' : 'log-upgrade';
      let msg = r.obj.name + ' — ' + r.label + ' ' + Math.round(r.confidence * 100) + '% — +' + r.pts + ' RP';
      if (r.isFirstOfType) msg = entityName() + ' confirmed first ' + r.obj.type + ': ' + r.obj.name;
      addLog(msg, tag);
      if (r.surveyEvent) surveyEvents.push(r.surveyEvent);
    });
    addLog(entityName() + ' survey complete: ' + results.length + ' objects, +' + totalPts + ' RP total', 'log-info');
  }
  // Emit one survey-progress message per active-survey contribution; only the
  // last 'completed' event matters for log clarity.
  const completed = surveyEvents.find(e => e.type === 'completed');
  if (completed) logSurveyEvent(completed);
  const followupTotal = applyFollowupPass(primaryIds);
  if (typeof state.consecutive_no_rp_turns !== 'number') state.consecutive_no_rp_turns = 0;
  state.consecutive_no_rp_turns = (state.research_points === rpBefore && followupTotal === 0)
    ? state.consecutive_no_rp_turns + 1 : 0;
  const ms = evaluateMilestonesJS();
  logMilestones(ms);
  const ob = evaluateObjectivesJS();
  logObjectives(ob);
  saveState();
  renderAll();
  showGuidanceHints();
}

function doUnlock(tierId) {
  const tier = tierMap[tierId];
  if (!tier) return;
  if (unlockTier(tierId)) {
    addLog(entityName() + ' unlocked: ' + tier.name + (tier.speculative ? ' [SPECULATIVE]' : ''), 'log-unlock');
    const ms = evaluateMilestonesJS();
    logMilestones(ms);
  const ob = evaluateObjectivesJS();
  logObjectives(ob);
    saveState();
    renderAll();
  }
}

function doStartSurvey(surveyId) {
  if (startSurvey(surveyId)) {
    const s = surveyMap[surveyId];
    addLog(entityName() + ' started survey: ' + s.name, 'log-info');
    renderAll();
  }
}

function doClaimSurvey(surveyId) {
  if (claimSurvey(surveyId)) {
    const s = surveyMap[surveyId];
    const cr = effectiveSurveyReward(s);
    addLog('Claimed reward for ' + s.name + ' — +' + cr + ' RP', 'log-unlock');
    renderAll();
  }
}

function doReset() {
  if (!confirm('Reset all progress for ' + entityName() + '? This cannot be undone.')) return;
  localStorage.removeItem(STORAGE_KEY);
  state = JSON.parse(JSON.stringify(INIT_STATE));
  ensureSurveyMilestoneFields();
  ensureObjectiveFields();
  firstDiscoveryCount = 0;
  firstTypesSeen = new Set();
  selectedObjId = null;
  logEl.innerHTML = '';
  addLog('Game state reset.', 'log-info');
  if (needsNaming()) showNaming(); else renderAll();
}

function doExport() {
  const blob = new Blob([JSON.stringify(state, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = 'game-state.json'; a.click();
  URL.revokeObjectURL(url);
  addLog('Game state exported.', 'log-info');
}

// ── Naming modal ──────────────────────────────────────────────────────
const overlay = document.getElementById('naming-overlay');
const nmName = document.getElementById('nm-name');
const nmType = document.getElementById('nm-type');
const nmMotto = document.getElementById('nm-motto');

(function initTypeDropdown() {
  Object.entries(ENTITY_TYPES).forEach(([val, label]) => {
    const opt = document.createElement('option');
    opt.value = val;
    opt.textContent = label;
    nmType.appendChild(opt);
  });
})();

function showNaming() {
  overlay.style.display = 'flex';
  ensureEntity();
  nmName.value = state.research_entity.name === DEFAULT_ENTITY_NAME ? '' : state.research_entity.name;
  nmType.value = state.research_entity.entity_type || 'custom';
  nmMotto.value = state.research_entity.motto || '';
  setTimeout(() => nmName.focus(), 100);
}

function slugify(n) {
  return n.toLowerCase().trim().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'unnamed';
}

document.getElementById('nm-begin').onclick = () => {
  const name = nmName.value.trim() || DEFAULT_ENTITY_NAME;
  const slug = slugify(name);
  ensureEntity();
  state.research_entity.name = name;
  state.research_entity.entity_type = nmType.value;
  state.research_entity.motto = nmMotto.value.trim();
  state.research_entity.id = slug + '-' + slug.length;
  state.research_entity.created_at = new Date().toISOString();
  saveState();
  overlay.style.display = 'none';
  addLog(entityName() + ' has begun formal survey operations.', 'log-info');
  if (state.research_entity.motto) addLog('"' + state.research_entity.motto + '"', 'log-info');
  renderAll();
};

document.getElementById('nm-random').onclick = () => {
  nmName.value = RANDOM_NAMES[Math.floor(Math.random() * RANDOM_NAMES.length)];
};

nmName.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') document.getElementById('nm-begin').click();
});

// ── Tabs ──────────────────────────────────────────────────────────────
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.onclick = () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
  };
});

// ── Surveys / milestones renderers ────────────────────────────────────
function renderSurveys() {
  const el = document.getElementById('tab-surveys');
  let h = '<div style="font-size:10px;color:var(--dim);text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px">Survey Programs</div>';
  SURVEYS.forEach(s => {
    const status = surveyStatus(s);
    const prog = state.survey_progress[s.id];
    const done = prog ? prog.discoveries_completed : 0;
    let cls = 'tier-card';
    if (status === 'completed') cls += ' unlocked';
    else if (status === 'active') cls += ' available';
    else if (status === 'available') cls += '';
    else cls += ' locked';
    if (s.speculative) cls += ' speculative';
    h += `<div class="${cls}">`;
    h += `<span class="tier-name">${esc(s.name)}</span>`;
    if (s.speculative) h += '<span class="spec-badge">SPECULATIVE</span>';
    if (status === 'active') h += '<span style="font-size:9px;color:var(--accent);margin-left:6px">▶ ACTIVE</span>';
    if (status === 'completed') h += '<span style="font-size:9px;color:var(--green);margin-left:6px">✓ COMPLETED</span>';
    const rew = effectiveSurveyReward(s);
    const rewLabel = rew === s.reward_research_points ? `+${rew} RP` : `+${rew} RP (base ${s.reward_research_points})`;
    h += `<div class="tier-meta">Goal: ${done}/${s.completion_goal} · Reward: ${rewLabel}</div>`;
    h += `<div style="font-size:10px;color:var(--dim);margin-top:4px">${esc(s.description)}</div>`;
    if (s.required_tier_ids.length) {
      h += `<div style="font-size:9px;color:var(--dim);margin-top:3px">requires tiers: ${esc(s.required_tier_ids.join(', '))}</div>`;
    }
    if (s.required_signal_types.length) {
      h += `<div style="font-size:9px;color:var(--dim)">requires signals: ${esc(s.required_signal_types.join(', '))}</div>`;
    }
    if (s.flavor) h += `<div style="font-size:10px;font-style:italic;color:var(--dim);margin-top:4px">"${esc(s.flavor)}"</div>`;
    if (status === 'available') {
      h += `<button class="btn" onclick="doStartSurvey('${esc(s.id)}')">Start Survey</button>`;
    }
    if (status === 'completed' && prog && !prog.claimed_reward) {
      const cr = effectiveSurveyReward(s);
      h += `<button class="btn" onclick="doClaimSurvey('${esc(s.id)}')">Claim +${cr} RP</button>`;
    }
    h += '</div>';
  });
  el.innerHTML = h;
}

function renderMilestones() {
  const el = document.getElementById('tab-milestones');
  const achieved = MILESTONES.filter(m => state.milestones[m.id] && state.milestones[m.id].achieved);
  const remaining = MILESTONES.filter(m => !(state.milestones[m.id] && state.milestones[m.id].achieved));
  let h = '';
  h += `<div style="font-size:10px;color:var(--dim);text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px">Achieved (${achieved.length}/${MILESTONES.length})</div>`;
  if (achieved.length === 0) {
    h += '<div style="font-size:11px;color:var(--dim);margin-bottom:10px">No milestones yet — observe something.</div>';
  }
  achieved.forEach(m => {
    const spec = m.speculative ? '<span class="spec-badge">SPECULATIVE</span>' : '';
    const er = effectiveMilestoneReward(m);
    const rl = er === m.reward_research_points ? `+${er} RP` : `+${er} RP (base ${m.reward_research_points})`;
    h += `<div class="tier-card unlocked">`;
    h += `<span class="tier-name" style="color:var(--green)">✓ ${esc(m.name)}</span>${spec}`;
    h += `<div style="font-size:10px;color:var(--dim);margin-top:3px">${esc(m.description)}</div>`;
    h += `<div class="tier-meta">${rl} awarded</div>`;
    h += '</div>';
  });
  h += `<div style="font-size:10px;color:var(--dim);text-transform:uppercase;letter-spacing:0.1em;margin:12px 0 6px">Remaining</div>`;
  remaining.forEach(m => {
    const spec = m.speculative ? '<span class="spec-badge">SPECULATIVE</span>' : '';
    let cls = 'tier-card locked';
    if (m.speculative) cls += ' speculative';
    const er = effectiveMilestoneReward(m);
    const rl = er === m.reward_research_points ? `+${er} RP` : `+${er} RP (base ${m.reward_research_points})`;
    h += `<div class="${cls}">`;
    h += `<span class="tier-name">${esc(m.name)}</span>${spec}`;
    h += `<div style="font-size:10px;color:var(--dim);margin-top:3px">${esc(m.description)}</div>`;
    h += `<div class="tier-meta">Reward: ${rl}</div>`;
    h += '</div>';
  });
  el.innerHTML = h;
}

function renderCampaign() {
  const el = document.getElementById('tab-campaign');
  const camp = state.campaign || { active_scene_id: 'solar-system', scenes: {} };
  const activeId = camp.active_scene_id || 'solar-system';
  const catalogBundle = Array.isArray(SCENE_CATALOG) ? { scenes: SCENE_CATALOG } : SCENE_CATALOG;
  const scenes = catalogBundle.scenes || [];
  const rec = catalogBundle.recommended_next_scene_id;
  let h = '';
  h += `<div style="font-size:10px;color:var(--dim);text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px">Active scene</div>`;
  const activeDef = scenes.find(s => s.id === activeId);
  h += `<div class="tier-card unlocked"><span class="tier-name">${esc(activeDef ? activeDef.name : activeId)}</span>`;
  h += `<div style="font-size:10px;color:var(--dim);margin-top:3px">${esc(activeId)} — viewing ${esc(SCENE.name)}</div>`;
  h += `<div style="font-size:10px;color:var(--muted);margin-top:4px">Switch scenes via CLI; re-export this HTML for another scene file.</div></div>`;
  if (rec && rec !== activeId) {
    const rd = scenes.find(s => s.id === rec);
    h += `<div style="margin-top:10px;font-size:11px;color:var(--amber)">Recommended: ${esc(rd ? rd.name : rec)}</div>`;
    if (catalogBundle.recommended_generate_command) {
      h += `<div style="font-size:10px;color:var(--dim);margin-top:4px;font-family:monospace;word-break:break-all">${esc(catalogBundle.recommended_generate_command)}</div>`;
    }
    if (catalogBundle.recommended_set_scene_command) {
      h += `<div style="font-size:10px;color:var(--dim);margin-top:4px;font-family:monospace;word-break:break-all">${esc(catalogBundle.recommended_set_scene_command)}</div>`;
    }
  }
  h += `<div style="font-size:10px;color:var(--dim);text-transform:uppercase;letter-spacing:0.1em;margin:12px 0 6px">Scenes</div>`;
  scenes.forEach(s => {
    const st = (camp.scenes && camp.scenes[s.id]) || {};
    const unlocked = st.unlocked !== false && s.id === 'solar-system' ? true : !!st.unlocked;
    const cls = unlocked ? 'tier-card unlocked' : 'tier-card locked';
    const mark = s.id === activeId ? ' ★' : '';
    h += `<div class="${cls}">`;
    h += `<span class="tier-name">${unlocked ? '' : '🔒 '}${esc(s.name)}${mark}</span>`;
    h += `<div style="font-size:10px;color:var(--dim);margin-top:3px">${esc(s.teaching_summary || s.description || '')}</div>`;
    if (!unlocked && s.unlock_requirement) {
      h += `<div class="tier-meta">Unlock: ${esc(s.unlock_requirement)}</div>`;
    }
    if (unlocked && s.generate_command) {
      h += `<div class="tier-meta" style="font-family:monospace;font-size:9px;word-break:break-all">${esc(s.generate_command)}</div>`;
    }
    h += '</div>';
  });
  el.innerHTML = h;
}

// ── Wire up ───────────────────────────────────────────────────────────
document.getElementById('btn-observe').onclick = doObserve;
document.getElementById('btn-survey').onclick = doSurvey;
document.getElementById('btn-reset').onclick = doReset;
document.getElementById('btn-export').onclick = doExport;

function transientState(eid) {
  if (!state.transient_events) state.transient_events = {};
  if (!state.transient_events[eid]) {
    state.transient_events[eid] = { event_id: eid, active: false, discovered: false, observed_turns: [], expired: false, reward_claimed: false };
  }
  return state.transient_events[eid];
}

function refreshTransientFlags() {
  const turn = state.turn || 0;
  TRANSIENTS.forEach(defn => {
    const ts = transientState(defn.id);
    const start = defn.start_turn || 1;
    const end = start + (defn.duration_turns || 1);
    ts.active = turn >= start && turn < end;
    ts.expired = turn >= end;
  });
}

function canObserveTransient(defn) {
  refreshTransientFlags();
  if (SCENE.id !== defn.scene_id) return false;
  const ts = transientState(defn.id);
  if (ts.expired || !ts.active || ts.reward_claimed) return false;
  const minTier = defn.minimum_telescope_tier || 'naked_eye';
  const minIdx = (TECH_TREE.find(t => t.id === minTier) || { tier_index: -1 }).tier_index;
  const activeIdx = (TECH_TREE.find(t => t.id === state.active_telescope_tier) || { tier_index: -1 }).tier_index;
  if (!(state.unlocked_tiers || []).includes(minTier) && activeIdx < minIdx) return false;
  const req = defn.required_signal_types || [];
  if (req.length && !req.some(s => (state.known_signal_types || []).includes(s))) return false;
  return true;
}

function observeTransient(defn) {
  if (!canObserveTransient(defn)) return;
  const ts = transientState(defn.id);
  const rp = defn.reward_research_points || 0;
  state.research_points = (state.research_points || 0) + rp;
  ts.discovered = true;
  ts.reward_claimed = true;
  ts.first_observed_turn = ts.first_observed_turn ?? state.turn;
  ts.observed_turns = ts.observed_turns || [];
  ts.observed_turns.push(state.turn);
  const spec = defn.speculative ? ' [SPECULATIVE]' : '';
  addLog(`Transient: ${defn.name}${spec} — +${rp} RP`, 'log-discovery');
  saveState();
  renderAll();
}


function renderObjectives() {
  const el = document.getElementById('tab-objectives');
  if (!el) return;
  let h = '<div class="panel-title">Tutorial Objectives</div>';
  const active = (state.active_objective_ids || []).map(id => OBJECTIVES.find(o => o.id === id)).filter(Boolean);
  if (active.length) {
    const o = active[0];
    h += '<div class="tier-card unlocked"><span class="tier-name">' + esc(o.title) + '</span>';
    h += '<div style="font-size:10px;color:var(--dim);margin-top:3px">' + esc(o.hint || o.description) + '</div>';
    if (o.suggested_command) h += '<div class="tier-meta" style="font-family:monospace;font-size:9px;word-break:break-all">' + esc(o.suggested_command) + '</div>';
    h += '</div>';
  }
  const done = OBJECTIVES.filter(o => state.objectives[o.id] && state.objectives[o.id].status === 'completed');
  if (done.length) {
    h += '<div style="font-size:10px;color:var(--dim);margin-top:10px">Completed</div>';
    done.forEach(o => { h += '<div style="font-size:11px;color:var(--green);margin-top:4px">✓ ' + esc(o.title) + ' (+' + o.reward_research_points + ' RP)</div>'; });
  }
  el.innerHTML = h;
}

function renderTransients() {
  const el = document.getElementById('tab-transients');
  if (!el) return;
  refreshTransientFlags();
  let h = '<div class="panel-title">Transient Events</div>';
  const sceneEvents = TRANSIENTS.filter(d => d.scene_id === SCENE.id);
  if (!sceneEvents.length) {
    el.innerHTML = h + '<p class="dim">No catalog events for this scene.</p>';
    return;
  }
  sceneEvents.forEach(defn => {
    const ts = transientState(defn.id);
    let status = 'upcoming';
    if (ts.expired) status = ts.reward_claimed ? 'expired (observed)' : 'expired';
    else if (ts.active) status = ts.reward_claimed ? 'active (done)' : 'active';
    const spec = defn.speculative ? ' <span class="spec">SPECULATIVE</span>' : '';
    h += `<div class="card"><strong>${defn.name}</strong>${spec}<br>`;
    h += `<span class="dim">${status} · turns ${defn.start_turn}–${defn.start_turn + defn.duration_turns - 1} · +${defn.reward_research_points} RP</span><br>`;
    h += `<span class="dim">${defn.description}</span>`;
    if (canObserveTransient(defn)) {
      h += `<br><button class="btn-small" onclick="observeTransient(TRANSIENTS.find(x=>x.id==='${defn.id}'))">Observe Event</button>`;
    }
    h += '</div>';
  });
  el.innerHTML = h;
}

function renderAll() {
  renderHeader();
  renderObjectList();
  renderDetail();
  renderTechTree();
  renderSurveys();
  renderMilestones();
  renderCampaign();
  renderTransients();
  renderObjectives();
  renderSkyMap();
  showGuidanceHints();
}

window.addEventListener('resize', renderSkyMap);

ensureEntity();
ensureSurveyMilestoneFields();
  ensureObjectiveFields();
if (needsNaming()) {
  showNaming();
} else {
  // Re-evaluate milestones on load — handles named_entity for state imported via CLI
  const ms = evaluateMilestonesJS();
  renderAll();
  addLog(entityName() + ' observatory console initialized.', 'log-info');
  logMilestones(ms);
}
</script>
</body>
</html>"""
