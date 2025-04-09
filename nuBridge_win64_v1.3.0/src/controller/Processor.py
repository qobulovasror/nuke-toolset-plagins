#!/usr/bin/env python
'''
The Processor module provides the frame work for the Processor class
to process files after they have been downloaded
'''
import sys
import common
import logging
import os
import posixpath
import shutil

#from PySide import QtCore
from Qt import QtCore

PY3 = sys.version_info[0] == 3
if PY3:
    unicode = str
    
LOGGER = logging.getLogger('Nukepedia.Processor')

class ProcessorBase(QtCore.QObject):
    '''
    Processor to handle downloaded files
    self.toolItem is set by the installer to provide info about the downloaded tool and looks like this:
    {'activeFileData':
         {'platform': '111000000',
         'version': '1.5',
         'id': 96},
     'minorVersion': 0,
     'majorVersion': 0,
    'shortDesc': u'mask based warper with transform controls',
    'downloadInfo': {'filename': u'ITransform.gizmo',
                    'downloadPath': u'/Users/frank/Nukepedia/downloaded/ITransform_96/1.5/ITransform.gizmo',
                    'version': 1.5,
                    'localPath': '',
                    'platform': '111000000'},
     'category': u'transform',
     'container': u'gizmos',
     'author': u'Frank Rueter',
     'fileType': u'gizmo',
      'category': u'transform',
      'altCount': 6,
      'updateAvailable': '',
      'containerid': 13,
      'toolType': u'gizmos',
      'downloads': 1877,
      'licenseagree': 0,
      'submitdate': time.struct_time(tm_year=2016, tm_mon=7, tm_mday=26, tm_hour=20, tm_min=31, tm_sec=17, tm_wday=1, tm_yday=208, tm_isdst=-1),
      'fileauthor': u'Frank Rueter',
      'nukeVersions': (10.0, 9.0, 8.0, 7.1, 7.0, 6.3, 6.2, 6.1, 6.0),
      'filetitle': u'ITransform',
      'filetype': u'gizmo',
      'id': 96,
      'filedate': time.struct_time(tm_year=2016, tm_mon=7, tm_mday=26, tm_hour=20, tm_min=31, tm_sec=16, tm_wday=1, tm_yday=208, tm_isdst=-1),
      'smalldesc': u'mask based warper with transform controls'},
      'nukeVersions': (10.0, 9.0, 8.0, 7.1, 7.0, 6.3, 6.2, 6.1, 6.0),
      'id_': 96,
      'toolType': u'gizmos',
      'downloads': 1877,
      'fileName': u'ITransform.gizmo',
      'isActive': False,
      'containerid': 13,
      'title': u'ITransform',
    '''
    newFilePathsReceived = QtCore.Signal(list)
    newPluginPathsReceived = QtCore.Signal(list)
    newMenuInfo = QtCore.Signal(list)

    def __init__(self, repoLocation, parent=None):
        super(ProcessorBase, self).__init__(parent)
        self.repoLocation = repoLocation

    def process(self):
        '''
        Process the downloaded file, e.g. unzip, un-rar etc.
        Emit signal for list of files that should be removed when the tool is uninstyalled.
        Emit path that shoudl be added to NUke's plugin path in order for the new tool to be loaded
        '''
        raise NotImplemented

    def registerFilePaths(self, pathList):
        '''
        Emit signal with files that need to be recorded in the local database
        so the tool can lbe uninstalled properly
        '''

        self.newFilePathsReceived.emit(pathList)

    def registerMenuCommands(self, infoList, title=None):
        '''Emit signal with the required info to create a menu item in the Nukepedia menu'''

        self.newMenuInfo.emit(infoList)
        
    def registerPluginPaths(self, paths):
        '''
        Emit signal with new plugin path that needs to be added to the init.
        paths - string or list of strings representing one or more plugin paths for Nuke to load
        '''

        assert isinstance(paths, (str, unicode, list)), 'registered plugin paths must be string, unicode or a list of strings/unicodes'
        if isinstance(paths, (str, unicode)):
            paths = [paths]

        self.newPluginPathsReceived.emit(paths)

    def setToolItem(self, toolItemProxy):
        '''
        By default this method is conneted to the Installer and receives a ToolItemProxy
        which carries all available information about the tool including it's local path after download.
        '''
        LOGGER.debug('Processor set to {}'.format(toolItemProxy))
        self.toolItem = toolItemProxy
        self.process()

    
class Processor(ProcessorBase):

    def __init__(self, parent=None):
        super(Processor, self).__init__(parent)
        self.fileListForUninstall = []

    def copyFilesToPluginPath(self, downloadPath):
        '''
        Copies the processed files to the plugin path where Nuke can pick them up
        '''
        self.createInstallDir()
        LOGGER.debug('copying {0} to  {1}'.format(downloadPath, self.pluginPath))
        # sanitise gizmo name so there are no dots in it (Nuke spits the dummy otherwise)
        # add version to gizmo name to ensure each version is a uniqe class in Nuke
        # this should help to avoid wrong versions ot tool sbeing picked up when an older script is brought back online
        baseName, ext = os.path.splitext(os.path.basename(downloadPath))       
        fileName = (baseName + '_' + self.toolItem.version).replace('.', '_') + ext

        # avoiding os.path.join to keep paths in DB OS indendent
        filePath = posixpath.join(self.pluginPath, fileName)
       
        shutil.copy2(downloadPath, filePath)
        return filePath

    def createInstallDir(self):
        '''
        Return the full directory the respective tool is meant to be copied to.
        If the directory doesn't exist, create it here.
        '''
 
        # avoiding os.path.join to keep paths in DB OS indendent
        self.pluginPath = posixpath.join(self.repoLocation,
                                       self.toolItem.toolType,
                                       '{}_{}'.format(self.toolItem.title, self.toolItem.id_),
                                       self.toolItem.version)

        if not os.path.isdir(self.pluginPath):
            os.makedirs(self.pluginPath)

    def process(self):
        '''
        Process downloaded file (e.g. file could be a zip file) and emit signals to inform nuBridge of the new plugin path
        as well as extracted files (in case we need to keep track of them for later uninstallation.
        The default processor should do nothing (for files that can be copied directly to the plugin path to be useful).
        '''

        fileExt = os.path.splitext(self.toolItem.fileName)[-1]
        # the file paths are stored relative to the repository location, so join the paths
        # to get a valid absolute path
        # avoiding os.path.join to keep paths in DB OS indendent       
        dlPath = posixpath.join(self.repoLocation, self.toolItem.downloadInfo['downloadPath'])
        
        if fileExt in ('.gizmo', '.nk'):
            # the downloaded file is a single gizmo file or single nk file.
            # Those files only need to be copied to the plugin path in order to make them work
            LOGGER.debug('processing (copying) {0}'.format(dlPath))
            filePath = self.copyFilesToPluginPath(dlPath)
            self.fileListForUninstall.append(filePath)
            pluginPath = os.path.dirname(filePath)

            ########################################################
            # register new file paths so the uninstaller can do it's job properly
            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            # NOTE:   any files and directories in the registered list will be deleted
            #         if/when the user choses to uninstall the tool via the local tool table
            #         in the settings dialog.
            #         Be very careful which paths to include in this list to guarantee
            #         a tidy but safe uninstalll process !!!
            self.registerFilePaths(self.fileListForUninstall)

            ########################################################
            # Register a list of plugin paths that should be added to load this tool.
            # In almost all cases this is only a single path but for flexibility this allows
            # a list of paths to be added for a single tool
            if fileExt == '.gizmo':
                # if the downloaded file is a gizmo we need to know it's plugin path.
                self.registerPluginPaths([pluginPath])

                ########################################################
                # Register info to create the new menu item (if needed).
                # For gizmos we can just use the file name without the extension to use as the command
                nodeClass = os.path.splitext(os.path.basename(filePath))[0]
                
                # create the command to be executed from the menu to run this tool
                # for gizmos use createGizmo() instead of nuke.createNode() to enable the bakeGizmo feature
                menuCommand = "createGizmo('{}')".format(nodeClass)
    
                # store one or more menu commands along with a title for the menu command in a dictionary
                menuInfo = {'command':menuCommand,         # this will be executed by Nuke
                            'title':self.toolItem.title}   # this is the menu item title used in Nuke to execute the command
            else:
                # if the downloaded file is not a .gizmo file it's a .nk file
                # in that case it just needs to be loaded explicitly from it's location in the file system
                
                # create the command to be executed from the menu to run this tool
                # for .nk files we need to paste form the file with it's path.
                # to keep the repo portable make sure to only store relative paths though

                relPath = posixpath.relpath(filePath, self.repoLocation)

                menuCommand = "nuke.nodePaste(NKPD_getRepoPath('{}'))".format(relPath)
                # store one or more menu commands along with a title for the menu command in a dictionary
                menuInfo = {'command':menuCommand,         # this will be executed by Nuke
                            'title':self.toolItem.title}   # this is the menu item title used in Nuke to execute the command
                

            # register the menuInfo dictionary
            # note thet this is a list, so you can add any number of commands for a given tool
            self.registerMenuCommands([menuInfo])          

        else:
            # raise IOError if processor cannot properly deal with the downloaded file
            # this will trigger an info message for the user to install the file manually
            raise IOError