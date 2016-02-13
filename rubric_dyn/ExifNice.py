#!/usr/bin/python
#
#

import os
import sys

import PIL.Image
import PIL.ExifTags

class ExifNiceStr:

    def __init__(self, img_file):

        if not os.path.isfile(img_file):
            print("Warning: ExifNice: image file not found:", img_file)
            self.display_str = None
            return

        self.img = PIL.Image.open(img_file)
        #exif_data = img._getexif()

        if not self.img._getexif():
            print("Warning: ExifNice: image has no EXIF data", img_file)
            self.display_str = None
            return

        self.exif = {
            PIL.ExifTags.TAGS[k]: v
            for k, v in self.img._getexif().items()
            if k in PIL.ExifTags.TAGS
        }

        if self.exif['FocalLength'][0] != 0:
            self.focal_length = str(self.exif['FocalLength'][0]) + "mm"
        else:
            self.focal_length = "-"
        self.iso = "ISO " + str(self.exif['ISOSpeedRatings'])
        self.software = self.exif['Software']
        self.datetime = self.exif['DateTimeOriginal']
        self.make = self.exif['Make'].strip()
        self.model = self.exif['Model'].strip()

        self.set_exposure_time()
        self.set_aperture()

        self.display_str = self.exposure_time + ", " + \
                           self.aperture + ", " + self.iso + ", " + \
                           self.focal_length + "\n" + \
                           self.datetime + "\n" + \
                           self.make + " " + self.model + "\n" + \
                           self.software

    def set_exposure_time(self):
        exp_time_num = self.exif['ExposureTime'][0]
        exp_time_den = self.exif['ExposureTime'][1]

        if exp_time_num < exp_time_den:
            self.exposure_time = str(exp_time_num) + "/" + str(exp_time_den) + "s"
        else:
            self.exposure_time = str(exp_time_num/exp_time_den) + "s"

    def set_aperture(self):
        if self.exif['FNumber'][0] != 0:
            aper_num = self.exif['FNumber'][0]
            aper_den = self.exif['FNumber'][1]

            self.aperture = "f/"+str(aper_num/aper_den)
        else:
            self.aperture = "-"
