
## Dag
```mermaid
flowchart TD
	node1["compute_lambdax@0"]
	node2["compute_lambdax@1"]
	node3["compute_lambdax@2"]
	node4["fetch_reference_data"]
	node5["method_output@0"]
	node6["method_output@1"]
	node7["method_output@2"]
	node4-->node1
	node4-->node2
	node4-->node3
	node5-->node1
	node6-->node2
	node7-->node3
```

## Dev (editable) Install
- clone repo:
`git clone https://github.com/quentinf00/my_ocb.git`
`cd my_ocb`
- install env:
`mamba create -n q_ocb`
`mamba env update -f env.yaml`
- install modules:
```
pip install -q -e modules/qf_interp_grid_on_track
pip install -q -e modules/ssh_tracks_loading
pip install -q -e modules/alongtrack_lambdax
```
- install pipeline:
```
pip install -q --no-deps -e pipelines/qf_alongtrack_lambdax_from_map
```


- run dag:
```
dvc --cd datachallenges/dc_ose_2021 repro
```
generate `stage_configs.yaml`
`qf_alongtrack_lambdax_from_map --cfg job  > datachallenges/dc_ose_2021/stage_configs.yaml`

Repro:
`dvc --cd datachallenges/dc_ose_2021 --verbose repro`
