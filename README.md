# MDD Reader Node
### Deformer plugin for Maya

#### Usage

1. Copy file to `MAYA_PLUG_IN_PATH`
2. Load mplugin in Plugin Manager
3. Select geometry
4. Execute:

```python
from maya import cmds
cmds.deformer(type='mddReader')
```

