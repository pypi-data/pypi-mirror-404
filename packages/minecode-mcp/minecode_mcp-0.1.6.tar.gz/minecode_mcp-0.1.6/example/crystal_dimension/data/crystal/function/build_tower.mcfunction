# Create a Crystal Structure at current position
# Builds a decorative amethyst tower

fill ~ ~ ~ ~2 ~10 ~2 minecraft:amethyst_block hollow
setblock ~1 ~11 ~1 minecraft:amethyst_cluster[facing=up]
setblock ~1 ~11 ~ minecraft:amethyst_cluster[facing=up]
setblock ~ ~11 ~1 minecraft:amethyst_cluster[facing=up]
setblock ~2 ~11 ~1 minecraft:amethyst_cluster[facing=up]
setblock ~1 ~11 ~2 minecraft:amethyst_cluster[facing=up]

setblock ~1 ~5 ~-1 minecraft:amethyst_cluster[facing=south]
setblock ~1 ~5 ~3 minecraft:amethyst_cluster[facing=north]
setblock ~-1 ~5 ~1 minecraft:amethyst_cluster[facing=east]
setblock ~3 ~5 ~1 minecraft:amethyst_cluster[facing=west]

fill ~1 ~ ~1 ~1 ~10 ~1 minecraft:budding_amethyst

setblock ~1 ~12 ~1 minecraft:beacon
fill ~ ~13 ~ ~2 ~13 ~2 minecraft:tinted_glass
fill ~1 ~-1 ~1 ~1 ~-5 ~1 minecraft:iron_block

tellraw @s {"text":"[Crystal Dimension] Crystal Tower created!","color":"light_purple"}
playsound minecraft:block.beacon.activate master @s ~ ~ ~ 1 1
