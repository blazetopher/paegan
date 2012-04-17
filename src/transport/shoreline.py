import numpy as np
import os
import math
from osgeo import ogr
from shapely import wkb, geometry
from shapely.geometry import LineString
from shapely.geometry import Point
from shapely.geometry import MultiLineString
from src.utils.asagreatcircle import AsaGreatCircle
from src.utils.asamath import AsaMath
from src.utils.asarandom import AsaRandom
from src.transport.location4d import Location4D

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

        self._type = kwargs.pop("type", "reverse")
        self._layer = source.GetLayer()
        self._geoms = []
        self.index(point=point, spatialbuffer=spatialbuffer)

    def get_geoms(self):
        return self._geoms
    geoms = property(get_geoms, None)

    def get_linestring(self):
        points = []
        for poly in self._geoms:
            plines = list(poly.exterior.coords)
            for i in xrange(0,len(plines)-1):
                points.append(Point(plines[i], plines[i+1]))

            points.append(Point(np.nan, np.nan)) # blank point needed to remove crossing of lines
        return LineString(map(lambda x: list(x.coords)[0], points))
    linestring = property(get_linestring, None)

    def index(self, **kwargs):
        """
            This queries the shapefile around a buffer of a point
            The results of this spatial query are used for shoreline detection.

            Using the entire shapefile without the spatial query takes over
            30 times the time with world land polygons.

        """

        point = kwargs.pop("point", None)
        spatialbuffer = kwargs.pop("spatialbuffer", 2)

        self._layer.SetSpatialFilter(None)
        self._spatial_query_object = None
        
        if point:
            self._spatial_query_object = point.buffer(spatialbuffer)
            poly = ogr.CreateGeometryFromWkt(self._spatial_query_object.wkt)
            self._layer.SetSpatialFilter(poly)
            poly.Destroy()

        self._geoms = []
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
            self.index(point=Point(ls.coords[0]), spatialbuffer=2)

        for element in self._geoms:
            inter = ls.intersection(element)
            if inter:
                # Test if starging on land
                spoint = Point(ls.coords[0])
                epoint = Point(ls.coords[-1])
                if spoint.within(element):
                    raise Exception('Starting point on land')
                else:
                    # Return the first point in the linestring, and the linestring that it hit
                    if isinstance(inter, MultiLineString):
                        inter = inter.geoms[0]
                        
                    
                    eache = None
                    plines = list(element.exterior.coords)
                    for i in xrange(0,len(plines)-1):
                        eache = LineString([plines[i], plines[i+1]])
                        inter2 = ls.intersection(eache)
                        if inter2:
                            break

                    return {'point':Point(inter.coords[0]), 'feature': eache}

    def react(self, **kwargs):
        """
            Bounce off of a shoreline
            feature = Linestring of two points, being the line segment the particle hit.
            angle = decimal degrees from 0 (x-axis), couter-clockwise (math style)
        """
        if self._type == "bounce":
            print "This shoreline type is NOT SUPPORTED and it broken"
            return self.__bounce(**kwargs)
        elif self._type == "reverse":
            return self.__reverse(**kwargs)
        else:
            print "Not reacting to shoreline (sticky with inifinite concentration)"

    def __bounce(self, **kwargs):
        """
            Bounce off of the shoreline.

            NOTE: This does not work, but left here for future implementation

            feature = Linestring of two points, being the line segment the particle hit.
            angle = decimal degrees from 0 (x-axis), couter-clockwise (math style)
        """
        start_point = kwargs.pop('start_point')
        hit_point = kwargs.pop('hit_point')
        end_point = kwargs.pop('end_point')
        feature = kwargs.pop('feature')
        distance = kwargs.pop('distance')
        angle = kwargs.pop('angle')

        # Figure out the angle of the shoreline here (beta)
        points_in_shore = map(lambda x: Point(x), list(feature.coords))
        points_in_shore = sorted(points_in_shore, key=lambda x: x.x)

        # The point on the left (least longitude is always the first Point)
        first_shore = points_in_shore[0]
        last_shore = points_in_shore[-1]

        shoreline_x = abs(abs(first_shore.x) - abs(last_shore.x))
        shoreline_y = abs(abs(first_shore.y) - abs(last_shore.y))
        beta = math.degrees(math.atan(shoreline_x / shoreline_y))

        theta = 90 - angle - beta
        bounce_azimuth = AsaMath.math_angle_to_azimuth(angle=2 * theta + angle)

        print "Beta:           " + str(beta)
        print "Incoming Angle: " + str(angle)
        print "ShorelineAngle: " + str(theta + angle)
        print "Bounce Azimuth: " + str(bounce_azimuth)
        print "Bounce Angle:   " + str(AsaMath.azimuth_to_math_angle(azimuth=bounce_azimuth))

        after_distance = distance - AsaGreatCircle.great_distance(start_point=start_point, end_point=hit_point)['distance']
        
        new_point = AsaGreatCircle.great_circle(distance=after_distance, azimuth=bounce_azimuth, start_point=hit_point)
        return Location4D(latitude=new_point['latitude'], longitude=new_point['longitude'], depth=start_point.depth)

    def __reverse(self, **kwargs):
        """
            Reverse particle just off of the shore in the direction that it came in.
            Adds a slight random factor to the distance and angle it is reversed in.
        """
        start_point = kwargs.pop('start_point')
        hit_point = kwargs.pop('hit_point')
        distance = kwargs.pop('distance')
        azimuth = kwargs.pop('azimuth')
        reverse_azimuth = kwargs.pop('reverse_azimuth')

        distance_reversed = 0.01 * AsaGreatCircle.great_distance(start_point=start_point, end_point=hit_point)['distance']

        #print "Incoming Azimuth: " + str(azimuth)
        #print "Reverse Azimuth: " + str(reverse_azimuth)
        #print "Distance Reversed:" + str(distance_reversed)

        new_point = AsaGreatCircle.great_circle(distance=distance_reversed, azimuth=reverse_azimuth, start_point=hit_point)
        return Location4D(latitude=new_point['latitude'], longitude=new_point['longitude'], depth=start_point.depth)