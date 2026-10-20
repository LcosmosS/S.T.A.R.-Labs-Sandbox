"""Assert the comparator report, which does not itself exit nonzero on differences."""
import json
from pathlib import Path
import sys
r = json.loads(Path(sys.argv[1]).read_text())
assert r['rows'] == [31502, 31502]
for key in ('field_metadata_equal', 'row_order_equal', 'typed_ordered_rows_equal', 'nulls_equal'):
    assert r[key] is True, key
for key in ('keyed_row_differences', 'ordered_row_differences'):
    assert r[key] == 0, key
for side in ('frozen', 'live'):
    assert r[side + '_typed_sha256'] == '4019ecb6dbe8dc8378388837fa26c4dc8d804bd3738955da6b6287636adbcdcf'
    assert r[side + '_cell_lexical_sha256'] == 'bb40a7227805c7a5bb4896cfcbb4a23e13497e2606da6112bdfd18f7bf1c82d3'
assert r['input_frozen_sha256'] == '654217f9b3414856c1a8b09071c81eb834a0b0fbc6ec3aea9777e01fdaea1079'
assert r['input_live_sha256'] == '008502caa196f15883f199dfdb8979cfb91f20b087fb63235cd5d26fecc5a4f2'
assert r['metadata_nodes_differ'] == 2
assert [d['position'] for d in r['first_metadata_differences']] == [1, 3]
assert r['nulls_frozen'] == r['nulls_live'] == {'DEO:empty': 344, 'Name:empty': 21114, 'RAO:empty': 344}
print('PASS: 31502 rows, 25 FIELD descriptions (comparator enforced), unique nonempty AGCs, AGC order, nulls, typed and lexical digests; exactly two XML metadata differences')
