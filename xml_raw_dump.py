# xml_raw_dump.py - Raw OME-XML Dump Tool for Zeiss CZI Files
# Run this from Fiji: Plugins > Scripting > Run
# Purpose: Dump complete raw OME-XML to understand Zeiss file structure
# Specifically designed to find all StageLabel positions in multi-tile CZI files

#@ String (label="CZI file to analyze", style="file") czi_file
#@ String (label="Save XML to file (optional)", style="file", required=false) output_file

from loci.formats import ImageReader, MetadataTools
from ij import IJ
import os

VERSION = "v1.2"

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
        
        # Step 2: Open file in separate series mode
        log(u"Step 2: Opening file (separate series mode)...")
        reader.setGroupFiles(False)  # KEY: Get individual tiles, not stitched canvas
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
        
        # Step 5a: Analyze OME-XML for StageLabel tags
        log(u"Step 5a: Analyzing OME-XML structure...")
        log(u"")
        
        # Count StageLabel occurrences
        import re
        stagelabel_pattern = re.compile(r'<(?:[A-Za-z0-9_]+:)?StageLabel\b([^>]*)/?>', re.IGNORECASE)
        matches = stagelabel_pattern.findall(ome_xml)
        log(u"  Found {} StageLabel tags in OME-XML".format(len(matches)))
        log(u"")
        
        # Extract and display each StageLabel from OME-XML
        ome_positions = []
        if len(matches) > 0:
            log(u"  StageLabel Details (from OME-XML):")
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
                
                ome_positions.append((name, x, y, z))
        else:
            log(u"  WARNING: No StageLabel tags found in OME-XML!")
            log(u"")
        
        # Step 5b: Mine Global Metadata for positions (Zeiss CZI workaround)
        log(u"Step 5b: Mining Global Metadata for tile positions...")
        log(u"  (Alternative method for Zeiss CZI files)")
        log(u"")
        
        global_meta = reader.getGlobalMetadata()
        # Convert keys to list to get count (Java Hashtable$Enumerator doesn't have len())
        key_count = len(list(global_meta.keys())) if global_meta else 0
        log(u"  Global metadata keys: {}".format(key_count))
        log(u"")
        
        if global_meta and series_count > 1:
            log(u"  Searching for tile positions in global metadata...")
            log(u"  " + u"-" * 66)
            
            global_positions = []
            
            # Search for each tile (1-based indexing in Zeiss metadata)
            for i in range(series_count):
                index_tag = u"#{}".format(i + 1)  # Zeiss uses #1, #2, etc.
                found_x = 0.0
                found_y = 0.0
                found_z = 0.0
                found_key = None
                
                # Search through all global metadata keys
                for key in global_meta.keys():
                    key_str = unicode(key)
                    
                    # Filter: Must contain tile index AND position keyword
                    # Exclude false positives like SampleHolder
                    if (index_tag in key_str and 
                        (u"Position" in key_str or u"Stage" in key_str or u"Center" in key_str) and
                        u"SampleHolder" not in key_str):
                        
                        try:
                            raw_value = unicode(global_meta.get(key))
                            
                            # Parse different formats
                            if u"," in raw_value:
                                # Format: "X, Y" as single string
                                parts = raw_value.split(u",")
                                if len(parts) >= 2:
                                    found_x = float(parts[0].strip())
                                    found_y = float(parts[1].strip())
                                    if len(parts) >= 3:
                                        found_z = float(parts[2].strip())
                                    found_key = key_str
                            elif u"X" in key_str:
                                # Separate X key
                                found_x = float(raw_value)
                                found_key = key_str
                            elif u"Y" in key_str:
                                # Separate Y key
                                found_y = float(raw_value)
                                found_key = key_str
                            elif u"Z" in key_str:
                                # Separate Z key
                                found_z = float(raw_value)
                                found_key = key_str
                        except:
                            pass  # Skip unparseable values
                
                if found_x != 0.0 or found_y != 0.0:
                    log(u"  Tile {}: X={:.2f}, Y={:.2f}, Z={:.2f} um".format(i, found_x, found_y, found_z))
                    if found_key:
                        log(u"         Key: {}".format(found_key[:80]))  # Show first 80 chars
                    global_positions.append((i, found_x, found_y, found_z))
            
            log(u"")
            log(u"  Found {} positions via global metadata mining".format(len(global_positions)))
            log(u"")
        else:
            log(u"  Skipped (single series or no global metadata)")
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
