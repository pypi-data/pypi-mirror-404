# Give player a Crystal Explorer kit
# Includes tools, armor, and supplies for exploring the Crystal Void

give @s minecraft:diamond_pickaxe{Enchantments:[{id:"fortune",lvl:3},{id:"efficiency",lvl:5},{id:"unbreaking",lvl:3}]} 1
give @s minecraft:netherite_sword{Enchantments:[{id:"sharpness",lvl:5},{id:"looting",lvl:3}]} 1
give @s minecraft:elytra 1
give @s minecraft:firework_rocket{Fireworks:{Flight:3}} 64
give @s minecraft:golden_apple 16
give @s minecraft:ender_pearl 16
give @s minecraft:amethyst_shard 64
give @s minecraft:spyglass 1
give @s minecraft:torch 64

tellraw @s {"text":"[Crystal Dimension] You received the Crystal Explorer kit!","color":"gold"}
playsound minecraft:entity.player.levelup master @s ~ ~ ~ 1 1
