import os, json, hashlib

from PySide.QtCore import QAbstractListModel, QModelIndex, Qt, Signal
from PySide.QtGui import QIcon

class ImageModel(QAbstractListModel):
    TagRole = 0x101
    #imageAdded = Signal(QModelIndex)
    imageAdded = Signal(int)
    
    def __init__(self, parent=None, troll_dir=None):
        QAbstractListModel.__init__(self, parent)

        # load data from disk
        default = os.path.expanduser(os.path.join("~", ".trollbox"))
        self.troll_dir = troll_dir if troll_dir else default
        if not os.path.exists(self.troll_dir):
            os.mkdir(self.troll_dir)
        self.metadata_path = os.path.join(self.troll_dir, "metadata.json")
        if os.path.exists(self.metadata_path):
            metadata = json.load(open(self.metadata_path, "rt"))
        else:
            metadata = []

        self.images = []
        for url, tags, local_path in metadata:
            abs_path = os.path.join(self.troll_dir, local_path)
            self.images.append((url, tags, local_path, abs_path, QIcon(abs_path)))

    def image_dir(self):
        return os.path.join(self.troll_dir, "images")

    def image_path(self, url):
        print "path is", os.path.join(self.image_dir(), hashlib.md5(url).hexdigest())
        return os.path.join(self.image_dir(), hashlib.md5(url).hexdigest())

    def rowCount(self, parent_qmi=None):
        if parent_qmi != None:
            i = parent_qmi.row()
            if i == -1: # invalid index
                i = 0
        else:
            i = 0
        return len(self.images[i:])

    def addImage(self, url, tags, local_path):
        '''
        Adds an image with url and tags that has already been downloaded
        to local_path (relative to troll_dir) to the model.
        '''
        print "addImage url", url 

        # set i to index of item in self.images with url, if it exists
        found = False
        for i in range(0, len(self.images)):
            if self.images[i][0] == url:
                print "%s exists at %d/%d" % (url, i, len(self.images))
                found = True
                break

        abs_path = os.path.join(self.troll_dir, local_path)
        icon = QIcon(abs_path)

        if not found:
            # if this is a new image, append it
            ct = self.rowCount()
            self.beginInsertRows(self.index(ct), ct, ct)
            print "new image"
            self.images.append((url, tags, local_path, abs_path, icon))
            self.save()
            self.endInsertRows()
        else:
            # otherwise replace the old image and delete its disk file
            print "replacing image at %d" % i
            if abs_path != self.images[i][3]:
                os.remove(self.images[i][3])
            self.images[i] = (url, tags, local_path, abs_path, icon)
            self.save()
            qmi = self.index(i)
            self.dataChanged.emit(qmi, qmi)
        
        self.imageAdded.emit(i)

    def save(self):
        json.dump([t[:3] for t in self.images], open(self.metadata_path, "wt"))

    def data(self, qmi, role=Qt.DisplayRole):
        """
        Returns the image data for role stored at index
        """
        index = qmi.row()
        url, tags, local_path, abs_path, icon = self.images[index]
        if role == Qt.DecorationRole:
            return icon
        elif role == Qt.DisplayRole:
            return url
        elif role == self.TagRole:
            return tags

    def deleteImage(self, url):
        for i in range(0, len(self.images)):
            if self.images[i][0] == url:
                print "found image at %d: %s" % (i, self.images[i])
                break
        qmi = self.index(i, i)
        self.beginRemoveRows(qmi, i, i)
        _, _, local_path, abs_path, _ = self.images[i]
        del self.images[i]
        self.save()
        try:
            os.remove(abs_path)
        except OSError as e:
            print str(e)
        self.endRemoveRows()

    def setData(self, qmi, value, role=Qt.DisplayRole):
        """
        Sets the role data for image stored at index to value
        """
        index = qmi.row()
        url, tags, local_path, abs_path, icon = self.images[index]
        print "value", value
        if role == Qt.DisplayRole:
            url = value
        elif role == self.TagRole:
            tags = value
        self.images[index] = url, tags, local_path, abs_path, icon
        self.save()
        self.dataChanged.emit(qmi, qmi)
        return True
