# xml_debug.py - Comprehensive OME-XML Diagnostic Tool for Jython
# Run this from Fiji: Plugins > Scripting > Run
# Purpose: Test all Bio-Formats XML reading methods to identify unicode issues

#@ String (label="CZI file to diagnose", style="file") czi_file

from loci.formats import ImageReader, MetadataTools
from loci.common import DebugTools
from ij import IJ
import sys

def safe_repr(obj):
    """Safe representation that handles unicode"""
    try:
        return repr(obj)
    except:
        return "<repr failed>"

def safe_type(obj):
    """Safe type checking"""
    try:
        t = type(obj)
        # Check if it's a Java object
        if hasattr(obj, 'toString') and not isinstance(obj, (str, bytes)):
            return "Java: " + str(t)
        return str(t)
    except:
        return "<type check failed>"

def test_unicode_conversion(data, method_name):
    """Test different unicode conversion approaches"""
    IJ.log("  Testing: " + method_name)
    
    # Method 1: Direct unicode()
    try:
        result = unicode(data)
        IJ.log("    unicode() - SUCCESS - type: " + str(type(result)))
        return result, "unicode()"
    except Exception as e:
        IJ.log("    unicode() - FAILED: " + str(e))
    
    # Method 2: str() then decode
    try:
        if isinstance(data, str):
            result = data.decode('utf-8', 'replace')
            IJ.log("    str.decode('utf-8') - SUCCESS - type: " + str(type(result)))
            return result, "str.decode('utf-8')"
    except Exception as e:
        IJ.log("    str.decode() - FAILED: " + str(e))
    
    # Method 3: Java toString()
    try:
        if hasattr(data, 'toString'):
            result = unicode(data.toString())
            IJ.log("    Java toString() - SUCCESS - type: " + str(type(result)))
            return result, "toString()"
    except Exception as e:
        IJ.log("    toString() - FAILED: " + str(e))
    
    # Method 4: String constructor
    try:
        result = unicode(str(data), 'utf-8', 'replace')
        IJ.log("    unicode(str(), 'utf-8') - SUCCESS - type: " + str(type(result)))
        return result, "unicode(str(), 'utf-8')"
    except Exception as e:
        IJ.log("    unicode(str()) - FAILED: " + str(e))
    
    return None, "ALL FAILED"

def main():
    IJ.log("=" * 70)
    IJ.log("OME-XML DIAGNOSTIC TOOL v1.0")
    IJ.log("=" * 70)
    IJ.log("")
    IJ.log("File: " + czi_file)
    IJ.log("")
    
    # Enable Bio-Formats debug
    DebugTools.setRootLevel("INFO")
    
    reader = None
    try:
        # Initialize reader
        IJ.log("Step 1: Initializing Bio-Formats reader...")
        reader = ImageReader()
        reader.setId(czi_file)
        IJ.log("  SUCCESS - Series count: " + str(reader.getSeriesCount()))
        IJ.log("")
        
        # Get metadata store
        IJ.log("Step 2: Getting metadata store...")
        metadata = MetadataTools.createOMEXMLMetadata()
        reader.setMetadataStore(metadata)
        reader.setId(czi_file)
        IJ.log("  SUCCESS - Metadata store created")
        IJ.log("")
        
        # Test Method 1: Direct getMetadataValue
        IJ.log("Step 3: Testing reader.getMetadataValue()...")
        try:
            test_key = "PhysicalSizeX"
            raw_value = reader.getMetadataValue(test_key)
            IJ.log("  Raw value type: " + safe_type(raw_value))
            IJ.log("  Raw value repr: " + safe_repr(raw_value))
            if raw_value:
                converted, method = test_unicode_conversion(raw_value, test_key)
                if converted:
                    IJ.log("  BEST METHOD: " + method)
        except Exception as e:
            IJ.log("  FAILED: " + str(e))
        IJ.log("")
        
        # Test Method 2: Global metadata
        IJ.log("Step 4: Testing reader.getGlobalMetadata()...")
        try:
            gMeta = reader.getGlobalMetadata()
            IJ.log("  Metadata keys count: " + str(len(gMeta.keys())))
            
            # Find keys with scaling information
            scaling_keys = [k for k in gMeta.keys() if 'scaling' in str(k).lower() or 'pixel' in str(k).lower()]
            IJ.log("  Found " + str(len(scaling_keys)) + " scaling-related keys")
            
            for key in scaling_keys[:5]:  # Test first 5
                IJ.log("")
                IJ.log("  Testing key: " + str(key))
                raw_value = gMeta.get(key)
                IJ.log("    Raw type: " + safe_type(raw_value))
                converted, method = test_unicode_conversion(raw_value, str(key))
                if converted and u'\xb5' in converted:
                    IJ.log("    *** CONTAINS MICRO SIGN! ***")
                    
        except Exception as e:
            IJ.log("  FAILED: " + str(e))
        IJ.log("")
        
        # Test Method 3: OME-XML string
        IJ.log("Step 5: Testing metadata.dumpXML()...")
        try:
            raw_xml = metadata.dumpXML()
            IJ.log("  Raw XML type: " + safe_type(raw_xml))
            IJ.log("  Raw XML length: " + str(len(str(raw_xml)) if raw_xml else 0))
            
            # Try to detect encoding
            xml_start = str(raw_xml)[:200] if raw_xml else ""
            IJ.log("  XML start: " + xml_start[:100])
            
            converted, method = test_unicode_conversion(raw_xml, "dumpXML")
            if converted:
                IJ.log("  BEST METHOD: " + method)
                IJ.log("  Converted length: " + str(len(converted)))
                
                # Check for micro sign
                if u'\xb5' in converted:
                    IJ.log("  *** CONTAINS UNICODE MICRO SIGN (U+00B5) ***")
                if '\xc2\xb5' in str(raw_xml):
                    IJ.log("  *** CONTAINS UTF-8 MICRO SIGN BYTES (0xC2 0xB5) ***")
                    
                # Try to extract PhysicalSizeX
                import re
                match = re.search(r'PhysicalSizeX="([^"]+)"', converted)
                if match:
                    IJ.log("  Found PhysicalSizeX: " + match.group(1))
                    
        except Exception as e:
            IJ.log("  FAILED: " + str(e))
            import traceback
            IJ.log("  Traceback:")
            IJ.log(traceback.format_exc())
        IJ.log("")
        
        # Test Method 4: OMEXMLMetadata object methods
        IJ.log("Step 6: Testing OMEXMLMetadata.getPixelsPhysicalSizeX()...")
        try:
            for i in range(min(3, reader.getSeriesCount())):
                reader.setSeries(i)
                px_size = metadata.getPixelsPhysicalSizeX(i)
                IJ.log("  Series " + str(i) + ":")
                IJ.log("    Type: " + safe_type(px_size))
                IJ.log("    Value: " + str(px_size))
                if px_size:
                    IJ.log("    Has value() method: " + str(hasattr(px_size, 'value')))
                    if hasattr(px_size, 'value'):
                        try:
                            val = px_size.value()
                            IJ.log("    value(): " + str(val) + " (type: " + str(type(val)) + ")")
                        except Exception as e2:
                            IJ.log("    value() failed: " + str(e2))
        except Exception as e:
            IJ.log("  FAILED: " + str(e))
        IJ.log("")
        
        # Summary
        IJ.log("=" * 70)
        IJ.log("DIAGNOSTIC COMPLETE")
        IJ.log("=" * 70)
        IJ.log("")
        IJ.log("RECOMMENDATIONS:")
        IJ.log("1. Use metadata.getPixelsPhysicalSizeX().value() for direct numeric access")
        IJ.log("2. For XML string, use .decode('utf-8', 'replace') on str type")
        IJ.log("3. For Java String objects, use unicode(obj.toString())")
        IJ.log("4. Always wrap in try/except with fallback to 'replace' error handling")
        
    except Exception as e:
        IJ.log("")
        IJ.log("FATAL ERROR: " + str(e))
        import traceback
        IJ.log(traceback.format_exc())
    finally:
        if reader:
            reader.close()

if __name__ == "__main__":
    main()
