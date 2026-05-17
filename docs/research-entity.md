# Research Entity

## What is a Research Entity?

A Research Entity is the player's identity in the telescope game. Rather than being an anonymous observer, the player names and represents a research organization — an observatory, institute, sky cult, or whatever they choose.

The entity name appears in:
- Game state JSON
- CLI status and observe output
- Discovery reports
- Telescope UI header and discovery log

## Entity types

| Value | Label |
|---|---|
| `backyard_observatory` | Backyard Observatory |
| `university_lab` | University Lab |
| `national_observatory` | National Observatory |
| `private_institute` | Private Institute |
| `orbital_consortium` | Orbital Consortium |
| `ai_research_bureau` | AI Research Bureau |
| `citizen_science_network` | Citizen Science Network |
| `occult_sky_society` | Occult Sky Society |
| `corporate_research_division` | Corporate Research Division |
| `custom` | Custom |

Entity type selects a **small mechanical modifier** (discovery RP, tier costs, survey/milestone payouts, optional confidence nudge). Effects are intentionally subtle — see [Entity backgrounds](entity-backgrounds.md).

## Naming from CLI

```bash
uv run universe game init \
  --name "Hydrogen Ghost Institute" \
  --entity-type private_institute \
  --motto "Listening for the old light." \
  --out data/generated/game-state.json
```

If `--name` is omitted, the entity is created as "Unnamed Research Entity".

## Naming from the Telescope UI

When the telescope UI loads with no entity name (or "Unnamed Research Entity"), a naming modal appears asking the player to:

1. Enter a Research Entity Name
2. Choose an Entity Type from a dropdown
3. Optionally enter a Motto
4. Click "Begin Observing" to start, or "Random Name" for inspiration

Random names are drawn from a curated list of fun research organization names.

## Example names

- Hydrogen Ghost Institute
- The Bureau of Unreasonable Telescopes
- Backyard Event Horizon Project
- Appalachian Deep Field Survey
- Cosmic Waffle Research Cooperative
- The Last Photon Club
- Dark Matter Complaint Department
- Sempervent Observatory
- The Gravitational Eavesdropping Office
- Lyman-Alpha Breakfast Society

## Where identity appears

- **CLI `game status`:** Entity name, type, motto, turn, survey/milestone counts
- **CLI `game observe`:** Entity name used in discovery, survey, and milestone messages
- **CLI `game surveys` / `game milestones`:** Section headers carry the entity name
- **CLI `game report`:** Entity name, type, and motto in report header; surveys and milestones included as sections
- **Telescope UI header:** Entity name replaces generic "Observatory Console"
- **Telescope UI discovery log:** Entity name used for first-of-type discoveries, survey starts, milestone awards, and upgrade messages
- **Exported game state JSON:** `research_entity` field with all entity data
- **Milestone:** Naming the entity (anything other than the default) triggers the `named_entity` Founding Charter milestone (+5 RP)

## Backward compatibility

Game state JSON files created before the entity feature will load correctly. Missing `research_entity` fields default to:

```json
{
  "id": "",
  "name": "Unnamed Research Entity",
  "entity_type": "custom",
  "motto": ""
}
```

The telescope UI will show the naming modal in this case.

## Current limitations

- Entity type has no mechanical effect
- No avatar or logo
- No multiplayer entity interactions
- Names are not validated for uniqueness

## Future possibilities

Entity type could eventually affect gameplay:

- University lab: cheaper science-tier upgrades
- Backyard observatory: cheaper early optical upgrades
- AI research bureau: better late-game signal classification
- Citizen science network: faster survey speed
- Occult sky society: flavor only (unless speculative mechanics exist)

These bonuses are not implemented. The entity is currently identity and flavor only.
