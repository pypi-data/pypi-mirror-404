# Teleport player back to Overworld
execute in minecraft:overworld run tp @s ~ 100 ~
title @s title {"text":"Overworld","color":"green","bold":true}
title @s subtitle {"text":"You have returned","color":"yellow"}
playsound minecraft:entity.enderman.teleport master @s ~ ~ ~ 1 1
