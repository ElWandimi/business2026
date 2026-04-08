import os
from pathlib import Path

print("Current working directory:", os.getcwd())
print("Home directory:", Path.home())

# Test writing to current directory
test_file = Path("test_write.txt")
try:
    test_file.write_text("test")
    print(f"✅ Can write to current directory: {test_file.absolute()}")
    test_file.unlink()
except Exception as e:
    print(f"❌ Cannot write to current directory: {e}")

# Test writing to instance directory
instance_dir = Path("instance")
instance_dir.mkdir(exist_ok=True)
test_file = instance_dir / "test_write.txt"
try:
    test_file.write_text("test")
    print(f"✅ Can write to instance directory: {test_file.absolute()}")
    test_file.unlink()
except Exception as e:
    print(f"❌ Cannot write to instance directory: {e}")

# Test writing to home directory
test_file = Path.home() / "test_write.txt"
try:
    test_file.write_text("test")
    print(f"✅ Can write to home directory: {test_file.absolute()}")
    test_file.unlink()
except Exception as e:
    print(f"❌ Cannot write to home directory: {e}")

print("\nChecking directory permissions:")
print(f"Instance directory exists: {instance_dir.exists()}")
if instance_dir.exists():
    print(f"Instance directory permissions: {oct(os.stat(instance_dir).st_mode)[-3:]}")
    print(f"Instance directory owner: {os.stat(instance_dir).st_uid}")
    print(f"Can list instance directory: {os.access(instance_dir, os.R_OK)}")
    print(f"Can write to instance directory: {os.access(instance_dir, os.W_OK)}")
