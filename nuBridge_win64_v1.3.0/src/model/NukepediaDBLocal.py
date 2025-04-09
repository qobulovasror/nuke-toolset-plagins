import logging
import os
import random
import shutil
import sqlite3
import time


from Qt import QtCore
from .NKPD import ToolModel
from .NKPD import FileItem
from .NKPD import ToolItemProxy
from compat import uni_str

logger = logging.getLogger('Nukepedia.NukepediaDBLocal')
MAX_TRIES = 10 #number of attempts to write to database if a database lock is encountered

class NPDBLocal(QtCore.QObject):
    """Object to deal with local sqlite database (installed tools)
    """

    TABLE_NAME_TOOLS = 'nuBridgeTools'
    TABLE_NAME_VERSIONS = 'nuBridgeVersions'
    TABLE_NAME_FILE_PATHS = 'nuBridgeFilePaths' # collects all file paths that need to be managed when removing a tool or moving/copying the repository
    TABLE_NAME_PLUGIN_PATHS = 'nuBridgePluginPaths' # collects all plugin paths required for a given tool version
    TABLE_NAME_MENU_CMDS = 'nuBridgeMenuCmds' # collects all plugin paths required for a given tool version
    MAX_BACKUPS = 10

    def __init__(self, dbFile):
        super(NPDBLocal, self).__init__()
        self.dbFile = dbFile
        parentDir = os.path.dirname(self.dbFile)
        self.bakDir = '/'.join([parentDir, '.db_backups'])
        if not os.path.isdir(parentDir):
            os.makedirs(parentDir)
        self.connection = sqlite3.connect(self.dbFile)

        # The below seems to be a lazy adapter.
        # I should probably get rid of this as it's not the
        # real model we need to use for handling local tools        
        self.model = ToolModel()
        self.model.setTools(self.getTools())
        self.destroyed.connect(self.__close)

    def __stubbornExec(self, sqlCmd, *sqlArgs):
        '''Run sqlCmd. In case of database lock error kep trying up to MAX_TRIES'''
    
        cursor = self.connection.cursor()
        curTry = 0
        e = BaseException('This exception is a placeholder and should never be raised')
        while curTry < MAX_TRIES:
            try:
                with self.connection: # using context manager to ensure connection commits
                    cursor.execute(sqlCmd, sqlArgs)
                    return cursor
            except sqlite3.OperationalError as e:
                if str(e) == 'database is locked':
                    curTry += 1
                    logger.warning('\t\tLOCK FOUND - trying again ({})'.format(curTry))
                    continue            
                else:
                    raise e
    
        # if MAX_TRIES was reached raise the exception
        raise e

    def __addColumn(self, column, cType, tableName):
        '''insert a column into the dabase with the given cType (e.g.: "TEXT", "INTEGER", "TIMEDATE")'''
        #cursor = self.connection.cursor()
        try:
            # test if column exists
            #cursor.execute('SELECT %s FROM %s' % (column, tableName))
            self.__stubbornExec('SELECT %s FROM %s' % (column, tableName))
            
        except:
            #cursor.execute('ALTER TABLE %s ADD COLUMN %s %s' % (tableName, column, cType))
            self.__stubbornExec('ALTER TABLE %s ADD COLUMN %s %s' % (tableName, column, cType))
        #cursor.close()
        #self.connection.commit()

    def __close(self):
        print("BYE")

    def __deleteOldBackups(self):
        '''Delete ld backups to ony ever keep MAX_BACKUPS'''
        # entries are files with sqlite extension
        entries = [os.path.join(self.bakDir, f) for f in os.listdir(self.bakDir) if os.path.isfile(os.path.join(self.bakDir, f)) and os.path.splitext(f)[-1] == '.sqlite']
        # sort them by date
        entries.sort(key=lambda x: os.stat(os.path.join(self.bakDir, x)).st_mtime)
        # delete the oldest ones
        oldFilePaths = entries[:-self.MAX_BACKUPS]
        for f in oldFilePaths:
            os.remove(f)

    def addPathForVersion(self, id_, path, pathType):
        '''Add a file path or plugin path to the given version'''

        #cursor = self.connection.cursor()
        tableNameLookup = {'filePath':self.TABLE_NAME_FILE_PATHS,
                           'pluginPath':self.TABLE_NAME_PLUGIN_PATHS}
        logger.debug('INSERT INTO {} ({}) VALUES {}'.format(tableNameLookup[pathType], # table name
                                                                'versionID,{}'.format(pathType), # column names
                                                                (id_, path)))
        try:
            #cursor.execute('INSERT INTO {} ({},{}) VALUES (?,?)'.format(tableNameLookup[pathType],
                                                                        #'versionID',
                                                                        #pathType),
                           #(id_, path)
                           #)
            self.__stubbornExec('INSERT INTO {} ({},{}) VALUES (?,?)'.format(tableNameLookup[pathType],
                                                                        'versionID',
                                                                        pathType),
                           id_, path)
        except sqlite3.IntegrityError:
            # record already exists so ignore it
            pass
        #finally:
            #cursor.close()
            #self.connection.commit()

    def addMenuCommandsForVersion(self, id_, cmdStringList):
        '''Add menu commands for the given version id'''

        #cursor = self.connection.cursor()
        for cmdString in cmdStringList:
            logger.debug('adding cmd string {} to {}'.format(cmdString, id_))
            try:
                #print 'adding cmd string {} to {}'.format(cmdString, id_)
                #cursor.execute('INSERT INTO {} ({},{}) VALUES (?,?)'.format(self.TABLE_NAME_MENU_CMDS,
                                                                            #'versionID',
                                                                            #'menuCmd'),
                               #(id_, cmdString)
                               #)
                self.__stubbornExec('INSERT INTO {} ({},{}) VALUES (?,?)'.format(self.TABLE_NAME_MENU_CMDS,
                                                                                        'versionID',
                                                                                        'menuCmd'),
                                           id_, cmdString
                                           )                
            except sqlite3.IntegrityError:
                # record already exists so ignore it
                pass
        #cursor.close()
        #self.connection.commit()

    def backup(self):
        '''
        Create time stamped backup of the current database file
        '''
        with self.connection:
            # Lock database before making a backup
            self.__stubbornExec('begin immediate')
            # Make new backup file
            dbName, dbExt = os.path.splitext(os.path.basename(self.dbFile))
            timeStamp = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
            randomValue = random.randint(1000,9999)
            dbBakFile = '/'.join([self.bakDir, '{}_{}_{}{}'.format(dbName, timeStamp, randomValue, dbExt)])
            if not os.path.isdir(self.bakDir):
                os.makedirs(self.bakDir)
            shutil.copyfile(self.dbFile, dbBakFile)
            # Unlock database
            self.connection.rollback()

        self.__deleteOldBackups()

    def createTables(self):
        '''Create all required database tables in dbFile. Create dbFile if it doesn't exist.'''

        logger.debug('*** creating database tables')
        #cursor = self.connection.cursor()

        tableFieldDict = {self.TABLE_NAME_TOOLS:['id INTEGER PRIMARY KEY'],
                          self.TABLE_NAME_VERSIONS:['id INTEGER PRIMARY KEY', 'isActive INTEGER', 'gizmoToGroup INTEGER'],
                          self.TABLE_NAME_FILE_PATHS:['id INTEGER PRIMARY KEY', 'versionID INTEGER', 'filePath VARCHAR(255)', 'UNIQUE (versionID, filePath)'],
                          self.TABLE_NAME_PLUGIN_PATHS:['id INTEGER PRIMARY KEY', 'versionID INTEGER', 'pluginPath VARCHAR(255)', 'UNIQUE (versionID, pluginPath)'],
                          self.TABLE_NAME_MENU_CMDS:['id INTEGER PRIMARY KEY', 'versionID INTEGER', 'menuCmd VARCHAR(255)', 'UNIQUE (versionID, menuCmd)'],}

        for tableName, columns in iter(tableFieldDict.items()):
            self.__stubbornExec('CREATE TABLE IF NOT EXISTS %s (%s)' % (tableName, ','.join(columns)))
            #try:
                ##cursor.execute('CREATE TABLE %s (%s)' % (tableName, ','.join(columns)))
                #self.__stubbornExec('CREATE TABLE %s (%s)' % (tableName, ','.join(columns)))
            #except sqlite3.OperationalError as e:
                #if str(e).endswith('already exists'):
                    #pass
                #else:
                    #raise
            #finally:
                #cursor.close()
                #self.connection.commit()

    def getDBAttrs(self, tableName, id_, *columns):
        '''Returns the value for the columns for record with id_ in tableName'''

        cursor = self.connection.cursor()
        #cursor.execute('''SELECT {} FROM {} where `id` == ?'''.format(','.join(columns), tableName), (id_,))
        #cursor.close()
        cursor = self.__stubbornExec('''SELECT {} FROM {} where `id` == ?'''.format(','.join(columns), tableName), id_)
        result = cursor.fetchall()[0][0]
        cursor.close()
        return result
        
    def getBakeGizmo(self, versionID):
        '''Check if gizmo should be reated as a group'''
        #import nuke
        #nuke.tprint('database bake stuff: {}'.format(result))
        
        try:
            return bool(int(self.getDBAttrs(self.TABLE_NAME_VERSIONS, versionID, 'gizmoToGroup')))
        except TypeError:
            # if data is Null of other type that can't be converted to bool
            return False

    def getBakeGizmoByPath(self, gizmoPath):
        pathDict = dict(self.getPathsWithID('pluginPath'))
        gizmoDirPath = os.path.dirname(gizmoPath)
        if gizmoDirPath in pathDict:
            return self.getBakeGizmo(pathDict[gizmoDirPath])
        
    def getMenuCmds(self):
        '''
        Return all menu commands for active tools items found in the local database so that the Nukepedia menu
        can be built on the fly with it
        '''

        logger.debug('retrieving menu commands from local database')
        logger.debug('opening local database connection to {}'.format(self.dbFile))
        cursor = self.connection.cursor()
        try:
            #cursor.execute('''SELECT menuCmd FROM {} where `versionID` IN (SELECT id FROM {} where `isActive` == 1)'''.format(self.TABLE_NAME_MENU_CMDS,
                                                                                                                             #self.TABLE_NAME_VERSIONS))
            result = self.__stubbornExec('''SELECT menuCmd FROM {} where `versionID` IN (SELECT id FROM {} where `isActive` == 1)'''.format(self.TABLE_NAME_MENU_CMDS,
                                                                                                                             self.TABLE_NAME_VERSIONS))
        except sqlite3.OperationalError as e:
            if str(e).startswith('no such table'):
                # this happens when there is no local database yet
                logger.debug('no database table found yet')
                return []
            # suppress any other exception so that Nuke can start but log it
            logger.critical('database error: {}'.format(e))
            return []
        #menuCmds = [i[0] for i in cursor.fetchall()]
        #cursor.close()
        menuCmds = [i[0] for i in result]
        return menuCmds
      
    def getPaths(self, pathType, id_=None):
        '''
        Get and return a list of all plugin paths for active file versions.
        If id_ is not None return a list of plugin paths only for the respective version id
        '''
        return [i[0] for i in self.getPathsWithID(pathType, id_)]

    def getPathsWithID(self, pathType, id_=None):
        '''
        Get list of tuples of all plugin paths for active file versions.
        If id_ is not None return a list of plugin paths only for the respective version id
        The return value is a list of tuples that contain the path and the version ID for each given id
        '''

        pathTypeLookup = {'pluginPath':self.TABLE_NAME_PLUGIN_PATHS,
                          'filePath':self.TABLE_NAME_FILE_PATHS}

        cursor = self.connection.cursor()
        try:
            if not id_:
                # get all plugin paths
                #cursor.execute('''SELECT {},{} FROM {} where `versionID` IN (SELECT id FROM {} where `isActive` == 1)'''.format(pathType,
                                                                                                                                #'versionID',
                                                                                                                             #pathTypeLookup[pathType],
                                                                                                                             #self.TABLE_NAME_VERSIONS))
                cursor = self.__stubbornExec('''SELECT {},{} FROM {} where `versionID` IN (SELECT id FROM {} where `isActive` == 1)'''.format(pathType,
                                                                                                                                            'versionID',
                                                                                                                                            pathTypeLookup[pathType],
                                                                                                                                         self.TABLE_NAME_VERSIONS))

            else:
                # get plugin paths for given version id only
                #cursor.execute('''SELECT {},{} FROM {} where `versionID` == ?'''.format(pathType,
                                                                                     #'versionID',
                                                                                     #pathTypeLookup[pathType]), (id_,))
                cursor = self.__stubbornExec('''SELECT {},{} FROM {} where `versionID` == ?'''.format(pathType,
                                                                                     'versionID',
                                                                                     pathTypeLookup[pathType]),
                                                 id_)

            pathWithID = [i for i in cursor.fetchall()]
        except sqlite3.OperationalError as e:
            if str(e).startswith('no such table'):
                # nothing has been installed, so the tables don't exist yet
                return []
            else:
                raise e
        finally:
            cursor.close()

        # if the init.py ever changes the way it finds the DB file the below needs to be updated
        rootPath = os.path.dirname(self.dbFile)
        return [(os.path.join(rootPath, p[0]), p[1]) for p in pathWithID]


    def getToolItems(self, activeOnly=False):
        '''
        Return a list of ToolProxyItems that represent the currently installed files in the local database.
        if activeOnly = True, only files are returned that have their "isActive" flag set to 1 in the nuBridgeFiles table.
        '''

        #cursor = self.connection.cursor()
        try:
            #cursor.execute('SELECT * FROM {}'.format(self.TABLE_NAME_VERSIONS))
            cursor = self.__stubbornExec('SELECT * FROM {}'.format(self.TABLE_NAME_VERSIONS))
        except sqlite3.OperationalError:
            # this happens when there is no local database yet
            return {}
        columns = [i[0] for i in cursor.description]
        proxyItems = []
        for toolItem in self.model.getTools():
            if activeOnly:
                # get active tool files (i.e. with isActive=1)
                #cursor.execute('SELECT * FROM {} WHERE toolID=? AND isActive=1'.format(self.TABLE_NAME_VERSIONS), (toolItem.id_,))
                cursor = self.__stubbornExec('SELECT * FROM {} WHERE toolID=? AND isActive=1'.format(self.TABLE_NAME_VERSIONS), toolItem.id_)
            else:
                # get all the tools files (i.e. versions and platforms)
                #cursor.execute('SELECT * FROM {} WHERE toolID=?'.format(self.TABLE_NAME_VERSIONS), (toolItem.id_,))
                cursor = self.__stubbornExec('SELECT * FROM {} WHERE toolID=?'.format(self.TABLE_NAME_VERSIONS), toolItem.id_)

            for row in cursor:
                # create one proxy instance per row in the file table
                fileData = dict(zip(columns, row))
                logger.debug('*** file data: {}'.format(fileData))
                fileItem = FileItem(fileData)
                proxyItem = ToolItemProxy(toolItem)
                proxyItem.activeFile = fileItem
                proxyItem.isActive = bool(fileData['isActive'])
                proxyItem.bakeGizmo = bool(fileData['gizmoToGroup'])
                proxyItem.downloadPath = fileData['downloadPath']
                proxyItem.pluginPaths = self.getPaths('pluginPath', fileData['id'])
                proxyItem.filePaths = self.getPaths('filePath', fileData['id'])
                proxyItem.versionID = row[0] # add the unique id for the version to the tool item, so it can be used for removing it later

                #try:
                    #proxyItem.localPath = fileData['localPath']
                #except KeyError:
                    ## localPath may not exist yet. The new installer logic registers the tool in the database
                    ## right after download, then an appropriate processor for the respective file is responsible
                    ## for processing it and adding info like the local path to the local database
                    #pass
                proxyItems.append(proxyItem)
        cursor.close()
        return proxyItems

    def getTools(self):
        '''This needs to return the same format as the NPDB class so they can both be used by the same model'''

        #cursor = self.connection.cursor()
        try:
            #cursor.execute('SELECT * FROM %s' % self.TABLE_NAME_TOOLS)
            cursor = self.__stubbornExec('SELECT * FROM {}'.format(self.TABLE_NAME_TOOLS))
        except sqlite3.OperationalError:
            # this happens when there is no local database yet
            return {}
        toolList = cursor.fetchall()
        columnHeaders = [info[0] for info in cursor.description]
        cursor.close()

        toolDict = {}
        for toolTuple in toolList:
            # TO DO: CONVERT STR TO OBJECTS AND COMPARE OUTPUT TO NukepediaDB output
            tool = dict(zip(columnHeaders, toolTuple))
            for date in ('submitdate', 'filedate'):
                tool[date] = time.strptime(tool[date], '%Y-%m-%d %H:%M:%S')
            try:
                toolDict[tool['toolType']].append(tool)
            except KeyError:
                toolDict[tool['toolType']] = [tool]
        return toolDict

    def insertTool(self, tool):
        '''Add NKPD.ToolProxyItem object to database. This replaces existing rows'''

        logger.debug(' *** INSERTING: {}'.format(tool))

        # LOOKUP TO CONVERT FROM PYTHON TYPE TO SQLITE TYPE
        typeLookup = {int:'INTEGER',
                      time.struct_time:'TIMEDATE',
                      float:'REAL'}
        #cursor = self.connection.cursor()

        # make a copy of the incoming data so we don't accidentally change it
        toolData = tool.toolData.copy()
        fileData = tool.downloadInfo.copy()

        logger.debug('inserting tool data: {}'.format(toolData))
        # add additional info for local database that doens't exist in tool object
        # create the db field with an empty value here so that an appropriate processor
        # can add the correct value after processing the tool
        fileData['toolID'] = tool.id_
        #fileData['menuCmd'] = ''
    
        # remove data we don't need in the local database
        del toolData['files'] # list of online siblings not needed
        del toolData['updateAvailable']   # this is calculated dynamically and would be confusing in the local database
        del toolData['hasBeenDownloaded'] # this is calculated dynamically and would be confusing in the local database
        
        # prep incompatible types
        toolData['nukeVersions'] = str(toolData['nukeVersions'])

        # add columns for file data
        for k, v in iter(fileData.items()):
            self.__addColumn(k, typeLookup.get(type(v), 'VARCHAR(32)'), self.TABLE_NAME_VERSIONS)

        # add columns for tool data
        for k, v in iter(toolData.items()):
            # add column to table (in case it doesn't exist yet). If data type is unknown default to TEXT
            self.__addColumn(k, typeLookup.get(type(v), 'VARCHAR(32)'), self.TABLE_NAME_TOOLS)
            if isinstance(v, time.struct_time):
                # convert time objects to readable string
                toolData[k] = time.strftime('%Y-%m-%d %H:%M:%S', v)
                continue
            if not isinstance(v, int):
                toolData[k] = uni_str(v)

        # insert tool
        cursor = self.__stubbornExec('SELECT * FROM {} WHERE id = ?'.format(self.TABLE_NAME_TOOLS), tool.id_)
        if cursor.fetchall():
            # delete existing db entry so we can insert an up-to-date entry
            self.__stubbornExec('DELETE FROM {} WHERE id = ?'.format(self.TABLE_NAME_TOOLS), tool.id_)
       
        # insert version if it doens't exist yet
        cursor = self.__stubbornExec('SELECT id FROM {} WHERE toolID = ? AND platform = ? AND version = ?'.format(self.TABLE_NAME_VERSIONS),
                            tool.id_,
                            fileData['platform'],
                            fileData['version'])
        existingFileIDs = [row for row in cursor] # this should only yield one match, otherwise we have a redundant file in the database and need to clean up manually
        if existingFileIDs:
            # delete existing db entries to avoid redundant entries
            if len(existingFileIDs) > 1:
                raise IOError("There is more than one entry for the same file in the local database ({}). Please report to admin@nukepedia.com".format(existingFileIDs))
            fileID = existingFileIDs[0][0] # keep track of existing ID so we can re-use it when re-creating the entry (IMPORTANT FOR DEPENDENT TABLE RECORDS!!)
            self.__stubbornExec('DELETE FROM {} WHERE ID=?'.format(self.TABLE_NAME_VERSIONS), fileID)
 
        try:
            fileData['id'] = fileID
        except UnboundLocalError:
            # first time this file is being entered into the database, so there is no existing id
            pass

        # (re)add tool entry
        exec_text_tool = 'INSERT INTO {} ({}) VALUES ({})'.format(self.TABLE_NAME_TOOLS,
                                                                      ','.join(toolData.keys()),
                                                              ','.join(['?'] * len(toolData.values())))
        self.__stubbornExec(exec_text_tool, *toolData.values())

        # (re)add file entry
        exec_text_file = 'INSERT INTO {} ({}) VALUES ({})'.format(self.TABLE_NAME_VERSIONS,
                                                                      ','.join(fileData.keys()),
                                                              ','.join(['?'] * len(fileData.values())))
        cursor = self.__stubbornExec(exec_text_file, *fileData.values())
        cursor.close()
        self.connection.commit()
        return cursor.lastrowid

    def setToolVersionAsActive(self, fileID):
        '''
        Set the entry with id=fileID in the file table to active and all it's peers to inactive.
        This will dictate which vesion of a tool is being loaded in Nuke
        '''

        # set file to be active
        cursor = self.connection.cursor()
        logger.debug('activating file id {}'.format(fileID))
        #cursor.execute('UPDATE {} SET isActive=? WHERE id=?'.format(self.TABLE_NAME_VERSIONS), (1, fileID))
        self.__stubbornExec('UPDATE {} SET isActive=? WHERE id=?'.format(self.TABLE_NAME_VERSIONS),
                            1, fileID)
        # get toolID for file
        #cursor.execute('SELECT toolID FROM {} WHERE id=?'.format(self.TABLE_NAME_VERSIONS), (fileID,))
        cursor = self.__stubbornExec('SELECT toolID FROM {} WHERE id=?'.format(self.TABLE_NAME_VERSIONS), fileID)
        toolID = cursor.fetchone()[0]
        # find siblings
        #cursor.execute('SELECT id FROM {} WHERE toolID=? AND NOT id=?'.format(self.TABLE_NAME_VERSIONS), (toolID, fileID))
        cursor = self.__stubbornExec('SELECT id FROM {} WHERE toolID=? AND NOT id=?'.format(self.TABLE_NAME_VERSIONS),
                                     toolID,
                                     fileID)

        # set siblings to be inactive
        for siblingAttrs in cursor.fetchall():
            siblingsID = siblingAttrs[0]
            logger.debug('sibling id is ()'.format(siblingsID))
            logger.debug('deactivating {}'.format(siblingsID))
            #cursor.execute('UPDATE {} SET isActive=? WHERE id=?'.format(self.TABLE_NAME_VERSIONS), (0, siblingsID))
            self.__stubbornExec('UPDATE {} SET isActive=? WHERE id=?'.format(self.TABLE_NAME_VERSIONS),
                                0,
                                siblingsID)
        self.connection.commit()
        cursor.close()
        
    def removeTool(self, tool):
        '''Remove all records that point to the toolID from all tables'''

        #cursor = self.connection.cursor()
        for table in (self.TABLE_NAME_FILE_PATHS, self.TABLE_NAME_MENU_CMDS, self.TABLE_NAME_PLUGIN_PATHS):
           
            # remove plugin paths, file paths and menu commands for given version
            #cursor.execute('DELETE FROM {} WHERE versionID = ?'.format(table), (tool.versionID,))
            self.__stubbornExec('DELETE FROM {} WHERE versionID = ?'.format(table), tool.versionID)

        # remove version entry
        #cursor.execute('DELETE FROM {} WHERE id = ?'.format(self.TABLE_NAME_VERSIONS), (tool.versionID,))
        self.__stubbornExec('DELETE FROM {} WHERE id = ?'.format(self.TABLE_NAME_VERSIONS), tool.versionID)

        # check if parent tool has any other versions remaining, if not delete it as well
        toolIsOrphaned = False
        #cursor.execute('SELECT * FROM {} WHERE toolID = ?'.format(self.TABLE_NAME_VERSIONS), (tool.id_,))
        result = self.__stubbornExec('SELECT * FROM {} WHERE toolID = ?'.format(self.TABLE_NAME_VERSIONS), tool.id_)
        if not result:
            #cursor.execute('DELETE FROM {} WHERE id = ?'.format(self.TABLE_NAME_TOOLS), (tool.id_,))
            self.__stubbornExec('DELETE FROM {} WHERE id = ?'.format(self.TABLE_NAME_TOOLS), tool.id_)
            toolIsOrphaned = True

        #cursor.close()
        self.connection.commit()
        return toolIsOrphaned

    def updateActiveState(self, id_, value):
        '''Update the "active" state for the incoming file id in the local database'''

        self.updateDBAttr(self.TABLE_NAME_VERSIONS, id_, isActive=value)

    def updateGizmoBakeAttr(self, id_, value):
        '''Change the gizmoToGroup value for the given file id'''
        
        self.updateDBAttr(self.TABLE_NAME_VERSIONS, id_, gizmoToGroup=value)

    def updateDBAttr(self, tableName, id_, **kwargs):
        if len(kwargs) < 1:
            raise ValueError("At least one keyword argument must be provided")
        cursor = self.connection.cursor()
        for attr, value in iter(kwargs.items()):
            #cursor.execute('UPDATE {} SET {}=? WHERE id=?'.format(tableName, attr), (value, id_))
            self.__stubbornExec('UPDATE {} SET {}=? WHERE id=?'.format(tableName, attr),
                                value,
                                id_)
        #cursor.close()
        self.connection.commit()

if __name__ == '__main__':
    import  sys
    from Qt import QtGui
    #app = QtWidgets.QApplication([])
    import os
    #import common

    #dbFile = os.path.join(common.NKPDSettings().repoLocation, common.NKPD_DB_NAME)
    #connection = sqlite3.connect(dbFile)
    #cursor = connection.cursor()
    #cursor.execute('SELECT menuCmd FROM {} where menuCmd IS NOT "" AND isActive = 1'.format(NPDBLocal.TABLE_NAME_VERSIONS))


    #import os    
    #import sys
    #from PySide.QtCore import QtCore.Qt
    #from NukepediaDB import NPDB
    #from NKPD import ToolModelLocal
    #from view.Dialogs import SettingsDialog
    ##from data import getTestData
    ##from NKPD import ToolItem
    #projectRoot = os.path.sep.join(sys.path[0].split(os.path.sep)[:-1])
    #sys.path.append(projectRoot)
    #from controller import common
    #from PySide import QtGui
    
    #app = QtWidgets.QApplication([])
    ### get tools online
    ##npdb = NPDB()
    ##model = ToolModel()
    ##toolDict = npdb.getTools()
    ##for onlineContainer, onlineToolList in iter(toolDict.items()):
        ##for onlineTool in onlineToolList:
            ##onlineTool['updateAvailable'] = False
    ##model.setTools(toolDict)

    #def changeActiveFileItem(item):
        #'''
        #Change the active state for the incoming item.
        #If it's being activated, make sure siblings (rows with same toolD) are unchecked.
        #Update the database for all siblings.
        #'''
        #model = item.model()
        #fileIdColumn = model.headerLabels.index('file id')
        #toolIdColumn = model.headerLabels.index('tool id')
        #toolId = model.item(item.row(), toolIdColumn).text()
        #fileId = model.item(item.row(), fileIdColumn).text()
        #npdbLocal.updateActiveState(fileId, bool(item.checkState()))

        #if item.checkState() == QtCore.Qt.Unchecked:
            ## if a file is deactivated don't do anything to the other checkboxes
            ## just update the database
            #return

        ## item is being checked, so let's uncheck all siblings and update the database accordingly
        #for r in xrange(model.rowCount()):
            #if r == item.row():
                ## don't do anything in the current row
                #continue
            #if model.item(r, toolIdColumn).text() == toolId:
                #sibling = model.item(r, item.column())
                #sibling.setCheckState(QtCore.Qt.Unchecked) # handle check state
                #siblingID = model.item(r, fileIdColumn).text()
                #npdbLocal.updateActiveState(siblingID, bool(sibling.checkState())) # update database


    ############ TEST LOCAL TOOL VIEW
    ## set tools in local database
    npdbLocal = NPDBLocal(os.path.join('/Users/frank/Nukepedia', 'NukepediaDB.sqlite'))
    print(npdbLocal)

    #gizmoFilePath = '/Users/frank/Nukepedia/gizmos/ITransform_96/1.5/ITransform_1_5.gizmo'
    #print npdbLocal.getPathWithID(pathType='pluginPath')
    #print npdbLocal.getPaths(pathType='pluginPath')
    #print npdbLocal.getBakeGizmoByPath(gizmoFilePath)
    #if os.path.dirname(gizmoFilePath) in npdbLocal.getPaths(pathType='pluginPath'):
        #print 'yes'
    
    #npdbLocal.addPathForVersion(1, u'/Users/frank/Nukepedia/gizmos/ITransform_96/1.5/ITransform.gizmo', pathType='filePath')
    #npdbLocal.addPathForVersion(1, u'/Users/frank/Nukepedia/gizmos/ITransform_96/1.5', pathType='pluginPath')

    
    #localToolProxyList = npdbLocal.getToolItems()
    #modelLocal = ToolModelLocal()
    #modelLocal.setTools(localToolProxyList)
    #modelLocal.itemChanged.connect(changeActiveFileItem)

    #settingsDialog = SettingsDialog()
    #settingsDialog.toolsTab.tableView.setModelAndTweak(modelLocal)
    ##settingsDialog.toolsTab.tableView.uninstallAction.triggered.connect(self.__uninstallTools)
    ##settingsDialog.toolsTab.tableView.moveAction.triggered.connect(self.__moveTools)
    ##settingsDialog.toolsTab.tableView.updateAction.triggered.connect(self.__updateTools)

    #settingsDialog.show()
    #settingsDialog.raise_()

    ############ END TEST LOCAL TOOL VIEW    

    #npdbLocal.createTables()

    #print model.getTools()
    
    #i = 0

    #for toolItem in tools:
        ##print '+' * 20
        #p = ToolItemProxy(toolItem)
        #if toolItem.id_ != 96:
            #continue        
        #for f in toolItem.files:
            #i += 1
            #print f
            #p.activeFile = f
            #fileID = npdbLocal.insertTool(p, '/tmp/fakePath/gizmos/%s' % (p.fileName))
            #npdbLocal.setToolVersionAsActive(fileID)
            #break


    ### GET LOCAL TOOLS
    #tools = npdbLocal.getTools()
    #print 'LOCAL'
    #for container, toolList in iter(tools.items()):
        #for tool in toolList:
            #if tool['id'] != 885:
                #continue
            #print tool['filetitle']
            #print type(tool['filetitle'])
            ##menuCmd = 'nuke.menu("Nodes").addCommand("Nukepedia/%(filetitle)s", lambda: nuke.createNode("%(filetitle)s"))' % tool
            ##print menu



    #sys.exit(app.exec_())