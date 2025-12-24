# OME-XML Metadata Accessor v1.0
# Reusable module for extracting OME-XML metadata from Bio-Formats readers
# Built on findings from xml_parser.py and xml_debug.py
#
# Usage:
#   from ome_metadata_accessor import OMEMetadataAccessor
#   accessor = OMEMetadataAccessor(reader)
#   pixel_size = accessor.get_physical_size_x(series=0)
#   channel_color = accessor.get_channel_color(series=0, channel=0)

from loci.formats.meta import MetadataTools
from ij import IJ
import re

def ensure_unicode(s):
    """Convert any string to unicode safely (Jython 2.7 compatible)"""
    if s is None:
        return None
    if isinstance(s, unicode):
        return s
    # Java Strings are already unicode
    if hasattr(s, 'toString') and not isinstance(s, (str, bytes)):
        return unicode(s.toString())
    # Jython str with UTF-8 bytes - use decode method to avoid ASCII pre-check
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

class OMEMetadataAccessor(object):
    """
    Clean API for accessing OME-XML metadata from Bio-Formats ImageReader.
    
    All methods are unicode-safe and handle missing values gracefully.
    """
    
    def __init__(self, reader):
        """
        Initialize accessor with Bio-Formats reader.
        
        Args:
            reader: loci.formats.ImageReader instance (must be opened with setId)
        """
        self.reader = reader
        
        # Create metadata store if not already attached
        try:
            self.metadata = reader.getMetadataStore()
            if not self.metadata:
                self.metadata = MetadataTools.createOMEXMLMetadata()
                # Need to create new reader with metadata store
                from loci.formats import ImageReader
                old_id = reader.getCurrentFile()
                reader.close()
                reader = ImageReader()
                reader.setMetadataStore(self.metadata)
                reader.setId(old_id)
                self.reader = reader
                self.metadata = reader.getMetadataStore()
        except:
            self.metadata = None
        
        # Cache OME-XML string for regex parsing
        self._ome_xml = None
        try:
            if self.metadata:
                xml_str = self.metadata.dumpXML()
                self._ome_xml = ensure_unicode(xml_str)
        except:
            pass
    
    def get_physical_size_x(self, series=0):
        """Get physical pixel size X in micrometers"""
        try:
            # Try metadata store API first
            if self.metadata:
                px = self.metadata.getPixelsPhysicalSizeX(series)
                if px and hasattr(px, 'value'):
                    val = float(px.value())
                    # Convert to micrometers if needed
                    unit = None
                    try:
                        unit = str(px.unit())
                    except:
                        pass
                    
                    if unit:
                        unit_lower = unit.lower()
                        if 'nm' in unit_lower or 'nanometer' in unit_lower:
                            val = val / 1000.0
                        elif 'mm' in unit_lower or 'millimeter' in unit_lower:
                            val = val * 1000.0
                        elif 'm' in unit_lower and 'µ' not in unit_lower and 'micro' not in unit_lower:
                            val = val * 1000000.0
                    
                    if 0.01 <= val <= 50.0:  # Sanity check
                        return val
        except:
            pass
        
        # Fallback: regex parse OME-XML
        if self._ome_xml:
            try:
                m = re.search(r'PhysicalSizeX\s*=\s*"([^"]+)"', self._ome_xml, re.IGNORECASE)
                if m:
                    val = float(m.group(1))
                    if 0.01 <= val <= 50.0:
                        return val
            except:
                pass
        
        return None
    
    def get_physical_size_y(self, series=0):
        """Get physical pixel size Y in micrometers"""
        try:
            if self.metadata:
                px = self.metadata.getPixelsPhysicalSizeY(series)
                if px and hasattr(px, 'value'):
                    val = float(px.value())
                    unit = None
                    try:
                        unit = str(px.unit())
                    except:
                        pass
                    
                    if unit:
                        unit_lower = unit.lower()
                        if 'nm' in unit_lower or 'nanometer' in unit_lower:
                            val = val / 1000.0
                        elif 'mm' in unit_lower or 'millimeter' in unit_lower:
                            val = val * 1000.0
                        elif 'm' in unit_lower and 'µ' not in unit_lower and 'micro' not in unit_lower:
                            val = val * 1000000.0
                    
                    if 0.01 <= val <= 50.0:
                        return val
        except:
            pass
        
        if self._ome_xml:
            try:
                m = re.search(r'PhysicalSizeY\s*=\s*"([^"]+)"', self._ome_xml, re.IGNORECASE)
                if m:
                    val = float(m.group(1))
                    if 0.01 <= val <= 50.0:
                        return val
            except:
                pass
        
        return None
    
    def get_channel_count(self, series=0):
        """Get number of channels"""
        try:
            if self.metadata:
                return self.metadata.getChannelCount(series)
        except:
            pass
        
        try:
            return self.reader.getSizeC()
        except:
            pass
        
        return 0
    
    def get_channel_name(self, series=0, channel=0):
        """Get channel name"""
        try:
            if self.metadata:
                name = self.metadata.getChannelName(series, channel)
                if name:
                    return ensure_unicode(name)
        except:
            pass
        
        if self._ome_xml:
            try:
                # Find channel by index
                channels = re.findall(r'<Channel\b([^>]*)>', self._ome_xml, re.IGNORECASE)
                if channel < len(channels):
                    m = re.search(r'Name\s*=\s*"([^"]+)"', channels[channel], re.IGNORECASE)
                    if m:
                        return ensure_unicode(m.group(1))
            except:
                pass
        
        return u"Channel {}".format(channel + 1)
    
    def get_channel_color(self, series=0, channel=0):
        """
        Get channel color as RGB tuple (r, g, b).
        Handles signed integer colors from OME-XML.
        """
        try:
            if self.metadata:
                color_obj = self.metadata.getChannelColor(series, channel)
                if color_obj:
                    color_int = color_obj.getValue()
                    # Convert signed to unsigned
                    color_unsigned = int(color_int) & 0xFFFFFFFF
                    # Extract RGB (RGBA format: 0xRRGGBBAA, but A is usually FF)
                    r = (color_unsigned >> 24) & 0xFF
                    g = (color_unsigned >> 16) & 0xFF
                    b = (color_unsigned >> 8) & 0xFF
                    return (r, g, b)
        except:
            pass
        
        # Fallback: regex parse OME-XML
        if self._ome_xml:
            try:
                channels = re.findall(r'<Channel\b([^>]*)>', self._ome_xml, re.IGNORECASE)
                if channel < len(channels):
                    m = re.search(r'Color\s*=\s*"([^"]+)"', channels[channel], re.IGNORECASE)
                    if m:
                        color_int = int(m.group(1))
                        color_unsigned = color_int & 0xFFFFFFFF
                        # RGBA format
                        r = (color_unsigned >> 24) & 0xFF
                        g = (color_unsigned >> 16) & 0xFF
                        b = (color_unsigned >> 8) & 0xFF
                        return (r, g, b)
            except:
                pass
        
        return None
    
    def get_channel_fluor(self, series=0, channel=0):
        """Get fluorophore name"""
        try:
            if self.metadata:
                fluor = self.metadata.getChannelFluor(series, channel)
                if fluor:
                    return ensure_unicode(fluor)
        except:
            pass
        
        if self._ome_xml:
            try:
                channels = re.findall(r'<Channel\b([^>]*)>', self._ome_xml, re.IGNORECASE)
                if channel < len(channels):
                    m = re.search(r'Fluor\s*=\s*"([^"]+)"', channels[channel], re.IGNORECASE)
                    if m:
                        return ensure_unicode(m.group(1))
            except:
                pass
        
        return None
    
    def get_image_name(self, series=0):
        """Get image name"""
        try:
            if self.metadata:
                name = self.metadata.getImageName(series)
                if name:
                    return ensure_unicode(name)
        except:
            pass
        
        return None
