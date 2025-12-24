# xml_raw_dump.py - Raw OME-XML Dump Tool for Zeiss CZI Files
# Run this from Fiji: Plugins > Scripting > Run
# Purpose: Dump complete raw OME-XML to understand Zeiss file structure
# Specifically designed to find all StageLabel positions in multi-tile CZI files

#@ String (label="CZI file to analyze", style="file") czi_file
#@ String (label="Save XML to file (optional)", style="file", required=false) output_file

from loci.formats import ImageReader, MetadataTools
from ij import IJ
import os

VERSION = "v1.0"

def log(msg):
    """Safe logging with unicode support"""
    try:
        IJ.log(unicode(msg))
    except:
        try:
            IJ.log(str(msg))
        except:
            IJ.log("<log failed>")

def dump_raw_xml(file_path):
    """Dump complete raw OME-XML from CZI file"""
    
    log("=" * 70)
    log("RAW OME-XML DUMP TOOL {}".format(VERSION))
    log("=" * 70)
    log("")
    
    # Validate file exists
    if not os.path.exists(file_path):
        log("ERROR: File not found: {}".format(file_path))
        return None
    
    log("File: {}".format(file_path))
    file_size_mb = os.path.getsize(file_path) / (1024.0 * 1024.0)
    log("Size: {:.1f} MB".format(file_size_mb))
    log("")
    
    reader = None
    ome_xml = None
    
    try:
        # Step 1: Create reader with OME-XML metadata store
        log("Step 1: Creating Bio-Formats reader with OMEXMLMetadata...")
        metadata = MetadataTools.createOMEXMLMetadata()
        reader = ImageReader()
        reader.setMetadataStore(metadata)
        
        # Step 2: Open file
        log("Step 2: Opening file...")
        reader.setId(file_path)
        
        series_count = reader.getSeriesCount()
        log("  Series count: {}".format(series_count))
        log("")
        
        # Step 3: Get metadata store type
        meta_store = reader.getMetadataStore()
        meta_type = type(meta_store).__name__
        log("Step 3: Metadata store type: {}".format(meta_type))
        log("")
        
        # Step 4: Dump OME-XML
        log("Step 4: Dumping OME-XML...")
        try:
            ome_xml = meta_store.dumpXML()
            xml_length = len(ome_xml)
            log("  SUCCESS: Extracted {} characters".format(xml_length))
            log("")
        except Exception as e:
            log("  ERROR: Failed to dump XML: {}".format(str(e)))
            log("  Metadata store may not support dumpXML()")
            return None
        
        # Step 5: Analyze OME-XML for StageLabel tags
        log("Step 5: Analyzing OME-XML structure...")
        log("")
        
        # Count StageLabel occurrences
        import re
        stagelabel_pattern = re.compile(r'<(?:[A-Za-z0-9_]+:)?StageLabel\b([^>]*)/?>', re.IGNORECASE)
        matches = stagelabel_pattern.findall(ome_xml)
        log("  Found {} StageLabel tags".format(len(matches)))
        log("")
        
        # Extract and display each StageLabel
        if len(matches) > 0:
            log("  StageLabel Details:")
            log("  " + "-" * 66)
            
            attr_pattern = re.compile(r'([A-Za-z_:][-A-Za-z0-9_:.]*)="([^"]*)"')
            
            for i, match in enumerate(matches):
                attrs = dict(attr_pattern.findall(match))
                name = attrs.get('Name') or attrs.get('name') or "?"
                x = attrs.get('X') or attrs.get('x') or "?"
                y = attrs.get('Y') or attrs.get('y') or "?"
                z = attrs.get('Z') or attrs.get('z') or "?"
                
                log("  [{}] Name: {}".format(i, name))
                log("      X: {} um".format(x))
                log("      Y: {} um".format(y))
                log("      Z: {} um".format(z))
                log("")
        else:
            log("  WARNING: No StageLabel tags found in OME-XML!")
            log("  This CZI may not have stage position metadata.")
            log("")
        
        # Step 6: Show XML structure summary
        log("Step 6: XML Structure Summary:")
        log("  " + "-" * 66)
        
        # Count key elements
        image_count = ome_xml.count('<Image ')
        pixels_count = ome_xml.count('<Pixels ')
        channel_count = ome_xml.count('<Channel ')
        
        log("  <Image> tags: {}".format(image_count))
        log("  <Pixels> tags: {}".format(pixels_count))
        log("  <Channel> tags: {}".format(channel_count))
        log("  <StageLabel> tags: {}".format(len(matches)))
        log("")
        
        # Step 7: Display first 2000 characters as preview
        log("Step 7: XML Preview (first 2000 characters):")
        log("  " + "-" * 66)
        preview = ome_xml[:2000]
        # Split into lines for better readability
        for line in preview.split('\n'):
            log("  " + line)
        if len(ome_xml) > 2000:
            log("  ...")
            log("  (XML continues for {} more characters)".format(len(ome_xml) - 2000))
        log("")
        
        return ome_xml
        
    except Exception as e:
        log("")
        log("ERROR: {}".format(str(e)))
        import traceback
        log("")
        log("Traceback:")
        for line in traceback.format_exc().split('\n'):
            log("  " + line)
        return None
    
    finally:
        # Always close reader
        if reader is not None:
            try:
                reader.close()
                log("Reader closed.")
            except:
                pass

# Main execution
log("")
ome_xml = dump_raw_xml(czi_file)

# Save to file if requested
if ome_xml and output_file and output_file.strip():
    try:
        log("")
        log("Saving XML to file...")
        log("Output: {}".format(output_file))
        
        with open(output_file, 'w') as f:
            # Convert unicode to UTF-8 for file writing
            if isinstance(ome_xml, unicode):
                f.write(ome_xml.encode('utf-8'))
            else:
                f.write(ome_xml)
        
        log("SUCCESS: XML saved to file.")
        log("")
    except Exception as e:
        log("ERROR: Could not save to file: {}".format(str(e)))
        log("")

log("=" * 70)
log("ANALYSIS COMPLETE")
log("=" * 70)
log("")

if ome_xml:
    log("SUMMARY:")
    log("  - OME-XML extracted successfully ({} characters)".format(len(ome_xml)))
    log("  - Check the log above for StageLabel positions")
    log("  - If StageLabels are present, they show the stage positions for each tile")
    log("")
    log("NEXT STEPS:")
    log("  1. Review the StageLabel details above")
    log("  2. If only 1 StageLabel found but multiple tiles exist,")
    log("     the CZI file may store positions differently")
    log("  3. Try saving XML to file for full inspection")
else:
    log("FAILED: Could not extract OME-XML from this file.")
    log("Check error messages above for details.")
