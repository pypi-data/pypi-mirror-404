# Teleport player to Crystal Void dimension
# Creates a safe platform at spawn

execute in crystal:crystal_void run setblock 0 64 0 minecraft:amethyst_block
execute in crystal:crystal_void run setblock 1 64 0 minecraft:amethyst_block
execute in crystal:crystal_void run setblock -1 64 0 minecraft:amethyst_block
execute in crystal:crystal_void run setblock 0 64 1 minecraft:amethyst_block
execute in crystal:crystal_void run setblock 0 64 -1 minecraft:amethyst_block
execute in crystal:crystal_void run setblock 1 64 1 minecraft:amethyst_block
execute in crystal:crystal_void run setblock 1 64 -1 minecraft:amethyst_block
execute in crystal:crystal_void run setblock -1 64 1 minecraft:amethyst_block
execute in crystal:crystal_void run setblock -1 64 -1 minecraft:amethyst_block

execute in crystal:crystal_void run tp @s 0 65 0
title @s title {"text":"Crystal Void","color":"light_purple","bold":true}
title @s subtitle {"text":"Welcome to the dimension of crystals","color":"aqua"}
playsound minecraft:block.amethyst_block.chime master @s ~ ~ ~ 1 0.5
