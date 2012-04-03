import os
from osgeo import ogr
from shapely import wkb, geometry
from shapely.geometry import LineString
from shapely.geometry import Point
from shapely.geometry import MultiLineString

class Shoreline(object):
    def __init__(self, **kwargs):
        """
            Optional named arguments: 
            * file (local path to OGC complient file)

            MUST BE land polygons!!
        """

        if "file" in kwargs:
            self._file = os.path.normpath(kwargs.pop('file'))
        else:
            self._file = os.path.normpath(os.path.join(__file__,"../../resources/shoreline/global/10m_land.shp"))

        point = kwargs.pop("point", None)
        spatialbuffer = kwargs.pop("buffer", 2)

        source = ogr.Open(self._file)
        if not source:
            raise Exception('Could not load {}'.format(self._file))

        self._layer = source.GetLayer()
        self._geoms = []
        self.index(point=point, spatialbuffer=spatialbuffer)

    def index(self, **kwargs):
        """
            This queries the shapefile around a buffer of a point
            The results of this spatial query are used for shoreline detection.

            Using the entire shapefile without the spatial query takes over
            30 times the time with world land polygons.

        """
        point = kwargs.pop("point", None)
        spatialbuffer = kwargs.pop("spatialbuffer", 2)

        self._spatial_query_object = None
        self._layer.SetSpatialFilter( self._spatial_query_object )

        if point:
            self._spatial_query_object = point.buffer(spatialbuffer)
            poly = ogr.CreateGeometryFromWkt( self._spatial_query_object.wkt )
            self._layer.SetSpatialFilter(poly)
            poly.Destroy()

        for element in self._layer:
            self._geoms.append(wkb.loads(element.GetGeometryRef().ExportToWkb()))

    def intersect(self, **kwargs):
        """
            Intersect a Line or Point Collection and the Shoreline

            Returns the point of intersection along the coastline
            Should also return a linestring buffer around the interseciton point
            so we can calculate the direction to bounce a particle.
        """
        ls = None
        if "linestring" in kwargs:
            ls = kwargs.pop('linestring')
        elif "start_point" and "end_point" in kwargs:
            ls = LineString(list(kwargs.pop('start_point').coords) + list(kwargs.pop('end_point').coords))
        else:
            raise TypeError( "must provide a LineString geometry object or (2) Point geometry objects" )

        inter = False

        # If the current point lies outside of our current shapefile index,
        # re-query the shapefile in a buffer around this point
        if self._spatial_query_object and not ls.within(self._spatial_query_object):
            self.index(point=Point(ls.coords[0]), buffer=2)

        for element in self._geoms:
            inter = ls.intersection(element)
            if inter:
                # Test if starging on land
                spoint = Point(ls.coords[0])
                epoint = Point(ls.coords[-1])
                if spoint.within(element):
                    raise Exception('Starting point on land')
                else:
                    # Return the first point in the linestring
                    if isinstance(inter, MultiLineString):
                        inter = inter.geoms[0]
                        
                    return Point(inter.coords[0])

                    #return inter.geoms

        #return {'intersection_point': inter_point, 'intersection_line': inter_line, 'message' }