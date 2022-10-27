# DigSilent Version 2019
# Python (!!!) Version 3.7 (!!!) muss installiert sein
# Copyright 2019 Christian Vavru

import powerfactory # Importieren des DigSilent Powerfactory Moduls
import os
import datetime as dt
import time

# Powerfactory-Objekte festlegen
app = powerfactory.GetApplication() # Application-Objekt
script = app.GetCurrentScript() # Aktives Powerfactory-Skript-Objekt

# KLASSEN
class ExportFileData:

        def  __init__(self, page, pgnumber, path, prefix, filesuffix, datesuffix, filetype):
                self.page = page # Page-Objekt (*.SetDeskpage) der Grafiksammlung von Powerfactory
                self.pagenumber = str(pgnumber).zfill(3) # Reihenfolge-Nr des Page-Objektes der Grafiksammlung
                self.path = path # ExportPath-Eingabe des Skripts
                self.prefix = prefix
                self.filesuffix = filesuffix
                self.datesuffix = datesuffix
                self.filetype = filetype

        # Funktion zur Erstellung des Dateinamens ohne Erweiterung
        def GetFileName(self):
                # Seitennummer gem. der Reihenfolgennummerierung (order) der Grafiksammlung
                # 3-Stellig mit führenden Nullen
                __pagenumber = str(self.pagenumber)
                if (__pagenumber != ''):
                        __pagenumber = __pagenumber + '_'
                else:
                         __pagenumber = ''

                return self.prefix + '_' + \
                        __pagenumber + self.page.loc_name +  \
                        self.filesuffix + \
                        self.datesuffix + \
                        '.' + self.filetype            

        def GetFullFileName(self):
                return os.path.join(self.path, self.GetFileName()) # + self.filetype)

        def FileExists(self):
                return os.path.isfile(self.GetFullFileName())

        def delete_file(self):
                ffn = self.GetFullFileName()
                try: # Versuche die vorhandenen Datei zu löschen
                        os.remove(ffn)
                except: #Wenn die Datei nicht gelöscht werden kann, Fehlermeldung ausgeben
                        app.PrintWarn('Export fehlgeschlagen: ' + str(ffn))
                        return False
                return True



# FUNKTIONEN / DEFINITITIONEN
def CheckExportPath(strPath):
        # Wenn angegebener Pfad ungültig oder nicht vorhanden ist, ...
        if os.path.exists(strPath) == False or strPath == '':
                # Leeren String zurück geben
                return ''
        else:
                # übergebenen Pfad als String zurück geben
                return strPath


def CheckCalctype(intCalctype):
        # Wenn die Benutzereingabe der Variable 'CalcType'
        # außerhalb des Bereiches 0-3 liegt, wird 'Falsch' zurück gegeben
        if intCalctype in range(0, 4):
                return True
        else:
                return False


def CheckScriptDateSuffix(intDatesuffix):
        # Wenn die Benutzereingabe der Variable 'DateSuffix' nicht 1 ist
        # wird selbige auf 0 gesetzt und eine Warnmeldung ausgegeben
        if (intDatesuffix != 0 and intDatesuffix != 1):
                script.SetInputParameterInt('DateSuffix', 0)
                app.PrintWarn('Falsche Eingabe für das DateSuffix! ' + \
                        'Wert wurde auf 0 zurückgesetzt!')
        return script.DateSuffix

def SetDateSuffix(intDatesuffix):
        if (intDatesuffix == 1):
                exportdate = dt.datetime.now()
                return '_' + exportdate.strftime('%Y%m%d')
        return ''


prefixtuple = ('Base', 'Ldfl', 'Shc3', 'Shc1') # Tuple-Collection der Präfixe

exportfiletype = 'svg' # Dateiendung festlegen (!!! OHNE PUNKT !!!)

files = [] # Leere Liste für Exportfile-Klassen erstellen
errormsgs = [] # Leere Liste für Fehlermeldungen erstellen

# Ausgabefenster von Powerfactory löschen
# app.ClearOutputWindow()

# Informationsausgabe
strInfoHeader = " STARTE SVG-EXPORT: "
app.PrintInfo(strInfoHeader.center(50, "#"))


# ---> "############### STARTE SVG-EXPORT: ###############"

# 1.) Überprüfen ob der im Skript angegebene Pfad existiert
exportpath = CheckExportPath(str(script.ExportPath))
if exportpath == '':
        errormsgs.append('Fehlender oder falscher Exportpfad! Skript-Abbruch!')

# 2.) Überprüfen der Berechnungsart
calctypeindex = int(script.CalcType)
calctype = CheckCalctype(int(script.CalcType))
if calctype == False:
        errormsgs.append('Die Variable CalcType liegt ausserhalb ' + \
                'des gültigen Bereiches (0-3)! Skript-Abbruch!')
else:
        calctypeindex = int(script.CalcType)

# 3.) Überprüfen ob Datum als Datei-Suffix hinzugefügt werden soll
checkdatesuffix = CheckScriptDateSuffix(int(script.DateSuffix))
datesuffix = SetDateSuffix(checkdatesuffix)

# 4.) File-Suffix
# ------ für spätere Erweiterung ------
#filesuffix = SetFileSuffixText(str(script.FileSuffix))
filesuffix = ''

# 5.)
# Überprüfen ob Fehlermeldungen in der Liste errormsgs vorhanden sind
# Wenn Ja, dann Fehlermeldungen anzeigen und Skript beenden
if len(errormsgs) > 0:
        for errmsg in errormsgs:
                app.PrintError(errmsg)
        exit()

# Grafiksammlung des aktiven Berechnungsfalles in Objekt laden
desktop = app.GetGraphicsBoard()

# Wenn Desktop-Objekt (aktives GraphicsBoard) leer ist, dann Skript verlassen
if not (desktop):
        exit()

# Inhalt des GraphicsBoard-Objektes in neue Liste 'pages' laden
pages = desktop.GetContents()

# Alle in der Grafiksammlung vorhandenen Netzgrafiken (*.SetDeskpage) durchlaufen,
# an Klasse 'ExportFileData' übergeben und selbige in einer Liste
# zwischenspeichern 
for page in pages: 
        # Überprüfen, ob es sich um ein 'SetDeskpage'-Objekt handelt und
        # die Eigenschaft 'Seite wiederverwerten' Wahr ist
        strObj = page.GetClassName()
        if (strObj == 'SetDeskpage' and page.iRecycl == True):
                diag = page.pGrph
                pagenr = page.order
                efd = ExportFileData(page, pagenr, exportpath, prefixtuple[calctypeindex], filesuffix, datesuffix, exportfiletype)

                files.append(efd)

exportssuccess = 0
exportsfailure = 0
for filedata in files:
        p = filedata.page #page-Objekt aus der Klasse auslesen
        pn = p.GetAttribute('loc_name') # oder auch nur page.loc_name falls Attribut bekannt
        fn = filedata.GetFullFileName()

        app.PrintPlain('Exportiere Grafik ' + pn)

        if filedata.FileExists() == True:
                if filedata.delete_file() == False: #Wenn die Datei nicht gelöscht werden kann, Fehlermeldung ausgeben
                        exportsfailure += 1

        
        if desktop.Show(p) == 0: # Grafik aufrufen und anzeigen
                app.SetGraphicUpdate(1)
                app.SetGuiUpdateEnabled(1)


                # QUELLE: https://www.digsilent.de/en/faq-reader-powerfactory/how-do-i-export-a-graphic-using-python.html
                # Aufruf des CommonWrite-Objektes von Powerfactory
                comWr = app.GetFromStudyCase('ComWr')
                comWr.iopt_rd = exportfiletype # z.B.: "bmp" for *.bmp
                comWr.iopt_nonly = 0  # to write a file
                comWr.iopt_savas = 0  # 0 = Write to path, 1 = Open Save Dialog
                comWr.f = str(fn) # Filename

                # Exportbereich festlegen
                # 0 = Gesamtes Diagramm
                # 1 = Gesamtes Diagramm mit aktuellen Zoomeinstellungen
                # 2 = Sichtbaren Bereich
                comWr.iRange = 0
                comWr.dpi = 1000 # Auflösung der Ausgabe in DPI
                comWr.Execute()

                exportssuccess += 1

if exportsfailure > 0:
        app.PrintWarn("Erfolgreiche Exporte: " + str(exportssuccess) + \
                ", Fehlgeschlagene Exporte: " + str(exportsfailure))
else:
        app.PrintInfo("Erfolgreiche Exporte: " + str(exportssuccess) + \
                ", Fehlgeschlagene Exporte: " + str(exportsfailure))
