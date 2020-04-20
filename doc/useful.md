Useful Resources:
* Latest Blender API: https://docs.blender.org/api/current/
* https://docs.blender.org/api/current/info_tips_and_tricks.html

#### Interactive debugging

Paste this into your code to drop into an interactive Python interpreter in this line:
```python
__import__('code').interact(local=dict(globals(), **locals()))
```

#### Change property without triggering update

If you want to edit a Blender property without triggering it's update function, 
access it like in this example:
```python
class Test:
    def update_a(self, context):
        # Wrong, would cause endless recursion
        # self.b = str(self.a)
        # Correct, does not trigger b's update method
        self["b"] = str(self.a)
        
    def update_b(self, context):
        self["a"] = int(self.b)

    a: IntProperty(update=update_a)
    b: StringProperty(update=update_b)
```

#### Creating a hidden datablock

Datablocks wich have a name starting with "." (dot) are hidden in UI dropdowns/menus by default, 
similar to hidden files on Linux. The user can still type in a dot in the search field to see all 
the hidden datablocks.

The VRay addon uses this to create hidden helper textures, for example to use their colorramp in a custom node 
(as a workaround to the fact that addons can't create colorramps).

#### Subscribe to a Blender-defined property

It is possible to attach a listener function to an existing property via `bpy.msgbus`:
* https://devtalk.blender.org/t/addon-development-question-attaching-callback-to-buttons/8677/2
* https://developer.blender.org/P563
