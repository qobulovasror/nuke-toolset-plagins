<h1 align="center">
  <br>
  <a href="https://www.foundry.com/products/nuke-family/nuke"><img src="https://github.com/user-attachments/assets/7e658816-d194-460b-8ae4-c37c75b03ab7" alt="NukeX" width="200"></a>
  <br>
  Nuke Toolset & Plugins
  <br>
</h1>

<h4 align="center">A curated collection of gizmos, plugins, hotkeys, custom nodes and workflow tools for The Foundry's Nuke / NukeX.</h4>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-whats-inside">What's Inside</a> •
  <a href="#-hotkeys">Hotkeys</a> •
  <a href="#-custom-tools">Custom Tools</a> •
  <a href="#-installation">Installation</a> •
  <a href="#-compatibility">Compatibility</a> •
  <a href="#-license">License</a>
</p>

![Screen-Recording-2025-02-04-101747](https://github.com/user-attachments/assets/037030c1-18fa-48d5-a707-54b077ebd4ba)

---

## ✨ Features

- **One-shot install** — drop the folder into `.nuke` and everything wires itself up.
- **Cross-platform** — `init.py` resolves paths for Windows, macOS and Linux.
- **Curated menus** — every external plugin is grouped under a single `AllAddedTools` menu so the toolbar stays clean.
- **W_hotbox v2.0** — Wouter Gilsing's radial hotbox is pre-configured with per-node action sets.
- **Custom workflow shortcuts** — ready-made node chains, FPS auto-sync from Read metadata, and an extended hotkey set.
- **3rd-party integration** — launch external tools like **XMem2** straight from the Node Graph.

---

## 📦 What's Inside

All third-party gizmo packs live under `AllAddedTools/` and are surfaced inside a single Nuke menu called **AllAddedTools**.

### 🎨 Pixelfudger 3.3 *(Dec 2024)*
Xavier Bourque's full gizmo pack — [pixelfudger.com](https://pixelfudger.com)

`PxF_AreaLight`, `PxF_Bandpass`, `PxF_ChromaBlur`, `PxF_DeepDefocus`, `PxF_DeepFade`, `PxF_DeepMask`, `PxF_DeepResample`, `PxF_Distort`, `PxF_EnvLight`, `PxF_Erode`, `PxF_Filler`, `PxF_GeoLight`, `PxF_Grain`, `PxF_HueSat`, `PxF_IDefocus`, `PxF_KillSpill`, `PxF_Line`, `PxF_MergeWrap`, `PxF_Nukebench`, `PxF_RingLight`, `PxF_ScreenClean`, `PxF_SmokeBox`, `PxF_Smoother`, `PxF_TimeMerge`, `PxF_TubeLight`, `PxF_VectorEdgeBlur`, `PxF_ZDefocus`

### 🧰 Nuke Survival Toolkit *(v2.1.1)*
Tony Lyons' portable toolbar — [GitHub](https://github.com/CreativeLyons/NukeSurvivalToolkit_publicRelease) • [Docs](https://docs.google.com/document/d/1eyh2JIecaphItZeq0uuGxlqoASuXNQy1leJGqFI-EeU/edit)

### 🥭 MangoSuite *(by Johannes Kretschmer)*
A complete compositing helper kit (≈30 nodes): antialias, alpha utilities, lens breathing/filter, edge matte, fine keyer, gridmaker, lightwrap mask, multi-blur, vector blur, rolling shutter, slate overlay, turbulence, vignette, Z-fix, and more.

### 🎯 KeenTools *(v2024.3.0)*
`GeoTracker`, `FaceTracker`, `FaceBuilder`, `PinTool`, `FacialExpressions`, `TextureBuilder`, `ReadRiggedGeo`, `TransformRiggedGeo`, plus a `Blendshapes` submenu (`JoinBlendshapes`, `MixBlendshapes`, `FACS`). Automatically falls back to a friendly warning if the Nuke version / OS doesn't match.

### 🎨 V!ctor Toolkit
`V_CheckMatte`, `V_IdBuilder`, `V_IdFilter`, `V_IdPackage`, `V_ColorRenditionChart`, `V_ColorTracker`, `V_CompareView`, `V_EdgeMatte`, `V_Slate`.

### 🎨 Secondary Colour Tools
`secondaryColour2`, `secondaryMattes`, `vibrancy`.

### 🧱 MyTools (Custom Gizmos)
A curated tree of community gizmos organized by purpose: `3d`, `chroma`, `color`, `edge`, `fx`, `glow`, `grain`, `id and matte`, `info`, `key`, `lens`, `mask`, `matchBW`, `rais`, `relight`, `spill`, `Stereo`, `TX_`, `vel`, `volume`, `z`, `Others`. Top-level extras: `Auto_cleanplate`, `ColorDilate`, `MagicMerge`, `Wipe`.

### 💡 Elias
`VrayPasses`, `RGBToAlpha`, `AutoRimLight` + `Relight` submenu (`Lighting`, `Mask_3D`, `Relighting`, `RelightingRig`, `Fresnel`, `AA`) and a `Shadow` submenu (`shadow3D`, `RenderBoth`).

### ➗ Expression Node Collection *(v1.5)*
Andrea Geremia's expression-driven nodes organized into `3D`, `Alpha`, `Conversions`, `Creations`, `Keying_Despill`, `Merge`, `Pixel`, `Transform`.

### 🌊 Frequency Separation
`CH_FrequencySeparation` — single-node frequency split workflow.

### 🛠️ NukeToolSet
A general-purpose gizmo/script collection with broad Nuke version support (Nuke 11–16).

### 🌐 NukeShared *(v2.6 — bundled, optional)*
Max van Leeuwen's shared-repository system (commented out in `init.py` by default — enable it if you want a pipeline-style shared plugin folder).

---

## 🚀 3rd Party Software Integration

The `Run3PartSoftware/` folder wires external tools into the Node Graph under a `3PartyTools` menu.

- **XMEM++** — drops an `XMem_Launcher` NoOp node with a button that runs [XMem2](https://github.com/hkchengrex/XMem) on the connected `Read` clip and writes results back to disk.

---

## ⚡ W_hotbox *(v2.0 — March 2025)*

The full [W_hotbox](https://www.nukepedia.com/python/ui/w_hotbox) by Wouter Gilsing is pre-installed with action sets prepared for the most common nodes:

`Camera2`, `Card2`, `Cube`, `ReadGeo2`, `Sphere`, `ChannelMerge`, `CheckerBoard2`, `Clamp`, `Colorspace`, `Constant`, `Copy`, `Crop`, `CurveTool`, `Defocus`, `DespillMadness`, `Difference`, `Dissolve`, `Dot`, `Emboss`, `Expression`, `FilterErode`, `FrameHold`, `Grade`, `IBKColourV3`, `IBKGizmoV3`, `Keymix`, `Merge2`, `MergeMat`, `Mirror2`, `Multiply`, `OCIOColorSpace`, `PointsTo3D`, `PositionToPoints`, `Premult`, `Ramp`, `Read`, `Reformat`, `RotoPaint`, `Saturation`, `ScanlineRender`, `Scene`, `Shuffle`, `StickyNote`, `Switch`, `TimeClip`, `TimeEcho`, `TimeOffset`, `Tracker4`, `Transform`, `TransformGeo`, `Unpremult`, `Viewer`, `Write`, `ZDefocus`.

Plus an "All / No Selection" action set for global utilities.

---

## ⌨️ Hotkeys

The hotkey set is layered on top of Nuke's defaults from `menu.py` and `init.py`.

### Defaults *(unchanged)*

| Key | Node |
|-----|------|
| `R` | Read |
| `W` | Write |
| `O` | Roto |
| `P` | RotoPaint |
| `SHIFT + A` | AddMix |
| `G` | Grade |
| `K` | Copy |
| `B` | Blur |
| `M` | Merge |
| `.` | Dot |

### Extended / Remapped

| Key | Action |
|-----|--------|
| `SHIFT + T` | Tracker |
| `SHIFT + P` | PlanarTracker |
| `SHIFT + C` | ColorCorrect |
| `C` | CameraTracker |
| `H` | FrameHold |
| `[` | Premult |
| `L` | Quick node chain *(Read → RotoPaint → FrameHold → Copy ↔ Roto → Premult → Merge → Viewer)* |
| `SHIFT + Y` | Set project FPS from selected Read's metadata |

> The file `menu.py` is where hotkeys are defined — feel free to add or override any of them.

---

## 🧪 Custom Tools

A `Custom Tools` menu (`Write.png` icon) groups workflow helpers built into `menu.py`:

- **Tayyor nodlar (L)** — creates and auto-arranges a complete `Read → RotoPaint → FrameHold → Copy ↔ Roto → Premult → Merge → Viewer` graph in one keystroke.
- **FPS ni to'g'irlash (SHIFT+Y)** — reads `input/frame_rate` metadata from the selected (or first) Read node and applies it to the project FPS.
- **Tugmalar** — quick on-screen cheat-sheet for all custom shortcuts.

The `Custom/` folder also contains experimental scripts (`AutoRotoNode.py`, `autoSelect.py`) for color-based roto generation — disabled by default in `init.py`, uncomment to try them.

---

## 🪟 Workspaces

The `Workspaces/Nuke/Scripting.xml` file ships a pre-built **Scripting** workspace tailored for python/gizmo development inside Nuke.

---

## 📥 Installation

Locate your `.nuke` directory:

| OS | Path |
|----|------|
| 🪟 Windows | `C:\Users\<USERNAME>\.nuke\` |
| 🍎 macOS | `/Users/<USERNAME>/.nuke/` |
| 🐧 Linux | `/home/<USERNAME>/.nuke/` |

Then:

```bash
# clone directly into .nuke, or unzip a release here
git clone https://github.com/qobulovasror/nuke-toolset-plagins.git .nuke
```

Or download the ZIP and extract everything into the `.nuke` folder.

That's it — `init.py` registers every plugin path automatically, and `menu.py` builds the toolbar on the next Nuke launch.

> **Note**
> If you already have `init.py` / `menu.py` in `.nuke`, merge the contents rather than overwriting them.

---

## 🧩 Compatibility

- **Nuke 11 – 16+** — the bundled `W_hotbox` auto-selects between PySide / PySide2 / PySide6.
- KeenTools entries display a friendly warning if the host Nuke / OS doesn't match the bundled build (currently Nuke 15.1, Windows).
- Paths inside `init.py` use `sys.platform` / `os.environ` checks so the toolset works on Windows, macOS and Linux without edits.

---

## 🙏 Credits

Many of the bundled plugins are the work of the wider Nuke community. Huge thanks to:

- **Xavier Bourque** — Pixelfudger
- **Wouter Gilsing** — W_hotbox
- **Tony Lyons (CreativeLyons)** — Nuke Survival Toolkit
- **Johannes Kretschmer** — Mango Suite
- **KeenTools team** — GeoTracker / FaceTracker / FaceBuilder
- **Max van Leeuwen** — NukeShared
- **Andrea Geremia** — Expression Node Collection

Please respect each individual plugin's license when redistributing.

---

## 📄 License

This repository's own scripts and menu integrations are released under the [MIT License](https://github.com/qobulovasror/nuke-toolset-plagins/blob/master/LICENSE).
Bundled third-party plugins retain their original licenses — see the corresponding folders for details.

---

<p align="center">
  Made with ❤️ for compositors • Pull requests welcome
</p>

<p align="center">
  <a href="https://www.qobulov.uz">qobulov.uz</a> &nbsp;·&nbsp;
  GitHub <a href="https://github.com/qobulovasror">@qobulovasror</a>
</p>
