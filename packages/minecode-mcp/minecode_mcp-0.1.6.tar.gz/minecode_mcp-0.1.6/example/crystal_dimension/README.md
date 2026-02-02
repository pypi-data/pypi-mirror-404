# Crystal Dimension Datapack

A custom Minecraft datapack featuring **The Crystal Void** - a unique dimension filled with crystal formations, rare ores, and mysterious creatures.

## Installation

1. Copy the `crystal_dimension` folder into your Minecraft world's `datapacks` folder
2. Run `/reload` in-game or restart the world
3. You should see the message: `[Crystal Dimension] Datapack loaded!`

## Features

### Custom Dimension: The Crystal Void
- Unique terrain with amethyst and crystal formations
- Custom sky and fog colors (purple/cyan theme)
- No rain or precipitation
- Special ambient lighting effects

### Custom Worldgen Features
- **Crystal Diamond Ore** - Large veins of diamond blocks
- **Crystal Emerald Ore** - Rich emerald deposits
- **Crystal Spikes** - Towering amethyst block formations
- **Amethyst Clusters** - Decorative cluster patches

### Mob Spawns
- **Allays** - Friendly crystal creatures
- **Phantoms** - Night hunters of the void
- **Endermen** - Mysterious wanderers

## Commands

| Command | Description |
|---------|-------------|
| `/function crystal:help` | Display all available commands |
| `/function crystal:teleport` | Teleport to The Crystal Void |
| `/function crystal:return` | Return to the Overworld |
| `/function crystal:give_kit` | Receive the Crystal Explorer kit |
| `/function crystal:spawn_boss` | Summon the Crystal Guardian boss |
| `/function crystal:build_tower` | Build a decorative Crystal Tower |

## Tips

- When entering The Crystal Void, you'll automatically receive night vision
- The Crystal Guardian boss has 500 HP and deals 25 damage - be prepared!
- Use the Explorer kit's elytra and fireworks to navigate the dimension
- Mine budding amethyst blocks from the Crystal Towers to farm amethyst shards

## Pack Information

- **Pack Format:** 94 (Minecraft 1.21.11)
- **Namespace:** `crystal`
- **Author:** Generated with MineCode

## File Structure

```
crystal_dimension/
├── pack.mcmeta
└── data/
    ├── crystal/
    │   ├── dimension/
    │   │   └── crystal_void.json
    │   ├── dimension_type/
    │   │   └── crystal_type.json
    │   ├── function/
    │   │   ├── load.mcfunction
    │   │   ├── tick.mcfunction
    │   │   ├── teleport.mcfunction
    │   │   ├── return.mcfunction
    │   │   ├── give_kit.mcfunction
    │   │   ├── spawn_boss.mcfunction
    │   │   ├── build_tower.mcfunction
    │   │   └── help.mcfunction
    │   └── worldgen/
    │       ├── biome/
    │       │   └── crystal_plains.json
    │       ├── configured_feature/
    │       │   ├── ore_crystal_diamond.json
    │       │   ├── ore_crystal_emerald.json
    │       │   ├── crystal_spikes.json
    │       │   └── amethyst_clusters.json
    │       ├── noise_settings/
    │       │   └── crystal_noise.json
    │       └── placed_feature/
    │           ├── ore_crystal_diamond.json
    │           ├── ore_crystal_emerald.json
    │           ├── crystal_spikes.json
    │           └── amethyst_clusters.json
    └── minecraft/
        └── tags/
            └── function/
                ├── load.json
                └── tick.json
```

## License

Free to use and modify. Created as an example for MineCode MCP tools.
