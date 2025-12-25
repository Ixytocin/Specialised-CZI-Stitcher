# Credits & Attribution

## Development Team

### Vision & Validation
**Ixytocin** ([GitHub Profile](https://github.com/Ixytocin))
- Concept and requirements definition
- Real-world testing with Zeiss ApoTome microscopy data
- Bug identification through hands-on use
- Feature prioritization based on actual workflow needs
- Documentation feedback from user perspective

### Implementation
**AI Research Partner** (GitHub Copilot)
- Code generation and implementation
- Bug fixing and refactoring
- Documentation assistance
- Iterative development following user feedback
- Technical research and API verification

### Methodology
**Vibe Coding** - User-Driven Iterative Development
1. User describes functionality or reports bug
2. AI implements/fixes
3. User tests with real data
4. User reports results
5. Cycle repeats until it works

---

## Inspiration & Starting Point

### The Journey
This project began with a YouTube tutorial and evolved through several attempts:

1. **Starting Point**: [Automatically stitching Zeiss .CZI files (LSM700) with Fiji/ImageJ](https://www.youtube.com/watch?v=JmED5U2R8zM&t=1s)
   - By seiryoku-zenyo
   - Demonstrated automated stitching workflow
   - Sparked the idea: "This should be possible!"

2. **First Attempt**: [Viveca Stitching Tool](https://github.com/seiryoku-zenyo/ImageJ-tools/blob/master/Viveca%20Stitching%20Tool)
   - By seiryoku-zenyo
   - Tailored to LSM700 imaging setup
   - **Problem**: Didn't work with ApoTome .czi files
   - Different metadata structure and tile organization

3. **Second Attempt**: BigStitcher/Stitching Plugin UI
   - Powerful and feature-rich
   - **Problem**: UI-driven workflow didn't meet batch processing needs
   - Required too many manual steps per file
   - Couldn't easily automate for multiple files

4. **Final Solution**: This Script
   - Scriptable batch processing
   - ApoTome-specific metadata handling
   - Automated 2D→3D workflow
   - Preserves LUTs and pixel size

---

## Core Technologies

### Stitching Logic
**BigStitcher / Stitching Plugin**
- By Stephan Preibisch, Stephan Saalfeld, et al.
- https://imagej.net/plugins/stitching/
- Grid/Collection stitching implementation
- Phase correlation for tile registration
- Linear blending and fusion methods

**Key Papers**:
- Preibisch et al., "Globally optimal stitching of tiled 3D microscopic image acquisitions", Bioinformatics, 2009
- Hörl et al., "BigStitcher: Reconstructing high-resolution image datasets of cleared and expanded samples", Nature Methods, 2019

### Metadata Handling
**Bio-Formats**
- By Open Microscopy Environment (OME)
- https://www.openmicroscopy.org/bio-formats/
- Zeiss .czi file format support
- OME-XML metadata extraction
- Multi-dimensional image handling

**Key Papers**:
- Linkert et al., "Metadata matters: access to image data in the real world", Journal of Cell Biology, 2010
- Goldberg et al., "The Open Microscopy Environment (OME) Data Model and XML file: open tools for informatics and quantitative analysis in biological imaging", Genome Biology, 2005

### Platform
**Fiji (Fiji Is Just ImageJ)**
- https://fiji.sc/
- ImageJ distribution for scientific image analysis
- Curated collection of plugins
- Scripting support (Jython, JavaScript, etc.)
- Active community and development

**Key Paper**:
- Schindelin et al., "Fiji: an open-source platform for biological-image analysis", Nature Methods, 2012

---

## Development Tools

### Primary Development
- **GitHub Copilot**: AI pair programmer by GitHub/OpenAI
- **Fiji**: Testing and debugging environment
- **Git**: Version control
- **Markdown**: Documentation format

### Research & Verification
- **Google Gemini**: Technical detail verification
- **ImageJ Documentation**: API reference
- **Image.sc Forum**: Community knowledge base
- **Bio-Formats Documentation**: Metadata specifications

---

## Development Timeline

### Estimated Breakdown
- **Initial Research**: 5-8 hours
  - Understanding .czi format issues
  - Reviewing existing tools
  - Planning architecture

- **Core Implementation**: 20-30 hours
  - Basic stitching workflow (v31.16h base)
  - LUT extraction and application (v36.5)
  - Unicode/encoding fixes (v34.8)
  - Integration and debugging

- **Bug Fixing & Iteration**: 10-15 hours
  - Compilation errors (v37.0)
  - Pixel size extraction (v37.0)
  - CompositeImage double-wrapping (v37.1-v37.3)
  - Exception handling (v37.4)

- **Documentation**: 5-7 hours
  - README, HELP, CHANGELOG
  - PITFALLS (lessons learned)
  - ETHICS, CREDITS (this file)
  - Code comments and docstrings

**Total: ~40-60 hours over 2-3 weeks**

### Version Evolution
- **v31.16h**: Dual 2D/3D stitching workflow (proven working)
- **v34.8**: UTF-8 handling, boolean fixes (proven working)
- **v36.5**: LUT detection from metadata (proven working)
- **v37.0**: Integration + compilation fixes
- **v37.1**: CompositeImage mode fixes
- **v37.2**: Exception handling + HyperStack creation fixes
- **v37.3**: Display mode setting fixes
- **v37.4**: Silent exception handling + comprehensive debugging (**First Beta**)

---

## Community Contributions

### Knowledge Sources
- **Image.sc Forum**: General ImageJ/Fiji knowledge
- **Stack Overflow**: Jython and Java interop questions
- **ImageJ Documentation**: Official API references
- **GitHub Issues**: Similar problems and solutions from other projects

### Inspiration from Community
- Rolling ball background subtraction (ImageJ standard tool)
- Phase correlation registration (Stitching Plugin)
- OME-XML parsing patterns (Bio-Formats examples)
- Jython/Java interop patterns (Fiji scripting examples)

---

## What This Project Builds Upon

### Standing on the Shoulders of Giants
This script would not be possible without:

1. **Decades of ImageJ Development** (Wayne Rasband, et al.)
2. **Stitching Algorithm Research** (Preibisch, Saalfeld, et al.)
3. **Bio-Formats Standardization** (OME Consortium)
4. **Open Microscopy Efforts** (Global microscopy community)
5. **Fiji Distribution** (Johannes Schindelin, et al.)
6. **Open Source Philosophy** (Countless contributors)

### Novel Contributions
What this script adds to existing work:
- **Batch automation** of BigStitcher workflow for .czi files
- **ApoTome-specific** metadata handling
- **LUT preservation** through entire workflow
- **Comprehensive error handling** with debug logging
- **Documented pitfalls** from real development experience
- **Vibe Coding methodology** demonstration (AI-assisted iterative development)

---

## Future Contributors

### How to Contribute
- **Bug Reports**: Open issue with debug log output
- **Feature Requests**: Describe use case and desired behavior
- **Code Contributions**: Pull requests welcome
- **Documentation**: Improvements to clarity and accuracy
- **Testing**: Reports of success/failure with different .czi files

### Recognition
All contributors will be credited in:
- This CREDITS.md file
- GitHub contributors page
- Release notes for version where contribution appears

---

## License & Usage

### Current Status
- No formal license yet (will be added for v1.0 release)
- Intended as open source contribution
- Free for research and non-commercial use
- Attribution appreciated but not required

### Recommended Citation
If you use this tool in published research:

```
Specialised CZI Stitcher v37.4 (2025)
Developed by Ixytocin with AI assistance (GitHub Copilot)
Built on Bio-Formats (OME) and BigStitcher/Stitching Plugin (Preibisch et al.)
Available at: https://github.com/Ixytocin/Specialised-CZI-Stitcher
```

---

## Acknowledgments

### Personal Thanks
- To seiryoku-zenyo for the tutorial that started this journey
- To the ImageJ/Fiji community for decades of tool development
- To the open source movement for making this possible
- To GitHub for providing Copilot and hosting platform
- To the scientific microscopy community for sharing knowledge

### Philosophical Note
This project demonstrates the power of:
- **Open Source**: Building on freely available tools
- **Community Knowledge**: Learning from shared experiences
- **AI Assistance**: Accelerating development with GitHub Copilot
- **Iterative Development**: User-driven "Vibe Coding" methodology
- **Transparency**: Honest documentation of process and limitations

---

**Last Updated**: January 2025 (v37.4 Beta Release)

**Version**: 37.4 (First Stable Minimal Viable Beta)

**Development Method**: Vibe Coding (User-Driven Iterative AI-Assisted Development)
