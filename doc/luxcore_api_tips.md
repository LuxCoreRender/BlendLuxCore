When one property of a key is set, all other (previously defined) properties of the key will be deleted.
Example:
Let's say we have set the following properties:
```
props.Set(pyluxcore.Property("scene.materials.test.type", "matte"))
props.Set(pyluxcore.Property("scene.materials.test.kd", [0.7, 0.7, 0.7]))
```
Now we want to set the material color to red. If we try the following, LuxCore will complain:
```
props.Set(pyluxcore.Property("scene.materials.test.kd", [0.8, 0, 0]))
```
This is because the line `"scene.materials.test.type", "matte"` will be deleted and the material definition is missing the material type information.
You have to explicitly set lines you want to keep, even if they have not changed.