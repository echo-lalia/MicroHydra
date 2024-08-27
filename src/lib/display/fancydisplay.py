"""
This module provides the FancyDisplay class, which subclasses the Display class
This module is intended to provide extra graphics drawing for apps who need it,
while keeping the regular Display class (relatively) lightweight.
"""

from . import Display
import array
from math import sin, cos, floor



def ease_in_out_sine(x):
    return -(cos(pi * x) - 1) / 2


def ease_in_out_circ(x):
    if x < 0.5:
        return (1 - sqrt(1 - pow(2 * x, 2))) / 2
    else:
        return (sqrt(1 - pow(-2 * x + 2, 2)) + 1) / 2



class FancyDisplay(Display):
    

    @micropython.viper
    @staticmethod
    def scale_poly(points, scale_pct:int):
        """
        Resize all the points in the array. Returns None.
        """
        point_ptr = ptr16(points)
        points_len = int(len(points))
        
        idx = 0
        while idx < points_len:
            # scale using integer math for speed
            point_ptr[idx] = (point_ptr[idx] * scale_pct) // 100
            idx += 1


    @staticmethod
    def rotate_points(points, angle=0, center_x=0, center_y=0):
        """
        Rotate all the points in the array, return resulting array.
        """
        if angle:
            cos_a = cos(angle)
            sin_a = sin(angle)
            rotated = array.array('h')
            for i in range(0,len(points),2):
                rotated.append(
                    center_x + floor((points[i] - center_x) * cos_a - (points[i+1] - center_y) * sin_a)
                )
                rotated.append(
                    center_y + floor((points[i] - center_x) * sin_a + (points[i+1] - center_y) * cos_a)    
                )
            return rotated
        else:
            return points


    @staticmethod
    def warp_points(points, tilt_center=0.5, ease=True, focus_center_x=True, smallest=None, largest=None):
        """
        Skew points on the y axis. Can create a faux 3d looking effect, or a kinda jelly-like effect.
        """
        if tilt_center == 0.5 and not ease:
            return points
        
        if smallest == None:
            smallest = min(points)
        if largest == None:
            largest = max(points)

        midpoint = (smallest + largest) / 2
        #shift numbers so that the smallest point = 0
        adj_largest = largest - smallest
        adj_midpoint = adj_largest / 2
        new_adj_midpoint = adj_largest * tilt_center
        
        #shift largest down, (along with newmidpoint), so that newmidpoint = 0
        #this is done so that we can interpolate between 0 and this number, then re-add the midpoint
        temp_largest = adj_largest - new_adj_midpoint
        
        #iterate over each point
        # if point is less than midpoint, interpolate point between 0 and new midpoint
        # if point is greater than midpoint, interpolate between new midpoint and largest
        # then add the smallest value back to the result, to shift the result into the original range
        #for index, point in enumerate(points):
        for index in range(1,len(points),2):
            point=points[index]
            
            if focus_center_x:
                #if focus_center_x, then apply the effect more strongly to points nearer to the center x
                adj_x_val = points[index-1] - smallest
                x_center_factor = abs(adj_x_val - adj_midpoint ) / adj_midpoint
                x_center_factor = ease_in_out_circ(x_center_factor)
            
            if point < midpoint:
                #find fac between 0 and adj_midpoint,
                #then interpolate between 0 and new midpoint
                adj_point = point - smallest
                factor = adj_point / adj_midpoint
                
                #fancy easing function to round out the shape more
                factor = ease_in_out_sine(factor)
                
                if focus_center_x:
                    points[index] = floor(
                        mix(
                            (new_adj_midpoint * factor) + smallest, points[index], x_center_factor
                            ))
                else:
                    points[index] = floor((new_adj_midpoint * factor) + smallest)


            else: # point >= midpoint:
                #find fac between adj_midpoint and adj_largest,
                #then interpolate between new midpoint and largest
                adj_point = point - smallest
                factor = (adj_point - adj_midpoint) / (adj_largest - adj_midpoint)
                
                #fancy easing function to round out the shape more
                factor = ease_in_out_sine(factor)
                
                if focus_center_x:
                    points[index] = floor(
                        mix(
                            (temp_largest * factor) + new_adj_midpoint + smallest,points[index],x_center_factor
                            )
                        )
                else:
                    points[index] = floor((temp_largest * factor) + new_adj_midpoint + smallest)       
                
        return points


    def polygon(self, points, x, y, color, angle=0, center_x=None, center_y=None, scale=1.0, warp=None, fill=False):
        """
        Draw a polygon on the display.

        Args:
            points (array('h')): Array of points to draw.
            x (int): X-coordinate of the polygon's position.
            y (int): Y-coordinate of the polygon's position.
            color (int): 565 encoded color.
            angle (float): Rotation angle in radians (default: 0).
            center_x (int): X-coordinate of the rotation center (default: 0).
            center_y (int): Y-coordinate of the rotation center (default: 0).
        """
        
        # super().polygon wrapper
        if angle == 0 and scale == 1.0 and warp == None:
            super().polygon(points, x, y, color, fill=fill)
        
        #complex polygon
        else:
            #clone array so we don't modify original
            points = array.array('h', points)
            
            #scale
            if scale != 1.0:
                # (convert scale to integer percentage for speed)
                self.scale_poly(points, int(scale * 100))

            #rotate
            if angle != 0:
                if center_x == None:
                    center_x = max(points) // 2
                if center_y == None:
                    center_y = max(points) // 2
                points = self.rotate_points(points, angle, center_x, center_y)
                
            if warp != None:
                self.warp_points(points, warp)
            
            super().polygon(points, x, y, color, fill=fill)

