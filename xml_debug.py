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
    """Test EXHAUSTIVE series of unicode conversion approaches"""
    IJ.log("  Testing: " + method_name)
    successful_methods = []
    
    # Method 1: Direct unicode()
    try:
        result = unicode(data)
        IJ.log("    [1] unicode(data) - SUCCESS - type: " + str(type(result)))
        successful_methods.append((result, "unicode(data)"))
    except Exception as e:
        IJ.log("    [1] unicode(data) - FAILED: " + str(e))
    
    # Method 2: unicode with UTF-8 encoding
    try:
        result = unicode(data, 'utf-8')
        IJ.log("    [2] unicode(data, 'utf-8') - SUCCESS")
        successful_methods.append((result, "unicode(data, 'utf-8')"))
    except Exception as e:
        IJ.log("    [2] unicode(data, 'utf-8') - FAILED: " + str(e))
    
    # Method 3: unicode with UTF-8 and replace
    try:
        result = unicode(data, 'utf-8', 'replace')
        IJ.log("    [3] unicode(data, 'utf-8', 'replace') - SUCCESS")
        successful_methods.append((result, "unicode(data, 'utf-8', 'replace')"))
    except Exception as e:
        IJ.log("    [3] unicode(data, 'utf-8', 'replace') - FAILED: " + str(e))
    
    # Method 4: unicode with latin-1
    try:
        result = unicode(data, 'latin-1')
        IJ.log("    [4] unicode(data, 'latin-1') - SUCCESS")
        successful_methods.append((result, "unicode(data, 'latin-1')"))
    except Exception as e:
        IJ.log("    [4] unicode(data, 'latin-1') - FAILED: " + str(e))
    
    # Method 5: str.decode('utf-8') for str type
    try:
        if isinstance(data, str):
            result = data.decode('utf-8')
            IJ.log("    [5] str.decode('utf-8') - SUCCESS")
            successful_methods.append((result, "str.decode('utf-8')"))
    except Exception as e:
        IJ.log("    [5] str.decode('utf-8') - FAILED: " + str(e))
    
    # Method 6: str.decode('utf-8', 'replace')
    try:
        if isinstance(data, str):
            result = data.decode('utf-8', 'replace')
            IJ.log("    [6] str.decode('utf-8', 'replace') - SUCCESS")
            successful_methods.append((result, "str.decode('utf-8', 'replace')"))
    except Exception as e:
        IJ.log("    [6] str.decode('utf-8', 'replace') - FAILED: " + str(e))
    
    # Method 7: str.decode('latin-1')
    try:
        if isinstance(data, str):
            result = data.decode('latin-1')
            IJ.log("    [7] str.decode('latin-1') - SUCCESS")
            successful_methods.append((result, "str.decode('latin-1')"))
    except Exception as e:
        IJ.log("    [7] str.decode('latin-1') - FAILED: " + str(e))
    
    # Method 8: Java toString() then unicode
    try:
        if hasattr(data, 'toString'):
            result = unicode(data.toString())
            IJ.log("    [8] unicode(data.toString()) - SUCCESS")
            successful_methods.append((result, "unicode(data.toString())"))
    except Exception as e:
        IJ.log("    [8] unicode(data.toString()) - FAILED: " + str(e))
    
    # Method 9: Java toString() then decode
    try:
        if hasattr(data, 'toString'):
            java_str = data.toString()
            if isinstance(java_str, str):
                result = java_str.decode('utf-8', 'replace')
                IJ.log("    [9] data.toString().decode('utf-8', 'replace') - SUCCESS")
                successful_methods.append((result, "data.toString().decode('utf-8', 'replace')"))
    except Exception as e:
        IJ.log("    [9] data.toString().decode() - FAILED: " + str(e))
    
    # Method 10: str() then unicode with encoding
    try:
        result = unicode(str(data), 'utf-8', 'replace')
        IJ.log("    [10] unicode(str(data), 'utf-8', 'replace') - SUCCESS")
        successful_methods.append((result, "unicode(str(data), 'utf-8', 'replace')"))
    except Exception as e:
        IJ.log("    [10] unicode(str(data), 'utf-8', 'replace') - FAILED: " + str(e))
    
    # Method 11: bytes type handling
    try:
        if isinstance(data, bytes):
            result = unicode(data, 'utf-8', 'replace')
            IJ.log("    [11] unicode(bytes, 'utf-8', 'replace') - SUCCESS")
            successful_methods.append((result, "unicode(bytes, 'utf-8', 'replace')"))
    except Exception as e:
        IJ.log("    [11] bytes handling - FAILED: " + str(e))
    
    # Method 12: Java String getBytes() approach
    try:
        if hasattr(data, 'getBytes'):
            java_bytes = data.getBytes('UTF-8')
            result = unicode(str(java_bytes), 'utf-8', 'replace')
            IJ.log("    [12] data.getBytes('UTF-8') approach - SUCCESS")
            successful_methods.append((result, "data.getBytes('UTF-8')"))
    except Exception as e:
        IJ.log("    [12] getBytes() - FAILED: " + str(e))
    
    # Method 13: codecs module approach
    try:
        import codecs
        result = codecs.decode(str(data), 'utf-8', 'replace')
        IJ.log("    [13] codecs.decode(str(data), 'utf-8', 'replace') - SUCCESS")
        successful_methods.append((result, "codecs.decode()"))
    except Exception as e:
        IJ.log("    [13] codecs.decode() - FAILED: " + str(e))
    
    # Method 14: Force encode then decode
    try:
        temp = str(data).encode('latin-1')
        result = temp.decode('utf-8', 'replace')
        IJ.log("    [14] str.encode('latin-1').decode('utf-8') - SUCCESS")
        successful_methods.append((result, "encode('latin-1').decode('utf-8')"))
    except Exception as e:
        IJ.log("    [14] encode/decode chain - FAILED: " + str(e))
    
    # Method 15: repr() then ast.literal_eval approach
    try:
        import ast
        repr_str = repr(data)
        if 'xc2' in repr_str.lower():
            IJ.log("    [15] repr() shows UTF-8 bytes: " + repr_str[:100])
            # Try to extract and decode
            if isinstance(data, str):
                result = data.decode('utf-8', 'replace')
                successful_methods.append((result, "repr detection + decode"))
    except Exception as e:
        IJ.log("    [15] repr() analysis - FAILED: " + str(e))
    
    # Summary
    if successful_methods:
        IJ.log("    TOTAL SUCCESS: " + str(len(successful_methods)) + " methods worked")
        # Return the first successful one
        return successful_methods[0][0], successful_methods[0][1]
    else:
        IJ.log("    ALL " + str(15) + " METHODS FAILED!")
        return None, "ALL FAILED"

def main():
    IJ.log("=" * 70)
    IJ.log("OME-XML DIAGNOSTIC TOOL v1.2")
    IJ.log("=" * 70)
    IJ.log("")
    
    # Validate and normalize file path
    import os
    # Convert to unicode to handle non-ASCII characters (ä, ü, etc.)
    try:
        if isinstance(czi_file, unicode):
            file_path = czi_file
        else:
            file_path = unicode(str(czi_file).strip(), 'utf-8', 'replace')
    except:
        file_path = str(czi_file).strip()
    
    # Check if file exists
    if not os.path.exists(file_path):
        try:
            IJ.log(u"ERROR: File does not exist: {}".format(file_path))
        except:
            IJ.log("ERROR: File does not exist (path contains special characters)")
        IJ.log("")
        IJ.log("Troubleshooting:")
        IJ.log("  1. Make sure to select the FULL path including .czi extension")
        IJ.log("  2. Check that the file isn't open in another program")
        IJ.log("  3. Verify the path doesn't contain special characters")
        IJ.log("")
        return
    
    try:
        IJ.log(u"File: {}".format(file_path))
        IJ.log(u"File exists: Yes")
        IJ.log(u"File size: {:.1f} MB".format(os.path.getsize(file_path) / 1024.0 / 1024.0))
    except UnicodeEncodeError:
        IJ.log("File: <path contains non-ASCII characters>")
        IJ.log("File exists: Yes")
        IJ.log("File size: {:.1f} MB".format(os.path.getsize(file_path) / 1024.0 / 1024.0))
    IJ.log("")
    
    # Enable Bio-Formats debug
    DebugTools.setRootLevel("INFO")
    
    reader = None
    try:
        # Initialize reader
        IJ.log("Step 1: Initializing Bio-Formats reader...")
        reader = ImageReader()
        IJ.log("  Setting file ID...")
        reader.setId(file_path)
        IJ.log("  SUCCESS - Series count: " + str(reader.getSeriesCount()))
        IJ.log("")
        
        # Get metadata store
        IJ.log("Step 2: Getting metadata store...")
        metadata = MetadataTools.createOMEXMLMetadata()
        reader.setMetadataStore(metadata)
        # Re-initialize with metadata store (Bio-Formats requirement)
        reader.close()
        reader.setId(file_path)
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
        
        # Test Method 5: Series metadata
        IJ.log("Step 7: Testing reader.getSeriesMetadata()...")
        try:
            for i in range(min(2, reader.getSeriesCount())):
                reader.setSeries(i)
                seriesMeta = reader.getSeriesMetadata()
                IJ.log("  Series " + str(i) + " metadata keys: " + str(len(seriesMeta.keys())))
                
                # Look for pixel size keys
                pixel_keys = [k for k in seriesMeta.keys() if 'pixel' in str(k).lower() or 'physical' in str(k).lower()]
                for key in pixel_keys[:3]:
                    IJ.log("    Key: " + str(key))
                    val = seriesMeta.get(key)
                    IJ.log("      Type: " + safe_type(val))
                    test_unicode_conversion(val, "SeriesMeta[" + str(key) + "]")
        except Exception as e:
            IJ.log("  FAILED: " + str(e))
        IJ.log("")
        
        # Test Method 6: Core metadata
        IJ.log("Step 8: Testing reader.getCoreMetadataList()...")
        try:
            coreList = reader.getCoreMetadataList()
            IJ.log("  Core metadata entries: " + str(len(coreList)))
            for i in range(min(2, len(coreList))):
                core = coreList[i]
                IJ.log("  Entry " + str(i) + ":")
                # Try different attribute access
                attrs = ['pixelType', 'sizeX', 'sizeY', 'sizeZ', 'sizeC', 'sizeT']
                for attr in attrs:
                    try:
                        if hasattr(core, attr):
                            val = getattr(core, attr)
                            IJ.log("    " + attr + ": " + str(val))
                    except:
                        pass
        except Exception as e:
            IJ.log("  FAILED: " + str(e))
        IJ.log("")
        
        # Test Method 7: Metadata store root
        IJ.log("Step 9: Testing metadata.getRoot()...")
        try:
            root = metadata.getRoot()
            IJ.log("  Root type: " + safe_type(root))
            IJ.log("  Root string length: " + str(len(str(root)) if root else 0))
            # Try converting root to XML
            if hasattr(root, 'asXMLString'):
                try:
                    xml_from_root = root.asXMLString()
                    IJ.log("  root.asXMLString() available")
                    converted, method = test_unicode_conversion(xml_from_root, "root.asXMLString()")
                    if converted and u'\xb5' in converted:
                        IJ.log("    *** CONTAINS MICRO SIGN! ***")
                except Exception as e2:
                    IJ.log("  root.asXMLString() failed: " + str(e2))
        except Exception as e:
            IJ.log("  FAILED: " + str(e))
        IJ.log("")
        
        # Test Method 8: Direct metadata field access
        IJ.log("Step 10: Testing all metadata.getPixels*() methods...")
        try:
            test_methods = [
                ('getPixelsPhysicalSizeX', 0),
                ('getPixelsPhysicalSizeY', 0),
                ('getPixelsPhysicalSizeZ', 0),
                ('getPixelsSizeX', 0),
                ('getPixelsSizeY', 0),
                ('getPixelsSizeC', 0),
                ('getPixelsSizeZ', 0),
                ('getPixelsType', 0),
            ]
            for method_name, image_idx in test_methods:
                try:
                    if hasattr(metadata, method_name):
                        method = getattr(metadata, method_name)
                        result = method(image_idx)
                        IJ.log("  " + method_name + "(0): " + str(result) + " (type: " + safe_type(result) + ")")
                        if result and hasattr(result, 'value'):
                            IJ.log("    .value(): " + str(result.value()))
                except Exception as e2:
                    IJ.log("  " + method_name + " - FAILED: " + str(e2))
        except Exception as e:
            IJ.log("  FAILED: " + str(e))
        IJ.log("")
        
        # Test Method 9: Exhaustive global metadata scan
        IJ.log("Step 11: EXHAUSTIVE scan of ALL global metadata...")
        try:
            gMeta = reader.getGlobalMetadata()
            all_keys = list(gMeta.keys())
            IJ.log("  Total keys to scan: " + str(len(all_keys)))
            
            # Scan ALL keys for micro sign
            keys_with_micro = []
            for key in all_keys:
                try:
                    val = gMeta.get(key)
                    val_str = str(val)
                    # Check for micro sign in multiple forms
                    if u'\xb5' in unicode(val_str, 'utf-8', 'replace') or '\xc2\xb5' in val_str or 'micro' in val_str.lower():
                        keys_with_micro.append((key, val))
                except:
                    pass
            
            IJ.log("  Found " + str(len(keys_with_micro)) + " keys containing micro sign or 'micro' text")
            for key, val in keys_with_micro[:10]:  # Show first 10
                IJ.log("")
                IJ.log("  Key: " + str(key))
                IJ.log("    Raw value: " + safe_repr(val)[:100])
                converted, method = test_unicode_conversion(val, str(key))
                if converted:
                    IJ.log("    Best method: " + method)
                    IJ.log("    Converted: " + converted[:100])
        except Exception as e:
            IJ.log("  FAILED: " + str(e))
        IJ.log("")
        
        # Test Method 10: Raw metadata table
        IJ.log("Step 12: Testing raw Hashtable access...")
        try:
            import java.util.Hashtable
            gMeta = reader.getGlobalMetadata()
            IJ.log("  Metadata class: " + str(gMeta.__class__))
            IJ.log("  Is Hashtable: " + str(isinstance(gMeta, java.util.Hashtable)))
            
            # Try different iteration methods
            IJ.log("  Trying entrySet() iteration...")
            entries = gMeta.entrySet()
            count = 0
            for entry in entries:
                if count >= 5:
                    break
                key = entry.getKey()
                value = entry.getValue()
                IJ.log("    Entry " + str(count) + ":")
                IJ.log("      Key type: " + safe_type(key))
                IJ.log("      Value type: " + safe_type(value))
                count += 1
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
        try:
            IJ.log(u"FATAL ERROR: {}".format(unicode(str(e), 'utf-8', 'replace')))
        except:
            IJ.log("FATAL ERROR: <error message contains special characters>")
        try:
            import traceback
            IJ.log(traceback.format_exc())
        except:
            pass
    finally:
        if reader:
            reader.close()

if __name__ == "__main__":
    main()
