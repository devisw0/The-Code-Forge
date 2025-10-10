import autogen
import importlib.metadata as im

print("module file:", autogen.__file__)
print("__version__ attr:", getattr(autogen, "__version__", "n/a"))

# Map import name -> distribution(s)
pkg2dist = im.packages_distributions()
dists = pkg2dist.get("autogen", [])
print("distributions that provide 'autogen':", dists)

for d in dists:
    print("\n=== DIST:", d, "===")
    print("version:", im.version(d))
    meta = im.metadata(d)
    print("name:", meta.get("Name"))
    print("home-page:", meta.get("Home-page"))
    print("summary:", meta.get("Summary"))
