# Generate Synthetic Data

Generate synthetic student profile data based on a schema description.

## Run the pipeline

```bash
pipelex run examples/c_advanced/gen_synthetic_data/bundle.plx -i examples/c_advanced/gen_synthetic_data/inputs.json
```

## Flowchart

![Flowchart](flowchart.png)

## Expected output

![Expected output](expected_output.png)


## Go further

You can go further by generating the python structures and runner code out of this bundle in order to add validation functions to the python BaseModel.

```bash
pipelex build runner examples/c_advanced/gen_synthetic_data/bundle.plx
```

This will create a new file `examples/c_advanced/gen_synthetic_data/run_gen_synthetic_data.py` and a `structures` directory containing the python structures.
