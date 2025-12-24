# xml_raw_dump.py - Raw OME-XML Dump Tool for Zeiss CZI Files
# Run this from Fiji: Plugins > Scripting > Run
# Purpose: Dump complete raw OME-XML to understand Zeiss file structure
# Specifically designed to find all StageLabel positions in multi-tile CZI files

#@ String (label="CZI file to analyze", style="file") czi_file
#@ String (label="Save XML to file (optional)", style="file", required=false) output_file

from loci.formats import ImageReader, MetadataTools
from ij import IJ
import os

VERSION = "v1.1"

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
    
    # Convert file path to unicode to handle German characters
    if not isinstance(file_path, unicode):
        file_path = unicode(file_path, 'utf-8')
    
    log(u"=" * 70)
    log(u"RAW OME-XML DUMP TOOL {}".format(VERSION))
    log(u"=" * 70)
    log(u"")
    
    # Validate file exists (convert back to str for os.path operations)
    file_path_str = file_path.encode('utf-8') if isinstance(file_path, unicode) else file_path
    if not os.path.exists(file_path_str):
        log(u"ERROR: File not found: {}".format(file_path))
        return None
    
    log(u"File: {}".format(file_path))
    file_size_mb = os.path.getsize(file_path_str) / (1024.0 * 1024.0)
    log(u"Size: {:.1f} MB".format(file_size_mb))
    log(u"")
    
    reader = None
    ome_xml = None
    
    try:
        # Step 1: Create reader with OME-XML metadata store
        log(u"Step 1: Creating Bio-Formats reader with OMEXMLMetadata...")
        metadata = MetadataTools.createOMEXMLMetadata()
        reader = ImageReader()
        reader.setMetadataStore(metadata)
        
        # Step 2: Open file
        log(u"Step 2: Opening file...")
        reader.setId(file_path_str)
        
        series_count = reader.getSeriesCount()
        log(u"  Series count: {}".format(series_count))
        log(u"")
        
        # Step 3: Get metadata store type
        meta_store = reader.getMetadataStore()
        meta_type = type(meta_store).__name__
        log(u"Step 3: Metadata store type: {}".format(meta_type))
        log(u"")
        
        # Step 4: Dump OME-XML
        log(u"Step 4: Dumping OME-XML...")
        try:
            ome_xml = meta_store.dumpXML()
            xml_length = len(ome_xml)
            log(u"  SUCCESS: Extracted {} characters".format(xml_length))
            log(u"")
        except Exception as e:
            log(u"  ERROR: Failed to dump XML: {}".format(unicode(e)))
            log(u"  Metadata store may not support dumpXML()")
            return None
        
        # Step 5: Analyze OME-XML for StageLabel tags
        log(u"Step 5: Analyzing OME-XML structure...")
        log(u"")
        
        # Count StageLabel occurrences
        import re
        stagelabel_pattern = re.compile(r'<(?:[A-Za-z0-9_]+:)?StageLabel\b([^>]*)/?>', re.IGNORECASE)
        matches = stagelabel_pattern.findall(ome_xml)
        log(u"  Found {} StageLabel tags".format(len(matches)))
        log(u"")
        
        # Extract and display each StageLabel
        if len(matches) > 0:
            log(u"  StageLabel Details:")
            log(u"  " + u"-" * 66)
            
            attr_pattern = re.compile(r'([A-Za-z_:][-A-Za-z0-9_:.]*)="([^"]*)"')
            
            for i, match in enumerate(matches):
                attrs = dict(attr_pattern.findall(match))
                name = attrs.get('Name') or attrs.get('name') or u"?"
                x = attrs.get('X') or attrs.get('x') or u"?"
                y = attrs.get('Y') or attrs.get('y') or u"?"
                z = attrs.get('Z') or attrs.get('z') or u"?"
                
                log(u"  [{}] Name: {}".format(i, name))
                log(u"      X: {} um".format(x))
                log(u"      Y: {} um".format(y))
                log(u"      Z: {} um".format(z))
                log(u"")
        else:
            log(u"  WARNING: No StageLabel tags found in OME-XML!")
            log(u"  This CZI may not have stage position metadata.")
            log(u"")
        
        # Step 6: Show XML structure summary
        log(u"Step 6: XML Structure Summary:")
        log(u"  " + u"-" * 66)
        
        # Count key elements
        image_count = ome_xml.count('<Image ')
        pixels_count = ome_xml.count('<Pixels ')
        channel_count = ome_xml.count('<Channel ')
        
        log(u"  <Image> tags: {}".format(image_count))
        log(u"  <Pixels> tags: {}".format(pixels_count))
        log(u"  <Channel> tags: {}".format(channel_count))
        log(u"  <StageLabel> tags: {}".format(len(matches)))
        log(u"")
        
        # Step 7: Display first 2000 characters as preview
        log(u"Step 7: XML Preview (first 2000 characters):")
        log(u"  " + u"-" * 66)
        preview = ome_xml[:2000]
        # Split into lines for better readability
        for line in preview.split('\n'):
            log(u"  " + unicode(line))
        if len(ome_xml) > 2000:
            log(u"  ...")
            log(u"  (XML continues for {} more characters)".format(len(ome_xml) - 2000))
        log(u"")
        
        return ome_xml
        
    except Exception as e:
        log(u"")
        log(u"ERROR: {}".format(unicode(e)))
        import traceback
        log(u"")
        log(u"Traceback:")
        for line in traceback.format_exc().split('\n'):
            log(u"  " + unicode(line))
        return None
    
    finally:
        # Always close reader
        if reader is not None:
            try:
                reader.close()
                log(u"Reader closed.")
            except:
                pass

# Main execution
log(u"")
ome_xml = dump_raw_xml(czi_file)

# Save to file if requested
if ome_xml and output_file and output_file.strip():
    try:
        log(u"")
        log(u"Saving XML to file...")
        log(u"Output: {}".format(unicode(output_file)))
        
        with open(output_file, 'w') as f:
            # Convert unicode to UTF-8 for file writing
            if isinstance(ome_xml, unicode):
                f.write(ome_xml.encode('utf-8'))
            else:
                f.write(ome_xml)
        
        log(u"SUCCESS: XML saved to file.")
        log(u"")
    except Exception as e:
        log(u"ERROR: Could not save to file: {}".format(unicode(e)))
        log(u"")

log(u"=" * 70)
log(u"ANALYSIS COMPLETE")
log(u"=" * 70)
log(u"")

if ome_xml:
    log(u"SUMMARY:")
    log(u"  - OME-XML extracted successfully ({} characters)".format(len(ome_xml)))
    log(u"  - Check the log above for StageLabel positions")
    log(u"  - If StageLabels are present, they show the stage positions for each tile")
    log(u"")
    log(u"NEXT STEPS:")
    log(u"  1. Review the StageLabel details above")
    log(u"  2. If only 1 StageLabel found but multiple tiles exist,")
    log(u"     the CZI file may store positions differently")
    log(u"  3. Try saving XML to file for full inspection")
else:
    log(u"FAILED: Could not extract OME-XML from this file.")
    log(u"Check error messages above for details.")
