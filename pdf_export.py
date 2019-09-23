import powerfactory # Importieren des DigSilent Powerfactory Moduls
import os
import datetime as dt
import time

# Powerfactory-Objekte festlegen
app = powerfactory.GetApplication() # Application-Objekt
script = app.GetCurrentScript() # Aktives Powerfactory-Skript-Objekt

# KLASSEN
class ExportFile:

        def  __init__(self, page, path, prefix, suffix, filetype):
                self.page = page # Page-Objekt von Powerfactory
                self.path = path # ExportPath-Eingabe des Skripts
                self.prefix = prefix
                self.suffix = suffix
                self.filetype = filetype

        # Funktion zur Erstellung des Dateinamens ohne Erweiterung
        def GetFileName(self):
                __date = dt.datetime.now()
                if self.suffix == 1:
                        return self.prefix + '_' + self.page.loc_name + '_' + \
                                __date.strftime('%Y%m%d')
                else:
                        return self.prefix + '_' + self.page.loc_name
                        

        def GetFullFileName(self):
                return os.path.join(self.path, self.GetFileName() + self.filetype)

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
        # Wenn angegebener appad ungültig oder nicht vorhanden ist, ...
        if os.path.exists(strPath) == False or strPath == '':
                # Leeren String zurück geben
                return ''
        else:
                # übergebenen appad als String zurück geben
                return strPath


def CheckCalctype(intCalctype):
        # Wenn die Benutzereingabe der Variable 'CalcType'
        # außerhalb des Bereiches 0-3 liegt, wird 'Falsch' zurück gegeben
        if intCalctype in range(0, 4):
                return True
        else:
                return False

def SetDateSuffix(intDatesuffix):
        # Wenn die Benutzereingabe der Variable 'DateSuffix' nicht 1 ist
        # wird selbige auf 0 gesetzt und eine Warnmeldung ausgegeben
        if (intDatesuffix != 0 and intDatesuffix != 1):
                script.SetInputParameterInt('DateSuffix', 0)
                app.PrintWarn('Falsche Eingabe für das DateSuffix! ' + \
                        'Wert wurde auf 0 zurückgesetzt!')
        return script.DateSuffix


prefixtuple = ('Base', 'Ldfl', 'Shc3', 'Shc1') # Tuple-Collection der Präfixe
exportfiletype = '.pdf' # Dateiendung festlegen

files = [] # Leere Liste für Exportfile-Klassen erstellen
errormsgs = [] # Leere Liste für Fehlermeldungen erstellen

# Ausgabefenster von Powerfactory löschen
app.ClearOutputWindow()

# Informationsausgabe
strInfoHeader = " STARTE PDF-EXPORT: "
app.PrintInfo(strInfoHeader.center(50, "#"))
# ---> "############### STARTE PDF-EXPORT: ###############"

# 1.) Überprüfen ob der im Skript angegebene appad existiert
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
datesuffix = SetDateSuffix(int(script.DateSuffix))


# 4.)
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

# Alle in der Grafiksammlung vorhandenen Netzgrafiken durchlaufen
# an Klasse 'ExportFile' übergeben und selbige in einer Liste
# zwischenspeichern 
for page in pages:
        ef = ExportFile(page, exportpath, prefixtuple[calctypeindex], datesuffix, exportfiletype)
        files.append(ef)

exportssuccess = 0
exportsfailure = 0
for file in files:
        p = file.page
        pn = p.GetAttribute('loc_name') # oder auch nur page.loc_name falls Attribut bekannt
        fn = file.GetFullFileName()

        app.PrintPlain('Exportiere Grafik ' + pn)

        if file.FileExists() == True:
                if file.delete_file() == False: #Wenn die Datei nicht gelöscht werden kann, Fehlermeldung ausgeben
                        exportsfailure += 1

        
        if desktop.Show(p) == 0: # Grafik aufrufen und anzeigen
                app.SetGraphicUpdate(1)
                app.SetGuiUpdateEnabled(1)


                # QUELLE: https://www.digsilent.de/en/faq-reader-powerfactory/how-do-i-export-a-currently-shown-plot-using-python.html
                # Aufruf des CommonWrite-Objektes von Powerfactory
                comWr = app.GetFromStudyCase('ComWr')
                comWr.iopt_rd = 'pdf' # z.B.: "bmp" for *.bmp
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






