# PIXEL SIZE CHECKER v1.0
# Quick diagnostic script to test pixel size extraction from CZI files
# 
# Purpose: Identify why pixel size is not being read from OME-XML
# Common issue: Getting "DummyMetadata" instead of "OMEXMLMetadataImpl"
#
# Run in Fiji to diagnose pixel size extraction issues

from ij import IJ
from ij.io import OpenDialog
from loci.formats import ImageReader
from loci.formats.meta import MetadataTools
import os, re

MICRO = u"\u00b5"

def ensure_unicode(s):
    """Convert any string to unicode safely"""
    if s is None:
        return None
    if isinstance(s, unicode):
        return s
    if hasattr(s, 'toString') and not isinstance(s, (str, bytes)):
        return unicode(s.toString())
    if isinstance(s, str):
        try:
            return s.decode('utf-8', 'replace')
        except:
            try:
                return s.decode('latin-1', 'replace')
            except:
                pass
    try:
        return unicode(s)
    except:
        return u""

def log(msg):
    """Log message with unicode handling"""
    try:
        IJ.log(ensure_unicode(msg))
    except:
        IJ.log(str(msg))

def main():
    # Select file
    od = OpenDialog("Select CZI file for pixel size check", None)
    if od.getFileName() is None:
        return
    
    file_path = os.path.join(od.getDirectory(), od.getFileName())
    
    # Header
    log(u"=" * 70)
    log(u"PIXEL SIZE CHECKER v1.0")
    log(u"=" * 70)
    log(u"")
    
    # File info
    try:
        log(u"File: {}".format(ensure_unicode(file_path)))
        log(u"File size: {:.1f} MB".format(os.path.getsize(file_path) / 1024.0 / 1024.0))
    except:
        log(u"File: <path contains special characters>")
    log(u"")
    
    results = {
        'metadata_type': None,
        'direct_api': None,
        'xml_regex': None,
        'fresh_reader': None
    }
    
    reader = None
    
    try:
        # =================================================================
        # TEST 1: Open file with basic ImageReader
        # =================================================================
        log(u"Step 1: Opening file with Bio-Formats...")
        reader = ImageReader()
        reader.setId(file_path)
        series_count = reader.getSeriesCount()
        log(u"  SUCCESS - Series count: {}".format(series_count))
        log(u"")
        
        # =================================================================
        # TEST 2: Check metadata store type
        # =================================================================
        log(u"Step 2: Checking metadata store type...")
        metadata = reader.getMetadataStore()
        metadata_type = type(metadata).__name__
        results['metadata_type'] = metadata_type
        log(u"  Metadata store class: {}".format(metadata_type))
        
        if 'Dummy' in metadata_type:
            log(u"  {}  WARNING: Got DummyMetadata instead of OMEXMLMetadataImpl".format(u"\u26a0"))
            log(u"  This is why pixel size extraction is failing!")
        elif 'OME' in metadata_type or 'XML' in metadata_type:
            log(u"  {}  GOOD: Got proper OME-XML metadata store".format(u"\u2713"))
        log(u"")
        
        # =================================================================
        # TEST 3: Try direct API method
        # =================================================================
        log(u"Step 3: Testing direct API (getPixelsPhysicalSizeX)...")
        try:
            if hasattr(metadata, 'getPixelsPhysicalSizeX'):
                px = metadata.getPixelsPhysicalSizeX(0)
                if px:
                    log(u"  Raw value: {}".format(px.value() if hasattr(px, 'value') else px))
                    log(u"  Unit: {}".format(px.unit() if hasattr(px, 'unit') else 'unknown'))
                    
                    val = float(px.value()) if hasattr(px, 'value') else float(px)
                    results['direct_api'] = val
                    log(u"  Converted to {}m: {}".format(MICRO, val))
                    log(u"  {} SUCCESS - Pixel size: {} {}m".format(u"\u2713", val, MICRO))
                else:
                    log(u"  {} Method returned None".format(u"\u2717"))
            else:
                log(u"  {} ERROR: Metadata store doesn't have getPixelsPhysicalSizeX".format(u"\u2717"))
                log(u"  (This is expected with DummyMetadata)")
        except Exception as e:
            log(u"  {} ERROR: {}".format(u"\u2717", ensure_unicode(str(e))))
        log(u"")
        
        # =================================================================
        # TEST 4: Try XML dump and regex
        # =================================================================
        log(u"Step 4: Testing OME-XML dump...")
        try:
            if hasattr(metadata, 'dumpXML'):
                xml_str = metadata.dumpXML()
                xml_unicode = ensure_unicode(xml_str)
                log(u"  OME-XML dumped: {} characters".format(len(xml_unicode)))
                
                # Try regex
                m = re.search(r'PhysicalSizeX\s*=\s*"([^"]+)"', xml_unicode, re.IGNORECASE)
                if m:
                    val = float(m.group(1))
                    results['xml_regex'] = val
                    log(u"  Regex found PhysicalSizeX: {}".format(val))
                    log(u"  {} SUCCESS - Pixel size from XML: {} {}m".format(u"\u2713", val, MICRO))
                else:
                    log(u"  {} PhysicalSizeX not found in XML".format(u"\u2717"))
            else:
                log(u"  {} ERROR: Metadata store doesn't have dumpXML method".format(u"\u2717"))
                log(u"  (This is expected with DummyMetadata)")
        except Exception as e:
            log(u"  {} ERROR: {}".format(u"\u2717", ensure_unicode(str(e))))
        log(u"")
        
        # Close first reader
        reader.close()
        
        # =================================================================
        # TEST 5: Try with fresh reader + metadata store attached FIRST
        # =================================================================
        log(u"Step 5: Testing with fresh reader + metadata store...")
        log(u"  (This is the CORRECT approach)")
        try:
            # Create proper metadata store
            ome_meta = MetadataTools.createOMEXMLMetadata()
            log(u"  Created OMEXMLMetadata")
            
            # Create new reader
            reader2 = ImageReader()
            
            # CRITICAL: Set metadata store BEFORE opening file
            reader2.setMetadataStore(ome_meta)
            log(u"  Attached metadata store before opening file")
            
            # Now open file
            reader2.setId(file_path)
            
            # Try to get pixel size
            px = ome_meta.getPixelsPhysicalSizeX(0)
            if px:
                val = float(px.value()) if hasattr(px, 'value') else float(px)
                results['fresh_reader'] = val
                log(u"  Pixel size: {} {}m".format(val, MICRO))
                log(u"  {} SUCCESS with this approach!".format(u"\u2713"))
            else:
                log(u"  {} Method returned None".format(u"\u2717"))
            
            reader2.close()
        except Exception as e:
            log(u"  {} ERROR: {}".format(u"\u2717", ensure_unicode(str(e))))
        log(u"")
        
        # =================================================================
        # SUMMARY
        # =================================================================
        log(u"=" * 70)
        log(u"RESULTS")
        log(u"=" * 70)
        
        # Metadata type
        if results['metadata_type']:
            if 'Dummy' in results['metadata_type']:
                log(u"{} Metadata store type: {} (WRONG - this is the problem!)".format(
                    u"\u2717", results['metadata_type']))
            else:
                log(u"{} Metadata store type: {} (correct)".format(
                    u"\u2713", results['metadata_type']))
        
        # Direct API
        if results['direct_api']:
            log(u"{} Direct API: {} {}m".format(u"\u2713", results['direct_api'], MICRO))
        else:
            log(u"{} Direct API: Failed".format(u"\u2717"))
        
        # XML regex
        if results['xml_regex']:
            log(u"{} XML regex: {} {}m".format(u"\u2713", results['xml_regex'], MICRO))
        else:
            log(u"{} XML regex: Failed".format(u"\u2717"))
        
        # Fresh reader
        if results['fresh_reader']:
            log(u"{} Fresh reader: {} {}m (WORKAROUND)".format(
                u"\u2713", results['fresh_reader'], MICRO))
        else:
            log(u"{} Fresh reader: Failed".format(u"\u2717"))
        
        log(u"")
        
        # Conclusion
        if 'Dummy' in str(results['metadata_type']):
            log(u"CONCLUSION: Pixel size extraction FAILING because getting DummyMetadata")
            log(u"")
            log(u"SOLUTION: Create OMEXMLMetadata with MetadataTools.createOMEXMLMetadata()")
            log(u"          and attach it to reader BEFORE calling setId()")
            log(u"")
            log(u"Code fix needed in main_v35_standalone:")
            log(u"  1. Import: from loci.formats.meta import MetadataTools")
            log(u"  2. Before opening: metadata = MetadataTools.createOMEXMLMetadata()")
            log(u"  3. Attach first: reader.setMetadataStore(metadata)")
            log(u"  4. Then open: reader.setId(file_path)")
        elif results['direct_api'] or results['xml_regex']:
            log(u"CONCLUSION: Pixel size extraction working correctly!")
        else:
            log(u"CONCLUSION: Unexpected error - metadata store is correct but methods fail")
        
    except Exception as e:
        log(u"")
        log(u"FATAL ERROR: {}".format(ensure_unicode(str(e))))
        try:
            import traceback
            log(traceback.format_exc())
        except:
            pass
    finally:
        if reader:
            try:
                reader.close()
            except:
                pass

if __name__ == '__main__' or __name__ == '__builtin__':
    main()
