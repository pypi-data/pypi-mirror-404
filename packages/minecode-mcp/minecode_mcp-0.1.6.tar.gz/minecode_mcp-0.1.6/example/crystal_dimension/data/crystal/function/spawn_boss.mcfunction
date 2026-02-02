# Spawn Crystal Guardian (custom boss mob)
# Summons a powerful guardian at the player's location

summon minecraft:warden ~ ~ ~ {CustomName:'{"text":"Crystal Guardian","color":"light_purple","bold":true}',CustomNameVisible:1b,Glowing:1b,Attributes:[{Name:"generic.max_health",Base:500},{Name:"generic.attack_damage",Base:25}],ActiveEffects:[{Id:10,Duration:999999,Amplifier:1,ShowParticles:0b}],HandItems:[{id:"minecraft:amethyst_shard",Count:1b},{}]}

title @a[distance=..50] title {"text":"CRYSTAL GUARDIAN","color":"dark_purple","bold":true}
title @a[distance=..50] subtitle {"text":"has awakened!","color":"red"}
playsound minecraft:entity.warden.emerge hostile @a[distance=..50] ~ ~ ~ 2 0.5
effect give @a[distance=..20] darkness 5 0
