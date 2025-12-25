# Ethical Statement & Transparency

## Research Context

### Test Samples
This script was developed and tested using:
- **Animal brain tissue samples** from research microscopy
- Zeiss ApoTome fluorescence microscopy images
- Multi-channel 3D image stacks

**Important Clarification**: 
- **NO animals were sacrificed specifically for this software development**
- All test samples were obtained from existing research projects
- Tissue collection had already occurred for other scientific purposes
- This software project used pre-existing microscopy data
- No additional animal procedures were performed for software testing

### Purpose & Context
- **Research Tool Development**: Created to address specific batch processing needs
- **Non-Commercial**: Not a commercial product, no sales or licensing fees
- **Use Case**: Zeiss ApoTome fluorescence microscopy stitching for brain tissue sections
- **Problem Solved**: Existing tools (Viveca Stitching Tool, BigStitcher UI) didn't meet specific workflow requirements

---

## Development Independence

### Financial & Professional Independence
- ✅ **No payment received** for this work
- ✅ **No coercion or external pressure** to develop this tool
- ✅ **No direct financial gains** from this project
- ✅ **Independent research and development** 
- ✅ **No conflicts of interest**
- ✅ **No institutional requirements** driving development

### Motivation
- Personal research need for better .czi stitching workflow
- Frustration with existing tools that didn't work for ApoTome .czi files
- Learning exercise in Fiji/ImageJ scripting and microscopy image processing
- Contribution to open source scientific tools community

---

## AI & Tool Usage (Disclosed)

### Primary Tools
- **GitHub Copilot**: Primary coding assistant for implementation
  - Used for code generation, debugging, refactoring
  - All code reviewed and tested by human developer
  - Iterative "Vibe Coding" methodology (user-driven development)

- **Google Gemini**: Technical research and documentation
  - Used to quickly check technical details
  - Research documentation conventions
  - Verify API calls and best practices
  - **Note**: Attempted to use for Vibe Coding but model kept dropping code snippets

### Development Methodology
- **"Vibe Coding"**: User-driven iterative development
  - User describes desired functionality and current issues
  - AI implements changes
  - User tests with real data
  - User reports results and requests next iteration
  - Cycle repeats until functionality works

### Human Oversight
- All code tested by human developer with real microscopy data
- All bugs identified through hands-on testing
- All features validated against actual use cases
- Documentation written to address real user confusion points

---

## Attribution & Intellectual Property

### Original Work
- **Not knowingly copied**: Implementation is original with proper attribution
- **Inspired by existing tools**: Built on concepts from Viveca Stitching Tool and BigStitcher
- **Uses standard libraries**: Bio-Formats, ImageJ Stitching Plugin (properly credited)
- **New combination**: Novel workflow combining 2D registration with 3D fusion

### Sources & Inspiration
- **YouTube Tutorial**: Started journey with [seiryoku-zenyo's LSM700 tutorial](https://www.youtube.com/watch?v=JmED5U2R8zM&t=1s)
- **Viveca Stitching Tool**: Inspired by [seiryoku-zenyo's tool](https://github.com/seiryoku-zenyo/ImageJ-tools) but tailored to different hardware
- **ImageJ Community**: General knowledge from Image.sc forums and documentation
- **Bio-Formats Docs**: OME-XML metadata parsing techniques
- **Stitching Plugin Docs**: Understanding of Grid/Collection stitching parameters

### Licensing Concerns
- **Contact Available**: If you believe any code was improperly used, please contact
- **Good Faith**: All attribution done in good faith to the best of knowledge
- **Open Source Spirit**: Intended as contribution to scientific community
- **No Commercial Intent**: Not seeking profit or competitive advantage

---

## Transparency & Disclosure

### What Was NOT Done
- ❌ No animals were harmed or sacrificed for this software
- ❌ No direct copying of proprietary code
- ❌ No violation of licenses or terms of service
- ❌ No undisclosed commercial interests
- ❌ No undisclosed funding sources
- ❌ No institutional approval required (personal project)

### What WAS Done
- ✅ Used AI coding assistants (GitHub Copilot, attempted Gemini)
- ✅ Used existing research microscopy data for testing
- ✅ Built on existing open source tools (properly attributed)
- ✅ Learned from community resources (Image.sc, GitHub, YouTube)
- ✅ Iterative development based on real-world testing

### Development Timeline
- **Estimated Time**: 40-60 hours over 2-3 weeks
- **Methodology**: Vibe Coding (user-driven iterative development with AI assistant)
- **Testing**: Continuous testing with real .czi files throughout development
- **Documentation**: ~80KB of documentation written to address real confusion points

---

## Limitations & Disclaimers

### Beta Status
- This is a **BETA release** - first stable minimal viable version
- Known issues documented honestly (LUT persistence in TIFF files)
- Not all parameter combinations exhaustively tested
- May have edge cases with unusual .czi files

### Not Feature Complete
- Some requested features not yet implemented (sharp-slice detection, ROI-based detection)
- Development ongoing based on user needs
- Script evolving based on real-world feedback

### Use At Your Own Risk
- **Research use only** - not for clinical or diagnostic purposes
- **Validate outputs** - always verify results against source data
- **Test before production** - try on sample data before batch processing
- **No warranties** - provided "as is" without guarantees

---

## Contact & Questions

### For Licensing Concerns
If you believe any code was improperly used or have licensing questions:
- Open an issue on the GitHub repository
- Contact via GitHub profile
- Willing to discuss and resolve any concerns

### For Technical Support
- Check [HELP_v37.4.md](HELP_v37.4.md) for troubleshooting
- Check [PITFALLS.md](PITFALLS.md) for known issues
- Open issue on GitHub with debug log output

### For Collaboration
- Pull requests welcome for bug fixes
- Feature requests can be submitted as issues
- Documentation improvements appreciated

---

## Acknowledgments

### Open Source Community
- Deep gratitude to the Fiji/ImageJ community
- Thanks to Bio-Formats team (OME) for metadata tools
- Thanks to Stitching Plugin developers (Preibisch et al.)
- Thanks to seiryoku-zenyo for tutorial that started this journey
- Thanks to Image.sc forum members for knowledge sharing

### AI Assistance
- GitHub Copilot for implementation assistance
- OpenAI and Anthropic for advancing AI coding capabilities
- Acknowledgment that this tool wouldn't exist without AI assistance

---

**Last Updated**: January 2025 (v37.4 Beta Release)

**Version**: 37.4 (First Stable Minimal Viable Beta)

**Status**: Active Development - feedback welcome
