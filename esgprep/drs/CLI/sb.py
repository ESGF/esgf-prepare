from datetime import datetime
from pathlib import Path

from esgprep.drs.make import DrsProcessor

possible_cmd = {"todo": "todo", "list": "list", "tree": "tree", "upgrade": "upgrade"}
cmd = possible_cmd["todo"]

test_data_dir = Path(
    "/home/ltroussellier/Bureau/dev/esgf-prepare/esgprep/tests/test_data"
)

root_dir = test_data_dir / "sb_root"

processor = DrsProcessor(root_dir=root_dir, mode="link", version=str(datetime.now()))

incoming_dir = test_data_dir / "incoming"
nc_files = list(incoming_dir.glob("**/*.nc"))

results = []
for file_path in nc_files:
    result = processor.process_file(file_path)
    results.append(result)

# Collect all operations
operations = []
for result in results:
    operations.extend(result.operations)


# Execute operations
success = processor.execute_operations(operations)
