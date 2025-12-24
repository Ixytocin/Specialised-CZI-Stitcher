# xml_parser.py - Focused OME-XML Parser for CZI Files
# Run this from Fiji: Plugins > Scripting > Run
# Purpose: Extract and display key metadata fields from CZI files

#@ String (label="CZI file to parse", style="file") czi_file

from loci.formats import ImageReader, MetadataTools
from loci.common import DebugTools
from ij import IJ
import re
import os

def ensure_unicode(obj):
    """Convert object to unicode safely"""
    if obj is None:
        return u""
    if isinstance(obj, unicode):
        return obj
    if hasattr(obj, 'toString') and not isinstance(obj, (str, bytes)):
        return unicode(obj.toString())
    if isinstance(obj, str):
        try:
            return obj.decode('utf-8', 'replace')
        except:
            try:
                return obj.decode('latin-1', 'replace')
            except:
                return unicode(str(obj), 'utf-8', 'replace')
    if isinstance(obj, bytes):
        return unicode(obj, 'utf-8', 'replace')
    return unicode(str(obj), 'utf-8', 'replace')

def extract_attribute(xml, element, attribute):
    """Extract attribute value from XML element"""
    pattern = r'<' + element + r'[^>]*\s' + attribute + r'="([^"]*)"'
    match = re.search(pattern, xml, re.IGNORECASE)
    if match:
        return ensure_unicode(match.group(1))
    return None

def extract_channel_info(xml):
    """Extract all channel information"""
    channels = []
    channel_pattern = r'<Channel[^>]*>(.*?)</Channel>'
    for match in re.finditer(channel_pattern, xml, re.IGNORECASE | re.DOTALL):
        channel_xml = match.group(0)
        channel = {}
        
        # Extract channel attributes
        channel['id'] = extract_attribute(channel_xml, 'Channel', 'id')
        channel['name'] = extract_attribute(channel_xml, 'Channel', 'name')
        channel['fluor'] = extract_attribute(channel_xml, 'Channel', 'fluor')
        channel['color'] = extract_attribute(channel_xml, 'Channel', 'color')
        channel['emission_wavelength'] = extract_attribute(channel_xml, 'Channel', 'emissionwavelength')
        channel['emission_unit'] = extract_attribute(channel_xml, 'Channel', 'emissionwavelengthunit')
        channel['excitation_wavelength'] = extract_attribute(channel_xml, 'Channel', 'excitationwavelength')
        channel['excitation_unit'] = extract_attribute(channel_xml, 'Channel', 'excitationwavelengthunit')
        channel['acquisition_mode'] = extract_attribute(channel_xml, 'Channel', 'acquisitionmode')
        channel['illumination_type'] = extract_attribute(channel_xml, 'Channel', 'illuminationtype')
        
        channels.append(channel)
    
    return channels

def parse_color(color_str):
    """Parse color integer to RGB"""
    if not color_str:
        return None
    try:
        color_int = int(color_str)
        # Handle negative (signed) integers
        if color_int < 0:
            color_int = color_int & 0xFFFFFFFF
        hex_str = "%08X" % color_int
        r = int(hex_str[0:2], 16)
        g = int(hex_str[2:4], 16)
        b = int(hex_str[4:6], 16)
        return "RGB({}, {}, {})".format(r, g, b)
    except:
        return color_str

def main():
    IJ.log("=" * 70)
    IJ.log("OME-XML PARSER v1.0")
    IJ.log("=" * 70)
    IJ.log("")
    
    # Validate file
    import os
    try:
        if isinstance(czi_file, unicode):
            file_path = czi_file
        else:
            file_path = unicode(str(czi_file).strip(), 'utf-8', 'replace')
    except:
        file_path = str(czi_file).strip()
    
    if not os.path.exists(file_path):
        IJ.log("ERROR: File does not exist")
        return
    
    try:
        IJ.log(u"File: {}".format(file_path))
        IJ.log(u"File size: {:.1f} MB".format(os.path.getsize(file_path) / 1024.0 / 1024.0))
    except:
        IJ.log("File: <path with special characters>")
        IJ.log(u"File size: {:.1f} MB".format(os.path.getsize(file_path) / 1024.0 / 1024.0))
    IJ.log("")
    
    reader = None
    try:
        # Initialize reader with metadata store
        IJ.log("Initializing Bio-Formats reader...")
        DebugTools.setRootLevel("WARN")
        
        metadata = MetadataTools.createOMEXMLMetadata()
        reader = ImageReader()
        reader.setMetadataStore(metadata)
        reader.setId(file_path)
        
        series_count = reader.getSeriesCount()
        IJ.log(u"SUCCESS - Found {} series".format(series_count))
        IJ.log("")
        
        # Get OME-XML string
        IJ.log("Extracting OME-XML metadata...")
        xml_raw = metadata.dumpXML()
        xml = ensure_unicode(xml_raw)
        IJ.log(u"XML length: {} characters".format(len(xml)))
        IJ.log("")
        
        # Process each series
        for series_idx in range(series_count):
            reader.setSeries(series_idx)
            
            IJ.log("=" * 70)
            IJ.log(u"SERIES {} / {}".format(series_idx + 1, series_count))
            IJ.log("=" * 70)
            IJ.log("")
            
            # Image Information
            IJ.log("IMAGE INFORMATION:")
            image_id = extract_attribute(xml, 'Image', 'ID')
            image_name = extract_attribute(xml, 'Image', 'Name')
            if image_id:
                IJ.log(u"  Image ID: {}".format(image_id))
            if image_name:
                IJ.log(u"  Image Name: {}".format(image_name))
            IJ.log("")
            
            # Stage Position
            IJ.log("STAGE POSITION:")
            stage_name = extract_attribute(xml, 'StageLabel', 'name')
            stage_x = extract_attribute(xml, 'StageLabel', 'x')
            stage_y = extract_attribute(xml, 'StageLabel', 'y')
            stage_z = extract_attribute(xml, 'StageLabel', 'z')
            stage_x_unit = extract_attribute(xml, 'StageLabel', 'xunit')
            stage_y_unit = extract_attribute(xml, 'StageLabel', 'yunit')
            stage_z_unit = extract_attribute(xml, 'StageLabel', 'zunit')
            
            if stage_name:
                IJ.log(u"  Name: {}".format(stage_name))
            if stage_x and stage_x_unit:
                IJ.log(u"  X: {} {}".format(stage_x, stage_x_unit))
            if stage_y and stage_y_unit:
                IJ.log(u"  Y: {} {}".format(stage_y, stage_y_unit))
            if stage_z and stage_z_unit:
                IJ.log(u"  Z: {} {}".format(stage_z, stage_z_unit))
            IJ.log("")
            
            # Pixels Metadata
            IJ.log("PIXELS METADATA:")
            pixels_id = extract_attribute(xml, 'Pixels', 'ID')
            size_x = extract_attribute(xml, 'Pixels', 'SizeX')
            size_y = extract_attribute(xml, 'Pixels', 'SizeY')
            size_z = extract_attribute(xml, 'Pixels', 'SizeZ')
            size_c = extract_attribute(xml, 'Pixels', 'SizeC')
            size_t = extract_attribute(xml, 'Pixels', 'SizeT')
            
            phys_size_x = extract_attribute(xml, 'Pixels', 'PhysicalSizeX')
            phys_size_y = extract_attribute(xml, 'Pixels', 'PhysicalSizeY')
            phys_size_z = extract_attribute(xml, 'Pixels', 'PhysicalSizeZ')
            phys_unit_x = extract_attribute(xml, 'Pixels', 'PhysicalSizeXUnit')
            phys_unit_y = extract_attribute(xml, 'Pixels', 'PhysicalSizeYUnit')
            phys_unit_z = extract_attribute(xml, 'Pixels', 'PhysicalSizeZUnit')
            
            pixel_type = extract_attribute(xml, 'Pixels', 'Type')
            bit_depth = extract_attribute(xml, 'Pixels', 'SignificantBits')
            
            if pixels_id:
                IJ.log(u"  Pixels ID: {}".format(pixels_id))
            if size_x and size_y:
                IJ.log(u"  Dimensions: {} x {} pixels".format(size_x, size_y))
            if size_c:
                IJ.log(u"  Channels: {}".format(size_c))
            if size_z:
                IJ.log(u"  Z-Slices: {}".format(size_z))
            if size_t:
                IJ.log(u"  Timepoints: {}".format(size_t))
            
            if phys_size_x and phys_unit_x:
                IJ.log(u"  Physical Size X: {} {}".format(phys_size_x, phys_unit_x))
            if phys_size_y and phys_unit_y:
                IJ.log(u"  Physical Size Y: {} {}".format(phys_size_y, phys_unit_y))
            if phys_size_z and phys_unit_z:
                IJ.log(u"  Physical Size Z: {} {}".format(phys_size_z, phys_unit_z))
            
            if pixel_type:
                IJ.log(u"  Pixel Type: {}".format(pixel_type))
            if bit_depth:
                IJ.log(u"  Bit Depth: {}".format(bit_depth))
            IJ.log("")
            
            # Objective Settings
            IJ.log("OBJECTIVE SETTINGS:")
            obj_id = extract_attribute(xml, 'ObjectiveSettings', 'ID')
            obj_medium = extract_attribute(xml, 'ObjectiveSettings', 'Medium')
            obj_ri = extract_attribute(xml, 'ObjectiveSettings', 'RefractiveIndex')
            
            if obj_id:
                IJ.log(u"  Objective ID: {}".format(obj_id))
            if obj_medium:
                IJ.log(u"  Medium: {}".format(obj_medium))
            if obj_ri:
                IJ.log(u"  Refractive Index: {}".format(obj_ri))
            IJ.log("")
            
            # Channel Information
            IJ.log("CHANNELS:")
            channels = extract_channel_info(xml)
            
            if not channels:
                IJ.log("  No channel information found")
            else:
                for i, ch in enumerate(channels):
                    IJ.log(u"  Channel {}:".format(i + 1))
                    if ch.get('id'):
                        IJ.log(u"    ID: {}".format(ch['id']))
                    if ch.get('name'):
                        IJ.log(u"    Name: {}".format(ch['name']))
                    if ch.get('fluor'):
                        IJ.log(u"    Fluorophore: {}".format(ch['fluor']))
                    if ch.get('color'):
                        rgb = parse_color(ch['color'])
                        IJ.log(u"    Color: {} ({})".format(ch['color'], rgb if rgb else 'N/A'))
                    if ch.get('excitation_wavelength') and ch.get('excitation_unit'):
                        IJ.log(u"    Excitation: {} {}".format(ch['excitation_wavelength'], ch['excitation_unit']))
                    if ch.get('emission_wavelength') and ch.get('emission_unit'):
                        IJ.log(u"    Emission: {} {}".format(ch['emission_wavelength'], ch['emission_unit']))
                    if ch.get('acquisition_mode'):
                        IJ.log(u"    Acquisition Mode: {}".format(ch['acquisition_mode']))
                    if ch.get('illumination_type'):
                        IJ.log(u"    Illumination: {}".format(ch['illumination_type']))
                    IJ.log("")
            
            IJ.log("")
        
        IJ.log("=" * 70)
        IJ.log("PARSING COMPLETE")
        IJ.log("=" * 70)
        
    except Exception as e:
        IJ.log("")
        try:
            IJ.log(u"FATAL ERROR: {}".format(ensure_unicode(str(e))))
        except:
            IJ.log("FATAL ERROR: <error message contains special characters>")
        try:
            import traceback
            IJ.log(traceback.format_exc())
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
