### Apply material to face of part
- [ ] Edit face uv's depending on if its a decal or texture.
- [ ] While face is selected assign the material to it.

### Check if part contains mesh.
- [ ] Only care about the first mesh inside of the part.
  - [ ] Download mesh (asset).
  - [ ] If mesh uses texture
    - [ ] Download texture.
    - [ ] Apply texture to the mesh.

### Group stuff depending on if they are inside models.
- [ ] Group support for fbx does not exist, but with blender we could create either collections or join parts.
    #### Joining objects would be better for performance. Maybe join collections? Should be alright since you'd be able to move them in blender then export the scene to unity.

### Exporting optimizations for game engines.
- [ ] Join objects based on same material.
    #### You won't be able to interact with the scene anymore, moving objects etc.
    #### Good for draw calls & performance.

### Check if part uses transparency.
- [ ] If true change alpha on the material so its roughly the same as ingame.