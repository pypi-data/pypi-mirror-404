# Crystal Dimension Datapack - Tick Function
# Runs every game tick (optional effects)

# Give night vision to players in the crystal dimension for better visibility
execute as @a[nbt={Dimension:"crystal:crystal_void"}] run effect give @s night_vision 13 0 true
