# Generate Crazy Image

Generate absurd, funny images with unexpected surreal elements using a two-step pipeline that first imagines a creative scene concept, then renders it as an image.

## Prerequisites

Before running this example, ensure you have set up your environment. See the [Clone and Install](../../../../README.md#1-clone-and-install) section in the main README.

## Run the pipeline

```bash
pipelex run bundle examples/b_basics/generate_visuals/gen_image/
```

## Flowchart

```mermaid
flowchart TD

    %% Pipe and stuff nodes within controller subgraph
    subgraph sg_n_290fc6ca86["generate_crazy_image"]
        n_77170afd7b["imagine_scene"]
        s_516cfa5e49(["image_prompt<br/>ImagePrompt"]):::stuff
        n_90e8600fb0["render_image"]
        s_4527283183(["crazy_image<br/>Image"]):::stuff
    end

    %% Data flow edges: producer -> stuff -> consumer
    n_77170afd7b --> s_516cfa5e49
    n_90e8600fb0 --> s_4527283183
    s_516cfa5e49 --> n_90e8600fb0

    %% Style definitions
    classDef failed fill:#ffcccc,stroke:#cc0000
    classDef stuff fill:#fff3e6,stroke:#cc6600,stroke-width:2px
    classDef controller fill:#e6f3ff,stroke:#0066cc

    %% Subgraph depth-based coloring
    style sg_n_290fc6ca86 fill:#e6f3ff
```

## How it works

1. **imagine_scene**: A `PipeLLM` that generates a creative, absurd image concept combining unexpected elements in surreal ways (e.g., flying spaghetti monsters, penguins in business suits at a disco, or a T-Rex doing yoga on the moon)

2. **render_image**: A `PipeImgGen` that takes the image prompt and generates the actual image

## Go further

You can go further by generating the python structures and runner code out of this bundle:

```bash
pipelex build runner bundle examples/b_basics/generate_visuals/gen_image/bundle.mthds
```

This will create a new file `examples/b_basics/generate_visuals/gen_image/run_crazy_image_generation.py` and a `structures` directory containing the python structures.
