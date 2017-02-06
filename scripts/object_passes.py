# PV Render Queue Cinema 4D Plugin
# Copyright (C) 2015  Niklas Rosenstein
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
This script creates a new job for each object selected in the Object
Manager and assign its a white luminance material while the rest of the
scene will be black. Children of the selected object will be included.
"""

__author__ = 'Niklas Rosenstein <rosensteinniklas@gmail.com>'
__version__ = '1.0.0'

import c4d
import nr.pvrq2
import re
import string


def safe_filename(filename):
    charset = string.letters + string.digits + ' ._-'
    filename = ''.join(x if x in charset else '_' for x in filename)
    return re.sub('_+', '_', filename)


class ObjectPassJob(nr.pvrq2.RenderJob):

    name = None

    def __init__(self, index, doc, obj, white_mat, black_mat):
        super(ObjectPassJob, self).__init__()
        self.rdata = doc.GetActiveRenderData()
        self.doc = doc
        self.obj = obj
        self.scene_name = doc.GetDocumentName()
        self.name = obj.GetName()
        self.white_mat = white_mat
        self.black_mat = black_mat

        path = self.rdata[c4d.RDATA_PATH]
        if not self.rdata[c4d.RDATA_SAVEIMAGE] or not path:
            self.path = None
        else:
            self.path = path + '_{0:0>4}_{1}'.format(
                index, safe_filename(self.name))

    def get_job_details(self):
        details = super(ObjectPassJob, self).get_job_details()
        details.update({
            'scene_name': self.scene_name,
            'object': self.name,
            'save_path': self.path})
        return details

    def get_scene(self):
        if self.path:
            self.rdata[c4d.RDATA_PATH] = self.path
        for obj in iter_objects(self.obj):
            tex = obj.GetTag(c4d.Ttexture)
            tex[c4d.TEXTURETAG_MATERIAL] = self.white_mat
        return self.doc

    def completed(self):
        for obj in iter_objects(self.obj):
            tex = obj.GetTag(c4d.Ttexture)
            tex[c4d.TEXTURETAG_MATERIAL] = self.black_mat
        self.doc = None
        self.obj = None


def iter_objects(node):
    if isinstance(node, c4d.documents.BaseDocument):
        for obj in node.GetObjects():
            for sub in iter_objects(obj):
                yield sub
    else:
        yield node
        for child in node.GetChildren():
            for sub in iter_objects(child):
                yield sub


def preprocess(doc):
    '''
    Removes the Global Illumination and Ambient Occlusion post effects
    and disabled various render options to speed up rendering of the
    object passes.
    '''

    rdata = doc.GetActiveRenderData()
    vp = rdata.GetFirstVideoPost()
    while vp:
        next_vp = vp.GetNext()
        if vp.GetType() in (c4d.VPglobalillumination, c4d.VPambientocclusion):
            vp.Remove()
        vp = next_vp
    rdata[c4d.RDATA_OPTION_TRANSPARENCY] = False
    rdata[c4d.RDATA_OPTION_REFRACTION] = False
    rdata[c4d.RDATA_OPTION_REFLECTION] = False
    rdata[c4d.RDATA_OPTION_SHADOW] = False
    rdata[c4d.RDATA_ENABLEBLURRY] = False
    rdata[c4d.RDATA_AUTOLIGHT] = False
    rdata[c4d.RDATA_TEXTURES] = False
    rdata[c4d.RDATA_VOLUMETRICLIGHTING] = False
    rdata[c4d.RDATA_POSTEFFECTS_ENABLE] = False
    rdata[c4d.RDATA_SSS] = False
    rdata[c4d.RDATA_ANTIALIASING] = c4d.RDATA_ANTIALIASING_GEOMETRY


def main():
    global doc
    doc = doc.GetClone(c4d.COPYFLAGS_0)
    objects = doc.GetActiveObjects(c4d.GETACTIVEOBJECTFLAGS_CHILDREN)
    if not objects:
        c4d.gui.MessageDialog('no objects selected')
        return

    preprocess(doc)
    black_mat = c4d.BaseMaterial(c4d.Mmaterial)
    black_mat[c4d.MATERIAL_USE_COLOR] = False
    black_mat[c4d.MATERIAL_USE_SPECULAR] = False

    white_mat = black_mat.GetClone(c4d.COPYFLAGS_0)
    white_mat[c4d.MATERIAL_USE_LUMINANCE] = True

    for mat in doc.GetMaterials():
        mat.Remove()
    for obj in iter_objects(doc):
        for tag in obj.GetTags():
            if tag.CheckType(c4d.Ttexture):
                tag.Remove()
        tag = obj.MakeTag(c4d.Ttexture)
        tag[c4d.TEXTURETAG_MATERIAL] = black_mat

    doc.InsertMaterial(white_mat)
    doc.InsertMaterial(black_mat)

    name = '{0} - Object Passes'.format(doc.GetDocumentName())
    folder = nr.pvrq2.Folder(name)
    for index, obj in enumerate(objects):
        folder.append(ObjectPassJob(index, doc, obj, white_mat, black_mat))
    nr.pvrq2.root.append(folder)
    c4d.EventAdd()


if __name__ == '__main__':
    main()
